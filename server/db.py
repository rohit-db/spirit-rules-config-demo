import os
import logging
import base64
import asyncpg
from typing import Optional
from server.config import get_workspace_client

logger = logging.getLogger(__name__)

SECRET_SCOPE = os.environ.get("SECRET_SCOPE", "spirit-rules-config")


def _read_secret(client, scope: str, key: str) -> str:
    """Read a secret value from Databricks Secrets."""
    resp = client.api_client.do(
        "GET", "/api/2.0/secrets/get",
        query={"scope": scope, "key": key},
    )
    return base64.b64decode(resp["value"]).decode("utf-8")


def _get_connection_config() -> dict:
    """Get Lakebase connection config from Databricks Secrets."""
    project_id = os.environ.get("LAKEBASE_PROJECT_ID")
    if not project_id:
        return {}

    client = get_workspace_client()

    try:
        host = _read_secret(client, SECRET_SCOPE, "db-host")
        user = _read_secret(client, SECRET_SCOPE, "db-user")
        password = _read_secret(client, SECRET_SCOPE, "db-password")
        database = _read_secret(client, SECRET_SCOPE, "db-name")
        logger.info("Loaded credentials from secrets scope: %s", SECRET_SCOPE)
    except Exception as e:
        logger.warning("Could not read secrets (%s), falling back to endpoint discovery", e)
        # Fall back to endpoint discovery + OAuth (for backwards compat)
        return _discover_from_endpoint(client, project_id)

    return {
        "host": host,
        "port": 5432,
        "database": database,
        "user": user,
        "password": password,
    }


def _discover_from_endpoint(client, project_id: str) -> dict:
    """Fall back to endpoint discovery with OAuth auth."""
    from server.config import get_oauth_token

    branch_id = os.environ.get("LAKEBASE_BRANCH_ID", "main")
    database = os.environ.get("LAKEBASE_DATABASE", "postgres")
    branch_path = f"projects/{project_id}/branches/{branch_id}"

    resp = client.api_client.do(
        "GET", f"/api/2.0/postgres/{branch_path}/endpoints",
    )
    for ep in resp.get("endpoints", []):
        status = ep.get("status", {})
        if "READ_WRITE" in status.get("endpoint_type", ""):
            host = status.get("hosts", {}).get("host")
            if host:
                me = client.current_user.me()
                return {
                    "host": host,
                    "port": 5432,
                    "database": database,
                    "user": me.user_name,
                    "password": get_oauth_token(),
                }
    return {}


class DatabasePool:
    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None

    async def get_pool(self) -> Optional[asyncpg.Pool]:
        if self._pool is None:
            try:
                conn = _get_connection_config()
                if not conn:
                    logger.warning("No Lakebase configuration — database not available")
                    return None

                logger.info("Connecting to Lakebase: host=%s db=%s user=%s",
                            conn["host"], conn["database"], conn["user"])
                self._pool = await asyncpg.create_pool(
                    host=conn["host"],
                    port=conn["port"],
                    database=conn["database"],
                    user=conn["user"],
                    password=conn["password"],
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
