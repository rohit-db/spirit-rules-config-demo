"""
Mock data for local development without a Lakebase database.
Provides sample rule headers, lines, and audit log entries.
"""

import copy
import json
import uuid
from datetime import date, datetime
from typing import Optional

# ---------------------------------------------------------------------------
# UUIDs (fixed so relationships are consistent)
# ---------------------------------------------------------------------------
HEADER_IDS = [
    "a1b2c3d4-1111-4000-a000-000000000001",
    "a1b2c3d4-2222-4000-a000-000000000002",
    "a1b2c3d4-3333-4000-a000-000000000003",
    "a1b2c3d4-4444-4000-a000-000000000004",
]

LINE_IDS = [
    # Header 1 lines
    "b1b2c3d4-0001-4000-a000-000000000001",
    "b1b2c3d4-0002-4000-a000-000000000002",
    "b1b2c3d4-0003-4000-a000-000000000003",
    "b1b2c3d4-0004-4000-a000-000000000004",
    # Header 2 lines
    "b1b2c3d4-0005-4000-a000-000000000005",
    "b1b2c3d4-0006-4000-a000-000000000006",
    "b1b2c3d4-0007-4000-a000-000000000007",
    # Header 3 lines
    "b1b2c3d4-0008-4000-a000-000000000008",
    "b1b2c3d4-0009-4000-a000-000000000009",
    # Header 4 lines
    "b1b2c3d4-0010-4000-a000-000000000010",
    "b1b2c3d4-0011-4000-a000-000000000011",
    "b1b2c3d4-0012-4000-a000-000000000012",
]

AUDIT_IDS = [
    "c1b2c3d4-0001-4000-a000-000000000001",
    "c1b2c3d4-0002-4000-a000-000000000002",
    "c1b2c3d4-0003-4000-a000-000000000003",
    "c1b2c3d4-0004-4000-a000-000000000004",
    "c1b2c3d4-0005-4000-a000-000000000005",
    "c1b2c3d4-0006-4000-a000-000000000006",
]

NOW = datetime(2026, 1, 15, 10, 30, 0)
EARLIER = datetime(2026, 1, 10, 8, 0, 0)

# ---------------------------------------------------------------------------
# Rule Headers
# ---------------------------------------------------------------------------
MOCK_HEADERS: list[dict] = [
    {
        "id": HEADER_IDS[0],
        "start_date": "2026-01-01",
        "end_date": "2026-03-31",
        "cost_category": "Fuel",
        "rate_category": "Domestic",
        "category": "Operating",
        "account_group": "Fuel-DOM",
        "groupby_costcenter": True,
        "groupby_account": False,
        "fixed_variable_pct_split": 0.65,
        "fixed_variable_type": "variable",
        "status": "draft",
        "version": 1,
        "cloned_from_id": None,
        "created_by": "local-dev",
        "created_at": EARLIER.isoformat(),
        "updated_at": NOW.isoformat(),
    },
    {
        "id": HEADER_IDS[1],
        "start_date": "2026-01-01",
        "end_date": "2026-03-31",
        "cost_category": "Crew",
        "rate_category": "Domestic",
        "category": "Operating",
        "account_group": "Crew-DOM",
        "groupby_costcenter": False,
        "groupby_account": True,
        "fixed_variable_pct_split": 0.80,
        "fixed_variable_type": "fixed",
        "status": "approved",
        "version": 2,
        "cloned_from_id": None,
        "created_by": "local-dev",
        "created_at": EARLIER.isoformat(),
        "updated_at": NOW.isoformat(),
    },
    {
        "id": HEADER_IDS[2],
        "start_date": "2025-10-01",
        "end_date": "2025-12-31",
        "cost_category": "Maintenance",
        "rate_category": "International",
        "category": "Non-Operating",
        "account_group": "MX-INT",
        "groupby_costcenter": True,
        "groupby_account": True,
        "fixed_variable_pct_split": 0.50,
        "fixed_variable_type": "mixed",
        "status": "archived",
        "version": 3,
        "cloned_from_id": None,
        "created_by": "local-dev",
        "created_at": datetime(2025, 9, 1, 9, 0, 0).isoformat(),
        "updated_at": datetime(2025, 12, 15, 14, 0, 0).isoformat(),
    },
    {
        "id": HEADER_IDS[3],
        "start_date": "2026-01-01",
        "end_date": "2026-03-31",
        "cost_category": "Fuel",
        "rate_category": "International",
        "category": "Operating",
        "account_group": "Fuel-INT",
        "groupby_costcenter": False,
        "groupby_account": False,
        "fixed_variable_pct_split": 0.70,
        "fixed_variable_type": "variable",
        "status": "in_review",
        "version": 1,
        "cloned_from_id": None,
        "created_by": "local-dev",
        "created_at": EARLIER.isoformat(),
        "updated_at": NOW.isoformat(),
    },
]

