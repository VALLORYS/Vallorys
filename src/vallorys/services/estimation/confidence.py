"""Confidence score calculation for valuations."""

from dataclasses import dataclass

from vallorys.schemas.property import PropertyProfile, DPERating
from vallorys.schemas.market import MarketContext, DataQuality
from vallorys.schemas.valuation import ConfidenceLevel


@dataclass
class ConfidenceFactors:
    """Factors contributing to confidence score."""
    data_quality: float  # 0-1
    comparable_count: float  # 0-1
    data_recency: float  # 0-1
    property_completeness: float  # 0-1
    market_stability: float  # 0-1


class ConfidenceCalculator:
    """Calculate confidence scores for valuations."""

    # Weights for each factor
    WEIGHTS = {
        "data_quality": 0.25,
        "comparable_count": 0.20,
        "data_recency": 0.15,
        "property_completeness": 0.25,
        "market_stability": 0.15,
    }

    # Thresholds for confidence levels
    HIGH_THRESHOLD = 0.75
    MEDIUM_THRESHOLD = 0.50

    # Margin adjustments based on confidence
    MARGINS = {
        ConfidenceLevel.HIGH: 7,
        ConfidenceLevel.MEDIUM: 10,
        ConfidenceLevel.LOW: 15,
    }

    def calculate(
        self,
        property: PropertyProfile,
        market: MarketContext,
    ) -> tuple[float, ConfidenceLevel, ConfidenceFactors]:
        """
        Calculate confidence score and level.

        Returns: (score, level, factors)
        """
        factors = self._calculate_factors(property, market)

        # Weighted average
        score = (
            factors.data_quality * self.WEIGHTS["data_quality"]
            + factors.comparable_count * self.WEIGHTS["comparable_count"]
            + factors.data_recency * self.WEIGHTS["data_recency"]
            + factors.property_completeness * self.WEIGHTS["property_completeness"]
            + factors.market_stability * self.WEIGHTS["market_stability"]
        )

        # Determine level
        if score >= self.HIGH_THRESHOLD:
            level = ConfidenceLevel.HIGH
        elif score >= self.MEDIUM_THRESHOLD:
            level = ConfidenceLevel.MEDIUM
        else:
            level = ConfidenceLevel.LOW

        return score, level, factors

    def get_margin_for_level(self, level: ConfidenceLevel) -> int:
        """Get price range margin for confidence level."""
        return self.MARGINS[level]

    def _calculate_factors(
        self,
        property: PropertyProfile,
        market: MarketContext,
    ) -> ConfidenceFactors:
        """Calculate individual confidence factors."""
        return ConfidenceFactors(
            data_quality=self._assess_data_quality(market),
            comparable_count=self._assess_comparable_count(market),
            data_recency=self._assess_data_recency(market),
            property_completeness=self._assess_property_completeness(property),
            market_stability=self._assess_market_stability(market),
        )

    def _assess_data_quality(self, market: MarketContext) -> float:
        """Assess market data quality (0-1)."""
        quality_scores = {
            DataQuality.HIGH: 1.0,
            DataQuality.MEDIUM: 0.7,
            DataQuality.LOW: 0.4,
        }
        return quality_scores.get(market.data_quality, 0.5)

    def _assess_comparable_count(self, market: MarketContext) -> float:
        """Assess number of comparable transactions (0-1)."""
        if market.transaction_count is None:
            return 0.5  # Unknown

        # Scale: <10 transactions = low, 10-50 = medium, 50+ = high
        if market.transaction_count < 10:
            return 0.3 + (market.transaction_count / 10) * 0.2
        elif market.transaction_count < 50:
            return 0.5 + ((market.transaction_count - 10) / 40) * 0.3
        else:
            return min(0.8 + (market.transaction_count - 50) / 200, 1.0)

    def _assess_data_recency(self, market: MarketContext) -> float:
        """Assess data recency (0-1)."""
        if market.last_update is None:
            return 0.6  # Assume reasonably recent

        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        if market.last_update.tzinfo is None:
            # Assume UTC if no timezone
            from datetime import timezone
            last_update = market.last_update.replace(tzinfo=timezone.utc)
        else:
            last_update = market.last_update

        days_old = (now - last_update).days

        # Scale: <30 days = high, 30-90 = medium, 90+ = low
        if days_old < 30:
            return 0.9 + (30 - days_old) / 300
        elif days_old < 90:
            return 0.7 - ((days_old - 30) / 60) * 0.2
        else:
            return max(0.3, 0.5 - (days_old - 90) / 365)

    def _assess_property_completeness(self, property: PropertyProfile) -> float:
        """Assess property data completeness (0-1)."""
        # Required fields (always present)
        score = 0.4

        # Important optional fields
        important_fields = [
            property.dpe_rating != DPERating.UNKNOWN,
            property.construction_year is not None,
            property.condition is not None,
            property.floor is not None if property.type.value == "appartement" else True,
        ]
        score += sum(important_fields) * 0.1

        # Nice to have fields
        nice_fields = [
            property.amenities is not None,
            property.environment is not None,
            property.bedrooms is not None,
            property.renovation is not None,
        ]
        score += sum(nice_fields) * 0.05

        return min(score, 1.0)

    def _assess_market_stability(self, market: MarketContext) -> float:
        """Assess market stability (0-1)."""
        if market.trend_12m_percent is None:
            return 0.6  # Unknown, assume moderate

        # Stable = small changes, volatile = large changes
        abs_trend = abs(market.trend_12m_percent)

        if abs_trend < 3:
            return 0.9  # Very stable
        elif abs_trend < 7:
            return 0.7  # Moderately stable
        elif abs_trend < 15:
            return 0.5  # Somewhat volatile
        else:
            return 0.3  # Very volatile
