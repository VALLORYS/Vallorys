"""Base CRM adapter interface."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from pydantic import BaseModel

from vallorys.schemas.property import PropertyProfile
from vallorys.schemas.seller import SellerProfile
from vallorys.schemas.valuation import ValuationResult


class CRMType(str, Enum):
    """Supported CRM types."""
    HUBSPOT = "hubspot"
    PIPEDRIVE = "pipedrive"
    GENERIC = "generic"


class CRMCredentials(BaseModel):
    """CRM API credentials."""
    api_key: str | None = None
    api_secret: str | None = None
    access_token: str | None = None
    refresh_token: str | None = None
    base_url: str | None = None


class CRMLeadData(BaseModel):
    """Normalized lead data from CRM."""
    crm_lead_id: str
    seller: SellerProfile
    properties: list[PropertyProfile] = []
    appointments: list[dict] = []
    notes: list[str] = []
    history: list[dict] = []


class CRMPropertyData(BaseModel):
    """Normalized property data from CRM."""
    crm_property_id: str
    property: PropertyProfile
    linked_lead_id: str | None = None
    photos_urls: list[str] = []


class CRMPushResult(BaseModel):
    """Result of pushing data to CRM."""
    success: bool
    crm_record_id: str | None = None
    task_id: str | None = None
    error_message: str | None = None


class CRMAdapter(ABC):
    """
    Abstract base class for CRM adapters.

    Each CRM integration must implement these methods to provide
    a unified interface for the VALLORYS platform.
    """

    def __init__(self, credentials: CRMCredentials, tenant_id: str):
        self.credentials = credentials
        self.tenant_id = tenant_id

    @property
    @abstractmethod
    def crm_type(self) -> CRMType:
        """Return the CRM type."""
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test the CRM connection."""
        pass

    @abstractmethod
    async def pull_lead(
        self,
        lead_id: str,
        include_history: bool = False,
    ) -> CRMLeadData:
        """
        Pull lead/contact data from CRM.

        Args:
            lead_id: CRM lead identifier
            include_history: Include interaction history

        Returns:
            Normalized lead data
        """
        pass

    @abstractmethod
    async def pull_property(
        self,
        property_id: str,
        include_photos: bool = False,
    ) -> CRMPropertyData:
        """
        Pull property data from CRM.

        Args:
            property_id: CRM property identifier
            include_photos: Include photo URLs

        Returns:
            Normalized property data
        """
        pass

    @abstractmethod
    async def push_valuation_report(
        self,
        lead_id: str,
        valuation: ValuationResult,
        report_url: str | None = None,
        create_task: bool = True,
    ) -> CRMPushResult:
        """
        Push valuation report to CRM.

        Args:
            lead_id: CRM lead identifier
            valuation: Valuation result to push
            report_url: URL to PDF report
            create_task: Create follow-up task

        Returns:
            Push result with CRM record ID
        """
        pass

    @abstractmethod
    async def create_task(
        self,
        lead_id: str,
        title: str,
        description: str,
        due_date: str | None = None,
    ) -> str:
        """
        Create a task in CRM.

        Returns:
            Task ID
        """
        pass

    @abstractmethod
    async def add_note(
        self,
        lead_id: str,
        content: str,
    ) -> str:
        """
        Add a note to a lead.

        Returns:
            Note ID
        """
        pass

    async def handle_webhook(self, event_type: str, payload: dict) -> dict:
        """
        Handle incoming webhook from CRM.

        Override in subclass for CRM-specific handling.
        """
        return {
            "status": "received",
            "event_type": event_type,
            "crm_type": self.crm_type.value,
        }

    def _normalize_property(self, raw_data: dict) -> PropertyProfile:
        """
        Normalize raw CRM property data to PropertyProfile.

        Override in subclass for CRM-specific field mapping.
        """
        raise NotImplementedError("Subclass must implement _normalize_property")

    def _normalize_seller(self, raw_data: dict) -> SellerProfile:
        """
        Normalize raw CRM contact data to SellerProfile.

        Override in subclass for CRM-specific field mapping.
        """
        raise NotImplementedError("Subclass must implement _normalize_seller")
