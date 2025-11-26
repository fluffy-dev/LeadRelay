from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.config import settings
from src.database import engine, Base
from src.crm.router import router as crm_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for database initialization.
    In a real production environment, use Alembic for migrations.
    For this test task, we auto-create tables on startup.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(
    title=settings.TITLE,
    lifespan=lifespan
)

app.include_router(crm_router)

@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}