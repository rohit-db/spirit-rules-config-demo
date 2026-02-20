import os
import logging
import asyncpg
from typing import Optional
from server.config import get_oauth_token

logger = logging.getLogger(__name__)


class DatabasePool:
    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None

    async def get_pool(self) -> Optional[asyncpg.Pool]:
        if self._pool is None:
            if not os.environ.get("PGHOST"):
                logger.warning("PGHOST not set — database not configured")
                return None
            try:
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
