# Deploying Spirit Rules Config

## What Gets Deployed

The Databricks Asset Bundle provisions everything automatically:

- **Lakebase Autoscaling** — Postgres-compatible database (project, branch, and read-write endpoint with autoscaling compute)
- **Databricks App** — FastAPI backend + React frontend, served at a `.databricksapps.com` URL
- **Database permissions** — The app's service principal gets `CAN_CONNECT_AND_CREATE` access

## Quick Start

1. **Clone the repo** and update `databricks.yml` with your workspace host under `targets`

2. **Authenticate** to your Databricks workspace:
   ```bash
   databricks auth login --host https://your-workspace.cloud.databricks.com --profile my-profile
   ```

3. **Deploy the bundle** — this creates the Lakebase instance, database, and app:
   ```bash
   databricks bundle deploy --profile my-profile
   ```

4. **Run the one-time database setup** — creates the Postgres role for the app's service principal:
   ```bash
   pip install asyncpg databricks-sdk
   python scripts/setup_lakebase.py --profile my-profile
   ```

5. **Start the app**:
   ```bash
   databricks apps start spirit-rules-config --profile my-profile
   ```
   The app URL will be shown in the output. First deployment takes ~30 seconds.

## Customizing

Override autoscaling limits per target in `databricks.yml`:

```yaml
targets:
  prod:
    variables:
      autoscaling_min_cu: 1
      autoscaling_max_cu: 4
```
