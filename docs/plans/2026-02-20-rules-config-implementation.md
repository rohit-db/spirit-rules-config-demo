# Spirit Airlines Rules Configuration App — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a master-detail React app for managing proration rate rules, deployed as a Databricks App with Lakebase backend.

**Architecture:** FastAPI backend serves a React SPA. Lakebase (Postgres) stores rule headers, child proration lines, and audit logs. Master-detail UI: left panel lists/filters rule headers, right panel shows header detail + editable lines table. Only draft rules are editable; approval workflow gates changes.

**Tech Stack:** React 18 + Vite + TypeScript, Chakra UI, TanStack Table, FastAPI, asyncpg, Lakebase, Databricks Apps

---

### Task 1: Scaffold Project Structure

**Files:**
- Create: `app.yaml`
- Create: `app.py`
- Create: `pyproject.toml`
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `server/__init__.py`
- Create: `server/config.py`
- Create: `server/db.py`
- Create: `frontend/` (via Vite scaffold)

**Step 1: Initialize git repo**

```bash
cd /Users/rohit.bhagwat/Desktop/spirit-rules-config
git init
```

**Step 2: Create .gitignore**

```gitignore
__pycache__/
*.py[cod]
.venv/
venv/
.env
node_modules/
npm-debug.log*
.idea/
.vscode/
*.swp
.databricks/
.DS_Store
```

**Step 3: Initialize Python backend with uv**

```bash
uv init
uv add fastapi uvicorn asyncpg pydantic python-multipart databricks-sdk
```

**Step 4: Create requirements.txt for deployment**

```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
asyncpg>=0.29.0
pydantic>=2.0.0
python-multipart>=0.0.9
databricks-sdk>=0.30.0
```

**Step 5: Create app.yaml**

```yaml
command:
  - "python"
  - "-m"
  - "uvicorn"
  - "app:app"
  - "--host"
  - "0.0.0.0"
  - "--port"
  - "8000"

env:
  - name: PGHOST
    valueFrom: database
  - name: PGPORT
    valueFrom: database
  - name: PGDATABASE
    valueFrom: database
  - name: PGUSER
    valueFrom: database
```

**Step 6: Create server/config.py** (dual-mode auth)

```python
import os
from databricks.sdk import WorkspaceClient

IS_DATABRICKS_APP = bool(os.environ.get("DATABRICKS_APP_NAME"))

def get_workspace_client() -> WorkspaceClient:
    if IS_DATABRICKS_APP:
        return WorkspaceClient()
    profile = os.environ.get("DATABRICKS_PROFILE", "DEFAULT")
    return WorkspaceClient(profile=profile)

def get_oauth_token() -> str:
    client = get_workspace_client()
    auth_headers = client.config.authenticate()
    if auth_headers and "Authorization" in auth_headers:
        return auth_headers["Authorization"].replace("Bearer ", "")
    raise RuntimeError("Failed to get OAuth token")

def get_current_user() -> str:
    if IS_DATABRICKS_APP:
        return os.environ.get("DATABRICKS_APP_USER", "system")
    return "local-dev"
```

**Step 7: Create server/db.py** (Lakebase pool)

```python
import os
import asyncpg
from typing import Optional
from server.config import get_oauth_token

class DatabasePool:
    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None

    async def get_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            token = get_oauth_token()
            self._pool = await asyncpg.create_pool(
                host=os.environ["PGHOST"],
                port=int(os.environ.get("PGPORT", "5432")),
                database=os.environ["PGDATABASE"],
                user=os.environ["PGUSER"],
                password=token,
                ssl="require",
                min_size=2,
                max_size=10,
            )
        return self._pool

    async def refresh_token(self):
        if self._pool:
            await self._pool.close()
            self._pool = None
        await self.get_pool()

    async def close(self):
        if self._pool:
            await self._pool.close()

db = DatabasePool()
```

**Step 8: Create minimal app.py**

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from server.db import db

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await db.close()

app = FastAPI(title="Spirit Rules Config", lifespan=lifespan)

