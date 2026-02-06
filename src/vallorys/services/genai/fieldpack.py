"""Field pack generator using LLM."""

import uuid
from datetime import datetime

import structlog

from vallorys.schemas.property import PropertyProfile
from vallorys.schemas.seller import SellerProfile, SellerType
from vallorys.schemas.valuation import ValuationResult
from vallorys.schemas.fieldpack import (
    FieldPackRequest,
    FieldPackResponse,
    Argumentaire,
    ArgumentPoint,
    RdvScript,
    ScriptPhase,
    Checklist,
    ChecklistCategory,
    ChecklistItem,
    Template,
    ObjectionTemplate,
    Tone,
    TemplateType,
)

logger = structlog.get_logger()


class FieldPackGenerator:
    """
    Generator for field pack content.

    Creates personalized argumentaires, RDV scripts, checklists,
    and templates based on property, seller, and valuation data.
    """

    def __init__(self, llm_client=None):
        """
        Initialize the generator.

        Args:
            llm_client: Optional LLM client for AI-powered generation.
                       If None, uses template-based generation.
        """
        self.llm_client = llm_client

    async def generate(
        self,
        request: FieldPackRequest,
        property: PropertyProfile,
        valuation: ValuationResult,
        seller: SellerProfile | None = None,
    ) -> FieldPackResponse:
        """
        Generate complete field pack.

        Args:
            request: Generation request with options
            property: Property profile
            valuation: Valuation result
            seller: Optional seller profile for personalization

        Returns:
            Complete field pack response
        """
        logger.info(
            "Generating field pack",
            valuation_id=request.valuation_id,
            generate_argumentaire=request.generate.argumentaire,
            generate_script=request.generate.script_rdv,
        )

        seller = seller or request.seller or SellerProfile()
        tone = request.get_tone()
        rdv_duration = request.get_rdv_duration()

        response = FieldPackResponse(
            fieldpack_id=f"fp_{uuid.uuid4().hex[:12]}",
            created_at=datetime.utcnow(),
            valuation_id=request.valuation_id,
        )

        if request.generate.argumentaire:
            response.argumentaire = await self._generate_argumentaire(
                property, valuation, seller, tone
            )

        if request.generate.script_rdv:
            response.script_rdv = await self._generate_rdv_script(
                property, valuation, seller, rdv_duration
            )

        if request.generate.checklist:
            response.checklist = await self._generate_checklist(property)

        for template_type in request.generate.templates:
            template = await self._generate_template(
                template_type, property, valuation, seller
            )
            response.templates[template_type.value] = template

        logger.info(
            "Field pack generated",
            fieldpack_id=response.fieldpack_id,
        )

        return response

    async def _generate_argumentaire(
        self,
        property: PropertyProfile,
        valuation: ValuationResult,
        seller: SellerProfile,
        tone: Tone,
    ) -> Argumentaire:
        """Generate personalized argumentaire."""

        # Adapt opening based on seller type
        openings = {
            SellerType.HEIR: (
                "Je comprends que vendre un bien familial est une décision "
                "chargée d'émotions. Mon rôle est de vous accompagner avec "
                "transparence et professionnalisme."
            ),
            SellerType.DIVORCING: (
                "Je sais que cette période est complexe. Mon objectif est de "
                "faciliter cette étape en vous donnant une vision claire et "
                "objective du marché."
            ),
            SellerType.INVESTOR: (
                "En tant qu'investisseur, vous connaissez l'importance d'une "
                "estimation précise pour optimiser votre rendement. Voici mon "
                "analyse du marché."
            ),
            SellerType.OWNER_OCCUPIER: (
                "Vendre sa résidence principale est une étape importante. "
                "Je suis là pour vous accompagner avec une estimation basée "
                "sur des données concrètes du marché."
            ),
        }

        opening = openings.get(
            seller.type,
            "Je vous remercie de votre confiance. Voici mon analyse détaillée "
            "de votre bien et du marché local."
        )

        # Build key points based on valuation
        key_points = []

        # Point 1: Market data
        if valuation.market_context:
            key_points.append(ArgumentPoint(
                point="Estimation basée sur des données réelles",
                argument=(
                    f"Notre estimation s'appuie sur {valuation.market_context.transaction_count or 'de nombreuses'} "
                    f"ventes réalisées dans votre secteur ces 12 derniers mois. "
                    "Ce n'est pas une estimation approximative, mais une analyse "
                    "factuelle du marché."
                ),
                proof=f"Prix médian constaté : {valuation.market_context.median_price_sqm:,.0f} €/m²",
            ))

        # Point 2: Handle competing estimates
        if seller.has_competing_estimates():
            highest = seller.get_highest_previous_estimate()
            if highest and highest > valuation.range_high:
                diff_percent = ((highest / valuation.price_point_recommended) - 1) * 100
                key_points.append(ArgumentPoint(
                    point="Écart avec les estimations précédentes",
                    argument=(
                        f"L'estimation précédente à {highest:,.0f} € est {diff_percent:.0f}% "
                        "au-dessus du marché. Une telle surévaluation risque de rallonger "
                        "significativement le délai de vente."
                    ),
                    proof="Les biens surévalués de plus de 15% restent en moyenne 4 mois de plus sur le marché.",
                ))

        # Point 3: Recommended price
        key_points.append(ArgumentPoint(
            point="Le bon prix pour une vente réussie",
            argument=(
                f"À {valuation.price_point_recommended:,.0f} €, votre bien se positionne "
                "dans la tranche haute du marché tout en restant attractif. "
                "C'est le prix qui génère le plus de visites qualifiées."
            ),
            proof=f"Fourchette recommandée : {valuation.range_low:,.0f} € - {valuation.range_high:,.0f} €",
        ))

        # Point 4: Key strengths (from valuation)
        if valuation.justification and valuation.justification.top_positive_factors:
            strengths = ", ".join(valuation.justification.top_positive_factors[:3])
            key_points.append(ArgumentPoint(
                point="Les atouts de votre bien",
                argument=(
                    f"Votre bien présente des caractéristiques recherchées : {strengths}. "
                    "Ces éléments ont été valorisés dans notre estimation."
                ),
            ))

        # Closing
        closings = {
            Tone.EMPATHETIC: (
                "Je comprends que le prix puisse vous surprendre. Mon objectif "
                "est de vous accompagner vers une vente sereine, au meilleur prix réaliste."
            ),
            Tone.DIRECT: (
                "C'est le prix du marché. Accepter ce positionnement vous permettra "
                "de vendre dans les meilleurs délais."
            ),
            Tone.REASSURING: (
                "Cette estimation vous garantit une vente dans les meilleurs délais, "
                "tout en maximisant votre prix de vente."
            ),
        }

        closing = closings.get(
            tone,
            "Je préfère vous donner un conseil honnête plutôt qu'un chiffre "
            "flatteur qui vous ferait perdre du temps."
        )

        return Argumentaire(
            opening=opening,
            key_points=key_points,
            closing=closing,
            tone=tone,
        )

    async def _generate_rdv_script(
        self,
        property: PropertyProfile,
        valuation: ValuationResult,
        seller: SellerProfile,
        duration_minutes: int,
    ) -> RdvScript:
        """Generate RDV script with phases."""

        # Adjust timings based on duration
        if duration_minutes >= 90:
            timings = [10, 20, 20, 25, 15]
        elif duration_minutes >= 60:
            timings = [5, 15, 15, 15, 10]
        else:
            timings = [5, 10, 10, 10, 5]

        phases = [
            ScriptPhase(
                phase="Accueil & mise en confiance",
                duration_minutes=timings[0],
                timing=f"0-{timings[0]} min",
                objectives=[
                    "Créer un climat de confiance",
                    "Montrer de l'empathie pour la situation",
                ],
                script=(
                    f"Bonjour, merci de me recevoir. Je suis [Prénom], de l'agence [Agence]. "
                    "Avant de parler chiffres, j'aimerais comprendre votre projet et vos attentes."
                ),
                tips=[
                    "Écouter activement",
                    "Ne pas parler prix immédiatement",
                    "Observer le bien pendant les échanges",
                ],
            ),
            ScriptPhase(
                phase="Découverte",
                duration_minutes=timings[1],
                timing=f"{timings[0]}-{timings[0]+timings[1]} min",
                objectives=[
                    "Comprendre le contexte de vente",
                    "Identifier les vraies motivations",
                    "Repérer les objections potentielles",
                ],
                script="Pour vous donner le meilleur conseil possible, j'ai besoin de comprendre votre situation...",
                questions=[
                    "Depuis quand êtes-vous propriétaire de ce bien ?",
                    "Qu'est-ce qui vous a décidé à vendre maintenant ?",
                    "Avez-vous un projet précis après la vente ?",
                    "Avez-vous déjà une idée du prix ?",
                    "Avez-vous consulté d'autres agences ?",
                ],
                tips=[
                    "Prendre des notes",
                    "Reformuler pour valider la compréhension",
                ],
            ),
            ScriptPhase(
                phase="Visite du bien",
                duration_minutes=timings[2],
                timing=f"{sum(timings[:2])}-{sum(timings[:3])} min",
                objectives=[
                    "Valider les informations du dossier",
                    "Identifier points forts et points faibles",
                    "Prendre des photos",
                ],
                script="Visitons ensemble le bien. Pouvez-vous me montrer les derniers travaux réalisés ?",
                checklist=[
                    "Surface réelle",
                    "État DPE/installations",
                    "Vue et luminosité",
                    "Nuisances éventuelles",
                    "État des parties communes (si appartement)",
                ],
            ),
            ScriptPhase(
                phase="Présentation de l'estimation",
                duration_minutes=timings[3],
                timing=f"{sum(timings[:3])}-{sum(timings[:4])} min",
                objectives=[
                    "Présenter l'estimation de façon pédagogique",
                    "Anticiper et traiter les objections",
                ],
                script=(
                    "Passons à l'estimation. Je vais vous expliquer précisément "
                    "comment nous arrivons à ce chiffre, étape par étape."
                ),
                key_moments=[
                    "Montrer la méthodologie",
                    "Présenter les données de marché",
                    "Expliquer les ajustements",
                    "Annoncer le prix recommandé",
                    "Laisser un silence après l'annonce",
                ],
                tips=[
                    "Utiliser des visuels/graphiques",
                    "Ne pas se justifier avant une objection",
                ],
            ),
            ScriptPhase(
                phase="Traitement objections & closing",
                duration_minutes=timings[4],
                timing=f"{sum(timings[:4])}-{duration_minutes} min",
                objectives=[
                    "Répondre aux objections",
                    "Obtenir le mandat ou un RDV de suivi",
                ],
                script="Avez-vous des questions sur cette estimation ?",
                common_objections=[
                    "C'est en dessous de ce que j'espérais",
                    "L'autre agence m'a dit plus",
                    "Je veux tester le marché plus haut",
                ],
                closing_options=[
                    "Mandat exclusif avec engagement de moyens renforcés",
                    "Test de 3 semaines au prix recommandé",
                    "Second RDV pour approfondir",
                ],
            ),
        ]

        return RdvScript(
            total_duration_minutes=duration_minutes,
            phases=phases,
        )

    async def _generate_checklist(
        self,
        property: PropertyProfile,
    ) -> Checklist:
        """Generate pre-mandat checklist."""

        categories = [
            ChecklistCategory(
                category="Documents à récupérer",
                items=[
                    ChecklistItem(
                        item="Titre de propriété ou attestation notariée",
                        required=True,
                    ),
                    ChecklistItem(
                        item="Diagnostics techniques (DPE, amiante, plomb, électricité, gaz)",
                        required=True,
                    ),
                    ChecklistItem(
                        item="Taxe foncière dernière année",
                        required=True,
                    ),
                    ChecklistItem(
                        item="Charges de copropriété (3 derniers appels)",
                        required=property.type.value == "appartement",
                    ),
                    ChecklistItem(
                        item="PV des 3 dernières AG",
                        required=property.type.value == "appartement",
                    ),
                    ChecklistItem(
                        item="Règlement de copropriété",
                        required=False,
                    ),
                    ChecklistItem(
                        item="Plans du bien",
                        required=False,
                    ),
                ],
            ),
            ChecklistCategory(
                category="Points à vérifier sur place",
                items=[
                    ChecklistItem(
                        item="Surface réelle (mesurer si doute)",
                        required=True,
                    ),
                    ChecklistItem(
                        item="Conformité installation électrique",
                        required=True,
                    ),
                    ChecklistItem(
                        item="État des fenêtres et volets",
                        required=True,
                    ),
                    ChecklistItem(
                        item="Fonctionnement chauffage/climatisation",
                        required=True,
                    ),
                    ChecklistItem(
                        item="État parties communes",
                        required=property.type.value == "appartement",
                    ),
                    ChecklistItem(
                        item="État toiture",
                        required=property.type.value == "maison",
                    ),
                ],
            ),
            ChecklistCategory(
                category="Photos à prendre",
                items=[
                    ChecklistItem(item="Façade/extérieur", required=True),
                    ChecklistItem(item="Entrée/hall", required=True),
                    ChecklistItem(item="Chaque pièce (2-3 angles)", required=True),
                    ChecklistItem(item="Cuisine équipée", required=True),
                    ChecklistItem(item="Salle de bain", required=True),
                    ChecklistItem(item="Vue depuis fenêtres", required=True),
                    ChecklistItem(item="Balcon/terrasse/jardin", required=False),
                    ChecklistItem(item="Cave/garage", required=False),
                ],
            ),
            ChecklistCategory(
                category="Questions à poser",
                items=[
                    ChecklistItem(
                        item="Travaux votés en AG non encore réalisés ?",
                        required=property.type.value == "appartement",
                    ),
                    ChecklistItem(
                        item="Litiges en cours ?",
                        required=True,
                    ),
                    ChecklistItem(
                        item="Servitudes ou contraintes particulières ?",
                        required=True,
                    ),
                    ChecklistItem(
                        item="Projets urbains à proximité ?",
                        required=False,
                    ),
                ],
            ),
        ]

        return Checklist(categories=categories)

    async def _generate_template(
        self,
        template_type: TemplateType,
        property: PropertyProfile,
        valuation: ValuationResult,
        seller: SellerProfile,
    ) -> Template | ObjectionTemplate:
        """Generate a specific template."""

        if template_type == TemplateType.OBJECTION_RESPONSE:
            return ObjectionTemplate(
                objection="L'autre agence m'a estimé plus haut",
                response_quick=(
                    "Je comprends. Permettez-moi de vous montrer précisément "
                    "sur quelles données s'appuie notre estimation."
                ),
                response_detailed=(
                    f"L'écart avec une autre estimation peut s'expliquer par "
                    "plusieurs facteurs. Notre estimation s'appuie sur "
                    f"{valuation.market_context.transaction_count if valuation.market_context else 'de nombreuses'} "
                    "ventes réelles dans votre secteur ces 12 derniers mois. "
                    "Les biens surévalués restent plus longtemps sur le marché "
                    "et finissent souvent par se vendre en dessous du prix "
                    "qu'ils auraient pu obtenir initialement."
                ),
                follow_up_question=(
                    "Avez-vous demandé sur quelles ventes comparables "
                    "s'appuie leur estimation ?"
                ),
            )

        elif template_type == TemplateType.EMAIL_PRE_RDV:
            return Template(
                template_type=template_type,
                subject="Notre rendez-vous du [DATE] - Estimation de votre bien",
                body=(
                    "Bonjour [PRENOM],\n\n"
                    "Je vous confirme notre rendez-vous le [DATE] à [HEURE] "
                    f"pour l'estimation de votre {property.type.value} "
                    f"situé {property.address.city}.\n\n"
                    "Pour que notre rencontre soit la plus productive possible, "
                    "pourriez-vous préparer :\n"
                    "- Le titre de propriété ou attestation notariée\n"
                    "- Les diagnostics techniques existants\n"
                    "- Les 3 derniers appels de charges (si copropriété)\n\n"
                    "Je prévois environ 1h pour la visite et la présentation de l'estimation.\n\n"
                    "N'hésitez pas à me contacter si vous avez des questions.\n\n"
                    "Bien cordialement,\n[SIGNATURE]"
                ),
                variables=["PRENOM", "DATE", "HEURE", "SIGNATURE"],
            )

        elif template_type == TemplateType.EMAIL_POST_RDV:
            return Template(
                template_type=template_type,
                subject="Suite à notre rendez-vous - Votre estimation",
                body=(
                    "Bonjour [PRENOM],\n\n"
                    "Je vous remercie pour notre échange d'aujourd'hui.\n\n"
                    "Comme convenu, je vous confirme mon estimation pour votre bien :\n"
                    f"- Fourchette de prix : {valuation.range_low:,.0f} € - {valuation.range_high:,.0f} €\n"
                    f"- Prix recommandé : {valuation.price_point_recommended:,.0f} €\n\n"
                    "Vous trouverez ci-joint le rapport détaillé avec l'analyse du marché.\n\n"
                    "Je reste à votre disposition pour répondre à vos questions "
                    "et vous accompagner dans votre projet de vente.\n\n"
                    "Bien cordialement,\n[SIGNATURE]"
                ),
                variables=["PRENOM", "SIGNATURE"],
            )

        elif template_type == TemplateType.SMS_REMINDER:
            return Template(
                template_type=template_type,
                body=(
                    "Bonjour, je vous confirme notre RDV demain à [HEURE] "
                    f"pour l'estimation de votre bien à {property.address.city}. "
                    "À demain ! [PRENOM_AGENT]"
                ),
                variables=["HEURE", "PRENOM_AGENT"],
            )

        else:
            return Template(
                template_type=template_type,
                body="Template non disponible pour ce type.",
                variables=[],
            )
