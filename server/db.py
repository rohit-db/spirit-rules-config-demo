import os
import time
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
    instance_name = os.environ.get("LAKEBASE_INSTANCE_NAME") or os.environ.get("LAKEBASE_PROJECT_ID")
    if not instance_name:
        return {}

    client = get_workspace_client()

    try:
        host = _read_secret(client, SECRET_SCOPE, "db-host")
        user = _read_secret(client, SECRET_SCOPE, "db-user")
        password = _read_secret(client, SECRET_SCOPE, "db-password")
        database = _read_secret(client, SECRET_SCOPE, "db-name")
        logger.info("Loaded credentials from secrets scope: %s", SECRET_SCOPE)
    except Exception as e:
        logger.warning("Could not read secrets (%s) — database not ready yet", e)
        return {}

    return {
        "host": host,
        "port": 5432,
        "database": database,
        "user": user,
        "password": password,
    }


class DatabasePool:
    """Connection pool that keeps retrying until the database is available.

    On every call to get_pool():
    - If we already have a working pool, return it immediately.
    - If not, try once to connect (no long blocking retry loop).
    - If that fails, return None — the caller falls back to mock mode.
    - Next request tries again. This way the app stays responsive while
      the provisioned Lakebase endpoint is still coming up, and automatically
      switches to the real DB once it's ready — no restart needed.
    """

    RETRY_COOLDOWN = 15  # seconds between connection attempts

    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None
        self._last_attempt: float = 0

    async def get_pool(self) -> Optional[asyncpg.Pool]:
        if self._pool is not None:
            return self._pool

        # Don't hammer the endpoint — respect cooldown between attempts
        now = time.monotonic()
        if now - self._last_attempt < self.RETRY_COOLDOWN:
            return None
        self._last_attempt = now

        conn = _get_connection_config()
        if not conn:
            logger.info("Database not configured yet — serving mock data")
            return None

        try:
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
            logger.info("Database pool created successfully")

            # Run schema init if this is the first successful connection
            if not getattr(self, 'schema_initialized', False):
                await self._run_schema_init()

            return self._pool
        except Exception as e:
            logger.warning("Database connection failed (will retry on next request): %s", e)
            return None

    async def _run_schema_init(self):
        """Apply schema.sql on first successful connection."""
        schema_path = getattr(self, 'schema_sql', None)
        if not schema_path or not os.path.exists(schema_path):
            return
        try:
            with open(schema_path) as f:
                sql = f.read()
            async with self._pool.acquire() as conn:
                await conn.execute(sql)
            logger.info("Database schema initialized (deferred)")
            self.schema_initialized = True
        except Exception as e:
            logger.warning("Schema init skipped (tables may already exist): %s", e)
            self.schema_initialized = True

    async def refresh_token(self):
        if self._pool:
            await self._pool.close()
            self._pool = None
        await self.get_pool()

    async def close(self):
        if self._pool:
            await self._pool.close()


db = DatabasePool()
