import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

# Ensure both backend/ and project root are in sys.path
_current_file = Path(__file__).resolve()
_backend_dir = _current_file.parent.parent
_root_dir = _backend_dir.parent

if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.verification_hub import router as verification_router
from app.api.v1.router import api_v1_router
from app.config import settings
from app.core.exceptions import AppException
from app.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup and shutdown events."""
    # Ensure storage paths exist
    settings.ensure_directories_exist()
    # Create tables if needed for dev/sqlite
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-assisted academic certificate authenticity assessment platform.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handlers
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions and format into standard error envelopes."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status_code": exc.status_code,
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all unhandled exception handler."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred processing your request.",
            "details": {"error": str(exc)} if settings.DEBUG else {},
        },
    )


# Root and /api Health Check probes
app.include_router(health_router, prefix="")
app.include_router(health_router, prefix="/api")

# Verification endpoints at root (/verify), /api (/api/verify), and /api/v1
app.include_router(verification_router, prefix="")
app.include_router(verification_router, prefix="/api")

# Auth endpoints available at /api and /api/v1
app.include_router(auth_router, prefix="/api")

# API v1 Router
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
def root_info() -> dict:
    """Root info endpoint."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": "0.1.0",
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR,
    }
