"""CRM adapter layer for multi-CRM integration."""

from vallorys.services.crm.base import CRMAdapter, CRMType
from vallorys.services.crm.factory import get_crm_adapter

__all__ = ["CRMAdapter", "CRMType", "get_crm_adapter"]