# ---------------------------------------------------------------------------
# Rule Lines
# ---------------------------------------------------------------------------
MOCK_LINES: list[dict] = [
    # --- Header 1 (Fuel/Domestic draft) - 4 lines ---
    {
        "id": LINE_IDS[0],
        "header_id": HEADER_IDS[0],
        "account_number": "5100-01",
        "account_name": "Fuel - Jet A Domestic",
        "stat_type": "ASMs",
        "proration_rate": 0.35,
        "effective_date": "2026-01-01",
        "notes": "Main domestic fuel allocation",
        "sort_order": 0,
        "created_at": EARLIER.isoformat(),
        "updated_at": NOW.isoformat(),
    },
    {
        "id": LINE_IDS[1],
        "header_id": HEADER_IDS[0],
        "account_number": "5100-02",
        "account_name": "Fuel - Jet A Regional",
        "stat_type": "Departures",
        "proration_rate": 0.25,
        "effective_date": "2026-01-01",
        "notes": "Regional hub departures",
        "sort_order": 1,
        "created_at": EARLIER.isoformat(),
        "updated_at": NOW.isoformat(),
    },
    {
        "id": LINE_IDS[2],
        "header_id": HEADER_IDS[0],
        "account_number": "5100-03",
        "account_name": "Fuel - Into-Plane Fees",
        "stat_type": "Block_Hours",
        "proration_rate": 0.22,
        "effective_date": "2026-01-01",
        "notes": "Into-plane handling charges",
        "sort_order": 2,
        "created_at": EARLIER.isoformat(),
        "updated_at": NOW.isoformat(),
    },
    {
        "id": LINE_IDS[3],
        "header_id": HEADER_IDS[0],
        "account_number": "5100-04",
        "account_name": "Fuel - Taxes & Surcharges",
        "stat_type": "RPMs",
        "proration_rate": 0.18,
        "effective_date": "2026-01-01",
        "notes": "Federal and state fuel taxes",
        "sort_order": 3,
        "created_at": EARLIER.isoformat(),
        "updated_at": NOW.isoformat(),
    },
    # --- Header 2 (Crew/Domestic approved) - 3 lines ---
    {
        "id": LINE_IDS[4],
        "header_id": HEADER_IDS[1],
        "account_number": "5200-01",
        "account_name": "Crew - Pilot Salaries",
        "stat_type": "Block_Hours",
        "proration_rate": 0.45,
        "effective_date": "2026-01-01",
        "notes": "Captain and FO salaries",
        "sort_order": 0,
        "created_at": EARLIER.isoformat(),
        "updated_at": NOW.isoformat(),
    },
    {
        "id": LINE_IDS[5],
        "header_id": HEADER_IDS[1],
        "account_number": "5200-02",
        "account_name": "Crew - Flight Attendants",
        "stat_type": "Departures",
        "proration_rate": 0.30,
        "effective_date": "2026-01-01",
        "notes": "FA crew costs by departure",
        "sort_order": 1,
        "created_at": EARLIER.isoformat(),
        "updated_at": NOW.isoformat(),
    },
    {
        "id": LINE_IDS[6],
        "header_id": HEADER_IDS[1],
        "account_number": "5200-03",
        "account_name": "Crew - Per Diem & Hotels",
        "stat_type": "Block_Hours",
        "proration_rate": 0.25,
        "effective_date": "2026-01-01",
        "notes": "Layover and per diem expenses",
        "sort_order": 2,
        "created_at": EARLIER.isoformat(),
        "updated_at": NOW.isoformat(),
    },
    # --- Header 3 (Maintenance/International archived) - 2 lines ---
    {
        "id": LINE_IDS[7],
        "header_id": HEADER_IDS[2],
        "account_number": "5300-01",
        "account_name": "MX - Airframe Heavy Checks",
        "stat_type": "Block_Hours",
        "proration_rate": 0.55,
        "effective_date": "2025-10-01",
        "notes": "C-checks and D-checks intl fleet",
        "sort_order": 0,
        "created_at": datetime(2025, 9, 1, 9, 0, 0).isoformat(),
        "updated_at": datetime(2025, 12, 15, 14, 0, 0).isoformat(),
    },
    {
        "id": LINE_IDS[8],
        "header_id": HEADER_IDS[2],
        "account_number": "5300-02",
        "account_name": "MX - Engine Overhauls",
        "stat_type": "RPMs",
        "proration_rate": 0.45,
        "effective_date": "2025-10-01",
        "notes": "Engine shop visit reserves",
        "sort_order": 1,
        "created_at": datetime(2025, 9, 1, 9, 0, 0).isoformat(),
        "updated_at": datetime(2025, 12, 15, 14, 0, 0).isoformat(),
    },
    # --- Header 4 (Fuel/International in_review) - 3 lines ---
    {
        "id": LINE_IDS[9],
        "header_id": HEADER_IDS[3],
        "account_number": "5100-10",
        "account_name": "Fuel - Jet A International",
        "stat_type": "ASMs",
        "proration_rate": 0.40,
        "effective_date": "2026-01-01",
        "notes": "Long-haul intl fuel allocation",
        "sort_order": 0,
        "created_at": EARLIER.isoformat(),
        "updated_at": NOW.isoformat(),
    },
    {
        "id": LINE_IDS[10],
        "header_id": HEADER_IDS[3],
        "account_number": "5100-11",
        "account_name": "Fuel - Caribbean Routes",
        "stat_type": "RPMs",
        "proration_rate": 0.35,
        "effective_date": "2026-01-01",
        "notes": "Caribbean and Latin America routes",
        "sort_order": 1,
        "created_at": EARLIER.isoformat(),
        "updated_at": NOW.isoformat(),
    },
    {
        "id": LINE_IDS[11],
        "header_id": HEADER_IDS[3],
        "account_number": "5100-12",
        "account_name": "Fuel - Intl Taxes & Fees",
        "stat_type": "Departures",
        "proration_rate": 0.25,
        "effective_date": "2026-01-01",
        "notes": "International fuel surcharges",
        "sort_order": 2,
        "created_at": EARLIER.isoformat(),
        "updated_at": NOW.isoformat(),
    },
]

