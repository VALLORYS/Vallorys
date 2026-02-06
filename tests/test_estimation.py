"""Tests for the estimation engine."""

import pytest

from vallorys.schemas.property import (
    PropertyProfile,
    PropertyAddress,
    PropertyType,
    PropertyCondition,
    PropertyAmenities,
    PropertyEnvironment,
    DPERating,
    ConditionLevel,
    WindowsType,
    ViewQuality,
    NoiseLevel,
)
from vallorys.schemas.market import MarketContext, DataQuality
from vallorys.services.estimation import EstimationEngine
from vallorys.services.estimation.weights import (
    calculate_surface_coefficient,
    get_floor_key,
)


class TestSurfaceCoefficient:
    """Tests for surface degression coefficient calculation."""

    def test_small_surface_no_degression(self):
        """Surfaces <= 100m² should have coefficient 1.0."""
        assert calculate_surface_coefficient(50) == 1.0
        assert calculate_surface_coefficient(100) == 1.0

    def test_large_surface_degression(self):
        """Surfaces > 100m² should have coefficient < 1.0."""
        coef = calculate_surface_coefficient(150)
        assert coef < 1.0
        assert coef > 0.9

    def test_very_large_surface_stronger_degression(self):
        """Very large surfaces should have stronger degression."""
        coef_200 = calculate_surface_coefficient(200)
        coef_300 = calculate_surface_coefficient(300)
        assert coef_300 < coef_200


class TestFloorKey:
    """Tests for floor adjustment key determination."""

    def test_ground_floor_no_garden(self):
        """Ground floor without garden."""
        key = get_floor_key(
            floor=0,
            floors_total=5,
            has_elevator=True,
            has_garden=False,
            property_type=PropertyType.APPARTEMENT,
        )
        assert key == "ground_no_garden"

    def test_ground_floor_with_garden(self):
        """Ground floor with garden."""
        key = get_floor_key(
            floor=0,
            floors_total=5,
            has_elevator=True,
            has_garden=True,
            property_type=PropertyType.APPARTEMENT,
        )
        assert key == "ground_with_garden"

    def test_high_floor_with_elevator(self):
        """High floor with elevator."""
        key = get_floor_key(
            floor=6,
            floors_total=8,
            has_elevator=True,
            has_garden=False,
            property_type=PropertyType.APPARTEMENT,
        )
        assert key == "floor_5_plus_with_elevator"

    def test_house_no_floor_key(self):
        """Houses should not have floor adjustment."""
        key = get_floor_key(
            floor=0,
            floors_total=2,
            has_elevator=False,
            has_garden=True,
            property_type=PropertyType.MAISON,
        )
        assert key == ""


class TestEstimationEngine:
    """Tests for the main estimation engine."""

    @pytest.fixture
    def sample_property(self) -> PropertyProfile:
        """Create a sample property for testing."""
        return PropertyProfile(
            id="test_prop_1",
            address=PropertyAddress(
                street="15 rue de la Paix",
                city="Lyon",
                citycode="69001",
                postal_code="69001",
            ),
            type=PropertyType.APPARTEMENT,
            surface_living=85,
            rooms=4,
            bedrooms=2,
            bathrooms=1,
            floor=3,
            floors_total=5,
            construction_year=1920,
            dpe_rating=DPERating.D,
            condition=PropertyCondition(
                global_=ConditionLevel.GOOD,
                windows=WindowsType.DOUBLE_GLAZING_RECENT,
            ),
            amenities=PropertyAmenities(
                cellar=True,
                balcony=True,
                elevator=True,
            ),
            environment=PropertyEnvironment(
                view=ViewQuality.PLEASANT,
                noise_level=NoiseLevel.MODERATE,
                nearby_shops=True,
                nearby_transport=True,
            ),
        )

    @pytest.fixture
    def sample_market(self) -> MarketContext:
        """Create sample market context."""
        return MarketContext(
            median_price_sqm=4250,
            p10_price_sqm=3500,
            p90_price_sqm=5200,
            transaction_count=156,
            trend_12m_percent=2.3,
            avg_days_on_market=65,
            data_quality=DataQuality.HIGH,
        )

    def test_basic_estimation(self, sample_property, sample_market):
        """Test basic estimation produces valid result."""
        engine = EstimationEngine()
        result = engine.estimate(sample_property, sample_market)

        assert result.range_low > 0
        assert result.range_high > result.range_low
        assert result.range_low <= result.price_point_recommended <= result.range_high
        assert 0 <= result.confidence_score <= 1

    def test_dpe_adjustment_applied(self, sample_property, sample_market):
        """Test that DPE rating affects estimation."""
        engine = EstimationEngine()

        # DPE D
        result_d = engine.estimate(sample_property, sample_market)

        # Change to DPE A
        sample_property.dpe_rating = DPERating.A
        result_a = engine.estimate(sample_property, sample_market)

        # DPE A should result in higher price
        assert result_a.price_point_recommended > result_d.price_point_recommended

    def test_confidence_level_affects_margin(self, sample_property, sample_market):
        """Test that confidence level affects price range margin."""
        engine = EstimationEngine()

        # High quality data
        result_high = engine.estimate(sample_property, sample_market)

        # Low quality data
        sample_market.data_quality = DataQuality.LOW
        sample_market.transaction_count = 5
        result_low = engine.estimate(sample_property, sample_market)

        # Lower confidence should have wider margin
        high_margin = (result_high.range_high - result_high.range_low) / result_high.price_point_recommended
        low_margin = (result_low.range_high - result_low.range_low) / result_low.price_point_recommended

        assert low_margin > high_margin

    def test_adjustments_are_capped(self, sample_property, sample_market):
        """Test that adjustments don't exceed caps."""
        engine = EstimationEngine()
        result = engine.estimate(sample_property, sample_market)

        total_adjustment = result.get_total_adjustment()

        # Total positive adjustment should not exceed max (25%)
        positive_adj = sum(
            a.impact_percent for a in result.adjustments
            if a.direction.value == "positive"
        )
        assert positive_adj <= engine.config.max_total_positive_adjustment

    def test_justification_generated(self, sample_property, sample_market):
        """Test that justification is generated."""
        engine = EstimationEngine()
        result = engine.estimate(sample_property, sample_market)

        assert result.justification is not None
        assert result.justification.summary
        assert result.justification.market_comparison

    def test_risk_factors_identified(self, sample_property, sample_market):
        """Test that risk factors are identified for DPE F/G."""
        sample_property.dpe_rating = DPERating.F

        engine = EstimationEngine()
        result = engine.estimate(sample_property, sample_market)

        # Should have regulatory risk for DPE F
        risk_types = [r.type for r in result.risk_factors]
        assert "regulatory" in risk_types


