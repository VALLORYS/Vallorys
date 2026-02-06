"""Analytics API endpoints."""

from datetime import datetime, timedelta
from typing import Annotated

import structlog
from fastapi import APIRouter, Query
from pydantic import BaseModel

logger = structlog.get_logger()
router = APIRouter()


class AccuracyMetrics(BaseModel):
    """Valuation accuracy metrics."""
    mae: float  # Mean Absolute Error
    mape: float  # Mean Absolute Percentage Error
    within_range_percent: float
    sample_size: int


class ObjectionStats(BaseModel):
    """Objection statistics."""
    category: str
    count: int
    resolution_rate: float


class DashboardMetrics(BaseModel):
    """Complete dashboard metrics."""
    scope: str
    period: str
    generated_at: datetime
    valuations: dict
    accuracy: AccuracyMetrics
    conversion: dict
    pricing: dict
    objections: dict
    usage: dict


@router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    scope: Annotated[str, Query(pattern="^(agent|agency|network)$")] = "agency",
    period: Annotated[str, Query(pattern="^(7d|30d|90d|12m)$")] = "30d",
    agent_id: str | None = None,
) -> DashboardMetrics:
    """
    Get dashboard metrics for the specified scope and period.

    Returns KPIs including valuation count, accuracy, conversion rates,
    objection handling stats, and tool usage.
    """
    logger.info(
        "Dashboard metrics requested",
        scope=scope,
        period=period,
        agent_id=agent_id,
    )

    # In production, calculate from actual data
    # For demo, return mock data
    return DashboardMetrics(
        scope=scope,
        period=period,
        generated_at=datetime.utcnow(),
        valuations={
            "total": 127,
            "by_type": {
                "maison": 45,
                "appartement": 82,
            },
            "avg_confidence": 0.82,
        },
        accuracy=AccuracyMetrics(
            mae=12500,
            mape=4.2,
            within_range_percent=78,
            sample_size=34,
        ),
        conversion={
            "rdv_scheduled": 89,
            "mandates_signed": 42,
            "conversion_rate": 0.47,
        },
        pricing={
            "avg_decote_vs_seller_expectation": -8.3,
            "avg_decote_vs_final_sale": -2.1,
        },
        objections={
            "total_handled": 156,
            "top_categories": [
                {"category": "price_too_low", "count": 67, "resolution_rate": 0.72},
                {"category": "neighbor_sold_higher", "count": 34, "resolution_rate": 0.68},
                {"category": "other_agency_estimate", "count": 28, "resolution_rate": 0.75},
            ],
        },
        usage={
            "fieldpack_generated": 98,
            "scripts_viewed": 156,
            "coach_sessions": 67,
            "avg_rdv_duration_minutes": 52,
        },
    )


@router.post("/export")
async def export_data(
    data_type: Annotated[str, Query(pattern="^(valuations|events|metrics)$")],
    format: Annotated[str, Query(pattern="^(csv|json)$")] = "csv",
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    """
    Export analytics data in CSV or JSON format.

    Creates an async export job and returns a download URL.
    """
    logger.info(
        "Data export requested",
        data_type=data_type,
        format=format,
    )

    # In production, queue export job
    export_id = "exp_demo123"

    return {
        "export_id": export_id,
        "status": "processing",
        "estimated_rows": 127,
        "download_url": f"/v1/analytics/export/{export_id}/download",
        "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
    }


@router.post("/track")
async def track_event(
    event_type: str,
    entity_id: str | None = None,
    entity_type: str | None = None,
    metadata: dict | None = None,
) -> dict:
    """
    Track an analytics event.

    Used internally to record events for metrics calculation.
    """
    logger.info(
        "Analytics event tracked",
        event_type=event_type,
        entity_id=entity_id,
    )

    # In production, save to events table
    return {
        "status": "tracked",
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
    }
