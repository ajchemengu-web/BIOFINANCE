from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/biofinance"

    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    daraja_consumer_key: str = ""
    daraja_consumer_secret: str = ""
    daraja_shortcode: str = ""
    daraja_passkey: str = ""
    daraja_environment: str = "sandbox"
    # Public HTTPS URL Safaricom calls back on completion (POST
    # {daraja_callback_base_url}/api/v1/providers/daraja/callback). Sandbox
    # rejects localhost — needs a tunnel (ngrok) or the Render deployment.
    daraja_callback_base_url: str = ""

    # Comma-separated origins allowed to call this API from a browser (the
    # Vercel-hosted mobile/ and biopos/ web builds). "*" is fine for this
    # MVP demo stage but should narrow to real origins before anything
    # beyond a demo touches this deployment.
    cors_allowed_origins: str = "*"

    @property
    def daraja_configured(self) -> bool:
        return bool(self.daraja_consumer_key and self.daraja_consumer_secret and self.daraja_shortcode)

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
