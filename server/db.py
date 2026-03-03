import os
import logging
import asyncpg
from typing import Optional
from server.config import get_oauth_token, get_workspace_client

logger = logging.getLogger(__name__)


def _discover_lakebase_connection() -> dict:
    """Discover Lakebase Autoscaling connection details via Databricks REST API."""
    project_id = os.environ.get("LAKEBASE_PROJECT_ID")
    branch_id = os.environ.get("LAKEBASE_BRANCH_ID", "main")
    database = os.environ.get("LAKEBASE_DATABASE", "postgres")

    if not project_id:
        # Fall back to legacy env vars for provisioned Lakebase
        if os.environ.get("PGHOST"):
            return {
                "host": os.environ["PGHOST"],
                "port": int(os.environ.get("PGPORT", "5432")),
                "database": os.environ.get("PGDATABASE", "postgres"),
                "user": os.environ.get("PGUSER", ""),
            }
        return {}

    client = get_workspace_client()

    # List endpoints via REST API (works with any SDK version)
    branch_path = f"projects/{project_id}/branches/{branch_id}"
    resp = client.api_client.do(
        "GET",
        f"/api/2.0/postgres/{branch_path}/endpoints",
    )
    endpoints = resp.get("endpoints", [])

    host = None
    for ep in endpoints:
        status = ep.get("status", {})
        ep_type = status.get("endpoint_type", "")
        if "READ_WRITE" in ep_type:
            hosts = status.get("hosts", {})
            host = hosts.get("host")
            break

    if not host:
        raise RuntimeError(f"No active read-write endpoint found for {branch_path}")

    logger.info("Discovered Lakebase endpoint: %s", host)

    # Resolve user identity
    me = client.current_user.me()
    user = me.user_name

    return {
        "host": host,
        "port": 5432,
        "database": database,
        "user": user,
    }


class DatabasePool:
    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None

    async def get_pool(self) -> Optional[asyncpg.Pool]:
        if self._pool is None:
            try:
                conn = _discover_lakebase_connection()
                if not conn:
                    logger.warning("No Lakebase configuration found — database not available")
                    return None

                token = get_oauth_token()
                logger.info("Connecting to Lakebase: host=%s port=%d db=%s user=%s",
                            conn["host"], conn["port"], conn["database"], conn["user"])
                self._pool = await asyncpg.create_pool(
                    host=conn["host"],
                    port=conn["port"],
                    database=conn["database"],
                    user=conn["user"],
                    password=token,
                    ssl="require",
                    min_size=2,
                    max_size=10,
                )
            except Exception as e:
                logger.error("Failed to create database pool: %s", e)
                return None
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
