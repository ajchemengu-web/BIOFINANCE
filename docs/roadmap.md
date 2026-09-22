# BioFinance — Roadmap

Source: project PRD, §46. Tracked here as a checklist so progress is visible across sessions.

## Phase 0 — Architecture (this pass)
- [x] Architecture diagram — `docs/architecture.md`
- [x] Database schema — `docs/database-schema.md`
- [x] API specification — `docs/api-spec.md`
- [x] Security model — `docs/security-model.md`
- [x] Flutter project structure — `mobile/`
- [x] Backend skeleton (FastAPI app, stub routers, provider interface, models) — `backend/`

## Phase 1 — Flutter Prototype
- [x] Authentication screens (mock)
- [x] Dashboard (mock balances)
- [x] Provider connection UI (mock)
- [x] Routing policy UI (mock)
- [x] Transaction history UI (mock)
- [x] Payment flow (mock BioRouter with fallback) — not in the original phase list but implemented since it demonstrates the core product loop end-to-end; see `mobile/lib/features/payments/`
Uses mock/local data via Riverpod — no backend calls yet. Verified: `flutter analyze` clean, `flutter test` passes (incl. a full login → pay → history integration test).

## Phase 2 — PostgreSQL + FastAPI
- [x] Real `DATABASE_URL` provisioned (local PostgreSQL 17 via winget, superuser `postgres`/`postgres`)
- [x] Alembic migrations applied against a live database
- [x] Auth, BioID, Providers, Balances, Routing endpoints wired to and verified against real PostgreSQL (`backend/app/services/`)
- [x] Flutter → FastAPI → PostgreSQL wired end-to-end (`mobile/lib/repositories/`, real Riverpod `FutureProvider`/`AsyncNotifier`s replacing the Phase 1 mock state) — verified via `mobile/test/payment_flow_test.dart`, which drives the actual UI (login, connect a provider, set routing policy, pay, view history) against a live `uvicorn` + PostgreSQL backend over real HTTP
- [x] Hardcoded/mock financial data removed from the Flutter app — dashboard, providers, routing, and transactions all read from the backend; only the payment-provider mock balances themselves are intentionally mock (Daraja replaces MPESA in Phase 4)

## Phase 3 — BioRouter
- [x] Primary provider routing (`backend/app/services/router_service.py`)
- [x] Fallback provider routing
- [x] Transaction state machine implemented in `payment_service.py`
- [x] Idempotency enforced on `POST /payments`
- [x] Verified end-to-end against real PostgreSQL — `backend/tests/test_payment_flow.py` (9/9 tests passing, incl. decline→fallback and idempotent replay)

