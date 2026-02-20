import json
import logging
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from server.db import db
from server.config import get_current_user
from server.mock_data import mock_store
from server.models import (
    RuleHeaderCreate,
    RuleHeaderUpdate,
    RuleHeaderResponse,
    StatusUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rules", tags=["rules"])

# Valid status transitions: (from_status) -> [allowed to_statuses]
VALID_TRANSITIONS = {
    "draft": ["in_review"],
    "in_review": ["approved", "draft"],
    "approved": ["archived"],
}


def _row_to_header(row) -> dict:
    """Convert an asyncpg Record to a dict suitable for RuleHeaderResponse."""
    d = dict(row)
    # Decimal -> float for JSON serialisation
    if d.get("fixed_variable_pct_split") is not None:
        d["fixed_variable_pct_split"] = float(d["fixed_variable_pct_split"])
    return d


async def _get_pool_or_none():
    """Return the database pool, or None if not configured (mock mode)."""
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


# ---------- LIST ----------

@router.get("", response_model=None)
async def list_rules(
    status: Optional[str] = Query(None),
    cost_category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    pool = await _get_pool_or_none()

    if pool is None:
        # Mock mode
        return mock_store.list_headers(status=status, cost_category=cost_category, search=search)

    clauses: list[str] = []
    params: list = []
    idx = 1

    if status:
        clauses.append(f"status = ${idx}")
        params.append(status)
        idx += 1
    if cost_category:
        clauses.append(f"cost_category = ${idx}")
        params.append(cost_category)
        idx += 1
    if search:
        clauses.append(
            f"(cost_category ILIKE ${idx} OR rate_category ILIKE ${idx} "
            f"OR category ILIKE ${idx} OR account_group ILIKE ${idx})"
        )
        params.append(f"%{search}%")
        idx += 1

    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    query = f"SELECT * FROM rule_headers{where} ORDER BY updated_at DESC"

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)

    return [RuleHeaderResponse(**_row_to_header(r)) for r in rows]


# ---------- GET ----------

@router.get("/{rule_id}", response_model=None)
async def get_rule(rule_id: str):
    pool = await _get_pool_or_none()

    if pool is None:
        header = mock_store.get_header(rule_id)
        if header is None:
            raise HTTPException(status_code=404, detail="Rule not found")
        return header

    uid = UUID(rule_id)
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM rule_headers WHERE id = $1", uid)
    if row is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    return RuleHeaderResponse(**_row_to_header(row))


# ---------- CREATE ----------

@router.post("", response_model=None, status_code=201)
async def create_rule(body: RuleHeaderCreate):
    pool = await _get_pool_or_none()

    if pool is None:
        data = body.model_dump(mode="json")
        return mock_store.create_header(data)

    user = get_current_user()

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO rule_headers (
                start_date, end_date, cost_category, rate_category, category,
                account_group, groupby_costcenter, groupby_account,
                fixed_variable_pct_split, fixed_variable_type, created_by
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
            RETURNING *
            """,
            body.start_date,
            body.end_date,
            body.cost_category,
            body.rate_category,
            body.category,
            body.account_group,
            body.groupby_costcenter,
            body.groupby_account,
            body.fixed_variable_pct_split,
            body.fixed_variable_type,
            user,
        )
        await _audit(conn, row["id"], "create", new_values=body.model_dump(mode="json"))

    return RuleHeaderResponse(**_row_to_header(row))


# ---------- UPDATE ----------

@router.put("/{rule_id}", response_model=None)
async def update_rule(rule_id: str, body: RuleHeaderUpdate):
    pool = await _get_pool_or_none()

    if pool is None:
        header = mock_store.get_header(rule_id)
        if header is None:
            raise HTTPException(status_code=404, detail="Rule not found")
        if header["status"] != "draft":
            raise HTTPException(status_code=400, detail="Only draft rules can be edited")
        updates = body.model_dump(exclude_none=True)
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        result = mock_store.update_header(rule_id, updates)
        return result

    uid = UUID(rule_id)
    async with pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT * FROM rule_headers WHERE id = $1", uid)
        if existing is None:
            raise HTTPException(status_code=404, detail="Rule not found")
        if existing["status"] != "draft":
            raise HTTPException(status_code=400, detail="Only draft rules can be edited")

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
        set_clauses.append(f"updated_at = NOW()")

        query = (
            f"UPDATE rule_headers SET {', '.join(set_clauses)} "
            f"WHERE id = ${idx} RETURNING *"
        )
        params.append(uid)

        row = await conn.fetchrow(query, *params)

        old_values = {k: _serialize(existing[k]) for k in updates}
        new_values = {k: _serialize(row[k]) for k in updates}
        await _audit(conn, uid, "update", old_values=old_values, new_values=new_values)

    return RuleHeaderResponse(**_row_to_header(row))


# ---------- DELETE ----------

@router.delete("/{rule_id}", status_code=204)
async def delete_rule(rule_id: str):
    pool = await _get_pool_or_none()

    if pool is None:
        if not mock_store.delete_header(rule_id):
            raise HTTPException(status_code=404, detail="Rule not found")
        return

    uid = UUID(rule_id)
    user = get_current_user()

    async with pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT * FROM rule_headers WHERE id = $1", uid)
        if existing is None:
            raise HTTPException(status_code=404, detail="Rule not found")

        await _audit(
            conn,
            uid,
            "delete",
            old_values=_row_to_serializable(existing),
        )
        await conn.execute("DELETE FROM rule_headers WHERE id = $1", uid)


# ---------- CLONE ----------

@router.post("/{rule_id}/clone", response_model=None, status_code=201)
async def clone_rule(rule_id: str):
    pool = await _get_pool_or_none()

    if pool is None:
        result = mock_store.clone_header(rule_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Source rule not found")
        return result

    uid = UUID(rule_id)
    user = get_current_user()

    async with pool.acquire() as conn:
        source = await conn.fetchrow("SELECT * FROM rule_headers WHERE id = $1", uid)
        if source is None:
            raise HTTPException(status_code=404, detail="Source rule not found")

        new_version = source["version"] + 1

        new_header = await conn.fetchrow(
            """
            INSERT INTO rule_headers (
                start_date, end_date, cost_category, rate_category, category,
                account_group, groupby_costcenter, groupby_account,
                fixed_variable_pct_split, fixed_variable_type,
                status, version, cloned_from_id, created_by
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,'draft',$11,$12,$13)
            RETURNING *
            """,
            source["start_date"],
            source["end_date"],
            source["cost_category"],
            source["rate_category"],
            source["category"],
            source["account_group"],
            source["groupby_costcenter"],
            source["groupby_account"],
            source["fixed_variable_pct_split"],
            source["fixed_variable_type"],
            new_version,
            uid,
            user,
        )

        # Copy rule lines
        lines = await conn.fetch("SELECT * FROM rule_lines WHERE header_id = $1", uid)
        for line in lines:
            await conn.execute(
                """
                INSERT INTO rule_lines (
                    header_id, account_number, account_name, stat_type,
                    proration_rate, effective_date, notes, sort_order
                ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
                """,
                new_header["id"],
                line["account_number"],
                line["account_name"],
                line["stat_type"],
                line["proration_rate"],
                line["effective_date"],
                line["notes"],
                line["sort_order"],
            )

        await _audit(
            conn,
            new_header["id"],
            "clone",
            old_values={"cloned_from": str(uid)},
            new_values={"id": str(new_header["id"]), "version": new_version},
        )

    return RuleHeaderResponse(**_row_to_header(new_header))


# ---------- STATUS TRANSITION ----------

@router.put("/{rule_id}/status", response_model=None)
async def update_status(rule_id: str, body: StatusUpdate):
    pool = await _get_pool_or_none()

    if pool is None:
        result = mock_store.update_status(rule_id, body.status)
        if result is None:
            header = mock_store.get_header(rule_id)
            if header is None:
                raise HTTPException(status_code=404, detail="Rule not found")
            raise HTTPException(
                status_code=400,
                detail=f"Cannot transition from '{header['status']}' to '{body.status}'",
            )
        return result

    uid = UUID(rule_id)
    async with pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT * FROM rule_headers WHERE id = $1", uid)
        if existing is None:
            raise HTTPException(status_code=404, detail="Rule not found")

        current_status = existing["status"]
        new_status = body.status

        allowed = VALID_TRANSITIONS.get(current_status, [])
        if new_status not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot transition from '{current_status}' to '{new_status}'",
            )

        row = await conn.fetchrow(
            "UPDATE rule_headers SET status = $1, updated_at = NOW() WHERE id = $2 RETURNING *",
            new_status,
            uid,
        )

        await _audit(
            conn,
            uid,
            "status_change",
            old_values={"status": current_status},
            new_values={"status": new_status},
        )

    return RuleHeaderResponse(**_row_to_header(row))


# ---------- helpers ----------

def _serialize(val):
    """Make a value JSON-safe."""
    if val is None:
        return None
    if isinstance(val, (str, int, float, bool)):
        return val
    return str(val)


def _row_to_serializable(row) -> dict:
    return {k: _serialize(v) for k, v in dict(row).items()}
