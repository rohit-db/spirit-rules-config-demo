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