frontend_dir = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.exists(frontend_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dir, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        return FileResponse(os.path.join(frontend_dir, "index.html"))
```

**Step 9: Scaffold React frontend**

```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install @chakra-ui/react @emotion/react @emotion/styled framer-motion
npm install @tanstack/react-table
npm install axios zustand react-icons
npm install -D @types/node
cd ..
```

**Step 10: Commit**

```bash
git add -A
git commit -m "chore: scaffold Spirit rules config project structure"
```

---

### Task 2: Database Schema & Migration

**Files:**
- Create: `server/schema.sql`
- Create: `server/routes/__init__.py`
- Create: `server/routes/health.py`
- Modify: `app.py` — add health route and schema init

**Step 1: Create server/schema.sql**

```sql
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS rule_headers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    cost_category VARCHAR(100) NOT NULL,
    rate_category VARCHAR(100),
    category VARCHAR(100),
    account_group VARCHAR(100),
    groupby_costcenter BOOLEAN DEFAULT FALSE,
    groupby_account BOOLEAN DEFAULT FALSE,
    fixed_variable_pct_split DECIMAL(5,2),
    fixed_variable_type VARCHAR(50),
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    version INTEGER NOT NULL DEFAULT 1,
    cloned_from_id UUID REFERENCES rule_headers(id),
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rule_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    header_id UUID NOT NULL REFERENCES rule_headers(id) ON DELETE CASCADE,
    account_number VARCHAR(50) NOT NULL,
    account_name VARCHAR(200),
    stat_type VARCHAR(50) NOT NULL,
    proration_rate DECIMAL(10,6) NOT NULL,
    effective_date DATE,
    notes TEXT,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rule_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    header_id UUID NOT NULL REFERENCES rule_headers(id) ON DELETE CASCADE,
    action VARCHAR(20) NOT NULL,
    changed_by VARCHAR(100) NOT NULL,
    changed_at TIMESTAMP DEFAULT NOW(),
    old_values JSONB,
    new_values JSONB
);

CREATE INDEX IF NOT EXISTS idx_rule_headers_status ON rule_headers(status);
CREATE INDEX IF NOT EXISTS idx_rule_headers_cost_category ON rule_headers(cost_category);
CREATE INDEX IF NOT EXISTS idx_rule_lines_header_id ON rule_lines(header_id);
CREATE INDEX IF NOT EXISTS idx_rule_audit_header_id ON rule_audit_log(header_id);
```

**Step 2: Create server/routes/health.py**

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/api/health")
async def health():
    return {"status": "ok"}
```

**Step 3: Update app.py lifespan to run schema on startup**

Add schema initialization in the lifespan function so tables are created on first boot.

**Step 4: Commit**

```bash
git add -A
git commit -m "feat: add Lakebase schema and health endpoint"
```

---

### Task 3: Backend — Rule Headers CRUD API

**Files:**
- Create: `server/models.py` — Pydantic models
- Create: `server/routes/rules.py` — header CRUD endpoints
- Modify: `app.py` — register rules router

**Step 1: Create server/models.py**

```python
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from uuid import UUID

class RuleHeaderCreate(BaseModel):
    start_date: date
    end_date: date
    cost_category: str
    rate_category: Optional[str] = None
    category: Optional[str] = None
    account_group: Optional[str] = None
    groupby_costcenter: bool = False
    groupby_account: bool = False
    fixed_variable_pct_split: Optional[float] = None
    fixed_variable_type: Optional[str] = None

class RuleHeaderUpdate(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    cost_category: Optional[str] = None
    rate_category: Optional[str] = None
    category: Optional[str] = None
    account_group: Optional[str] = None
    groupby_costcenter: Optional[bool] = None
    groupby_account: Optional[bool] = None
    fixed_variable_pct_split: Optional[float] = None
    fixed_variable_type: Optional[str] = None

class RuleHeaderResponse(BaseModel):
    id: UUID
    start_date: date
    end_date: date
    cost_category: str
    rate_category: Optional[str]
    category: Optional[str]
    account_group: Optional[str]
    groupby_costcenter: bool
    groupby_account: bool
    fixed_variable_pct_split: Optional[float]
    fixed_variable_type: Optional[str]
    status: str
    version: int
    cloned_from_id: Optional[UUID]
    created_by: str
    created_at: datetime
    updated_at: datetime

class StatusUpdate(BaseModel):
    status: str  # "draft", "in_review", "approved", "archived"

class RuleLineCreate(BaseModel):
    account_number: str
    account_name: Optional[str] = None
    stat_type: str
    proration_rate: float
    effective_date: Optional[date] = None
    notes: Optional[str] = None
    sort_order: int = 0

class RuleLineUpdate(BaseModel):
    account_number: Optional[str] = None
    account_name: Optional[str] = None
    stat_type: Optional[str] = None
    proration_rate: Optional[float] = None
    effective_date: Optional[date] = None
    notes: Optional[str] = None
    sort_order: Optional[int] = None

class RuleLineResponse(BaseModel):
    id: UUID
    header_id: UUID
    account_number: str
    account_name: Optional[str]
    stat_type: str
    proration_rate: float
    effective_date: Optional[date]
    notes: Optional[str]
    sort_order: int
    created_at: datetime
    updated_at: datetime
```