# ---------------------------------------------------------------------------
# Audit Log
# ---------------------------------------------------------------------------
MOCK_AUDIT: list[dict] = [
    {
        "id": AUDIT_IDS[0],
        "header_id": HEADER_IDS[0],
        "action": "create",
        "changed_by": "local-dev",
        "changed_at": EARLIER.isoformat(),
        "old_values": None,
        "new_values": {"cost_category": "Fuel", "rate_category": "Domestic"},
    },
    {
        "id": AUDIT_IDS[1],
        "header_id": HEADER_IDS[0],
        "action": "add_lines",
        "changed_by": "local-dev",
        "changed_at": NOW.isoformat(),
        "old_values": None,
        "new_values": {"lines_added": 4},
    },
    {
        "id": AUDIT_IDS[2],
        "header_id": HEADER_IDS[1],
        "action": "create",
        "changed_by": "local-dev",
        "changed_at": EARLIER.isoformat(),
        "old_values": None,
        "new_values": {"cost_category": "Crew", "rate_category": "Domestic"},
    },
    {
        "id": AUDIT_IDS[3],
        "header_id": HEADER_IDS[1],
        "action": "status_change",
        "changed_by": "local-dev",
        "changed_at": NOW.isoformat(),
        "old_values": {"status": "in_review"},
        "new_values": {"status": "approved"},
    },
    {
        "id": AUDIT_IDS[4],
        "header_id": HEADER_IDS[2],
        "action": "create",
        "changed_by": "local-dev",
        "changed_at": datetime(2025, 9, 1, 9, 0, 0).isoformat(),
        "old_values": None,
        "new_values": {"cost_category": "Maintenance", "rate_category": "International"},
    },
    {
        "id": AUDIT_IDS[5],
        "header_id": HEADER_IDS[3],
        "action": "status_change",
        "changed_by": "local-dev",
        "changed_at": NOW.isoformat(),
        "old_values": {"status": "draft"},
        "new_values": {"status": "in_review"},
    },
]

