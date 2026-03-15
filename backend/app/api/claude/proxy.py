"""Claude API proxy endpoint.

Provides a /v1/messages endpoint compatible with the Anthropic API.
Authenticates users via OpenClade API key, checks balance, routes to a
miner's Anthropic API key, records usage, and deducts billing.
"""

import uuid

import structlog
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import DbDep
from app.core.security import verify_api_key
from app.models.user import ApiKey, User
from app.schemas.proxy import MessagesRequest, MessagesResponse
from app.services.billing_service import calculate_cost, check_and_deduct_balance
from app.services.routing_service import NoAvailableMinerError, route_request
from app.services.user_service import get_user_by_id

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/v1", tags=["proxy"])


async def _authenticate_request(request: Request, db: AsyncSession) -> tuple[User, ApiKey]:
    """Authenticate via OpenClade API key (x-api-key or Bearer token).

    Returns (user, api_key_record).
    Raises HTTPException on auth failure.
    """
    api_key_plain: str | None = None

    x_api_key = request.headers.get("x-api-key", "")
    auth_header = request.headers.get("authorization", "")

    if x_api_key.startswith("oc_"):
        api_key_plain = x_api_key
    elif auth_header.startswith("Bearer oc_"):
        api_key_plain = auth_header[7:]

    if not api_key_plain:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid API key. Use an OpenClade API key (oc_...).",
            headers={"WWW-Authenticate": "Bearer"},
        )

    from app.services.api_key_service import authenticate_by_api_key

    api_key_record = await authenticate_by_api_key(db, api_key_plain)
    if not api_key_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    user = await get_user_by_id(db, str(api_key_record.user_id))
    if not user or user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account inactive",
        )

    return user, api_key_record


@router.post("/messages", response_model=MessagesResponse)
async def messages(
    payload: MessagesRequest,
    request: Request,
    db: DbDep,
) -> MessagesResponse:
    """Proxy POST /v1/messages to a miner's Anthropic API key.

    Flow:
      1. Authenticate OpenClade API key
      2. Check balance (pre-flight estimate)
      3. Route request to selected miner
      4. Record actual token usage and deduct billing
      5. Return Anthropic-compatible response
    """
    request_id = str(uuid.uuid4())
    redis = request.app.state.redis

    # 1. Authenticate
    user, api_key_record = await _authenticate_request(request, db)
    logger.info(
        "proxy request received",
        request_id=request_id,
        user_id=str(user.id),
        model=payload.model,
        stream=payload.stream,
    )

    # 2. Pre-flight balance check (estimate: 1000 tokens)
    estimated_cost = calculate_cost(payload.model, tokens_in=1000, tokens_out=1000)
    if user.balance < estimated_cost:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Insufficient balance. Current balance: {user.balance:.6f} USD. "
            f"Please recharge at /api/v1/billing/recharge",
        )

    # 3. Route to miner
    request_payload = payload.model_dump(exclude_none=True)
    # Remove 'stream' from forwarded payload if False (Anthropic default)
    if not payload.stream:
        request_payload.pop("stream", None)

    try:
        response_body, miner_id = await route_request(
            redis=redis,
            model=payload.model,
            request_payload=request_payload,
            request_id=request_id,
        )
    except NoAvailableMinerError as exc:
        logger.error("no miner available", request_id=request_id, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No miners available to serve this request. Please try again later.",
        ) from exc

    # 4. Deduct billing based on actual token usage
    usage = response_body.get("usage", {})
    tokens_in = usage.get("input_tokens", 0)
    tokens_out = usage.get("output_tokens", 0)

    try:
        miner_uuid = uuid.UUID(miner_id) if miner_id else None
        await check_and_deduct_balance(
            db=db,
            user_id=user.id,
            model=payload.model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            miner_id=miner_uuid,
        )
    except ValueError as exc:
        # Balance issue detected after routing (rare race condition)
        logger.error(
            "billing deduction failed post-routing",
            request_id=request_id,
            error=str(exc),
        )
        # Still return the response — don't penalize user for our race condition
        # In production: log to billing dispute queue

    logger.info(
        "proxy request completed",
        request_id=request_id,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        miner_id=miner_id,
    )

    return MessagesResponse(
        id=response_body.get("id", request_id),
        type="message",
        role="assistant",
        model=response_body.get("model", payload.model),
        content=response_body.get("content", []),
        stop_reason=response_body.get("stop_reason"),
        stop_sequence=response_body.get("stop_sequence"),
        usage=usage,
    )
