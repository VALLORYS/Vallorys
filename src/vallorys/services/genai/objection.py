"""Objection coach agent for real-time objection handling."""

import uuid
from datetime import datetime

import structlog

from vallorys.schemas.objection import (
    ObjectionRequest,
    ObjectionResponse,
    ObjectionCategory,
    SuggestedTone,
    ProactiveSuggestRequest,
    ProactiveSuggestResponse,
    ProactiveSuggestion,
)
from vallorys.schemas.valuation import ValuationResult
from vallorys.schemas.seller import SellerProfile

logger = structlog.get_logger()


class ObjectionCoach:
    """
    AI-powered objection coach for real-time assistance.

    Provides quick and detailed responses to common seller objections,
    with contextual proof points from the valuation.
    """

    # Pre-built response templates by category
    RESPONSE_TEMPLATES = {
        ObjectionCategory.PRICE_TOO_LOW: {
            "quick": (
                "Je comprends votre réaction. Permettez-moi de vous expliquer "
                "précisément comment nous arrivons à ce prix."
            ),
            "detailed": (
                "Le prix proposé reflète la réalité du marché actuel. "
                "Notre estimation s'appuie sur {transaction_count} ventes réelles "
                "dans votre secteur ces 12 derniers mois. "
                "Un prix trop élevé risque de rallonger le délai de vente "
                "et in fine de vous faire perdre des acquéreurs sérieux. "
                "Les statistiques montrent que les biens surévalués finissent "
                "souvent par se vendre en dessous du prix initial réaliste."
            ),
            "follow_up": (
                "Quel prix aviez-vous en tête, et sur quoi vous basez-vous "
                "pour cette estimation ?"
            ),
            "tone": SuggestedTone.FACTUAL,
        },
        ObjectionCategory.NEIGHBOR_SOLD_HIGHER: {
            "quick": (
                "Intéressant ! Pouvez-vous me dire à quel étage et quelle surface ? "
                "Chaque bien a ses spécificités."
            ),
            "detailed": (
                "La vente de votre voisin est une référence intéressante, "
                "mais plusieurs facteurs peuvent expliquer la différence. "
                "Le marché évolue rapidement, et chaque bien est unique : "
                "l'étage, l'exposition, l'état intérieur, les travaux réalisés... "
                "Sans connaître les détails précis de cette vente, "
                "il est difficile de comparer. Notre estimation s'appuie sur "
                "l'ensemble des transactions du secteur, pas sur un cas isolé."
            ),
            "follow_up": (
                "Savez-vous si votre voisin avait fait des travaux de rénovation "
                "avant la vente ? Et à quelle date a-t-il vendu exactement ?"
            ),
            "tone": SuggestedTone.FACTUAL,
        },
        ObjectionCategory.OTHER_AGENCY_ESTIMATE: {
            "quick": (
                "Je comprends. Sur quelles données s'appuyait cette estimation ?"
            ),
            "detailed": (
                "Un écart significatif entre deux estimations mérite d'être analysé. "
                "Notre estimation s'appuie sur les données DVF (Demandes de Valeurs Foncières), "
                "c'est-à-dire les prix réels des transactions enregistrées par les notaires. "
                "Une surestimation peut sembler flatteuse, mais elle risque de vous faire "
                "perdre les premiers mois cruciaux où votre bien génère le plus d'intérêt. "
                "Je préfère vous donner un prix réaliste qui vous permettra de vendre "
                "dans les meilleures conditions."
            ),
            "follow_up": (
                "L'agence vous a-t-elle montré les ventes comparables "
                "sur lesquelles elle s'appuie ?"
            ),
            "tone": SuggestedTone.FACTUAL,
        },
        ObjectionCategory.WANT_TO_TEST_MARKET: {
            "quick": (
                "Je comprends cette envie. Mais savez-vous que les 3 premières semaines "
                "sont cruciales pour une vente ?"
            ),
            "detailed": (
                "Tester le marché à un prix élevé peut sembler sans risque, "
                "mais c'est en réalité contre-productif. Les acheteurs sérieux "
                "connaissent les prix du marché et ignorent les biens surévalués. "
                "Après quelques semaines sans visite, votre bien sera perçu comme "
                "'grillé' sur le marché. Les statistiques montrent que les biens "
                "qui démarrent au bon prix se vendent plus vite ET à un meilleur prix final "
                "que ceux qui ont dû baisser après plusieurs mois."
            ),
            "follow_up": (
                "Seriez-vous prêt à baisser significativement si au bout de 2 mois "
                "vous n'avez pas d'offre ?"
            ),
            "tone": SuggestedTone.CHALLENGING,
        },
        ObjectionCategory.NOT_URGENT: {
            "quick": (
                "Je comprends. Qu'est-ce qui vous ferait accélérer si une opportunité "
                "se présentait ?"
            ),
            "detailed": (
                "Ne pas être pressé est un atout pour négocier. Cependant, "
                "le marché immobilier évolue. Si vous attendez trop longtemps, "
                "les conditions peuvent changer. De plus, un bien qui reste longtemps "
                "sur le marché sans se vendre envoie un signal négatif aux acheteurs. "
                "Commencer maintenant au bon prix vous laisse la liberté d'attendre "
                "la bonne offre sans subir la pression d'un délai."
            ),
            "follow_up": (
                "Y a-t-il un événement particulier qui pourrait changer votre calendrier ?"
            ),
            "tone": SuggestedTone.EMPATHETIC,
        },
        ObjectionCategory.NEED_TIME_TO_THINK: {
            "quick": (
                "Bien sûr, c'est une décision importante. De quelles informations "
                "supplémentaires auriez-vous besoin ?"
            ),
            "detailed": (
                "Prendre le temps de réfléchir est tout à fait normal. "
                "Je vous laisse le dossier complet avec l'analyse du marché. "
                "N'hésitez pas à me rappeler si vous avez des questions. "
                "Je serai disponible pour un second rendez-vous si vous souhaitez "
                "approfondir certains points."
            ),
            "follow_up": (
                "Qu'est-ce qui vous aiderait à prendre votre décision ? "
                "Y a-t-il d'autres personnes à consulter ?"
            ),
            "tone": SuggestedTone.REASSURING,
        },
        ObjectionCategory.COMMISSION_TOO_HIGH: {
            "quick": (
                "Je comprends que les honoraires représentent un budget. "
                "Permettez-moi de vous expliquer ce qu'ils incluent."
            ),
            "detailed": (
                "Nos honoraires couvrent l'ensemble des services : "
                "estimation professionnelle, photos de qualité, diffusion sur tous les portails, "
                "gestion des visites, négociation, accompagnement jusqu'à la signature. "
                "Un agent qui brade ses honoraires aura moins de moyens pour promouvoir votre bien. "
                "Nos honoraires sont dans la moyenne du marché et reflètent "
                "la qualité du service que nous vous apportons."
            ),
            "follow_up": (
                "Quel est l'élément de notre service qui vous semble le plus important ?"
            ),
            "tone": SuggestedTone.FACTUAL,
        },
        ObjectionCategory.DONT_TRUST_ESTIMATES: {
            "quick": (
                "C'est une réaction compréhensible. Laissez-moi vous montrer "
                "sur quelles données précises repose notre méthode."
            ),
            "detailed": (
                "Votre méfiance est compréhensible dans un secteur où les estimations "
                "varient parfois fortement. Notre différence : nous utilisons les données "
                "officielles DVF publiées par l'État, qui recensent toutes les transactions "
                "réellement effectuées. Ce ne sont pas des estimations approximatives, "
                "mais des prix réels payés par des acheteurs. "
                "Je peux vous montrer les ventes comparables qui ont servi à notre calcul."
            ),
            "follow_up": (
                "Souhaitez-vous que je vous montre les 5 dernières ventes "
                "dans votre quartier ?"
            ),
            "tone": SuggestedTone.REASSURING,
        },
    }

    def __init__(self, llm_client=None):
        """
        Initialize the coach.

        Args:
            llm_client: Optional LLM client for enhanced responses.
        """
        self.llm_client = llm_client

    async def respond(
        self,
        request: ObjectionRequest,
        valuation: ValuationResult | None = None,
        seller: SellerProfile | None = None,
    ) -> ObjectionResponse:
        """
        Generate response to an objection.

        Args:
            request: Objection request with text and context
            valuation: Optional valuation for proof points
            seller: Optional seller profile for personalization

        Returns:
            Complete objection response
        """
        logger.info(
            "Processing objection",
            category=request.objection_category,
            has_valuation=valuation is not None,
        )

        objection_id = f"obj_{uuid.uuid4().hex[:12]}"

        # Detect category if not provided
        category = request.objection_category or self._detect_category(
            request.objection_text
        )

        # Get template for category
        template = self.RESPONSE_TEMPLATES.get(
            category,
            self.RESPONSE_TEMPLATES[ObjectionCategory.PRICE_TOO_LOW],
        )

        # Build responses with context
        quick_response = template["quick"]
        detailed_response = self._personalize_response(
            template["detailed"],
            valuation,
        )
        follow_up = template["follow_up"]

        # Build proof point from valuation
        proof_point = self._build_proof_point(valuation)

        response = ObjectionResponse(
            objection_id=objection_id,
            quick_response=quick_response,
            detailed_response=detailed_response,
            follow_up_question=follow_up,
            proof_point=proof_point,
            suggested_tone=template["tone"],
            additional_tips=self._get_tips_for_category(category),
            detected_category=category,
        )

        logger.info(
            "Objection response generated",
            objection_id=objection_id,
            category=category.value if category else "unknown",
        )

        return response

    async def suggest_proactive(
        self,
        request: ProactiveSuggestRequest,
        valuation: ValuationResult | None = None,
    ) -> ProactiveSuggestResponse:
        """
        Generate proactive suggestions based on current phase.

        Args:
            request: Request with current phase and context
            valuation: Optional valuation for context

        Returns:
            Proactive suggestions
        """
        suggestions = []

        phase_suggestions = {
            "discovery": [
                ProactiveSuggestion(
                    trigger="Si le vendeur mentionne une autre estimation",
                    message="Demandez sur quelles données elle s'appuie",
                    priority="high",
                ),
                ProactiveSuggestion(
                    trigger="Si le vendeur semble pressé",
                    message="Identifiez la vraie raison de l'urgence",
                    priority="medium",
                ),
            ],
            "presentation": [
                ProactiveSuggestion(
                    trigger="Avant d'annoncer le prix",
                    message="Récapitulez les points forts du bien",
                    priority="high",
                ),
                ProactiveSuggestion(
                    trigger="Après avoir annoncé le prix",
                    message="Laissez un silence, ne vous justifiez pas immédiatement",
                    priority="high",
                ),
            ],
            "objection_handling": [
                ProactiveSuggestion(
                    trigger="Face à une objection prix",
                    message="Revenez toujours aux données de marché",
                    priority="high",
                ),
                ProactiveSuggestion(
                    trigger="Si le vendeur compare à un voisin",
                    message="Demandez les détails précis (surface, étage, état)",
                    priority="medium",
                ),
            ],
            "closing": [
                ProactiveSuggestion(
                    trigger="Si le vendeur hésite",
                    message="Proposez une période test de 3 semaines",
                    priority="high",
                ),
                ProactiveSuggestion(
                    trigger="Si pas de décision",
                    message="Proposez un second RDV avec les décisionnaires",
                    priority="medium",
                ),
            ],
        }

        suggestions = phase_suggestions.get(request.current_phase, [])

        return ProactiveSuggestResponse(suggestions=suggestions)

    def _detect_category(self, text: str) -> ObjectionCategory:
        """Detect objection category from text."""
        text_lower = text.lower()

        keywords = {
            ObjectionCategory.PRICE_TOO_LOW: [
                "trop bas", "pas assez", "vaut plus", "sous-estime",
            ],
            ObjectionCategory.NEIGHBOR_SOLD_HIGHER: [
                "voisin", "à côté", "même immeuble", "l'autre a vendu",
            ],
            ObjectionCategory.OTHER_AGENCY_ESTIMATE: [
                "autre agence", "agence concurrent", "estimation plus haute",
                "m'a dit plus",
            ],
            ObjectionCategory.WANT_TO_TEST_MARKET: [
                "tester", "essayer", "commencer plus haut", "voir ce que ça donne",
            ],
            ObjectionCategory.NOT_URGENT: [
                "pas pressé", "pas urgent", "on verra", "prendre le temps",
            ],
            ObjectionCategory.NEED_TIME_TO_THINK: [
                "réfléchir", "besoin de temps", "en parler", "consulter",
            ],
            ObjectionCategory.COMMISSION_TOO_HIGH: [
                "commission", "honoraires", "frais", "pourcentage",
            ],
            ObjectionCategory.DONT_TRUST_ESTIMATES: [
                "pas confiance", "fiable", "croire", "n'importe quoi",
            ],
        }

        for category, kws in keywords.items():
            if any(kw in text_lower for kw in kws):
                return category

        return ObjectionCategory.OTHER

    def _personalize_response(
        self,
        template: str,
        valuation: ValuationResult | None,
    ) -> str:
        """Personalize response template with valuation data."""
        if not valuation:
            return template.format(transaction_count="de nombreuses")

        replacements = {
            "transaction_count": str(
                valuation.market_context.transaction_count
                if valuation.market_context
                else "de nombreuses"
            ),
        }

        result = template
        for key, value in replacements.items():
            result = result.replace(f"{{{key}}}", value)

        return result

    def _build_proof_point(self, valuation: ValuationResult | None) -> str:
        """Build proof point from valuation."""
        if not valuation:
            return "Notre estimation s'appuie sur les données de marché DVF."

        if valuation.market_context:
            return (
                f"Notre estimation s'appuie sur {valuation.market_context.transaction_count or 'de nombreuses'} "
                f"ventes dans votre secteur. Prix médian : "
                f"{valuation.market_context.median_price_sqm:,.0f} €/m²."
            )

        return (
            f"Fourchette recommandée : {valuation.range_low:,.0f}€ - "
            f"{valuation.range_high:,.0f}€, basée sur l'analyse du marché local."
        )

    def _get_tips_for_category(self, category: ObjectionCategory) -> list[str]:
        """Get handling tips for objection category."""
        tips = {
            ObjectionCategory.PRICE_TOO_LOW: [
                "Restez calme et factuel",
                "Ne vous justifiez pas de manière défensive",
                "Ramenez toujours aux données de marché",
            ],
            ObjectionCategory.NEIGHBOR_SOLD_HIGHER: [
                "Ne dénigrez jamais la vente du voisin",
                "Demandez des précisions factuelles",
                "Proposez de vérifier ensemble",
            ],
            ObjectionCategory.OTHER_AGENCY_ESTIMATE: [
                "Ne critiquez pas le concurrent",
                "Concentrez-vous sur votre méthodologie",
                "Proposez de comparer les approches",
            ],
            ObjectionCategory.WANT_TO_TEST_MARKET: [
                "Expliquez les risques du 'grillage'",
                "Donnez des statistiques de délai",
                "Proposez une durée de test limitée",
            ],
        }

        return tips.get(category, [
            "Écoutez attentivement",
            "Reformulez l'objection",
            "Répondez avec des faits",
        ])
