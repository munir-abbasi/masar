"""FastAPI application factory for Masar."""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from masar.agent_control import AgentControlPlane
from masar.api.routes import router
from masar.verification.accretive_store import AccretiveStore


def create_app(
    db_path: str | Path = "corpus.db",
    curated_db: str | Path = "masar-curated.db",
    session_db: str | Path = "masar_session.db",
) -> FastAPI:
    """Instantiate and configure the FastAPI application."""
    app = FastAPI(
        title="Masar API",
        description="High-precision Hadith Takhrīj variant discovery and curation engine",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.db_path = str(db_path)
    app.state.curated_store = AccretiveStore(curated_db)
    app.state.control = AgentControlPlane(db_path, curated_db, session_db)

    app.include_router(router)
    return app
