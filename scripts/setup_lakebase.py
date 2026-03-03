#!/usr/bin/env python3
"""One-time Lakebase setup for Spirit Rules Config.

Run this ONCE after `databricks bundle deploy` to configure the Lakebase
database for the app's service principal. Must be run by a user with
project owner access (typically the person who deployed the bundle).

Usage:
    python scripts/setup_lakebase.py --profile <databricks-profile>

Example:
    databricks bundle deploy --profile fe-vm-serverless-jsr0s9
    python scripts/setup_lakebase.py --profile fe-vm-serverless-jsr0s9
"""

import argparse
import asyncio
import asyncpg
import sys


async def main(profile: str, project_id: str, database: str, app_name: str):
    from databricks.sdk import WorkspaceClient

    client = WorkspaceClient(profile=profile)
    me = client.current_user.me()
    print(f"Authenticated as: {me.user_name}")

    # Discover the read-write endpoint
    branch_path = f"projects/{project_id}/branches/main"
    resp = client.api_client.do("GET", f"/api/2.0/postgres/{branch_path}/endpoints")
    endpoints = resp.get("endpoints", [])

    host = None
    for ep in endpoints:
        status = ep.get("status", {})
        if "READ_WRITE" in status.get("endpoint_type", ""):
            host = status.get("hosts", {}).get("host")
            break

    if not host:
        print(f"ERROR: No active read-write endpoint for {branch_path}")
        sys.exit(1)

    print(f"Lakebase endpoint: {host}")

    # Get OAuth token for DB connection
    auth_headers = client.config.authenticate()
    token = auth_headers["Authorization"].replace("Bearer ", "")

    # Look up the app's service principal
    app_info = client.api_client.do("GET", f"/api/2.0/apps/{app_name}")
    sp_client_id = app_info.get("service_principal_client_id")
    if not sp_client_id:
        print(f"ERROR: Could not find service principal for app '{app_name}'")
        sys.exit(1)

    print(f"App service principal: {sp_client_id}")

    # Connect to the target database
    try:
        conn = await asyncpg.connect(
            host=host, port=5432, database=database,
            user=me.user_name, password=token, ssl="require",
        )
    except asyncpg.InvalidCatalogNameError:
        # Database doesn't exist yet — connect to postgres and create it
        print(f"Database '{database}' doesn't exist, creating...")
        conn = await asyncpg.connect(
            host=host, port=5432, database="postgres",
            user=me.user_name, password=token, ssl="require",
        )
        await conn.execute(f"CREATE DATABASE {database}")
        await conn.close()
        print(f"Created database: {database}")
        conn = await asyncpg.connect(
            host=host, port=5432, database=database,
            user=me.user_name, password=token, ssl="require",
        )

    print(f"Connected to database: {database}")

    # Install databricks_auth extension
    await conn.execute("CREATE EXTENSION IF NOT EXISTS databricks_auth CASCADE")
    print("Installed databricks_auth extension")

    # Create OAuth role for the service principal
    try:
        result = await conn.fetchval(
            "SELECT databricks_create_role($1::text, $2::text)",
            sp_client_id, "SERVICE_PRINCIPAL",
        )
        print(f"Created OAuth role: {result}")
    except asyncpg.UniqueViolationError:
        print(f"OAuth role already exists for {sp_client_id}")
    except Exception as e:
        if "already exists" in str(e).lower():
            print(f"OAuth role already exists for {sp_client_id}")
        else:
            raise

    # Grant permissions
    await conn.execute(f'GRANT ALL ON DATABASE {database} TO "{sp_client_id}"')
    print(f"Granted ALL on database {database}")

    await conn.execute(f'GRANT ALL ON SCHEMA public TO "{sp_client_id}"')
    print("Granted ALL on public schema")

    await conn.execute(
        f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "{sp_client_id}"'
    )
    print("Granted default privileges on future tables")

    # Grant on existing tables (idempotent)
    await conn.execute(
        f'GRANT ALL ON ALL TABLES IN SCHEMA public TO "{sp_client_id}"'
    )
    print("Granted ALL on existing tables")

    await conn.close()
    print("\nSetup complete! The app can now connect to Lakebase.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="One-time Lakebase setup for Spirit Rules Config")
    parser.add_argument("--profile", required=True, help="Databricks CLI profile name")
    parser.add_argument("--project-id", default="spirit-rules-db", help="Lakebase project ID")
    parser.add_argument("--database", default="spirit_rules", help="Database name")
    parser.add_argument("--app-name", default="spirit-rules-config", help="Databricks app name")
    args = parser.parse_args()

    asyncio.run(main(args.profile, args.project_id, args.database, args.app_name))
