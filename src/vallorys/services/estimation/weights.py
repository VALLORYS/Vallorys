"""Weighting configuration and adjustment factors for estimation."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from vallorys.schemas.property import (
    PropertyProfile,
    PropertyType,
    DPERating,
    ConditionLevel,
    WindowsType,
    SystemCondition,
    ViewQuality,
    NoiseLevel,
)


class AdjustmentCategory(str, Enum):
    """Categories of adjustments."""
    LOCATION = "location"
    CONDITION = "condition"
    ENERGY = "energy"
    AMENITIES = "amenities"
    ENVIRONMENT = "environment"
    SIZE = "size"


@dataclass
class AdjustmentFactor:
    """An adjustment factor with its impact rules."""
    name: str
    category: AdjustmentCategory
    description: str
    base_impact_percent: float
    max_impact_percent: float
    min_impact_percent: float
    weight: float = 1.0  # For combining multiple factors in same category

    def clamp(self, impact: float) -> tuple[float, bool]:
        """Clamp impact to allowed range, return (clamped_value, was_capped)."""
        if impact > self.max_impact_percent:
            return self.max_impact_percent, True
        if impact < self.min_impact_percent:
            return self.min_impact_percent, True
        return impact, False


@dataclass
class WeightingConfig:
    """Configuration for weighting and adjustment rules."""

    # Global caps
    max_total_positive_adjustment: float = 25.0  # %
    max_total_negative_adjustment: float = -30.0  # %
    max_single_factor_impact: float = 10.0  # %

    # Category caps
    category_caps: dict[AdjustmentCategory, float] = field(default_factory=lambda: {
        AdjustmentCategory.LOCATION: 8.0,
        AdjustmentCategory.CONDITION: 15.0,
        AdjustmentCategory.ENERGY: 10.0,
        AdjustmentCategory.AMENITIES: 10.0,
        AdjustmentCategory.ENVIRONMENT: 5.0,
        AdjustmentCategory.SIZE: 8.0,
    })

    # DPE adjustments
    dpe_impacts: dict[DPERating, float] = field(default_factory=lambda: {
        DPERating.A: 5.0,
        DPERating.B: 3.0,
        DPERating.C: 0.0,  # Reference
        DPERating.D: -3.0,
        DPERating.E: -6.0,
        DPERating.F: -10.0,
        DPERating.G: -15.0,
        DPERating.UNKNOWN: -2.0,  # Penalty for unknown
    })

    # Global condition adjustments
    condition_impacts: dict[ConditionLevel, float] = field(default_factory=lambda: {
        ConditionLevel.EXCELLENT: 8.0,
        ConditionLevel.GOOD: 2.0,
        ConditionLevel.AVERAGE: 0.0,  # Reference
        ConditionLevel.POOR: -8.0,
        ConditionLevel.TO_RENOVATE: -15.0,
    })

    # Windows adjustments
    windows_impacts: dict[WindowsType, float] = field(default_factory=lambda: {
        WindowsType.DOUBLE_GLAZING_RECENT: 2.0,
        WindowsType.DOUBLE_GLAZING_OLD: 0.0,
        WindowsType.SINGLE_GLAZING: -4.0,
    })

    # System condition adjustments (electrical, plumbing, heating)
    system_impacts: dict[SystemCondition, float] = field(default_factory=lambda: {
        SystemCondition.RECENT: 2.0,
        SystemCondition.UP_TO_CODE: 1.0,
        SystemCondition.FUNCTIONAL: 0.0,
        SystemCondition.TO_RENOVATE: -4.0,
        SystemCondition.TO_REPLACE: -6.0,
    })

    # View adjustments
    view_impacts: dict[ViewQuality, float] = field(default_factory=lambda: {
        ViewQuality.EXCEPTIONAL: 5.0,
        ViewQuality.PLEASANT: 2.0,
        ViewQuality.ORDINARY: 0.0,
        ViewQuality.OBSTRUCTED: -3.0,
    })

    # Noise level adjustments
    noise_impacts: dict[NoiseLevel, float] = field(default_factory=lambda: {
        NoiseLevel.VERY_QUIET: 3.0,
        NoiseLevel.QUIET: 1.0,
        NoiseLevel.MODERATE: 0.0,
        NoiseLevel.NOISY: -5.0,
    })

    # Amenities base impacts (to be scaled)
    amenities_impacts: dict[str, float] = field(default_factory=lambda: {
        "garage": 3.0,
        "parking_spots": 1.5,  # Per spot, capped at 2
        "cellar": 1.5,
        "pool": 5.0,
        "terrace": 3.0,
        "balcony": 2.0,
        "garden": 3.0,
        "elevator": 2.0,  # Only for apartments above 2nd floor
        "fireplace": 1.0,
    })

    # Floor adjustments for apartments
    floor_adjustments: dict[str, float] = field(default_factory=lambda: {
        "ground_no_garden": -3.0,
        "ground_with_garden": 2.0,
        "floor_1": 0.0,
        "floor_2": 1.0,
        "floor_3_4": 2.0,
        "floor_5_plus_no_elevator": -2.0,
        "floor_5_plus_with_elevator": 3.0,
        "top_floor_no_elevator": 0.0,
        "top_floor_with_elevator": 4.0,
    })

    # Surface degression thresholds (for very large properties)
    surface_degression: list[tuple[float, float]] = field(default_factory=lambda: [
        (100, 1.0),   # 0-100m²: full price/m²
        (150, 0.95),  # 100-150m²: 95% price/m²
        (200, 0.90),  # 150-200m²: 90% price/m²
        (300, 0.85),  # 200-300m²: 85% price/m²
        (float("inf"), 0.80),  # 300m²+: 80% price/m²
    ])

    # Proximity impacts
    proximity_impacts: dict[str, float] = field(default_factory=lambda: {
        "nearby_shops": 1.0,
        "nearby_transport": 2.0,
        "nearby_schools": 1.0,
    })

    def get_category_cap(self, category: AdjustmentCategory) -> float:
        """Get the cap for a category."""
        return self.category_caps.get(category, self.max_single_factor_impact)


# Default configuration
DEFAULT_WEIGHTING_CONFIG = WeightingConfig()


def calculate_surface_coefficient(
    surface: float,
    config: WeightingConfig = DEFAULT_WEIGHTING_CONFIG,
) -> float:
    """
    Calculate degressive coefficient for large surfaces.

    For surfaces > 100m², apply degression to avoid overvaluation.
    """
    if surface <= 100:
        return 1.0

    # Calculate weighted average across tiers
    remaining = surface
    weighted_sum = 0.0
    prev_threshold = 0

    for threshold, coef in config.surface_degression:
        tier_size = min(remaining, threshold - prev_threshold)
        if tier_size <= 0:
            break
        weighted_sum += tier_size * coef
        remaining -= tier_size
        prev_threshold = threshold

    return weighted_sum / surface


def get_floor_key(
    floor: int | None,
    floors_total: int | None,
    has_elevator: bool,
    has_garden: bool,
    property_type: PropertyType,
) -> str:
    """Determine floor adjustment key based on property characteristics."""
    if property_type != PropertyType.APPARTEMENT:
        return ""  # No floor adjustment for houses

    if floor is None:
        return ""

    is_top_floor = floors_total is not None and floor == floors_total

    if floor == 0:  # Ground floor
        return "ground_with_garden" if has_garden else "ground_no_garden"

    if is_top_floor:
        return "top_floor_with_elevator" if has_elevator else "top_floor_no_elevator"

    if floor >= 5:
        return "floor_5_plus_with_elevator" if has_elevator else "floor_5_plus_no_elevator"

    if floor >= 3:
        return "floor_3_4"

    if floor == 2:
        return "floor_2"

    return "floor_1"
