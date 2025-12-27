from fastapi import APIRouter

from app.api.v1.endpoints import names, preferences, enrichment, profiles, name_enhancements, prefix_tree

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(names.router, prefix="/names", tags=["names"])
api_router.include_router(
    preferences.router, prefix="/preferences", tags=["preferences"]
)
api_router.include_router(
    enrichment.router, prefix="/enrichment", tags=["enrichment"]
)
api_router.include_router(
    profiles.router, prefix="/profiles", tags=["profiles"]
)
api_router.include_router(
    name_enhancements.router, prefix="/enhancements", tags=["enhancements"]
)
api_router.include_router(
    prefix_tree.router, prefix="/prefix", tags=["prefix-tree"]
)
