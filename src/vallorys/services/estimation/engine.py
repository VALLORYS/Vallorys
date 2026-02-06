"""Core estimation engine."""

import uuid
from datetime import datetime

import structlog

from vallorys.schemas.property import PropertyProfile, PropertyType, DPERating, ConditionLevel
from vallorys.schemas.market import MarketContext
from vallorys.schemas.valuation import (
    ValuationResult,
    ValuationAdjustment,
    ValuationJustification,
    ValuationRiskFactor,
    AdjustmentDirection,
    ConfidenceLevel,
    RiskSeverity,
)
from vallorys.services.estimation.weights import (
    WeightingConfig,
    AdjustmentCategory,
    DEFAULT_WEIGHTING_CONFIG,
    calculate_surface_coefficient,
    get_floor_key,
)
from vallorys.services.estimation.confidence import ConfidenceCalculator

logger = structlog.get_logger()


class EstimationEngine:
    """
    Core estimation engine with weighting rules and clamping.

    Methodology:
    1. Start with median price/m² from market data
    2. Apply surface degression for large properties
    3. Calculate adjustments for each factor
    4. Apply category-level and global caps
    5. Calculate confidence score
    6. Determine price range based on confidence
    """

    def __init__(self, config: WeightingConfig | None = None):
        self.config = config or DEFAULT_WEIGHTING_CONFIG
        self.confidence_calc = ConfidenceCalculator()

    def estimate(
        self,
        property: PropertyProfile,
        market: MarketContext,
    ) -> ValuationResult:
        """
        Generate a complete valuation for a property.

        Args:
            property: Property profile with all characteristics
            market: Market context with price data

        Returns:
            Complete valuation result with range, adjustments, and justification
        """
        logger.info(
            "Starting estimation",
            citycode=property.address.citycode,
            property_type=property.type.value,
            surface=property.surface_living,
        )

        # Step 1: Calculate base price
        base_price_sqm = market.median_price_sqm
        surface = property.surface_living

        # Apply surface degression
        surface_coef = calculate_surface_coefficient(surface, self.config)
        effective_price_sqm = base_price_sqm * surface_coef

        base_price = effective_price_sqm * surface

        logger.debug(
            "Base price calculated",
            base_price_sqm=base_price_sqm,
            surface_coef=surface_coef,
            base_price=base_price,
        )

        # Step 2: Calculate all adjustments
        adjustments = self._calculate_all_adjustments(property, market)

        # Step 3: Apply caps and calculate total impact
        adjustments = self._apply_caps(adjustments)
        total_adjustment_percent = sum(adj.impact_percent for adj in adjustments)

        # Step 4: Calculate final price
        price_point = base_price * (1 + total_adjustment_percent / 100)

        # Step 5: Calculate confidence
        confidence_score, confidence_level, _ = self.confidence_calc.calculate(
            property, market
        )

        # Step 6: Determine margin and range
        margin_percent = self.confidence_calc.get_margin_for_level(confidence_level)
        range_low = price_point * (1 - margin_percent / 100)
        range_high = price_point * (1 + margin_percent / 100)

        # Round prices to nearest 1000€
        price_point = round(price_point / 1000) * 1000
        range_low = round(range_low / 1000) * 1000
        range_high = round(range_high / 1000) * 1000

        # Step 7: Generate justification
        justification = self._generate_justification(
            property, market, adjustments, price_point
        )

        # Step 8: Identify risk factors
        risk_factors = self._identify_risk_factors(property, market, adjustments)

        # Step 9: Calculate data completeness
        data_completeness = self._calculate_data_completeness(property)

        result = ValuationResult(
            id=f"val_{uuid.uuid4().hex[:12]}",
            created_at=datetime.utcnow(),
            property_id=property.id,
            range_low=range_low,
            range_high=range_high,
            price_point_recommended=price_point,
            confidence_score=confidence_score,
            confidence_level=confidence_level,
            margin_percent=margin_percent,
            base_price_sqm_used=base_price_sqm,
            adjustments=adjustments,
            justification=justification,
            risk_factors=risk_factors,
            market_context=market,
            data_completeness=data_completeness,
        )

        logger.info(
            "Estimation completed",
            valuation_id=result.id,
            price_point=price_point,
            range_low=range_low,
            range_high=range_high,
            confidence=confidence_level.value,
            total_adjustment=total_adjustment_percent,
        )

        return result

    def _calculate_all_adjustments(
        self,
        property: PropertyProfile,
        market: MarketContext,
    ) -> list[ValuationAdjustment]:
        """Calculate all adjustment factors."""
        adjustments = []

        # DPE/Energy adjustment
        dpe_adj = self._calculate_dpe_adjustment(property)
        if dpe_adj:
            adjustments.append(dpe_adj)

        # Condition adjustments
        condition_adjs = self._calculate_condition_adjustments(property)
        adjustments.extend(condition_adjs)

        # Floor adjustment (apartments only)
        floor_adj = self._calculate_floor_adjustment(property)
        if floor_adj:
            adjustments.append(floor_adj)

        # Amenities adjustments
        amenities_adjs = self._calculate_amenities_adjustments(property)
        adjustments.extend(amenities_adjs)

        # Environment adjustments
        env_adjs = self._calculate_environment_adjustments(property)
        adjustments.extend(env_adjs)

        # Location premium (based on market position)
        location_adj = self._calculate_location_adjustment(property, market)
        if location_adj:
            adjustments.append(location_adj)

        return adjustments

    def _calculate_dpe_adjustment(
        self,
        property: PropertyProfile,
    ) -> ValuationAdjustment | None:
        """Calculate DPE energy rating adjustment."""
        impact = self.config.dpe_impacts.get(property.dpe_rating, 0)

        if impact == 0:
            return None

        direction = AdjustmentDirection.POSITIVE if impact > 0 else AdjustmentDirection.NEGATIVE

        explanations = {
            "A": "DPE A : excellent bilan énergétique, très recherché",
            "B": "DPE B : très bon bilan énergétique",
            "C": "DPE C : bilan énergétique dans la moyenne",
            "D": "DPE D : légère décote énergétique",
            "E": "DPE E : décote énergétique significative",
            "F": "DPE F : passoire thermique, travaux à prévoir",
            "G": "DPE G : passoire thermique, travaux importants nécessaires",
            "unknown": "DPE inconnu : incertitude pénalisante",
        }

        return ValuationAdjustment(
            factor="dpe_rating",
            impact_percent=impact,
            direction=direction,
            explanation=explanations.get(property.dpe_rating.value, ""),
            capped=False,
        )

    def _calculate_condition_adjustments(
        self,
        property: PropertyProfile,
    ) -> list[ValuationAdjustment]:
        """Calculate condition-related adjustments."""
        adjustments = []
        condition = property.get_effective_condition()

        # Global condition
        if condition.global_:
            impact = self.config.condition_impacts.get(condition.global_, 0)
            if impact != 0:
                direction = (
                    AdjustmentDirection.POSITIVE if impact > 0
                    else AdjustmentDirection.NEGATIVE
                )
                adjustments.append(ValuationAdjustment(
                    factor="condition_global",
                    impact_percent=impact,
                    direction=direction,
                    explanation=f"État général {condition.global_.value}",
                    capped=False,
                ))

        # Windows
        if condition.windows:
            impact = self.config.windows_impacts.get(condition.windows, 0)
            if impact != 0:
                direction = (
                    AdjustmentDirection.POSITIVE if impact > 0
                    else AdjustmentDirection.NEGATIVE
                )
                adjustments.append(ValuationAdjustment(
                    factor="windows",
                    impact_percent=impact,
                    direction=direction,
                    explanation=f"Fenêtres : {condition.windows.value.replace('_', ' ')}",
                    capped=False,
                ))

        # Electrical
        if condition.electrical:
            impact = self.config.system_impacts.get(condition.electrical, 0)
            if impact != 0:
                direction = (
                    AdjustmentDirection.POSITIVE if impact > 0
                    else AdjustmentDirection.NEGATIVE
                )
                adjustments.append(ValuationAdjustment(
                    factor="electrical",
                    impact_percent=impact,
                    direction=direction,
                    explanation=f"Installation électrique : {condition.electrical.value}",
                    capped=False,
                ))

        return adjustments

    def _calculate_floor_adjustment(
        self,
        property: PropertyProfile,
    ) -> ValuationAdjustment | None:
        """Calculate floor adjustment for apartments."""
        if property.type != PropertyType.APPARTEMENT:
            return None

        amenities = property.get_effective_amenities()
        floor_key = get_floor_key(
            floor=property.floor,
            floors_total=property.floors_total,
            has_elevator=amenities.elevator,
            has_garden=amenities.garden,
            property_type=property.type,
        )

        if not floor_key:
            return None

        impact = self.config.floor_adjustments.get(floor_key, 0)
        if impact == 0:
            return None

        direction = (
            AdjustmentDirection.POSITIVE if impact > 0
            else AdjustmentDirection.NEGATIVE
        )

        explanation_parts = []
        if property.floor == 0:
            explanation_parts.append("Rez-de-chaussée")
            if amenities.garden:
                explanation_parts.append("avec jardin privatif")
        elif property.floor is not None:
            explanation_parts.append(f"{property.floor}ème étage")
            if amenities.elevator:
                explanation_parts.append("avec ascenseur")
            else:
                explanation_parts.append("sans ascenseur")

        return ValuationAdjustment(
            factor="floor",
            impact_percent=impact,
            direction=direction,
            explanation=" ".join(explanation_parts),
            capped=False,
        )

    def _calculate_amenities_adjustments(
        self,
        property: PropertyProfile,
    ) -> list[ValuationAdjustment]:
        """Calculate amenities adjustments."""
        adjustments = []
        amenities = property.get_effective_amenities()

        amenity_checks = [
            ("garage", amenities.garage, "Garage"),
            ("cellar", amenities.cellar, "Cave"),
            ("pool", amenities.pool, "Piscine"),
            ("terrace", amenities.terrace, "Terrasse"),
            ("balcony", amenities.balcony, "Balcon"),
            ("fireplace", amenities.fireplace, "Cheminée"),
        ]

        # Garden only for houses
        if property.type == PropertyType.MAISON and amenities.garden:
            amenity_checks.append(("garden", True, "Jardin"))

        for key, has_amenity, label in amenity_checks:
            if has_amenity:
                impact = self.config.amenities_impacts.get(key, 0)
                if impact > 0:
                    adjustments.append(ValuationAdjustment(
                        factor=key,
                        impact_percent=impact,
                        direction=AdjustmentDirection.POSITIVE,
                        explanation=label,
                        capped=False,
                    ))

        # Parking spots (max 2 counted)
        if amenities.parking_spots > 0:
            spots = min(amenities.parking_spots, 2)
            impact = self.config.amenities_impacts.get("parking_spots", 0) * spots
            adjustments.append(ValuationAdjustment(
                factor="parking",
                impact_percent=impact,
                direction=AdjustmentDirection.POSITIVE,
                explanation=f"{amenities.parking_spots} place(s) de parking",
                capped=False,
            ))

        return adjustments

    def _calculate_environment_adjustments(
        self,
        property: PropertyProfile,
    ) -> list[ValuationAdjustment]:
        """Calculate environment adjustments."""
        adjustments = []
        env = property.get_effective_environment()

        # View
        if env.view:
            impact = self.config.view_impacts.get(env.view, 0)
            if impact != 0:
                direction = (
                    AdjustmentDirection.POSITIVE if impact > 0
                    else AdjustmentDirection.NEGATIVE
                )
                adjustments.append(ValuationAdjustment(
                    factor="view",
                    impact_percent=impact,
                    direction=direction,
                    explanation=f"Vue {env.view.value}",
                    capped=False,
                ))

        # Noise
        if env.noise_level:
            impact = self.config.noise_impacts.get(env.noise_level, 0)
            if impact != 0:
                direction = (
                    AdjustmentDirection.POSITIVE if impact > 0
                    else AdjustmentDirection.NEGATIVE
                )
                adjustments.append(ValuationAdjustment(
                    factor="noise",
                    impact_percent=impact,
                    direction=direction,
                    explanation=f"Niveau sonore {env.noise_level.value}",
                    capped=False,
                ))

        # Proximity
        proximity_items = [
            ("nearby_shops", env.nearby_shops, "Commerces à proximité"),
            ("nearby_transport", env.nearby_transport, "Transports à proximité"),
            ("nearby_schools", env.nearby_schools, "Écoles à proximité"),
        ]

        for key, has_proximity, label in proximity_items:
            if has_proximity:
                impact = self.config.proximity_impacts.get(key, 0)
                if impact > 0:
                    adjustments.append(ValuationAdjustment(
                        factor=key,
                        impact_percent=impact,
                        direction=AdjustmentDirection.POSITIVE,
                        explanation=label,
                        capped=False,
                    ))

        return adjustments

    def _calculate_location_adjustment(
        self,
        property: PropertyProfile,
        market: MarketContext,
    ) -> ValuationAdjustment | None:
        """
        Calculate location premium based on market position.

        If the property is in a sought-after area (high transaction volume,
        positive trend), apply a modest premium.
        """
        if market.transaction_count is None:
            return None

        # High volume + positive trend = premium location
        impact = 0.0

        if market.transaction_count > 100:
            impact += 2.0  # High liquidity premium

        if market.trend_12m_percent is not None and market.trend_12m_percent > 3:
            impact += min(market.trend_12m_percent / 2, 3.0)  # Trend premium, capped

        if impact <= 0:
            return None

        # Cap at 5%
        capped = impact > 5
        impact = min(impact, 5.0)

        return ValuationAdjustment(
            factor="location_premium",
            impact_percent=impact,
            direction=AdjustmentDirection.POSITIVE,
            explanation="Secteur recherché avec forte liquidité",
            capped=capped,
            raw_impact_percent=impact if not capped else impact + 1,
        )

    def _apply_caps(
        self,
        adjustments: list[ValuationAdjustment],
    ) -> list[ValuationAdjustment]:
        """Apply category-level and global caps to adjustments."""
        # Group by category (simplified - in real impl, would track categories)
        total_positive = sum(
            adj.impact_percent for adj in adjustments
            if adj.direction == AdjustmentDirection.POSITIVE
        )
        total_negative = sum(
            adj.impact_percent for adj in adjustments
            if adj.direction == AdjustmentDirection.NEGATIVE
        )

        # Apply global caps
        if total_positive > self.config.max_total_positive_adjustment:
            scale = self.config.max_total_positive_adjustment / total_positive
            for adj in adjustments:
                if adj.direction == AdjustmentDirection.POSITIVE:
                    original = adj.impact_percent
                    adj.impact_percent = adj.impact_percent * scale
                    if original != adj.impact_percent:
                        adj.capped = True
                        adj.raw_impact_percent = original

        if total_negative < self.config.max_total_negative_adjustment:
            scale = self.config.max_total_negative_adjustment / total_negative
            for adj in adjustments:
                if adj.direction == AdjustmentDirection.NEGATIVE:
                    original = adj.impact_percent
                    adj.impact_percent = adj.impact_percent * scale
                    if original != adj.impact_percent:
                        adj.capped = True
                        adj.raw_impact_percent = original

        return adjustments

    def _generate_justification(
        self,
        property: PropertyProfile,
        market: MarketContext,
        adjustments: list[ValuationAdjustment],
        price_point: float,
    ) -> ValuationJustification:
        """Generate human-readable justification."""
        positive = [
            adj for adj in adjustments
            if adj.direction == AdjustmentDirection.POSITIVE
        ]
        negative = [
            adj for adj in adjustments
            if adj.direction == AdjustmentDirection.NEGATIVE
        ]

        # Sort by impact
        positive.sort(key=lambda x: x.impact_percent, reverse=True)
        negative.sort(key=lambda x: x.impact_percent)

        top_positive = [adj.explanation for adj in positive[:3]]
        top_negative = [adj.explanation for adj in negative[:3]]

        price_sqm = price_point / property.surface_living
        diff_percent = ((price_sqm / market.median_price_sqm) - 1) * 100

        market_comparison = (
            f"Prix au m² estimé : {price_sqm:,.0f} €/m² "
            f"vs médiane secteur {market.median_price_sqm:,.0f} €/m² "
            f"({diff_percent:+.1f}%)"
        )

        summary_parts = [
            f"{property.type.value.capitalize()} de {property.surface_living}m²",
            f"situé à {property.address.city}.",
        ]

        if top_positive:
            summary_parts.append(f"Points forts : {', '.join(top_positive[:2]).lower()}.")

        if top_negative:
            summary_parts.append(f"Points d'attention : {', '.join(top_negative[:2]).lower()}.")

        return ValuationJustification(
            summary=" ".join(summary_parts),
            top_positive_factors=top_positive,
            top_negative_factors=top_negative,
            market_comparison=market_comparison,
        )

    def _identify_risk_factors(
        self,
        property: PropertyProfile,
        market: MarketContext,
        adjustments: list[ValuationAdjustment],
    ) -> list[ValuationRiskFactor]:
        """Identify risk factors in the valuation."""
        risks = []

        # DPE regulatory risk
        if property.dpe_rating in (DPERating.F, DPERating.G):
            risks.append(ValuationRiskFactor(
                type="regulatory",
                description=(
                    f"DPE {property.dpe_rating.value} : interdiction de location "
                    "prévue par la loi Climat. Travaux de rénovation énergétique nécessaires."
                ),
                severity=RiskSeverity.HIGH,
            ))
        elif property.dpe_rating == DPERating.E:
            risks.append(ValuationRiskFactor(
                type="regulatory",
                description=(
                    "DPE E : interdiction de location à partir de 2034 "
                    "sans rénovation énergétique."
                ),
                severity=RiskSeverity.MEDIUM,
            ))

        # Market volatility risk
        if market.trend_12m_percent is not None and abs(market.trend_12m_percent) > 10:
            direction = "hausse" if market.trend_12m_percent > 0 else "baisse"
            risks.append(ValuationRiskFactor(
                type="market",
                description=f"Marché volatil avec {direction} de {abs(market.trend_12m_percent):.1f}% sur 12 mois.",
                severity=RiskSeverity.MEDIUM,
            ))

        # Data quality risk
        if market.data_quality == "low":
            risks.append(ValuationRiskFactor(
                type="data",
                description="Données de marché limitées, estimation moins fiable.",
                severity=RiskSeverity.MEDIUM,
            ))

        # Condition risk
        condition = property.get_effective_condition()
        if condition.global_ in (ConditionLevel.POOR, ConditionLevel.TO_RENOVATE):
            risks.append(ValuationRiskFactor(
                type="condition",
                description="État général nécessitant des travaux importants.",
                severity=RiskSeverity.MEDIUM,
            ))

        return risks

    def _calculate_data_completeness(self, property: PropertyProfile) -> float:
        """Calculate data completeness score."""
        total_fields = 15
        filled = 5  # Required fields always present

        optional_checks = [
            property.dpe_rating != DPERating.UNKNOWN,
            property.construction_year is not None,
            property.bedrooms is not None,
            property.bathrooms is not None,
            property.condition is not None,
            property.amenities is not None,
            property.environment is not None,
            property.floor is not None,
            property.floors_total is not None,
            property.renovation is not None,
        ]

        filled += sum(optional_checks)
        return filled / total_fields
