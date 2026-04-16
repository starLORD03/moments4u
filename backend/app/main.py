"""
FastAPI application factory — the main entry point.

Creates the app, registers routers, middleware, and startup/shutdown events.

Run with:
    uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import engine, async_session_factory
from .routers import auth, photos, gallery, faces, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    settings = get_settings()
    print(f"🚀 Starting {settings.app_name} ({settings.app_env})")
    yield
    # Shutdown: close DB connections
    await engine.dispose()
    print("👋 Shutting down")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="moments4u API",
        description="Photo capture and sharing platform for playgroups",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/api/docs" if not settings.is_production else None,
        redoc_url="/api/redoc" if not settings.is_production else None,
    )

    # ── CORS ──
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ──
    app.include_router(auth.router)
    app.include_router(photos.router)
    app.include_router(gallery.router)
    app.include_router(faces.router)
    app.include_router(admin.router)

    # ── Health check ──
    @app.get("/api/v1/health", tags=["system"])
    async def health_check():
        return {"status": "healthy", "service": settings.app_name, "env": settings.app_env}

    return app


app = create_app()
