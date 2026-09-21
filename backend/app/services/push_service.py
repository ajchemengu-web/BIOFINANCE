"""
Firebase Cloud Messaging adapter — sends the advisory push notification for
BioFinance ID push pairing (docs/security-model.md: "The push notification
is advisory only, never a trust boundary" — it tells the customer's app
which transaction to look at, it authorizes nothing). Every public method
here swallows its own failures and returns False rather than raising: a
push failing to send must never block or fail the payment request it's
attached to. GET /payments/pending is the fallback for exactly that case.

NOT YET LIVE-TESTED — no real Firebase project/service-account credentials
were available this session. Written strictly to Google's published
OAuth2 service-account (JWT-bearer) grant and FCM HTTP v1 API contracts,
covered by tests against a mocked HTTP transport
(tests/test_push_service.py), not a real Firebase project. Same caveat as
app/providers/daraja.py.
"""

import json
import logging
import time
from decimal import Decimal

import httpx
import jwt

from app.core.config import Settings

logger = logging.getLogger(__name__)

_TOKEN_URL = "https://oauth2.googleapis.com/token"
_FCM_SCOPE = "https://www.googleapis.com/auth/firebase.messaging"
_JWT_LIFETIME_SECONDS = 3600


class PushService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._service_account = json.loads(settings.fcm_service_account_json) if settings.fcm_service_account_json else {}

    async def _get_access_token(self) -> str:
        now = int(time.time())
        assertion = jwt.encode(
            {
                "iss": self._service_account["client_email"],
                "scope": _FCM_SCOPE,
                "aud": _TOKEN_URL,
                "iat": now,
                "exp": now + _JWT_LIFETIME_SECONDS,
            },
            self._service_account["private_key"],
            algorithm="RS256",
        )
        async with httpx.AsyncClient() as client:
            response = await client.post(
                _TOKEN_URL,
                data={
                    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                    "assertion": assertion,
                },
            )
            response.raise_for_status()
            return response.json()["access_token"]

    async def send_payment_approval_request(
        self,
        push_token: str,
        transaction_id: str,
        merchant_name: str,
        amount: Decimal,
        currency: str,
    ) -> bool:
        """
        Best-effort — returns whether the send succeeded, never raises. The
        transaction row (not this call's outcome) is always the source of
        truth; a caller that needs the request to actually reach the
        customer has GET /payments/pending as the fallback.
        """
        if not self._settings.fcm_configured:
            return False

        try:
            access_token = await self._get_access_token()
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://fcm.googleapis.com/v1/projects/{self._settings.fcm_project_id}/messages:send",
                    headers={"Authorization": f"Bearer {access_token}"},
                    json={
                        "message": {
                            "token": push_token,
                            "notification": {
                                "title": "Payment request",
                                "body": f"{merchant_name} is requesting {currency} {amount}",
                            },
                            "data": {
                                "type": "PAYMENT_APPROVAL_REQUEST",
                                "transaction_id": transaction_id,
                            },
                        }
                    },
                )
            response.raise_for_status()
            return True
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            # KeyError/ValueError: malformed fcm_service_account_json.
            # httpx.HTTPError: network failure or a non-2xx from Google
            # (e.g. a stale/unregistered push_token) — FCM tokens go stale
            # routinely (docs/security-model.md, "Delivery isn't
            # guaranteed"), so this is an expected, not exceptional, case.
            logger.warning("Push notification failed for transaction %s: %s", transaction_id, exc)
            return False
