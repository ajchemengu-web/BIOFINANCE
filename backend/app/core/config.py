from decimal import Decimal
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

    # Firebase Cloud Messaging — sends the advisory push notification for
    # BioFinance ID push pairing (docs/security-model.md). The service
    # account's whole JSON key file, pasted as one env var (matches how
    # Render env vars work — one value per key, no file uploads). Get one
    # from the Firebase console: Project Settings > Service Accounts >
    # Generate new private key.
    fcm_project_id: str = ""
    fcm_service_account_json: str = ""

    # Per-transaction cap (docs/security-model.md "Fraud protection (MVP
    # scope)" — "Transaction limits"), not a daily/aggregate one. Default
    # roughly matches M-PESA's own real-world per-transaction ceiling —
    # a placeholder to tune, not a regulatory figure this app has derived
    # or verified. Checked at payment-creation time in both
    # PaymentService.create_payment and create_payment_request.
    max_transaction_amount: Decimal = Decimal("150000.00")

    # Comma-separated origins allowed to call this API from a browser (the
    # Vercel-hosted mobile/ and biopos/ web builds). "*" is fine for this
    # MVP demo stage but should narrow to real origins before anything
    # beyond a demo touches this deployment.
    cors_allowed_origins: str = "*"

    @property
    def daraja_configured(self) -> bool:
        return bool(self.daraja_consumer_key and self.daraja_consumer_secret and self.daraja_shortcode)

    @property
    def fcm_configured(self) -> bool:
        return bool(self.fcm_project_id and self.fcm_service_account_json)

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