## Phase 4 — Daraja Sandbox
- [x] `DarajaProvider` implements `PaymentProvider` (OAuth, STK push, status query) — `backend/app/providers/daraja.py`
- [x] Callback webhook parses Safaricom's payload and treats it as the authoritative state transition — `POST /providers/daraja/callback`, `PaymentService.handle_daraja_callback`
- [x] `registry.py` routes MPESA to `DarajaProvider` automatically once `DARAJA_CONSUMER_KEY`/`SECRET`/`SHORTCODE` are set, mock otherwise — no code change needed to switch over
- [x] BioRouter no longer fires a fallback attempt while the primary is `PENDING` (an async provider's request in flight) — would otherwise double-send an STK prompt
- [ ] **Not yet verified against the real sandbox** — no Safaricom developer account/credentials were available this session. Covered instead by `backend/tests/test_daraja_provider.py` (mocked HTTP, confirms request/response shapes match the published API) and `backend/tests/test_daraja_callback.py` (real DB, confirms the callback handler's state transitions). Get sandbox credentials at https://developer.safaricom.co.ke, set them in `.env`, set `DARAJA_CALLBACK_BASE_URL` to a public HTTPS URL (sandbox rejects localhost — needs a tunnel like ngrok, or the Render deployment), and re-run a real payment to confirm.
- [ ] `refund_payment` — needs a `SecurityCredential` (initiator password encrypted with Safaricom's public certificate), a separate credential this app doesn't collect yet. Deliberately left unimplemented rather than guessed at.
- [ ] `get_balance` — Daraja has no customer-balance API; BioWallet just won't show a balance for MPESA once Daraja replaces the mock (`balances.py` already handles this gracefully).

## Phase 5 — BioPOS
- [x] New Flutter app (merchant-facing) — `biopos/`, feature-first layout matching `mobile/`
- [x] Merchant authentication screen — calls real `POST /merchants` on sign-in; wasn't real auth at the time (see below — the backend now is, `biopos/` isn't wired to it yet)
- [x] Payment request creation + waiting-for-customer screen — wired to real `POST /payments/request` and polls real `GET /payments/{id}` every 2s (`biopos/lib/features/payment/waiting_screen.dart`)
- [x] Receipt screen — shows the real terminal status (`COMPLETED`/etc.), amount, reference id, and selected provider
- [x] **Backend gap resolved**: `Transaction.bio_id` is now nullable (migration `0002`). `POST /payments/request` (unauthenticated) opens a request with no customer attached, sitting in `AUTHENTICATION_PENDING`; `POST /payments/{id}/claim` (authenticated as the customer) attaches their BioID and routes it through the exact same BioRouter path `POST /payments` uses (`PaymentService._route_and_resolve`, shared by both). `GET /payments/{id}` stayed unauthenticated so BioPOS can poll it. 7 new backend tests in `backend/tests/test_biopos_payment_flow.py` (28/28 passing overall).
- [x] **`biopos/` wired to these endpoints** — `AmountEntryScreen` creates via `POST /payments/request`, `WaitingScreen` polls `GET /payments/{id}` on a real `Timer.periodic`, `Cancel` calls `POST /payments/{id}/cancel`. No in-app "simulate customer" button — that's deliberately not BioPOS's job; a real customer claims from their own `mobile/` session. Verified end-to-end by `biopos/test/payment_flow_test.dart`, which drives BioPOS's actual UI to create a request, then plays "the customer, on another device" via raw HTTP (register → connect a provider → set routing → `POST /payments/{id}/claim`) and confirms BioPOS's polling picks up the `COMPLETED` result and shows the receipt.
- [x] **Real merchant authentication (backend)** — `POST /merchants/register`/`login`/`me`, a merchant-scoped JWT (`type: "merchant_access"`/`"merchant_refresh"`, structurally distinct from a customer's — `app/core/security.py`, `app/core/deps.py` `get_current_merchant`). `POST /payments/request` and `POST /payments/{id}/cancel` both now require it, deriving `merchant_id` from the token rather than trusting the request body (`cancel` also 403s a different merchant's token). `merchants.email`/`password_hash` nullable, not backfilled (migration `0005`) — a merchant row from before this existed has no credential and can't log in. See `docs/security-model.md` "Merchant-side integrity". 21 new backend tests (`backend/tests/test_merchant_auth.py`, plus rewired `test_biopos_payment_flow.py`), 64/64 passing overall.
  - [ ] `biopos/`: replace "sign in creates a fresh Merchant" with real register/login screens, store the merchant token, stop sending `merchant_id` in `POST /payments/request`'s body (server derives it now — the old call shape 404s/401s, not just stops being "real"). (Flutter — deferred.)
  - [ ] `merchant_devices` enforcement — still open. Authenticating *which merchant* is real now; there's no check yet that the calling *device* is one of that merchant's registered terminals (needs a `merchant_devices` registration endpoint, which doesn't exist, unlike the customer-side `devices` table). A stolen/shared merchant credential could still be used from any device. See `docs/security-model.md`.
- [ ] `POST /payments/{id}/claim` has no pairing mechanism (QR code, proximity, merchant confirmation) — whoever calls it first with a valid customer session gets the request. Fine for an MVP demo, not for production (`docs/security-model.md`).
- [ ] **BioFinance ID push pairing** — backend complete, Flutter not started (deliberately deferred — no laptop to run `flutter analyze`/`flutter test` against right now). STK-Push-style flow: merchant enters the customer's BioFinance ID at the terminal instead of opening a blind request. Full design: `docs/architecture.md` ("BioFinance ID push pairing"), `docs/security-model.md` (same heading, trust-boundary detail), `docs/api-spec.md` (Devices section + updated Payments rows), `docs/database-schema.md` (`devices.push_token`/`platform`). Implementation steps, roughly in dependency order:
  - [x] Migration: `devices.push_token`, `devices.platform` columns (`0003_devices_push_token`).
  - [x] `POST /devices/register` — first endpoint to actually use the (previously unused) `devices` table; upserts on (`user_id`, `device_identifier`), 4 new tests in `backend/tests/test_devices.py`.
  - [x] `bio_id_code` param on `POST /payments/request` — resolves to a `bio_id`, attaches it at creation instead of leaving it null (404 if the code doesn't match); row still starts `AUTHENTICATION_PENDING`, attaching identity isn't authenticating it.
  - [x] `claim` ownership check — 403 when the caller's `user_id` doesn't match a pre-attached `bio_id`; the open-claim path (no `bio_id_code`) is unchanged.
  - [x] `push_service.py` (FCM) — sends the advisory notification once `bio_id_code` resolves and the target has a registered device, via Google's OAuth2 service-account (JWT-bearer) grant + FCM HTTP v1 send. **Not yet verified against a real Firebase project** — same caveat as `DarajaProvider`: no real `FCM_PROJECT_ID`/service-account credentials were available this session, so it's covered by `backend/tests/test_push_service.py` against a mocked HTTP transport only. Best-effort by design — never raises, never blocks request creation; silently a no-op when `FCM_PROJECT_ID`/`FCM_SERVICE_ACCOUNT_JSON` aren't set.
  - [x] `GET /payments/pending` — fallback listing (this user's own targeted requests still `AUTHENTICATION_PENDING`) for when push delivery fails, isn't configured, or the customer just opens the app before the push arrives.
  - [x] Rate limiting on `POST /payments/request` when `bio_id_code` is supplied — an in-process sliding window (`app/core/rate_limit.py`), 5/60s per targeted `bio_id_code` and 20/60s per merchant. In-process only (documented limit: doesn't hold once this app runs more than one instance — `render.yaml` deploys exactly one today).
  - [ ] `biopos/`: replace blind amount-entry with a BioFinance-ID-entry step. (Flutter — deferred.)
  - [ ] `mobile/`: receive push → approval screen (merchant name, amount) → local biometric prompt → `claim` call. (Flutter — deferred.)
  - 17 new backend tests across this item (devices, bio_id_code targeting, pending list, push service unit + wiring, rate limiting) — 52/52 passing overall against real Postgres.

## Phase 6 — End-to-End Demonstration
- [ ] Full path: customer biometric → BioID → BioRouter → Daraja → M-PESA → merchant confirmation → customer transaction history

## Phase 7 — International Provider Catalog
- [x] `provider_catalog` table (migration `0004`) — the business/product truth of which providers exist and can be connected, separate from `app/providers/registry.py` (the technical truth of how to talk to each one). Columns: `code`, `display_name`, `country_code` (ISO 3166-1 alpha-2), `currency` (ISO 4217), `category` (`MOBILE_MONEY`/`BANK`/`CARD`/`WALLET`), `status` (`AVAILABLE`/`COMING_SOON`/`DISABLED`). Seeded with the existing MPESA/EQUITY/AIRTEL as Kenya/KES entries. `provider_connections.provider_code` now has a real foreign key into it — the database itself rejects a connection to a code the catalog doesn't know about, on top of the API-level check below.
- [x] `GET /provider-catalog` — public (reference data, not user data), optional `?country=KE` filter. This is what a provider-selection screen renders after sign-up instead of a hardcoded list.
- [x] `POST /providers/connect` validates `provider_code` against the catalog — 404 unknown code, 409 `COMING_SOON`/`DISABLED`. Previously any string was accepted and only failed later, at payment-routing time.
- [x] `GenericMockProvider` (`app/providers/mock_generic.py`) — `registry.py`'s fallback for any catalog code without a bespoke adapter yet, so a brand-new catalog entry (a new country, a new partner not yet integrated) can be connected and routed through immediately for demo purposes. The three original providers keep their specific mocks (matching balances existing tests assert on); Daraja is still the only real adapter.
- [x] `mobile/`'s provider-selection screen (`features/providers/providers_screen.dart`) now renders from `GET /provider-catalog` instead of a hardcoded `['MPESA', 'EQUITY', 'AIRTEL']` list, showing `COMING_SOON`/`DISABLED` entries as a status chip rather than a connect button.
- [ ] **What this doesn't do**: none of this stands up a real integration with any provider outside Kenya — "add any provider worldwide" means the *system* no longer needs a code change to list and demo-connect one; actually moving real money through a new provider still needs a real adapter (à la `DarajaProvider`) and, per the National Payment System Act posture in `docs/security-model.md`, an actual commercial/regulatory agreement with that provider in that jurisdiction. No such agreements exist yet — don't seed the catalog with real providers BioFinance hasn't actually agreed with.
- [ ] Not done: `mobile/`'s other provider-aware screens (`dashboard_screen.dart`, `routing_screen.dart`) still use the old hardcoded `providerDisplayNames` map in `models/provider_connection.dart` as a display-name fallback — harmless (it's only missing a *label* for a catalog provider it doesn't recognize, never blocking a connection), but not yet fully catalog-driven.
- [ ] Country-aware filtering isn't wired up client-side yet (`?country=` exists on the endpoint, unused by `mobile/`) — there's no user country/locale field to filter by.
- [ ] Rate limiting / anti-abuse on `GET /provider-catalog` if it ever needs it — currently low-risk since it's read-only reference data with no per-user cost.

## Not in MVP (do not build yet)
National biometric database · government identity integration · physical biometric cards · custom fingerprint hardware · real bank integrations · real Airtel integration · cross-bank settlement · customer fund custody · lending · insurance · investments · cryptocurrency · AI financial advisor · nationwide deployment.

## Success criteria (§47)

The project succeeds technically when: a user creates a BioID → authenticates via device biometrics → sees connected balances → sets M-PESA as preferred provider → a merchant creates a payment request → BioFinance identifies the user → BioRouter selects M-PESA → the Daraja adapter initiates the sandbox transaction → the backend receives the callback → the transaction reaches `COMPLETED` → the merchant sees "PAYMENT SUCCESSFUL" → the customer sees it in their transaction history.
