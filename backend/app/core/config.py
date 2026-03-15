from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_name: str = "OpenClade API"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://openclaude:openclaude@localhost:5432/openclaude"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    secret_key: str = "changeme-in-production-use-openssl-rand-hex-32"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

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


settings = Settings()