class TestGoldenCases:
    """Golden test cases with real-world scenarios."""

    def test_renovated_apartment_lyon(self):
        """Renovated apartment in Lyon city center."""
        property = PropertyProfile(
            address=PropertyAddress(city="Lyon", citycode="69001"),
            type=PropertyType.APPARTEMENT,
            surface_living=75,
            rooms=3,
            bedrooms=2,
            floor=4,
            floors_total=6,
            dpe_rating=DPERating.B,
            condition=PropertyCondition(global_=ConditionLevel.EXCELLENT),
            amenities=PropertyAmenities(elevator=True, balcony=True),
        )
        market = MarketContext(
            median_price_sqm=4500,
            transaction_count=200,
            trend_12m_percent=3,
            data_quality=DataQuality.HIGH,
        )

        engine = EstimationEngine()
        result = engine.estimate(property, market)

        # Should be above median due to good condition and DPE
        effective_price_sqm = result.price_point_recommended / property.surface_living
        assert effective_price_sqm > market.median_price_sqm

    def test_house_to_renovate(self):
        """House requiring renovation."""
        property = PropertyProfile(
            address=PropertyAddress(city="Nantes", citycode="44000"),
            type=PropertyType.MAISON,
            surface_living=120,
            surface_land=500,
            rooms=5,
            bedrooms=3,
            dpe_rating=DPERating.F,
            condition=PropertyCondition(global_=ConditionLevel.TO_RENOVATE),
            amenities=PropertyAmenities(garage=True, garden=True),
        )
        market = MarketContext(
            median_price_sqm=3000,
            transaction_count=100,
            data_quality=DataQuality.MEDIUM,
        )

        engine = EstimationEngine()
        result = engine.estimate(property, market)

        # Should be below median due to poor condition
        effective_price_sqm = result.price_point_recommended / property.surface_living
        assert effective_price_sqm < market.median_price_sqm
        assert result.confidence_level.value in ("medium", "low")

    def test_small_studio_paris(self):
        """Small studio in Paris."""
        property = PropertyProfile(
            address=PropertyAddress(city="Paris", citycode="75011"),
            type=PropertyType.APPARTEMENT,
            surface_living=25,
            rooms=1,
            floor=2,
            floors_total=6,
            dpe_rating=DPERating.E,
            amenities=PropertyAmenities(elevator=True),
        )
        market = MarketContext(
            median_price_sqm=10000,
            transaction_count=300,
            trend_12m_percent=-2,
            data_quality=DataQuality.HIGH,
        )

        engine = EstimationEngine()
        result = engine.estimate(property, market)

        # Small surface should not have degression
        assert result.price_point_recommended > 0
        assert result.confidence_score > 0.5
