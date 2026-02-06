"""Valuation API endpoints."""

import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query

from vallorys.schemas.valuation import (
    ValuationRequest,
    ValuationResponse,
    ValuationResult,
)
from vallorys.schemas.market import MarketContext, DataQuality
from vallorys.services.estimation import EstimationEngine

logger = structlog.get_logger()
router = APIRouter()


# In-memory storage for demo (replace with database in production)
_valuations_store: dict[str, ValuationResult] = {}


def get_estimation_engine() -> EstimationEngine:
    """Dependency to get estimation engine."""
    return EstimationEngine()


async def get_market_context(
    citycode: str,
    property_type: str,
) -> MarketContext:
    """
    Fetch market context from DVF API or cache.

    In production, this would call the DVF API and cache results.
    For demo, returns mock data.
    """
    # TODO: Implement real DVF API integration
    # Mock market data based on citycode
    mock_data = {
        "69001": {"median": 4250, "trend": 2.3, "count": 156},  # Lyon 1er
        "75001": {"median": 12500, "trend": -1.2, "count": 89},  # Paris 1er
        "33000": {"median": 3800, "trend": 4.1, "count": 234},  # Bordeaux
        "13001": {"median": 3200, "trend": 1.8, "count": 178},  # Marseille
    }

    data = mock_data.get(citycode, {"median": 3000, "trend": 0, "count": 50})

    return MarketContext(
        median_price_sqm=data["median"],
        p10_price_sqm=data["median"] * 0.75,
        p90_price_sqm=data["median"] * 1.30,
        transaction_count=data["count"],
        trend_12m_percent=data["trend"],
        avg_days_on_market=65,
        data_quality=DataQuality.HIGH if data["count"] > 100 else DataQuality.MEDIUM,
    )


@router.post("/run", response_model=ValuationResponse)
async def run_valuation(
    request: ValuationRequest,
    engine: Annotated[EstimationEngine, Depends(get_estimation_engine)],
) -> ValuationResponse:
    """
    Run a property valuation.

    Generates a complete valuation with price range, confidence score,
    adjustments, and justification.
    """
    logger.info(
        "Valuation request received",
        citycode=request.property.address.citycode,
        property_type=request.property.type.value,
    )

    # Get market context if not provided
    market = request.market_context
    if not market:
        market = await get_market_context(
            request.property.address.citycode,
            request.property.type.value,
        )

    # Run estimation
    try:
        result = engine.estimate(request.property, market)
    except Exception as e:
        logger.error("Valuation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Valuation failed: {str(e)}")

    # Store result
    valuation_id = result.id or f"val_{uuid.uuid4().hex[:12]}"
    _valuations_store[valuation_id] = result

    # Build response
    response = ValuationResponse.from_result(result, valuation_id)

    logger.info(
        "Valuation completed",
        valuation_id=valuation_id,
        price_point=result.price_point_recommended,
        confidence=result.confidence_level.value,
    )

    return response


@router.get("/{valuation_id}", response_model=ValuationResponse)
async def get_valuation(valuation_id: str) -> ValuationResponse:
    """
    Get an existing valuation by ID.
    """
    result = _valuations_store.get(valuation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Valuation not found")

    return ValuationResponse.from_result(result, valuation_id)


@router.get("/{valuation_id}/explain")
async def explain_valuation(
    valuation_id: str,
    detail_level: Annotated[str, Query(pattern="^(summary|detailed|technical)$")] = "detailed",
) -> dict:
    """
    Get detailed explanation of a valuation.
    """
    result = _valuations_store.get(valuation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Valuation not found")

    # Build explanation based on detail level
    explanation = {
        "valuation_id": valuation_id,
        "detail_level": detail_level,
        "explanation": {
            "methodology": (
                "L'estimation utilise la méthode des comparables ajustée "
                "avec pondération des critères. Base : prix/m² médian du secteur "
                "sur 12 mois glissants."
            ),
            "base_calculation": {
                "median_price_sqm": result.base_price_sqm_used,
                "formula": f"{result.base_price_sqm_used} €/m² × surface",
            },
            "adjustments_breakdown": [
                {
                    "factor": adj.factor,
                    "impact_percent": adj.impact_percent,
                    "direction": adj.direction.value,
                    "explanation": adj.explanation,
                    "capped": adj.capped,
                }
                for adj in result.adjustments
            ],
            "final_calculation": {
                "price_point": result.price_point_recommended,
                "range_margin": result.margin_percent,
                "range_low": result.range_low,
                "range_high": result.range_high,
            },
            "confidence_factors": {
                "data_completeness": result.data_completeness,
                "final_score": result.confidence_score,
                "level": result.confidence_level.value,
            },
        },
    }

    if detail_level == "summary":
        explanation["explanation"] = {
            "summary": result.justification.summary if result.justification else "",
            "price_point": result.price_point_recommended,
            "confidence": result.confidence_level.value,
        }

    return explanation