**Step 2: Create server/routes/rules.py**

Implement these endpoints:
- `GET /api/rules` — list headers with optional query params: `status`, `cost_category`, `search`
- `GET /api/rules/{id}` — get single header with its lines
- `POST /api/rules` — create header
- `PUT /api/rules/{id}` — update header (only if status=draft)
- `DELETE /api/rules/{id}` — delete header + cascade lines
- `POST /api/rules/{id}/clone` — clone header + all lines, set status=draft, increment version
- `PUT /api/rules/{id}/status` — transition status with validation (draft->in_review->approved->archived, or in_review->draft for reject)

Each write operation should log to `rule_audit_log`.

**Step 3: Register router in app.py**

```python
from server.routes import rules, health
app.include_router(rules.router)
app.include_router(health.router)
```

**Step 4: Test locally**

```bash
uv run uvicorn app:app --reload --port 8000
# Test: curl http://localhost:8000/api/health
# Test: curl http://localhost:8000/api/rules
```

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: add rule headers CRUD API with audit logging"
```

---

### Task 4: Backend — Rule Lines CRUD + Import/Export

**Files:**
- Create: `server/routes/lines.py` — lines CRUD + CSV import/export
- Modify: `app.py` — register lines router

**Step 1: Create server/routes/lines.py**

Endpoints:
- `GET /api/rules/{id}/lines` — list lines for a header, ordered by sort_order
- `POST /api/rules/{id}/lines` — add one or more lines (accept list)
- `PUT /api/rules/{id}/lines/{line_id}` — update a line (only if header status=draft)
- `DELETE /api/rules/{id}/lines/{line_id}` — delete a line (only if header status=draft)
- `POST /api/rules/{id}/import` — accept CSV file upload, parse, insert lines
- `GET /api/rules/{id}/export` — return lines as CSV download
- `GET /api/rules/{id}/audit` — return audit log entries

CSV format for import/export:
```
account_number,account_name,stat_type,proration_rate,effective_date,notes
5100-01,Fuel Direct,ASMs,0.342000,2026-01-01,
5100-02,Fuel Overhead,Departures,0.158000,2026-01-01,adjusted from Q4
```

**Step 2: Register router in app.py**

**Step 3: Commit**

```bash
git add -A
git commit -m "feat: add rule lines CRUD with CSV import/export"
```

---

### Task 5: Frontend — App Shell & Routing

**Files:**
- Create: `frontend/src/App.tsx` — main app with Chakra provider
- Create: `frontend/src/theme.ts` — Spirit Airlines color theme
- Create: `frontend/src/api/client.ts` — axios client
- Create: `frontend/src/store/rulesStore.ts` — zustand state
- Create: `frontend/src/types.ts` — TypeScript interfaces
- Modify: `frontend/src/main.tsx` — wrap with providers
- Modify: `frontend/vite.config.ts` — add proxy to backend

**Step 1: Define types in frontend/src/types.ts**

```typescript
export interface RuleHeader {
  id: string;
  start_date: string;
  end_date: string;
  cost_category: string;
  rate_category: string | null;
  category: string | null;
  account_group: string | null;
  groupby_costcenter: boolean;
  groupby_account: boolean;
  fixed_variable_pct_split: number | null;
  fixed_variable_type: string | null;
  status: "draft" | "in_review" | "approved" | "archived";
  version: number;
  cloned_from_id: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface RuleLine {
  id: string;
  header_id: string;
  account_number: string;
  account_name: string | null;
  stat_type: string;
  proration_rate: number;
  effective_date: string | null;
  notes: string | null;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface AuditEntry {
  id: string;
  header_id: string;
  action: string;
  changed_by: string;
  changed_at: string;
  old_values: Record<string, unknown> | null;
  new_values: Record<string, unknown> | null;
}
```

**Step 2: Create API client, zustand store, and Spirit-themed Chakra theme**

Spirit brand colors: yellow (#FFC72C), black (#000000), dark gray (#333333).

**Step 3: Configure vite proxy**

```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
```

**Step 4: Build app shell with header bar**

```
┌─────────────────────────────────────────┐
│ ✈ Spirit Airlines — Rules Configuration │
└─────────────────────────────────────────┘
│              (content area)             │
```

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: scaffold React app shell with theme, store, and API client"
```

---

### Task 6: Frontend — Left Panel (Rule Headers List)

**Files:**
- Create: `frontend/src/components/RuleHeaderList.tsx`
- Create: `frontend/src/components/RuleHeaderCard.tsx`
- Create: `frontend/src/components/StatusBadge.tsx`
- Create: `frontend/src/components/FilterBar.tsx`

**Step 1: Build StatusBadge component**

Color-coded badges: Draft (gray), In Review (orange), Approved (green), Archived (blue).

**Step 2: Build RuleHeaderCard component**

Shows: cost_category, rate_category, date range, status badge, version. Clickable to select.

**Step 3: Build FilterBar component**

Dropdowns for: Status, Cost Category, Date Range. Plus a search input.

**Step 4: Build RuleHeaderList component**

Scrollable list with FilterBar at top, "+ New Rule" and "Import CSV" buttons, list of RuleHeaderCards. Selected card highlighted.

**Step 5: Wire to zustand store — fetch headers on mount, handle selection**

**Step 6: Commit**

```bash
git add -A
git commit -m "feat: add rule headers list panel with filters and status badges"
```

---

### Task 7: Frontend — Right Panel (Header Detail + Lines Table)

**Files:**
- Create: `frontend/src/components/RuleDetail.tsx` — right panel container
- Create: `frontend/src/components/HeaderDetailCard.tsx` — header fields display/edit
- Create: `frontend/src/components/LinesTable.tsx` — TanStack Table with inline editing
- Create: `frontend/src/components/ActionBar.tsx` — Save, Clone, Submit, Export buttons

**Step 1: Build HeaderDetailCard**

Shows all header fields. If status=draft, fields are editable (inline form). Otherwise read-only. Edit/Save toggle button.

**Step 2: Build LinesTable with TanStack Table**

Columns: Account #, Account Name, Stat Type, Proration Rate, Effective Date, Notes, Actions (edit/delete).
- Inline editing: click a cell to edit, tab to move between cells
- Add row button at bottom
- Only editable when header status=draft
- Sort by sort_order column

**Step 3: Build ActionBar**

Buttons conditional on status:
- Draft: [Save] [Clone] [Submit for Review] [Export CSV] [Delete]
- In Review: [Approve] [Reject] [Clone] [Export CSV]
- Approved: [Clone] [Export CSV] [Archive]
- Archived: [Clone] [Export CSV]

**Step 4: Build RuleDetail container**

Composes HeaderDetailCard + LinesTable + ActionBar. Shows empty state when no header selected.

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: add rule detail panel with inline-editable lines table"
```

---

### Task 8: Frontend — Master-Detail Layout Integration

**Files:**
- Modify: `frontend/src/App.tsx` — compose left/right panels

**Step 1: Create split-pane layout**

```
┌──────────────┬────────────────────────────┐
│ RuleHeader   │ RuleDetail                 │
│ List (350px) │ (flex-1)                   │
│              │                            │
│ [scrollable] │ HeaderDetailCard           │
│              │ LinesTable                 │
│              │ ActionBar                  │
└──────────────┴────────────────────────────┘
```

Left panel: fixed 350px width, full height, scrollable.
Right panel: flex-1, scrollable.
Resizable divider (optional stretch goal — skip for now).

**Step 2: Wire selection — clicking a header in left panel loads detail in right panel**

**Step 3: Wire CRUD — creating/editing/deleting rules refreshes the left panel list**

**Step 4: Commit**

```bash
git add -A
git commit -m "feat: integrate master-detail layout with full CRUD wiring"
```

---

### Task 9: Frontend — New Rule & Clone Dialogs

**Files:**
- Create: `frontend/src/components/NewRuleDialog.tsx`
- Create: `frontend/src/components/CloneConfirmDialog.tsx`
- Create: `frontend/src/components/ImportDialog.tsx`

**Step 1: Build NewRuleDialog**

Modal form with all header fields. On submit, POST to /api/rules, then select the new rule.

**Step 2: Build CloneConfirmDialog**

Confirmation modal: "Clone [cost_category] v[N] as new Draft v[N+1]?" On confirm, POST to /api/rules/{id}/clone.

**Step 3: Build ImportDialog**

File upload for CSV. Shows preview of parsed rows before confirming import. POST to /api/rules/{id}/import.

**Step 4: Wire dialogs to ActionBar buttons**

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: add new rule, clone, and import dialogs"
```

---

### Task 10: Frontend — Status Transitions & Audit Log

**Files:**
- Create: `frontend/src/components/AuditLog.tsx`
- Modify: `frontend/src/components/ActionBar.tsx` — wire status transitions

**Step 1: Wire status transition buttons**

Submit for Review: PUT /api/rules/{id}/status {"status": "in_review"}
Approve: PUT /api/rules/{id}/status {"status": "approved"}
Reject: PUT /api/rules/{id}/status {"status": "draft"}
Archive: PUT /api/rules/{id}/status {"status": "archived"}

Show confirmation dialog before each transition. After transition, refresh header and toggle editability.

**Step 2: Build AuditLog component**

Collapsible section at bottom of RuleDetail. Shows timeline of changes: who, when, what action, with expandable diff of old/new values.

**Step 3: Commit**

```bash
git add -A
git commit -m "feat: add status transitions and audit log display"
```

---

### Task 11: Build, Polish & Local Testing

**Files:**
- Modify: various — fix styling, loading states, error handling

**Step 1: Add loading spinners and error toasts**

Use Chakra's `useToast` for success/error messages. Show skeleton loaders while data loads.

**Step 2: Add empty states**

"No rules found" when list is empty. "Select a rule to view details" when nothing selected.

**Step 3: Build frontend for production**

```bash
cd frontend && npm run build && cd ..
```

**Step 4: Test full stack locally**

```bash
uv run uvicorn app:app --reload --port 8000
# Open http://localhost:5173 (vite dev) or http://localhost:8000 (built)
```

**Step 5: Validate with Chrome DevTools MCP**

- Navigate to app, take screenshot
- Check console for errors
- Test CRUD flows via click interactions

**Step 6: Commit**

```bash
git add -A
git commit -m "feat: polish UI with loading states, error handling, and empty states"
```

---

### Task 12: Deploy as Databricks App

**Step 1: Authenticate with Databricks workspace**

Use `databricks-authentication` skill to authenticate CLI.

**Step 2: Create Lakebase instance**

Use `databricks-lakebase` skill to provision a Lakebase database.

**Step 3: Create Databricks App**

```bash
databricks apps create spirit-rules-config --description "Spirit Airlines Rules Configuration" -p <profile>
```

**Step 4: Sync and deploy**

```bash
databricks sync . /Workspace/Users/<user>/spirit-rules-config \
  --exclude node_modules --exclude .venv --exclude __pycache__ \
  --exclude .git --exclude "frontend/src" --exclude "frontend/public" \
  -p <profile>

databricks apps deploy spirit-rules-config \
  --source-code-path /Workspace/Users/<user>/spirit-rules-config \
  -p <profile>
```

**Step 5: Add Lakebase resource to app**

Via Databricks UI: Compute > Apps > spirit-rules-config > Edit > Add Database resource.

**Step 6: Verify deployment**

Navigate to app URL, test all flows.

**Step 7: Commit**

```bash
git add -A
git commit -m "chore: configure for Databricks App deployment"
```
