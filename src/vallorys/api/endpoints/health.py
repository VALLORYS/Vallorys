"""Health check endpoints."""

from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: datetime
    services: dict[str, str]


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns the health status of all services.
    """
    # TODO: Actually check service health
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow(),
        services={
            "database": "healthy",
            "redis": "healthy",
            "dvf_api": "healthy",
        },
    )


@router.get("/ready")
async def readiness_check() -> dict:
    """Kubernetes readiness probe."""
    return {"ready": True}


@router.get("/live")
async def liveness_check() -> dict:
    """Kubernetes liveness probe."""
    return {"live": True}
