"""Generic REST API CRM adapter."""

import httpx
import structlog

from vallorys.schemas.property import (
    PropertyProfile,
    PropertyAddress,
    PropertyType,
    DPERating,
)
from vallorys.schemas.seller import SellerProfile, SellerType, UrgencyLevel
from vallorys.schemas.valuation import ValuationResult
from vallorys.services.crm.base import (
    CRMAdapter,
    CRMType,
    CRMCredentials,
    CRMLeadData,
    CRMPropertyData,
    CRMPushResult,
)

logger = structlog.get_logger()


class GenericCRMAdapter(CRMAdapter):
    """
    Generic CRM adapter for REST APIs.

    Expects a configurable field mapping and standard REST endpoints.
    """

    def __init__(
        self,
        credentials: CRMCredentials,
        tenant_id: str,
        field_mapping: dict | None = None,
    ):
        super().__init__(credentials, tenant_id)
        self.field_mapping = field_mapping or self._default_field_mapping()
        self.base_url = credentials.base_url or "https://api.example-crm.com"
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._get_headers(),
            timeout=30.0,
        )

    @property
    def crm_type(self) -> CRMType:
        return CRMType.GENERIC

    def _get_headers(self) -> dict:
        """Get request headers with authentication."""
        headers = {"Content-Type": "application/json"}
        if self.credentials.api_key:
            headers["X-API-Key"] = self.credentials.api_key
        if self.credentials.access_token:
            headers["Authorization"] = f"Bearer {self.credentials.access_token}"
        return headers

    def _default_field_mapping(self) -> dict:
        """Default field mapping for generic CRM."""
        return {
            "lead": {
                "id": "id",
                "first_name": "first_name",
                "last_name": "last_name",
                "email": "email",
                "phone": "phone",
                "type": "contact_type",
                "urgency": "urgency_level",
                "price_expectation": "expected_price",
            },
            "property": {
                "id": "id",
                "address": "full_address",
                "city": "city",
                "postal_code": "postal_code",
                "type": "property_type",
                "surface": "living_area",
                "rooms": "rooms",
                "bedrooms": "bedrooms",
                "dpe": "energy_rating",
            },
        }

    async def test_connection(self) -> bool:
        """Test CRM connection."""
        try:
            response = await self.client.get("/health")
            return response.status_code == 200
        except Exception as e:
            logger.error("CRM connection test failed", error=str(e))
            return False

    async def pull_lead(
        self,
        lead_id: str,
        include_history: bool = False,
    ) -> CRMLeadData:
        """Pull lead data from generic CRM."""
        logger.info("Pulling lead from CRM", lead_id=lead_id)

        try:
            response = await self.client.get(f"/contacts/{lead_id}")
            response.raise_for_status()
            data = response.json()

            seller = self._normalize_seller(data)

            # Get linked properties
            properties = []
            if "properties" in data:
                for prop_data in data["properties"]:
                    properties.append(self._normalize_property(prop_data))

            # Get history if requested
            history = []
            if include_history:
                hist_response = await self.client.get(
                    f"/contacts/{lead_id}/activities"
                )
                if hist_response.status_code == 200:
                    history = hist_response.json().get("activities", [])

            return CRMLeadData(
                crm_lead_id=lead_id,
                seller=seller,
                properties=properties,
                history=history,
            )

        except httpx.HTTPError as e:
            logger.error("Failed to pull lead", lead_id=lead_id, error=str(e))
            raise

    async def pull_property(
        self,
        property_id: str,
        include_photos: bool = False,
    ) -> CRMPropertyData:
        """Pull property data from generic CRM."""
        logger.info("Pulling property from CRM", property_id=property_id)

        try:
            response = await self.client.get(f"/properties/{property_id}")
            response.raise_for_status()
            data = response.json()

            property_profile = self._normalize_property(data)

            photos = []
            if include_photos and "photos" in data:
                photos = [p.get("url") for p in data["photos"] if p.get("url")]

            return CRMPropertyData(
                crm_property_id=property_id,
                property=property_profile,
                linked_lead_id=data.get("contact_id"),
                photos_urls=photos,
            )

        except httpx.HTTPError as e:
            logger.error("Failed to pull property", property_id=property_id, error=str(e))
            raise

    async def push_valuation_report(
        self,
        lead_id: str,
        valuation: ValuationResult,
        report_url: str | None = None,
        create_task: bool = True,
    ) -> CRMPushResult:
        """Push valuation report to CRM."""
        logger.info("Pushing valuation to CRM", lead_id=lead_id, valuation_id=valuation.id)

        try:
            # Create valuation record
            payload = {
                "contact_id": lead_id,
                "valuation_id": valuation.id,
                "range_low": valuation.range_low,
                "range_high": valuation.range_high,
                "recommended_price": valuation.price_point_recommended,
                "confidence": valuation.confidence_level.value,
                "report_url": report_url,
                "created_at": valuation.created_at.isoformat(),
            }

            response = await self.client.post("/valuations", json=payload)
            response.raise_for_status()
            result = response.json()

            # Create follow-up task
            task_id = None
            if create_task:
                task_id = await self.create_task(
                    lead_id=lead_id,
                    title="Suivi estimation VALLORYS",
                    description=(
                        f"Estimation réalisée : {valuation.range_low:,.0f}€ - "
                        f"{valuation.range_high:,.0f}€\n"
                        f"Prix recommandé : {valuation.price_point_recommended:,.0f}€"
                    ),
                )

            return CRMPushResult(
                success=True,
                crm_record_id=result.get("id"),
                task_id=task_id,
            )

        except httpx.HTTPError as e:
            logger.error("Failed to push valuation", lead_id=lead_id, error=str(e))
            return CRMPushResult(
                success=False,
                error_message=str(e),
            )

    async def create_task(
        self,
        lead_id: str,
        title: str,
        description: str,
        due_date: str | None = None,
    ) -> str:
        """Create a task in CRM."""
        payload = {
            "contact_id": lead_id,
            "title": title,
            "description": description,
            "due_date": due_date,
            "type": "follow_up",
        }

        response = await self.client.post("/tasks", json=payload)
        response.raise_for_status()
        return response.json().get("id", "")

    async def add_note(
        self,
        lead_id: str,
        content: str,
    ) -> str:
        """Add a note to a lead."""
        payload = {
            "contact_id": lead_id,
            "content": content,
        }

        response = await self.client.post("/notes", json=payload)
        response.raise_for_status()
        return response.json().get("id", "")

    def _normalize_property(self, raw_data: dict) -> PropertyProfile:
        """Normalize CRM property data to PropertyProfile."""
        mapping = self.field_mapping["property"]

        # Map property type
        type_mapping = {
            "house": PropertyType.MAISON,
            "apartment": PropertyType.APPARTEMENT,
            "flat": PropertyType.APPARTEMENT,
            "land": PropertyType.TERRAIN,
            "maison": PropertyType.MAISON,
            "appartement": PropertyType.APPARTEMENT,
        }

        raw_type = raw_data.get(mapping["type"], "").lower()
        property_type = type_mapping.get(raw_type, PropertyType.MAISON)

        # Map DPE
        dpe_mapping = {
            "a": DPERating.A,
            "b": DPERating.B,
            "c": DPERating.C,
            "d": DPERating.D,
            "e": DPERating.E,
            "f": DPERating.F,
            "g": DPERating.G,
        }
        raw_dpe = raw_data.get(mapping.get("dpe", ""), "").lower()
        dpe = dpe_mapping.get(raw_dpe, DPERating.UNKNOWN)

        # Extract citycode from postal code (French format)
        postal_code = raw_data.get(mapping.get("postal_code", ""), "")
        citycode = postal_code[:5] if len(postal_code) >= 5 else "00000"

        return PropertyProfile(
            id=str(raw_data.get(mapping["id"], "")),
            address=PropertyAddress(
                street=raw_data.get(mapping.get("address", ""), ""),
                city=raw_data.get(mapping["city"], "Unknown"),
                citycode=citycode,
                postal_code=postal_code,
            ),
            type=property_type,
            surface_living=float(raw_data.get(mapping["surface"], 50)),
            rooms=int(raw_data.get(mapping.get("rooms", ""), 3) or 3),
            bedrooms=raw_data.get(mapping.get("bedrooms")),
            dpe_rating=dpe,
        )

    def _normalize_seller(self, raw_data: dict) -> SellerProfile:
        """Normalize CRM contact data to SellerProfile."""
        mapping = self.field_mapping["lead"]

        # Map seller type
        type_mapping = {
            "owner": SellerType.OWNER_OCCUPIER,
            "investor": SellerType.INVESTOR,
            "heir": SellerType.HEIR,
            "divorce": SellerType.DIVORCING,
        }
        raw_type = raw_data.get(mapping.get("type", ""), "").lower()
        seller_type = type_mapping.get(raw_type, SellerType.OTHER)

        # Map urgency
        urgency_mapping = {
            "urgent": UrgencyLevel.URGENT,
            "high": UrgencyLevel.URGENT,
            "moderate": UrgencyLevel.MODERATE,
            "medium": UrgencyLevel.MODERATE,
            "low": UrgencyLevel.NO_RUSH,
        }
        raw_urgency = raw_data.get(mapping.get("urgency", ""), "").lower()
        urgency = urgency_mapping.get(raw_urgency, UrgencyLevel.UNKNOWN)

        return SellerProfile(
            id=str(raw_data.get(mapping["id"], "")),
            type=seller_type,
            urgency=urgency,
            price_expectation=raw_data.get(mapping.get("price_expectation")),
        )

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
