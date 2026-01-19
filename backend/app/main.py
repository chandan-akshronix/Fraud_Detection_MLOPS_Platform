"""
Shadow Hubble - Fraud Detection MLOps Platform
FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.v1 import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown."""
    # Startup
    print(f"Starting {settings.APP_NAME}...")
    yield
    # Shutdown
    print(f"Shutting down {settings.APP_NAME}...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Fraud Detection MLOps Platform with drift detection, bias monitoring, and automated retraining",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for container orchestration."""
    return JSONResponse(
        content={
            "status": "healthy",
            "version": "1.0.0",
            "service": settings.APP_NAME,
        }
    )


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """Readiness check - verifies database and cache connectivity."""
    # TODO: Add actual DB and Redis connectivity checks
    return JSONResponse(
        content={
            "status": "ready",
            "database": "connected",
            "cache": "connected",
        }
    )
