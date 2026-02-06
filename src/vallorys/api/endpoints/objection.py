"""Objection handling API endpoints."""

import structlog
from fastapi import APIRouter, HTTPException

from vallorys.schemas.objection import (
    ObjectionRequest,
    ObjectionResponse,
    ObjectionLogRequest,
    ProactiveSuggestRequest,
    ProactiveSuggestResponse,
)
from vallorys.services.genai import ObjectionCoach

logger = structlog.get_logger()
router = APIRouter()

# Reference to valuations store
from vallorys.api.endpoints.valuation import _valuations_store


def get_objection_coach() -> ObjectionCoach:
    """Dependency to get objection coach."""
    return ObjectionCoach()


@router.post("/respond", response_model=ObjectionResponse)
async def respond_to_objection(
    request: ObjectionRequest,
) -> ObjectionResponse:
    """
    Get response to a seller objection.

    Provides quick (10s) and detailed (45s) responses,
    with a follow-up question and proof point from the valuation.
    """
    logger.info(
        "Objection response requested",
        category=request.objection_category,
        has_valuation=request.valuation_id is not None,
    )

    # Get valuation if provided
    valuation = None
    if request.valuation_id:
        valuation = _valuations_store.get(request.valuation_id)

    # Get response from coach
    coach = get_objection_coach()

    try:
        response = await coach.respond(
            request=request,
            valuation=valuation,
        )
    except Exception as e:
        logger.error("Objection response failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Objection response failed: {str(e)}",
        )

    logger.info(
        "Objection response generated",
        objection_id=response.objection_id,
        category=response.detected_category.value if response.detected_category else "unknown",
    )

    return response


@router.post("/suggest", response_model=ProactiveSuggestResponse)
async def suggest_proactive(
    request: ProactiveSuggestRequest,
) -> ProactiveSuggestResponse:
    """
    Get proactive suggestions for current meeting phase.

    Returns contextual suggestions to help the agent anticipate
    and handle objections.
    """
    coach = get_objection_coach()

    valuation = None
    if request.valuation_id:
        valuation = _valuations_store.get(request.valuation_id)

    return await coach.suggest_proactive(request, valuation)


@router.post("/log")
async def log_objection_outcome(
    request: ObjectionLogRequest,
) -> dict:
    """
    Log the outcome of an objection handling.

    Used for analytics and improving the coach's responses.
    """
    logger.info(
        "Objection outcome logged",
        objection_id=request.objection_id,
        outcome=request.outcome.value,
        response_used=request.response_used.value,
        feedback=request.agent_feedback.value if request.agent_feedback else None,
    )

    # In production, save to database for analytics
    return {
        "status": "logged",
        "objection_id": request.objection_id,
    }
