import csv
import io
import json
import logging
from datetime import date
from typing import List, Optional, Union
from uuid import UUID

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse

from server.db import db
from server.config import get_current_user
from server.mock_data import mock_store
from server.models import RuleLineCreate, RuleLineUpdate, RuleLineResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rules", tags=["lines"])


# ---------- helpers ----------

async def _get_pool_or_none():
    pool = await db.get_pool()
    return pool


async def _audit(conn, header_id: UUID, action: str, old_values=None, new_values=None):
    user = get_current_user()
    await conn.execute(
        """
        INSERT INTO rule_audit_log (header_id, action, changed_by, old_values, new_values)
        VALUES ($1, $2, $3, $4, $5)
        """,
        header_id,
        action,
        user,
        json.dumps(old_values) if old_values else None,
        json.dumps(new_values) if new_values else None,
    )


async def _get_header_or_404(conn, rule_id: UUID):
    """Fetch a rule header or raise 404."""
    row = await conn.fetchrow("SELECT * FROM rule_headers WHERE id = $1", rule_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    return row


def _require_draft(header):
    """Raise 400 if the header is not in draft status."""
    if header["status"] != "draft":
        raise HTTPException(
            status_code=400, detail="Lines can only be modified on draft rules"
        )


def _serialize(val):
    """Make a value JSON-safe."""
    if val is None:
        return None
    if isinstance(val, (str, int, float, bool)):
        return val
    return str(val)


def _row_to_line(row) -> dict:
    """Convert an asyncpg Record to a dict suitable for RuleLineResponse."""
    d = dict(row)
    if d.get("proration_rate") is not None:
        d["proration_rate"] = float(d["proration_rate"])
    return d


def _row_to_serializable(row) -> dict:
    return {k: _serialize(v) for k, v in dict(row).items()}


# ---------- LIST LINES ----------

@router.get("/{rule_id}/lines", response_model=None)
async def list_lines(rule_id: str):
    """List all lines for a rule header, ordered by sort_order."""
    pool = await _get_pool_or_none()

    if pool is None:
        header = mock_store.get_header(rule_id)
        if header is None:
            raise HTTPException(status_code=404, detail="Rule not found")
        return mock_store.list_lines(rule_id)

    uid = UUID(rule_id)
    async with pool.acquire() as conn:
        await _get_header_or_404(conn, uid)
        rows = await conn.fetch(
            "SELECT * FROM rule_lines WHERE header_id = $1 ORDER BY sort_order, created_at",
            uid,
        )
    return [RuleLineResponse(**_row_to_line(r)) for r in rows]


# ---------- ADD LINES ----------

@router.post("/{rule_id}/lines", response_model=None, status_code=201)
async def add_lines(rule_id: str, body: Union[RuleLineCreate, List[RuleLineCreate]]):
    """Add one or more lines to a rule header. Header must be in draft status."""
    pool = await _get_pool_or_none()

    # Normalise to a list
    items: List[RuleLineCreate] = body if isinstance(body, list) else [body]

    if pool is None:
        header = mock_store.get_header(rule_id)
        if header is None:
            raise HTTPException(status_code=404, detail="Rule not found")
        if header["status"] != "draft":
            raise HTTPException(status_code=400, detail="Lines can only be modified on draft rules")
        created = []
        for item in items:
            data = item.model_dump(mode="json")
            line = mock_store.create_line(rule_id, data)
            created.append(line)
        return created

    uid = UUID(rule_id)
    async with pool.acquire() as conn:
        header = await _get_header_or_404(conn, uid)
        _require_draft(header)

        created_rows = []
        for item in items:
            row = await conn.fetchrow(
                """
                INSERT INTO rule_lines (
                    header_id, account_number, account_name, stat_type,
                    proration_rate, effective_date, notes, sort_order
                ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
                RETURNING *
                """,
                uid,
                item.account_number,
                item.account_name,
                item.stat_type,
                item.proration_rate,
                item.effective_date,
                item.notes,
                item.sort_order,
            )
            created_rows.append(row)

        await _audit(
            conn,
            uid,
            "add_lines",
            new_values=[
                line.model_dump(mode="json") for line in items
            ],
        )

    return [RuleLineResponse(**_row_to_line(r)) for r in created_rows]


# ---------- UPDATE LINE ----------

@router.put("/{rule_id}/lines/{line_id}", response_model=None)
async def update_line(rule_id: str, line_id: str, body: RuleLineUpdate):
    """Update a single line. Header must be in draft status."""
    pool = await _get_pool_or_none()

    if pool is None:
        header = mock_store.get_header(rule_id)
        if header is None:
            raise HTTPException(status_code=404, detail="Rule not found")
        if header["status"] != "draft":
            raise HTTPException(status_code=400, detail="Lines can only be modified on draft rules")
        updates = body.model_dump(exclude_none=True)
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        result = mock_store.update_line(rule_id, line_id, updates)
        if result is None:
            raise HTTPException(status_code=404, detail="Line not found")
        return result

    uid = UUID(rule_id)
    lid = UUID(line_id)
    async with pool.acquire() as conn:
        header = await _get_header_or_404(conn, uid)
        _require_draft(header)

        existing = await conn.fetchrow(
            "SELECT * FROM rule_lines WHERE id = $1 AND header_id = $2",
            lid,
            uid,
        )
        if existing is None:
            raise HTTPException(status_code=404, detail="Line not found")

        updates = body.model_dump(exclude_none=True)
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        set_clauses: list[str] = []
        params: list = []
        idx = 1
        for col, val in updates.items():
            set_clauses.append(f"{col} = ${idx}")
            params.append(val)
            idx += 1
        set_clauses.append("updated_at = NOW()")

        query = (
            f"UPDATE rule_lines SET {', '.join(set_clauses)} "
            f"WHERE id = ${idx} AND header_id = ${idx + 1} RETURNING *"
        )
        params.extend([lid, uid])

        row = await conn.fetchrow(query, *params)

        old_values = {k: _serialize(existing[k]) for k in updates}
        new_values = {k: _serialize(row[k]) for k in updates}
        await _audit(
            conn,
            uid,
            "update_line",
            old_values={"line_id": str(lid), **old_values},
            new_values={"line_id": str(lid), **new_values},
        )

    return RuleLineResponse(**_row_to_line(row))


# ---------- DELETE LINE ----------

@router.delete("/{rule_id}/lines/{line_id}", status_code=204)
async def delete_line(rule_id: str, line_id: str):
    """Delete a single line. Header must be in draft status."""
    pool = await _get_pool_or_none()

    if pool is None:
        header = mock_store.get_header(rule_id)
        if header is None:
            raise HTTPException(status_code=404, detail="Rule not found")
        if header["status"] != "draft":
            raise HTTPException(status_code=400, detail="Lines can only be modified on draft rules")
        if not mock_store.delete_line(rule_id, line_id):
            raise HTTPException(status_code=404, detail="Line not found")
        return

    uid = UUID(rule_id)
    lid = UUID(line_id)
    async with pool.acquire() as conn:
        header = await _get_header_or_404(conn, uid)
        _require_draft(header)

        existing = await conn.fetchrow(
            "SELECT * FROM rule_lines WHERE id = $1 AND header_id = $2",
            lid,
            uid,
        )
        if existing is None:
            raise HTTPException(status_code=404, detail="Line not found")

        await _audit(
            conn,
            uid,
            "delete_line",
            old_values=_row_to_serializable(existing),
        )
        await conn.execute(
            "DELETE FROM rule_lines WHERE id = $1 AND header_id = $2",
            lid,
            uid,
        )


# ---------- CSV IMPORT ----------

CSV_COLUMNS = [
    "account_number",
    "account_name",
    "stat_type",
    "proration_rate",
    "effective_date",
    "notes",
]


@router.post("/{rule_id}/import")
async def import_csv(rule_id: str, file: UploadFile = File(...)):
    """
    Import lines from a CSV file upload.
    Expected columns: account_number, account_name, stat_type, proration_rate, effective_date, notes.
    Header must be in draft status. Invalid rows are skipped and reported.
    """
    pool = await _get_pool_or_none()

    if pool is None:
        header = mock_store.get_header(rule_id)
        if header is None:
            raise HTTPException(status_code=404, detail="Rule not found")
        if header["status"] != "draft":
            raise HTTPException(status_code=400, detail="Lines can only be modified on draft rules")

        content = await file.read()
        text = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        imported = 0
        errors: list[dict] = []
        existing_lines = mock_store.list_lines(rule_id)
        sort_order = max((l["sort_order"] for l in existing_lines), default=-1) + 1

        for row_num, row in enumerate(reader, start=2):
            try:
                account_number = (row.get("account_number") or "").strip()
                if not account_number:
                    raise ValueError("account_number is required")
                stat_type = (row.get("stat_type") or "").strip()
                if not stat_type:
                    raise ValueError("stat_type is required")
                proration_rate_str = (row.get("proration_rate") or "").strip()
                if not proration_rate_str:
                    raise ValueError("proration_rate is required")
                proration_rate = float(proration_rate_str)
                account_name = (row.get("account_name") or "").strip() or None
                effective_date_str = (row.get("effective_date") or "").strip()
                effective_date = effective_date_str if effective_date_str else None
                notes = (row.get("notes") or "").strip() or None

                mock_store.create_line(rule_id, {
                    "account_number": account_number,
                    "account_name": account_name,
                    "stat_type": stat_type,
                    "proration_rate": proration_rate,
                    "effective_date": effective_date,
                    "notes": notes,
                    "sort_order": sort_order,
                })
                imported += 1
                sort_order += 1
            except Exception as exc:
                errors.append({"row": row_num, "error": str(exc)})

        return {"imported": imported, "errors": errors}

    uid = UUID(rule_id)
    async with pool.acquire() as conn:
        header = await _get_header_or_404(conn, uid)
        _require_draft(header)

        content = await file.read()
        text = content.decode("utf-8-sig")  # handle BOM from Excel exports
        reader = csv.DictReader(io.StringIO(text))

        imported = 0
        errors: list[dict] = []
        sort_order = 0

        # Get max existing sort_order so we append after existing lines
        max_sort = await conn.fetchval(
            "SELECT COALESCE(MAX(sort_order), -1) FROM rule_lines WHERE header_id = $1",
            uid,
        )
        sort_order = max_sort + 1

        for row_num, row in enumerate(reader, start=2):  # row 1 is header
            try:
                account_number = (row.get("account_number") or "").strip()
                if not account_number:
                    raise ValueError("account_number is required")

                stat_type = (row.get("stat_type") or "").strip()
                if not stat_type:
                    raise ValueError("stat_type is required")

                proration_rate_str = (row.get("proration_rate") or "").strip()
                if not proration_rate_str:
                    raise ValueError("proration_rate is required")
                proration_rate = float(proration_rate_str)

                account_name = (row.get("account_name") or "").strip() or None

                effective_date_str = (row.get("effective_date") or "").strip()
                effective_date = None
                if effective_date_str:
                    effective_date = date.fromisoformat(effective_date_str)

                notes = (row.get("notes") or "").strip() or None

                await conn.execute(
                    """
                    INSERT INTO rule_lines (
                        header_id, account_number, account_name, stat_type,
                        proration_rate, effective_date, notes, sort_order
                    ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
                    """,
                    uid,
                    account_number,
                    account_name,
                    stat_type,
                    proration_rate,
                    effective_date,
                    notes,
                    sort_order,
                )
                imported += 1
                sort_order += 1

            except Exception as exc:
                errors.append({"row": row_num, "error": str(exc)})

        await _audit(
            conn,
            uid,
            "import_csv",
            new_values={"imported": imported, "errors": len(errors), "filename": file.filename},
        )

    return {
        "imported": imported,
        "errors": errors,
    }


# ---------- CSV EXPORT ----------

@router.get("/{rule_id}/export")
async def export_csv(rule_id: str):
    """Export all lines for a rule header as a downloadable CSV file."""
    pool = await _get_pool_or_none()

    if pool is None:
        header = mock_store.get_header(rule_id)
        if header is None:
            raise HTTPException(status_code=404, detail="Rule not found")
        lines = mock_store.list_lines(rule_id)

        def generate():
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(CSV_COLUMNS)
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

            for line in lines:
                writer.writerow([
                    line["account_number"],
                    line["account_name"] or "",
                    line["stat_type"],
                    float(line["proration_rate"]),
                    str(line["effective_date"]) if line["effective_date"] else "",
                    line["notes"] or "",
                ])
                yield output.getvalue()
                output.seek(0)
                output.truncate(0)

        filename = f"rule_{rule_id}_lines.csv"
        return StreamingResponse(
            generate(),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    uid = UUID(rule_id)
    async with pool.acquire() as conn:
        header = await _get_header_or_404(conn, uid)

        rows = await conn.fetch(
            "SELECT * FROM rule_lines WHERE header_id = $1 ORDER BY sort_order, created_at",
            uid,
        )

    def generate():
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(CSV_COLUMNS)
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)

        for row in rows:
            writer.writerow([
                row["account_number"],
                row["account_name"] or "",
                row["stat_type"],
                float(row["proration_rate"]),
                str(row["effective_date"]) if row["effective_date"] else "",
                row["notes"] or "",
            ])
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

    filename = f"rule_{uid}_lines.csv"
    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------- AUDIT LOG ----------

@router.get("/{rule_id}/audit")
async def get_audit_log(rule_id: str):
    """Return audit log entries for a rule header, ordered by changed_at DESC."""
    pool = await _get_pool_or_none()

    if pool is None:
        header = mock_store.get_header(rule_id)
        if header is None:
            raise HTTPException(status_code=404, detail="Rule not found")
        return mock_store.get_audit(rule_id)

    uid = UUID(rule_id)
    async with pool.acquire() as conn:
        await _get_header_or_404(conn, uid)

        rows = await conn.fetch(
            """
            SELECT id, header_id, action, changed_by, changed_at, old_values, new_values
            FROM rule_audit_log
            WHERE header_id = $1
            ORDER BY changed_at DESC
            """,
            uid,
        )

    results = []
    for row in rows:
        entry = dict(row)
        # Parse JSONB fields back to Python objects for proper JSON response
        if entry["old_values"] is not None:
            entry["old_values"] = json.loads(entry["old_values"]) if isinstance(entry["old_values"], str) else entry["old_values"]
        if entry["new_values"] is not None:
            entry["new_values"] = json.loads(entry["new_values"]) if isinstance(entry["new_values"], str) else entry["new_values"]
        # Convert UUID to string for JSON serialisation
        entry["id"] = str(entry["id"])
        entry["header_id"] = str(entry["header_id"])
        entry["changed_at"] = entry["changed_at"].isoformat()
        results.append(entry)

    return results
