"""CRM adapter factory."""

from vallorys.services.crm.base import CRMAdapter, CRMType, CRMCredentials
from vallorys.services.crm.generic import GenericCRMAdapter


def get_crm_adapter(
    crm_type: CRMType,
    credentials: CRMCredentials,
    tenant_id: str,
    **kwargs,
) -> CRMAdapter:
    """
    Factory function to get the appropriate CRM adapter.

    Args:
        crm_type: Type of CRM to connect to
        credentials: CRM API credentials
        tenant_id: Tenant identifier
        **kwargs: Additional adapter-specific arguments

    Returns:
        Configured CRM adapter instance
    """
    adapters = {
        CRMType.GENERIC: GenericCRMAdapter,
        CRMType.HUBSPOT: GenericCRMAdapter,  # TODO: Implement HubSpotAdapter
        CRMType.PIPEDRIVE: GenericCRMAdapter,  # TODO: Implement PipedriveAdapter
    }

    adapter_class = adapters.get(crm_type)
    if not adapter_class:
        raise ValueError(f"Unsupported CRM type: {crm_type}")

    return adapter_class(
        credentials=credentials,
        tenant_id=tenant_id,
        **kwargs,
    )
