# Spirit Rules Config — Deployment Guide

## Prerequisites

- Databricks CLI installed (`databricks --version` should return 0.240+)
- A Databricks workspace with Lakebase enabled
- Authenticated CLI profile (`databricks auth login <workspace-url> --profile <name>`)

No Node.js required — the frontend is pre-built and included in the repo.

## Step 1: Configure

Edit two files:

### databricks.yml

Set your workspace URL:

```yaml
targets:
  dev:
    workspace:
      host: https://your-workspace.cloud.databricks.com
```

Optionally change any variable defaults (instance name, app name, capacity, etc.).

### app.yaml

Update these two env vars to match `databricks.yml`:

```yaml
env:
  - name: LAKEBASE_INSTANCE_NAME
    value: "spirit-rules-db"        # must match lakebase_instance_name
  - name: SECRET_SCOPE
    value: "spirit-rules-config"    # must match secret_scope
```

These cannot be auto-substituted by the bundle — you must set them manually.

## Step 2: Deploy infrastructure

```bash
databricks bundle deploy --profile <your-profile>
```

This creates the Lakebase provisioned instance, Databricks App, and setup job.

## Step 3: Start the app

```bash
databricks apps start spirit-rules-config --profile <your-profile>
```

The app will serve mock data until the database is ready — it auto-switches to the real DB with no restart needed.

## Step 4: Run setup job

```bash
databricks bundle run setup_lakebase --profile <your-profile>
```

This job will:
1. Wait for the Lakebase instance to become AVAILABLE (up to 10 minutes)
2. Create the database and tables
3. Create the Postgres role and store credentials in secrets
4. Grant the app's service principal access to those secrets

If the instance isn't ready within 10 minutes, just re-run the job.

Once the setup job completes, the app will automatically connect to the real database on its next request (within 15 seconds).

## Step 5: Deploy app code (if needed)

If the app was already running before the setup job, deploy the latest code:

```bash
databricks apps deploy spirit-rules-config \
  --source-code-path "/Workspace/Users/<you>/.bundle/spirit-rules-config/dev/files" \
  --profile <your-profile>
```

## Configuration Reference

All configurable values are in `databricks.yml` under `variables:`:

| Variable | Default | Description |
|----------|---------|-------------|
| `lakebase_instance_name` | `spirit-rules-db` | Lakebase instance name |
| `lakebase_database_name` | `spirit_rules` | Database name |
| `app_name` | `spirit-rules-config` | Databricks App name |
| `secret_scope` | `spirit-rules-config` | Databricks secret scope |
| `db_role` | `spirit_rules_app` | Postgres role for the app |
| `lakebase_capacity` | `CU_1` | Instance size: CU_1, CU_2, CU_4, or CU_8 |

## Troubleshooting

**Setup job fails with "not AVAILABLE" error**: Provisioned Lakebase instances can take several minutes to provision. Just re-run the setup job.

**App shows mock data**: The app auto-retries the database connection every 15 seconds. If the setup job has completed successfully, the app will switch to the real DB on the next request. If it persists, check that the setup job granted the app SP access to secrets:
```bash
databricks secrets list-acls <secret-scope> --profile <your-profile>
```

**Files not appearing in workspace after deploy**: Local sync cache may be stale. Fix:
```bash
rm -rf .databricks/bundle/dev/sync-snapshots/
rm -f .databricks/bundle/dev/deployment.json
databricks bundle deploy --profile <your-profile>
```

**App can't read secrets**: Re-run the setup job, or manually grant access:
```bash
databricks apps get <app-name> --profile <your-profile>
# copy service_principal_client_id
databricks secrets put-acl <secret-scope> <sp-client-id> READ --profile <your-profile>
```
