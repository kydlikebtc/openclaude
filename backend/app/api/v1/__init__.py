from fastapi import APIRouter

from app.api.v1 import api_keys, auth, billing, miners

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(api_keys.router)
router.include_router(billing.router)
router.include_router(miners.router)
