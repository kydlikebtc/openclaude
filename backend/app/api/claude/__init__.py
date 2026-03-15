from fastapi import APIRouter

from app.api.claude import proxy

router = APIRouter()
router.include_router(proxy.router)