# ---------------------------------------------------------------------------
# In-memory mutable store (deep-copied from constants on init)
# ---------------------------------------------------------------------------

class MockStore:
    """In-memory data store for mock mode.  Mutated by mock route handlers."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.headers: list[dict] = copy.deepcopy(MOCK_HEADERS)
        self.lines: list[dict] = copy.deepcopy(MOCK_LINES)
        self.audit: list[dict] = copy.deepcopy(MOCK_AUDIT)

    # --- Headers ---

    def list_headers(
        self,
        status: Optional[str] = None,
        cost_category: Optional[str] = None,
        search: Optional[str] = None,
    ) -> list[dict]:
        results = list(self.headers)
        if status:
            results = [h for h in results if h["status"] == status]
        if cost_category:
            results = [h for h in results if h["cost_category"] == cost_category]
        if search:
            s = search.lower()
            results = [
                h for h in results
                if s in (h.get("cost_category") or "").lower()
                or s in (h.get("rate_category") or "").lower()
                or s in (h.get("category") or "").lower()
                or s in (h.get("account_group") or "").lower()
            ]
        results.sort(key=lambda h: h["updated_at"], reverse=True)
        return results

    def get_header(self, rule_id: str) -> Optional[dict]:
        for h in self.headers:
            if h["id"] == rule_id:
                return h
        return None

    def create_header(self, data: dict) -> dict:
        new_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        header = {
            "id": new_id,
            "start_date": data["start_date"],
            "end_date": data["end_date"],
            "cost_category": data["cost_category"],
            "rate_category": data.get("rate_category"),
            "category": data.get("category"),
            "account_group": data.get("account_group"),
            "groupby_costcenter": data.get("groupby_costcenter", False),
            "groupby_account": data.get("groupby_account", False),
            "fixed_variable_pct_split": data.get("fixed_variable_pct_split"),
            "fixed_variable_type": data.get("fixed_variable_type"),
            "status": "draft",
            "version": 1,
            "cloned_from_id": None,
            "created_by": "local-dev",
            "created_at": now,
            "updated_at": now,
        }
        self.headers.append(header)
        self._add_audit(new_id, "create", new_values=data)
        return header

    def update_header(self, rule_id: str, updates: dict) -> Optional[dict]:
        header = self.get_header(rule_id)
        if header is None:
            return None
        old_values = {k: header.get(k) for k in updates}
        for k, v in updates.items():
            if v is not None:
                header[k] = v
        header["updated_at"] = datetime.utcnow().isoformat()
        self._add_audit(rule_id, "update", old_values=old_values, new_values=updates)
        return header

    def delete_header(self, rule_id: str) -> bool:
        header = self.get_header(rule_id)
        if header is None:
            return False
        self._add_audit(rule_id, "delete", old_values={"id": rule_id})
        self.headers = [h for h in self.headers if h["id"] != rule_id]
        self.lines = [l for l in self.lines if l["header_id"] != rule_id]
        return True

    def clone_header(self, rule_id: str) -> Optional[dict]:
        source = self.get_header(rule_id)
        if source is None:
            return None
        new_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        cloned = copy.deepcopy(source)
        cloned["id"] = new_id
        cloned["status"] = "draft"
        cloned["version"] = source["version"] + 1
        cloned["cloned_from_id"] = rule_id
        cloned["created_at"] = now
        cloned["updated_at"] = now
        self.headers.append(cloned)

        # Clone lines
        source_lines = [l for l in self.lines if l["header_id"] == rule_id]
        for sl in source_lines:
            new_line = copy.deepcopy(sl)
            new_line["id"] = str(uuid.uuid4())
            new_line["header_id"] = new_id
            new_line["created_at"] = now
            new_line["updated_at"] = now
            self.lines.append(new_line)

        self._add_audit(
            new_id, "clone",
            old_values={"cloned_from": rule_id},
            new_values={"id": new_id, "version": cloned["version"]},
        )
        return cloned

    def update_status(self, rule_id: str, new_status: str) -> Optional[dict]:
        header = self.get_header(rule_id)
        if header is None:
            return None
        valid = {
            "draft": ["in_review"],
            "in_review": ["approved", "draft"],
            "approved": ["archived"],
        }
        allowed = valid.get(header["status"], [])
        if new_status not in allowed:
            return None  # invalid transition
        old_status = header["status"]
        header["status"] = new_status
        header["updated_at"] = datetime.utcnow().isoformat()
        self._add_audit(
            rule_id, "status_change",
            old_values={"status": old_status},
            new_values={"status": new_status},
        )
        return header

    # --- Lines ---

    def list_lines(self, header_id: str) -> list[dict]:
        return sorted(
            [l for l in self.lines if l["header_id"] == header_id],
            key=lambda l: (l["sort_order"], l["created_at"]),
        )

    def create_line(self, header_id: str, data: dict) -> dict:
        new_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        line = {
            "id": new_id,
            "header_id": header_id,
            "account_number": data["account_number"],
            "account_name": data.get("account_name"),
            "stat_type": data["stat_type"],
            "proration_rate": data["proration_rate"],
            "effective_date": data.get("effective_date"),
            "notes": data.get("notes"),
            "sort_order": data.get("sort_order", 0),
            "created_at": now,
            "updated_at": now,
        }
        self.lines.append(line)
        self._add_audit(header_id, "add_lines", new_values=data)
        return line

    def update_line(self, header_id: str, line_id: str, updates: dict) -> Optional[dict]:
        for line in self.lines:
            if line["id"] == line_id and line["header_id"] == header_id:
                old_values = {k: line.get(k) for k in updates}
                for k, v in updates.items():
                    if v is not None:
                        line[k] = v
                line["updated_at"] = datetime.utcnow().isoformat()
                self._add_audit(
                    header_id, "update_line",
                    old_values={"line_id": line_id, **old_values},
                    new_values={"line_id": line_id, **updates},
                )
                return line
        return None

    def delete_line(self, header_id: str, line_id: str) -> bool:
        for i, line in enumerate(self.lines):
            if line["id"] == line_id and line["header_id"] == header_id:
                self._add_audit(header_id, "delete_line", old_values=line)
                self.lines.pop(i)
                return True
        return False

    # --- Audit ---

    def get_audit(self, header_id: str) -> list[dict]:
        entries = [a for a in self.audit if a["header_id"] == header_id]
        entries.sort(key=lambda a: a["changed_at"], reverse=True)
        return entries

    def _add_audit(self, header_id, action, old_values=None, new_values=None):
        self.audit.append({
            "id": str(uuid.uuid4()),
            "header_id": header_id,
            "action": action,
            "changed_by": "local-dev",
            "changed_at": datetime.utcnow().isoformat(),
            "old_values": old_values,
            "new_values": new_values,
        })


# Singleton
mock_store = MockStore()
