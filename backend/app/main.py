from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from .api import router as api_router
from .config import get_geoapify_api_key_status
from .database import DEFAULT_DATABASE_PATH, initialize_database
from .demo_api import router as demo_router


async def health_check() -> dict[str, str]:
    """Return the service health state."""

    return {
        "status": "ok",
        "geoapify_api_key": get_geoapify_api_key_status(),
    }


def create_app(
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> FastAPI:
    """Create an application bound to one SQLite database path."""

    resolved_database_path = Path(database_path)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        initialize_database(resolved_database_path)
        yield

    application = FastAPI(title="Expedia Lite API", lifespan=lifespan)
    application.state.database_path = resolved_database_path
    application.include_router(api_router)
    application.include_router(demo_router)
    application.add_api_route("/health", health_check, methods=["GET"])
    application.add_api_route("/api/health", health_check, methods=["GET"])
    return application


app = create_app()
