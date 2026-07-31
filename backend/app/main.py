from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.users import router as users_router
from app.api.v1.routers.datasets import router as datasets_router
from app.api.v1.routers.kpi import router as kpi_router
from app.api.v1.routers.ml import router as ml_router
from app.api.v1.routers.ai import router as ai_router
from app.api.v1.routers.reports import router as reports_router
from app.api.v1.routers.logs import router as logs_router
from app.api.v1.routers.settings import router as settings_router
from app.infrastructure.db.base import Base
from app.infrastructure.db.session import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown lifecycle events.
    Why: Conditionally creates database tables if not in a production config.
    """
    if not settings.is_production:
        Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title=settings.app_name,
    description="Backend service for AI-Powered Business Intelligence & Decision Support Platform.",
    version="0.1.0",
    lifespan=lifespan,
)

# Apply CORS middleware using the list of allowed origins from configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v1 REST endpoints under the /api/v1 prefix
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(logs_router, prefix="/api/v1")
app.include_router(settings_router, prefix="/api/v1")
app.include_router(datasets_router, prefix="/api/v1/datasets", tags=["datasets"])
app.include_router(kpi_router, prefix="/api/v1/kpi", tags=["kpi"])
app.include_router(ml_router, prefix="/api/v1/ml", tags=["ml"])
app.include_router(ai_router, prefix="/api/v1/ai", tags=["ai"])
app.include_router(reports_router, prefix="/api/v1/reports", tags=["reports"])

@app.get("/")
def get_root():
    """
    Root endpoint offering a welcome message.
    """
    return {
        "message": f"Welcome to {settings.app_name} API backend!",
        "docs_url": "/docs"
    }

@app.get("/health")
def get_health():
    """
    Health check endpoint for checking API status and metadata.
    """
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "environment": settings.app_env,
    }
