# BioFinance — Security Model

## Principles

- **Authenticate locally; don't collect raw biometric templates unnecessarily.** The Flutter app uses the device's native secure biometric system (Android Keystore / iOS Secure Enclave). Raw fingerprint/face data never leaves the device and is never sent to or stored by the backend.
- Kenya's Data Protection Act treats biometric data (including fingerprinting) as personal data — biometric privacy is an architectural requirement, not an optional feature.
- BioFinance never stores a fingerprint "as" the wallet. The chain is always: biometric → local device authentication success → BioID → routing decision → provider authorization. See `docs/architecture.md`.

## Authentication & sessions

- Password hashing: bcrypt (`passlib`).
- Session tokens: short-lived JWT access token + longer-lived refresh token. Access tokens are not stored server-side; refresh tokens can be revoked.
- Every sensitive operation is authorized server-side — the Flutter client is never trusted to self-report "biometric succeeded" without a corresponding server-verifiable session state.

## Secrets

- Daraja credentials (`DARAJA_CONSUMER_KEY`, `DARAJA_CONSUMER_SECRET`, `DARAJA_SHORTCODE`, `DARAJA_PASSKEY`, `DARAJA_ENVIRONMENT`, `DARAJA_CALLBACK_BASE_URL`) live only in backend environment configuration (`.env`, or Render's environment variable dashboard in production). Never in Flutter source, never committed to git, never stored in PostgreSQL.
- `.env` is gitignored; `.env.example` documents the required keys with placeholder values only.
- `POST /providers/daraja/callback` is deliberately unauthenticated — Safaricom calls it directly, with no BioFinance session to attach a bearer token to. It only ever *reads* a `CheckoutRequestID` we generated ourselves and applies a state transition to the matching transaction; it can't be used to create or target arbitrary transactions. Safaricom's IP allowlisting isn't implemented yet — worth adding before any production use.

## CORS

- `CORS_ALLOWED_ORIGINS` (`backend/app/main.py`, `backend/app/core/config.py`) defaults to `*` — needed so the Vercel-hosted `mobile/`/`biopos/` web builds can call the API cross-origin at all before their deployment URLs are known. `allow_credentials` is `False` (auth is a bearer token in the `Authorization` header, not cookies, so credentialed CORS mode isn't needed — and can't be combined with a wildcard origin regardless). Narrow `CORS_ALLOWED_ORIGINS` to the actual Vercel URL(s) once deployed — see README "Deploying" — a wildcard origin is a reasonable demo default, not a production one.

## Device binding

- The `devices` table associates authorized devices with a user (`docs/database-schema.md`). Future hardening: hardware-backed key pair per device, cryptographic signature on transaction authorization instead of a bare "success" flag.

## Merchant-side integrity

- **Real merchant authentication (built)**: `POST /merchants/register`/`login` issue a merchant-scoped JWT (`type: "merchant_access"`/`"merchant_refresh"`, distinct from a customer's `"access"`/`"refresh"` — `app/core/security.py`, `app/core/deps.py` `get_current_merchant`), and `POST /payments/request` / `POST /payments/{id}/cancel` both now require it. `merchant_id` is derived from that token, never accepted from the request body — a merchant can only ever open or cancel a request against its own id; `cancel` additionally checks the request's `merchant_id` matches the caller's, 403 otherwise. This closes "anyone can currently open a payment request against any merchant ID" from below. `email`/`password_hash` are nullable on `merchants` (migration `0005`) rather than backfilled — a merchant row from before this existed simply has no login.
- Only devices registered in `merchant_devices` may initiate production payment requests (§33 of the source PRD) — an unregistered device cannot pose as a merchant terminal. **Still not enforced**: authenticating *which merchant* is now real, but `POST /payments/request` doesn't yet check that the calling device is one of that merchant's registered `merchant_devices` — a stolen or shared merchant credential could still be used from any device. `merchant_devices` has no registration endpoint yet, unlike the customer-side `devices` table (`POST /devices/register`, BioFinance ID push pairing).
- `POST /payments/{id}/claim`: without a targeted `bio_id_code` at request creation, whoever calls `claim` first, with a valid customer session, still claims the request — there's no pairing mechanism (QR code, proximity check, merchant-side confirmation) binding a specific customer to a specific merchant terminal's specific request. Acceptable for an MVP demo where the request ID isn't guessable and isn't exposed anywhere public; not acceptable before production use as the *only* path. **Fixed for the targeted case**: BioFinance ID push pairing, below — a merchant who has the customer's BioFinance ID no longer needs to rely on this.

## BioFinance ID push pairing (partially built)

Replaces the open-claim gap above with an STK-Push-style flow, keyed on the BioFinance ID (`bio_ids.code`) instead of a phone number. Concrete flow: `docs/architecture.md`. Full endpoint/schema changes: `docs/api-spec.md`, `docs/database-schema.md`. Backend-complete: `bio_id_code` resolution and the ownership check on `claim` (`backend/app/services/payment_service.py`), the push send itself (`backend/app/services/push_service.py`, FCM — **not yet verified against a real Firebase project**, same caveat as `DarajaProvider`), `GET /payments/pending` as the fallback when it doesn't arrive, and rate limiting on the targeted path (below). Only the Flutter side remains — receiving the push and the BioPOS ID-entry screen — deliberately deferred (`docs/roadmap.md` Phase 5). This section covers the trust boundary the whole design rests on.

- **The push notification is advisory only, never a trust boundary.** It tells the customer's app which transaction to show; it proves nothing to the backend and the backend never treats "a push was sent" as any part of authorization. This follows the same principle already established above: the Flutter client is never trusted to self-report success. The one moment that actually authorizes the payment is the authenticated `POST /payments/{id}/claim` call after a local biometric prompt succeeds on-device — identical trust chain to every other authentication in this app (biometric → local device success → BioID → routing decision), never a fingerprint check against anything a provider or the backend holds.
- **Ownership check replaces "first caller wins."** Once `POST /payments/request` attaches a `bio_id` (resolved from the merchant-entered code), `claim` must verify the caller's `user_id` matches it — a stranger with a valid session but the wrong identity gets 403, even if they somehow learn the transaction id.
- **BioFinance ID is not secret, and shouldn't need to be.** It's meant to be spoken aloud at a till, the same way a phone number is for STK push. The push-plus-biometric-claim design is what has to carry the actual security weight, not the ID's obscurity — treat a leaked or guessed BioFinance ID as no worse than a leaked phone number.
- **Abuse surface: unsolicited push spam.** Anyone who knows (or brute-forces) a valid BioFinance ID can trigger a push to that person merely by opening a request against it — no payment completes without their device biometric, but it's still an annoyance/harassment vector. **Mitigated, not eliminated**: `POST /payments/request` rate-limits the targeted path (`bio_id_code` given) to 5/60s per code and 20/60s per merchant (`app/core/rate_limit.py`) — a sliding window held in process memory, not a shared store, so the guarantee is per-instance (real today, since `render.yaml` deploys one instance; would need a shared store like Redis before that stops being true). Feeding repeated unclaimed push-pairing requests against the same `bio_id` into the suspicious-activity logging under "Fraud protection" below is still unbuilt.
- **Push tokens are device data, not identity data** — store `devices.push_token` as an opaque string, never logged in `audit_events.metadata`, and revoke it (null it out / mark the device `REVOKED`) on logout and on explicit device removal, same as `public_key` handling already implied by device binding (§37).
- **Delivery isn't guaranteed** — FCM tokens go stale, phones lose connectivity, apps get force-closed. `GET /payments/pending` (see `docs/api-spec.md`) is the fallback: the customer can open the app, see the pending request themselves, and claim it manually if the push never arrived. The transaction row, not the push, is always the source of truth.

## Fraud protection (MVP scope)

- Transaction limits, basic rate limiting, device verification, mandatory idempotency keys on payment creation, suspicious-transaction logging, repeated-biometric-failure detection.
- Explicitly deferred: behavioral anomaly detection, ML-based risk scoring, device fingerprinting beyond the basic `device_identifier`, merchant risk scoring.

## Audit logging

Append-only `audit_events` table. Minimum event set to implement as features land:

```
LOGIN_SUCCESS          LOGIN_FAILED
BIOMETRIC_SUCCESS      BIOMETRIC_FAILED
DEVICE_REGISTERED      DEVICE_REMOVED
PROVIDER_CONNECTED     PROVIDER_DISCONNECTED
ROUTING_CHANGED
PAYMENT_CREATED        PAYMENT_AUTHORIZED
PAYMENT_COMPLETED      PAYMENT_FAILED
BIOID_LOCKED
```

`metadata` (jsonb) on each event must never contain secrets or raw biometric data — reference IDs only.

## Regulatory posture

The prototype intentionally avoids positioning BioFinance as custodian of customer funds — no customer deposits, no production financial balances, sandbox/mock providers only. The National Payment System Act defines payment-service-provider activity broadly; before any deployment that touches real customer funds, the exact regulatory classification needs Kenyan legal/regulatory advice. This is a hard boundary for MVP scope, not a formality — see `docs/roadmap.md` "Not in MVP."
