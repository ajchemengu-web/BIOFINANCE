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

- The `devices` table associates authorized devices with a user (`docs/database-schema.md`). `POST /devices/register` / `DELETE /devices/{id}` manage that association; revoking clears `push_token` and drops the device from BioFinance ID push pairing's targets. Future hardening: hardware-backed key pair per device, cryptographic signature on transaction authorization instead of a bare "success" flag — device registration today is self-service bookkeeping, not a cryptographic binding, and nothing yet checks device identity on the customer's own payment actions (`POST /payments`, `claim`) the way `merchant_devices` now checks it on the merchant side.

## Merchant-side integrity

- **Real merchant authentication (built)**: `POST /merchants/register`/`login` issue a merchant-scoped JWT (`type: "merchant_access"`/`"merchant_refresh"`, distinct from a customer's `"access"`/`"refresh"` — `app/core/security.py`, `app/core/deps.py` `get_current_merchant`), and `POST /payments/request` / `POST /payments/{id}/cancel` both now require it. `merchant_id` is derived from that token, never accepted from the request body — a merchant can only ever open or cancel a request against its own id; `cancel` additionally checks the request's `merchant_id` matches the caller's, 403 otherwise. This closes "anyone can currently open a payment request against any merchant ID" from below. `email`/`password_hash` are nullable on `merchants` (migration `0005`) rather than backfilled — a merchant row from before this existed simply has no login.
- **`merchant_devices` enforcement (built)**: only devices registered in `merchant_devices` may initiate production payment requests (§33 of the source PRD) — an unregistered device cannot pose as a merchant terminal, even with a valid merchant token. `POST /payments/request` requires a `Device-Identifier` header and 403s unless it names an `ACTIVE` row for that exact merchant (`app/services/merchant_device_service.py`, `require_registered`) — checked against the *authenticated* merchant's id, not a client-supplied one, so a device registered to merchant A never authorizes a request for merchant B even with B's own valid token. `POST /merchant-devices/register` is self-service (any authenticated merchant can register any `device_identifier` for itself), same trust model as the customer-side `POST /devices/register` — this narrows "a leaked credential works from anywhere" down to "a leaked credential works from a device that's been registered," it doesn't eliminate device-registration abuse by someone who already has valid merchant credentials. Device *possession* proof (attestation, a provisioning flow requiring something beyond the merchant password) is future hardening, not built. `DELETE /merchant-devices/{id}` deactivates a device (a revoked one immediately fails `require_registered`) — the actual mechanism for a lost/stolen POS terminal, not just registration bookkeeping.
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

- **Transaction limits — wired.** `Settings.max_transaction_amount` (env `MAX_TRANSACTION_AMOUNT`, default `150000.00` KES) is checked in both `PaymentService.create_payment` and `create_payment_request` before a transaction is created — 400 over the cap. Per-transaction only, not a daily/aggregate limit (that would need querying a customer's recent history, not built).
- **Mandatory idempotency keys on payment creation — wired** (`Idempotency-Key` header, both payment-creation endpoints, since Phase 3).
- **Basic rate limiting — partially wired.** The `bio_id_code`-targeted path of `POST /payments/request` is rate-limited (`app/core/rate_limit.py`, see "BioFinance ID push pairing" above); general payment creation (customer-initiated `POST /payments`, or an open merchant request) isn't.
- **Device verification — partially wired.** `merchant_devices` enforcement (above) verifies the *merchant's* device on `POST /payments/request`; there's no equivalent check on the *customer* side (`POST /payments`, `claim`) — a customer's `devices` table entries (BioFinance ID push pairing) are used for push delivery, not as an authorization gate.
- **Suspicious-transaction logging — wired, narrowly.** `PaymentService._log_payment_failed` logs `SUSPICIOUS_TRANSACTION` (metadata `reason: "repeated_payment_failures"`) once a user hits 3 `PAYMENT_FAILED` events within a 10-minute window (`_SUSPICIOUS_FAILURE_THRESHOLD`/`_SUSPICIOUS_FAILURE_WINDOW_SECONDS`) — a fixed count/window rule built on the audit trail below, not statistical or behavioral modeling (that's the explicitly-deferred item just below). Detection only, no consequence attached yet (no account lock, no alert, no rate-limit tightening) — logging the pattern, not yet acting on it.
- **Repeated-biometric-failure detection — not wired, and can't be without contradicting this doc's own principles.** There is no backend signal: biometric failures never reach the backend at all (client-side only, above), so there is nothing to count. The suspicious-transaction check above is the closest available analogue — payment failures are a backend-visible proxy for "something about this session keeps not working" — but it is not the same signal and this doc doesn't pretend otherwise.
- Explicitly deferred: behavioral anomaly detection, ML-based risk scoring, device fingerprinting beyond the basic `device_identifier`, merchant risk scoring.

## Audit logging

Append-only `audit_events` table, wired (`app/services/audit_service.py`) — the table existed since the first migration but nothing wrote to it until now.

```
LOGIN_SUCCESS          LOGIN_FAILED           — wired (app/api/auth.py)
BIOMETRIC_SUCCESS      BIOMETRIC_FAILED       — not wired, see below
DEVICE_REGISTERED      DEVICE_REMOVED         — both wired (app/services/device_service.py): REGISTERED once per
                                                 new device, not on every push-token refresh; REMOVED on
                                                 DELETE /devices/{id}, which also clears push_token
PROVIDER_CONNECTED     PROVIDER_DISCONNECTED  — wired (app/api/providers.py)
ROUTING_CHANGED                               — wired (app/api/routing.py)
PAYMENT_CREATED        PAYMENT_AUTHORIZED     — wired (app/services/payment_service.py, both payment-creation paths)
PAYMENT_COMPLETED      PAYMENT_FAILED         — wired, including the async Daraja-callback path
                                                 (handle_daraja_callback), not just the synchronous mock-provider one
BIOID_LOCKED                                  — wired (app/api/bioid.py)
SUSPICIOUS_TRANSACTION                        — wired, not in the original list — see "Fraud protection" above
```

**`BIOMETRIC_SUCCESS`/`BIOMETRIC_FAILED` are deliberately not wired.** Biometric authentication happens entirely client-side (this doc, above: "raw biometric data never leaves the device") — there is no backend signal to log. The only way to produce one would be a new endpoint where the Flutter client reports its own biometric outcome, which is exactly the self-report this doc already rules out relying on ("the Flutter client is never trusted to self-report 'biometric succeeded' without a corresponding server-verifiable session state"). A future version could log it as clearly-labeled client telemetry, distinct from any authorization signal — not built this pass.

**`GET /audit-events`** returns the caller's own events, newest first, `?limit=` capped at 200 (default 50) — a user's own activity/security log, not an admin view. There is no admin/role concept anywhere in this app, and this endpoint doesn't invent one: it can only ever answer "what happened on my account." A broader operational view (across all users, for support/fraud-ops tooling) would need that role concept built first — not done.

`metadata` (jsonb) on each event never contains secrets or raw biometric data — reference IDs and statuses only (transaction ids, provider codes, routing mode, etc.), matching every event wired above.

No endpoint reads `audit_events` yet — this closes the write side the PRD requires; consuming the trail (an admin view, alerting, the "repeated-biometric-failure detection" and "suspicious-transaction logging" under Fraud protection below) is unbuilt follow-up work, not in scope here.

## Regulatory posture

The prototype intentionally avoids positioning BioFinance as custodian of customer funds — no customer deposits, no production financial balances, sandbox/mock providers only. The National Payment System Act defines payment-service-provider activity broadly; before any deployment that touches real customer funds, the exact regulatory classification needs Kenyan legal/regulatory advice. This is a hard boundary for MVP scope, not a formality — see `docs/roadmap.md` "Not in MVP."
