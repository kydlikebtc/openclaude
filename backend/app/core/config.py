import structlog
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = structlog.get_logger(__name__)

_INSECURE_SECRET_KEY = "changeme-in-production-use-openssl-rand-hex-32"
_INSECURE_ENCRYPTION_KEY = "changeme-use-openssl-rand-hex-32-for-redis"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_name: str = "OpenClade API"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://openclaude:openclaude@localhost:5432/openclaude"

    # Redis (单实例模式)
    redis_url: str = "redis://localhost:6379/0"

    # Redis Sentinel HA 模式（优先于 redis_url）
    # 格式: "host1:26379,host2:26379,host3:26379"
    redis_sentinel_hosts: str = ""
    redis_sentinel_master_name: str = "mymaster"
    redis_sentinel_password: str = ""

    # JWT
    secret_key: str = _INSECURE_SECRET_KEY
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # Redis API key encryption (AES-256-GCM) — must be a 32-byte hex string (64 hex chars)
    # Generate with: openssl rand -hex 32
    redis_encryption_key: str = _INSECURE_ENCRYPTION_KEY

    # Cookie authentication
    cookie_secure: bool = False  # Set True in production (requires HTTPS)
    cookie_samesite: str = "lax"  # "strict" in production; "lax" for local dev CORS

    # CORS — empty by default for production safety.
    # Set via CORS_ORIGINS env var (comma-separated or JSON list):
    #   CORS_ORIGINS='["https://app.openclaude.io","https://dashboard.openclaude.io"]'
    # For local development, set in .env:
    #   CORS_ORIGINS='["http://localhost:3000"]'
    cors_origins: list[str] = []

    # Pricing (% of official Anthropic price)
    price_ratio: float = 0.25

    # Miner eligibility thresholds
    min_probe_success_rate: float = 0.90
    min_online_rate: float = 0.80
    max_avg_latency_ms: int = 3000
    min_stake_tao: float = 5.0
    max_referral_bonus: float = 0.30

    # Routing
    max_retries: int = 3
    request_timeout: int = 300

    # Anthropic API — override for local mock/benchmark environments
    anthropic_base_url: str = "https://api.anthropic.com"


settings = Settings()

# Warn loudly if insecure defaults are in use (allow in debug/test mode)
if not settings.debug:
    if settings.secret_key == _INSECURE_SECRET_KEY:
        logger.warning(
            "SECURITY WARNING: Using default JWT secret_key — set SECRET_KEY env var in production"
        )
    if settings.redis_encryption_key == _INSECURE_ENCRYPTION_KEY:
        logger.warning(
            "SECURITY WARNING: Using default redis_encryption_key — "
            "set REDIS_ENCRYPTION_KEY env var in production"
        )
