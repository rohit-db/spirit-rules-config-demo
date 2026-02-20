from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import logging
from server.db import db
from server.routes import health

logger = logging.getLogger(__name__)


async def _init_schema():
    """Execute schema.sql against the database if available."""
    pool = await db.get_pool()
    if pool is None:
        logger.warning("Skipping schema init — database not available")
        return
    schema_path = os.path.join(os.path.dirname(__file__), "server", "schema.sql")
    with open(schema_path) as f:
        sql = f.read()
    async with pool.acquire() as conn:
        await conn.execute(sql)
    logger.info("Database schema initialized")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await _init_schema()
    yield
    await db.close()


app = FastAPI(title="Spirit Rules Config", lifespan=lifespan)

app.include_router(health.router)

frontend_dir = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.exists(frontend_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dir, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        return FileResponse(os.path.join(frontend_dir, "index.html"))
