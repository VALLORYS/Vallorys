"""Pydantic schemas for VALLORYS."""

from vallorys.schemas.property import (
    PropertyProfile,
    PropertyCondition,
    PropertyAmenities,
    PropertyEnvironment,
    PropertyAddress,
)
from vallorys.schemas.seller import SellerProfile, PreviousEstimate
from vallorys.schemas.market import MarketContext
from vallorys.schemas.valuation import (
    ValuationResult,
    ValuationAdjustment,
    ValuationJustification,
    ValuationRiskFactor,
    ValuationRequest,
    ValuationResponse,
)
from vallorys.schemas.fieldpack import (
    FieldPackRequest,
    FieldPackResponse,
    Argumentaire,
    RdvScript,
    Checklist,
)
from vallorys.schemas.objection import (
    ObjectionRequest,
    ObjectionResponse,
)

__all__ = [
    # Property
    "PropertyProfile",
    "PropertyCondition",
    "PropertyAmenities",
    "PropertyEnvironment",
    "PropertyAddress",
    # Seller
    "SellerProfile",
    "PreviousEstimate",
    # Market
    "MarketContext",
    # Valuation
    "ValuationResult",
    "ValuationAdjustment",
    "ValuationJustification",
    "ValuationRiskFactor",
    "ValuationRequest",
    "ValuationResponse",
    # FieldPack
    "FieldPackRequest",
    "FieldPackResponse",
    "Argumentaire",
    "RdvScript",
    "Checklist",
    # Objection
    "ObjectionRequest",
    "ObjectionResponse",
]
