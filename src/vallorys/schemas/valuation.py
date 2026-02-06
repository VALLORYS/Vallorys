"""Valuation schemas."""

from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field

from vallorys.schemas.property import PropertyProfile
from vallorys.schemas.seller import SellerProfile
from vallorys.schemas.market import MarketContext


class ConfidenceLevel(str, Enum):
    """Confidence level for valuation."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AdjustmentDirection(str, Enum):
    """Direction of adjustment impact."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class RiskSeverity(str, Enum):
    """Risk severity level."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ValuationAdjustment(BaseModel):
    """A single adjustment factor in the valuation."""
    factor: str
    impact_percent: float = Field(description="Impact in percentage points")
    direction: AdjustmentDirection
    explanation: str
    capped: bool = False
    raw_impact_percent: float | None = Field(
        default=None,
        description="Original impact before capping"
    )


class ValuationJustification(BaseModel):
    """Justification for the valuation."""
    summary: str
    top_positive_factors: list[str] = []
    top_negative_factors: list[str] = []
    market_comparison: str | None = None


class ValuationRiskFactor(BaseModel):
    """A risk factor identified in the valuation."""
    type: str
    description: str
    severity: RiskSeverity


class ValuationResult(BaseModel):
    """Complete valuation result."""
    id: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    property_id: str | None = None
    range_low: float
    range_high: float
    price_point_recommended: float
    confidence_score: Annotated[float, Field(ge=0, le=1)]
    confidence_level: ConfidenceLevel
    margin_percent: float = Field(default=7, description="Margin for range calculation")
    base_price_sqm_used: float
    adjustments: list[ValuationAdjustment] = []
    justification: ValuationJustification | None = None
    risk_factors: list[ValuationRiskFactor] = []
    market_context: MarketContext | None = None
    data_completeness: Annotated[float, Field(ge=0, le=1)] = 1.0
    methodology_version: str = "2.1.0"

    def get_total_adjustment(self) -> float:
        """Calculate total adjustment percentage."""
        return sum(adj.impact_percent for adj in self.adjustments)

    def is_within_market_range(self) -> bool:
        """Check if valuation is within market P10-P90 range."""
        if not self.market_context:
            return True
        p10, p90 = self.market_context.get_price_range()
        price_sqm = self.price_point_recommended / self.base_price_sqm_used
        return p10 <= price_sqm <= p90


class ValuationOptions(BaseModel):
    """Options for valuation request."""
    include_comparables: bool = False
    include_detailed_justification: bool = True
    force_confidence_level: ConfidenceLevel | None = None


class ValuationRequest(BaseModel):
    """Request for property valuation."""
    property: PropertyProfile
    seller: SellerProfile | None = None
    market_context: MarketContext | None = Field(
        default=None,
        description="If not provided, will be fetched from DVF"
    )
    options: ValuationOptions = Field(default_factory=ValuationOptions)


class ValuationResponse(BaseModel):
    """Response for valuation request."""
    valuation_id: str
    created_at: datetime
    property_id: str | None = None
    range_low: float
    range_high: float
    price_point_recommended: float
    confidence_score: float
    confidence_level: ConfidenceLevel
    margin_percent: float
    base_price_sqm_used: float
    adjustments: list[ValuationAdjustment]
    justification: ValuationJustification | None = None
    risk_factors: list[ValuationRiskFactor]
    market_context: MarketContext | None = None
    data_completeness: float
    methodology_version: str

    @classmethod
    def from_result(cls, result: ValuationResult, valuation_id: str) -> "ValuationResponse":
        """Create response from valuation result."""
        return cls(
            valuation_id=valuation_id,
            created_at=result.created_at,
            property_id=result.property_id,
            range_low=result.range_low,
            range_high=result.range_high,
            price_point_recommended=result.price_point_recommended,
            confidence_score=result.confidence_score,
            confidence_level=result.confidence_level,
            margin_percent=result.margin_percent,
            base_price_sqm_used=result.base_price_sqm_used,
            adjustments=result.adjustments,
            justification=result.justification,
            risk_factors=result.risk_factors,
            market_context=result.market_context,
            data_completeness=result.data_completeness,
            methodology_version=result.methodology_version,
        )
