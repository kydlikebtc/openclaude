import structlog
from fastapi import APIRouter, HTTPException, status

from app.core.deps import CurrentUser, DbDep
from app.core.security import create_access_token
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.user_service import authenticate_user, create_user, get_user_by_email

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: DbDep) -> TokenResponse:
    existing = await get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    user = await create_user(db, email=payload.email, password=payload.password)
    token = create_access_token(str(user.id))
    logger.info("User registered", user_id=str(user.id))
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: DbDep) -> TokenResponse:
    user = await authenticate_user(db, email=payload.email, password=payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    token = create_access_token(str(user.id))
    logger.info("User logged in", user_id=str(user.id))
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUser) -> UserResponse:
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        status=current_user.status,
    )
