"""API routes aggregation."""

from fastapi import APIRouter

from vallorys.api.endpoints import health, valuation, fieldpack, objection, crm, analytics

router = APIRouter()

# Include all endpoint routers
router.include_router(health.router, tags=["health"])
router.include_router(valuation.router, prefix="/valuation", tags=["valuation"])
router.include_router(fieldpack.router, prefix="/fieldpack", tags=["fieldpack"])
router.include_router(objection.router, prefix="/objection", tags=["objection"])
router.include_router(crm.router, prefix="/crm", tags=["crm"])
router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
