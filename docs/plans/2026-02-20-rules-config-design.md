# Spirit Airlines — Rules Configuration App Design

## Overview

Master-detail React application for managing proration rates between financial accounts and flight stats. Deployed as a Databricks App with Lakebase backend.

## Data Model

### rule_headers
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | Auto-generated |
| start_date | DATE | Effective start |
| end_date | DATE | Effective end |
| cost_category | VARCHAR(100) | e.g., "Fuel", "Crew" |
| rate_category | VARCHAR(100) | e.g., "Domestic", "International" |
| category | VARCHAR(100) | General classification |
| account_group | VARCHAR(100) | GL account grouping |
| groupby_costcenter | BOOLEAN | Whether to group by cost center |
| groupby_account | BOOLEAN | Whether to group by account |
| fixed_variable_pct_split | DECIMAL(5,2) | % split between fixed/variable |
| fixed_variable_type | VARCHAR(50) | "Fixed", "Variable", "Station_Fixed", "Station_Variable" |
| status | VARCHAR(20) | "draft", "in_review", "approved", "archived" |
| version | INTEGER | Version number, increments on clone |
| cloned_from_id | UUID FK nullable | Points to parent rule if cloned |
| created_by | VARCHAR(100) | User who created |
| created_at | TIMESTAMP | Auto |
| updated_at | TIMESTAMP | Auto |

### rule_lines
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | Auto-generated |
| header_id | UUID FK | References rule_headers.id |
| account_number | VARCHAR(50) | GL account number |
| account_name | VARCHAR(200) | Descriptive name |
| stat_type | VARCHAR(50) | "ASMs", "Departures", "Block_Hours", "RPMs", etc. |
| proration_rate | DECIMAL(10,6) | The rate/percentage |
| effective_date | DATE | When this line takes effect |
| notes | TEXT | Optional comments |
| sort_order | INTEGER | Display ordering |
| created_at | TIMESTAMP | Auto |
| updated_at | TIMESTAMP | Auto |

### rule_audit_log
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| header_id | UUID FK | Which rule was changed |
| action | VARCHAR(20) | "create", "update", "delete", "status_change", "clone" |
| changed_by | VARCHAR(100) | |
| changed_at | TIMESTAMP | |
| old_values | JSONB | Previous state |
| new_values | JSONB | New state |

## UI Layout

Master-detail split panel:
- Left panel: filterable list of rule headers with status badges, filters by status/cost category/date
- Right panel: header detail card (read-only or editable based on status) + editable proration lines table
- Inline editing on lines via TanStack Table
- Action buttons: New Rule, Clone, Submit for Review, Import/Export CSV

## Tech Stack

| Layer | Choice |
|-------|--------|
| Frontend | React 18 + Vite + TypeScript |
| UI Components | Chakra UI |
| Data Grid | TanStack Table |
| Backend | FastAPI (Python) |
| Database | Lakebase (Postgres) |
| Deployment | Databricks App |
| Auth | Databricks App built-in |

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | /api/rules | List headers (with filters) |
| GET | /api/rules/{id} | Get header + lines |
| POST | /api/rules | Create new header |
| PUT | /api/rules/{id} | Update header fields |
| DELETE | /api/rules/{id} | Delete header + cascading lines |
| POST | /api/rules/{id}/clone | Clone rule set |
| PUT | /api/rules/{id}/status | Transition status |
| GET | /api/rules/{id}/lines | List lines for a header |
| POST | /api/rules/{id}/lines | Add line(s) |
| PUT | /api/rules/{id}/lines/{line_id} | Update a line |
| DELETE | /api/rules/{id}/lines/{line_id} | Delete a line |
| POST | /api/rules/{id}/import | Bulk import from CSV |
| GET | /api/rules/{id}/export | Export as CSV |
| GET | /api/rules/{id}/audit | Get audit log |

## Approval Workflow

Draft -> In Review -> Approved -> Archived
- Only Draft rules are editable
- Reject sends back to Draft
- Cloning an Approved rule creates a new Draft version
