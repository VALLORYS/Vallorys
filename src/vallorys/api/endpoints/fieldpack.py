"""Field pack generation API endpoints."""

import structlog
from fastapi import APIRouter, HTTPException

from vallorys.schemas.fieldpack import FieldPackRequest, FieldPackResponse
from vallorys.schemas.property import PropertyProfile, PropertyAddress, PropertyType
from vallorys.schemas.valuation import ValuationResult
from vallorys.services.genai import FieldPackGenerator

logger = structlog.get_logger()
router = APIRouter()

# Reference to valuations store (shared with valuation endpoint)
# In production, this would be a database
from vallorys.api.endpoints.valuation import _valuations_store


def get_fieldpack_generator() -> FieldPackGenerator:
    """Dependency to get field pack generator."""
    return FieldPackGenerator()


@router.post("/generate", response_model=FieldPackResponse)
async def generate_fieldpack(
    request: FieldPackRequest,
) -> FieldPackResponse:
    """
    Generate a complete field pack.

    Creates personalized argumentaire, RDV script, checklist,
    and templates based on the valuation and seller context.
    """
    logger.info(
        "Field pack generation requested",
        valuation_id=request.valuation_id,
    )

    # Get valuation
    valuation = _valuations_store.get(request.valuation_id)
    if not valuation:
        raise HTTPException(status_code=404, detail="Valuation not found")

    # Get property from valuation (in production, fetch from DB)
    # For demo, create a minimal property profile
    property = PropertyProfile(
        address=PropertyAddress(
            city="Unknown",
            citycode="00000",
        ),
        type=PropertyType.APPARTEMENT,
        surface_living=100,  # Default
    )

    # Generate field pack
    generator = get_fieldpack_generator()

    try:
        response = await generator.generate(
            request=request,
            property=property,
            valuation=valuation,
            seller=request.seller,
        )
    except Exception as e:
        logger.error("Field pack generation failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Field pack generation failed: {str(e)}",
        )

    logger.info(
        "Field pack generated",
        fieldpack_id=response.fieldpack_id,
    )

    return response
