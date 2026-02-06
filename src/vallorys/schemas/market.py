"""Market context schemas."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class DataQuality(str, Enum):
    """Data quality level."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class MarketContext(BaseModel):
    """Market context for valuation."""
    median_price_sqm: float = Field(gt=0, description="Median price per m²")
    p10_price_sqm: float | None = Field(default=None, description="10th percentile price/m²")
    p90_price_sqm: float | None = Field(default=None, description="90th percentile price/m²")
    transaction_count: int | None = Field(default=None, ge=0)
    trend_12m_percent: float | None = Field(default=None, description="12-month trend in %")
    avg_days_on_market: int | None = None
    supply_demand_ratio: float | None = None
    data_quality: DataQuality = DataQuality.MEDIUM
    last_update: datetime | None = None

    def get_price_range(self) -> tuple[float, float]:
        """Get price range (p10, p90)."""
        p10 = self.p10_price_sqm or self.median_price_sqm * 0.8
        p90 = self.p90_price_sqm or self.median_price_sqm * 1.2
        return (p10, p90)

    def is_reliable(self) -> bool:
        """Check if market data is reliable enough."""
        return (
            self.data_quality in (DataQuality.HIGH, DataQuality.MEDIUM)
            and (self.transaction_count is None or self.transaction_count >= 10)
        )


class ComparableSale(BaseModel):
    """A comparable sale for market analysis."""
    sale_date: datetime
    price: float
    price_sqm: float
    surface: float
    rooms: int | None = None
    property_type: str
    distance_km: float | None = None
    citycode: str


class MarketStats(BaseModel):
    """Detailed market statistics."""
    citycode: str
    property_type: str
    period_months: int
    median_price_sqm: float
    mean_price_sqm: float
    std_price_sqm: float
    deciles: list[float]
    transaction_count: int
    avg_surface: float
    avg_rooms: float | None = None
    dpe_distribution: dict[str, float] | None = None
