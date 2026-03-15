from fastapi import APIRouter

from app.api.v1 import admin, api_keys, auth, billing, miners, usage

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(api_keys.router)
router.include_router(billing.router)
router.include_router(miners.router)
router.include_router(admin.router)
router.include_router(usage.router)
