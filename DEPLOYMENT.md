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

Optionally change any variable defaults (instance name, app name, etc.).

### app.yaml

Update these two env vars to match `databricks.yml`:

```yaml
env:
  - name: LAKEBASE_PROJECT_ID
    value: "spirit-rules-db"        # must match lakebase_instance_name
  - name: SECRET_SCOPE
    value: "spirit-rules-config"    # must match secret_scope
```

These cannot be auto-substituted by the bundle — you must set them manually.

## Step 2: Deploy infrastructure

```bash
databricks bundle deploy --profile <your-profile>
```

This creates the Lakebase instance, Databricks App, and setup job.

## Step 3: Run setup job

```bash
databricks bundle run setup_lakebase --profile <your-profile>
```

This creates the database, tables, Postgres role, stores credentials in secrets, and grants the app's service principal access to those secrets.

## Step 4: Start the app

```bash
databricks apps start spirit-rules-config --profile <your-profile>
```

Replace `spirit-rules-config` with your `app_name` if you changed it. The app URL is in the output.

## Configuration Reference

All configurable values are in `databricks.yml` under `variables:`:

| Variable | Default | Description |
|----------|---------|-------------|
| `lakebase_instance_name` | `spirit-rules-db` | Lakebase instance name |
| `lakebase_database_name` | `spirit_rules` | Database name |
| `app_name` | `spirit-rules-config` | Databricks App name |
| `secret_scope` | `spirit-rules-config` | Databricks secret scope |
| `db_role` | `spirit_rules_app` | Postgres role for the app |
| `autoscaling_min_cu` | `0.5` | Min compute units |
| `autoscaling_max_cu` | `2` | Max compute units |

## Troubleshooting

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
