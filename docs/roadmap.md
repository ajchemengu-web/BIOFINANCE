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
- [x] Merchant authentication screen — mock only, see gap below
- [x] Payment request creation + waiting-for-customer screen — mock only, see gap below
- [x] Receipt screen
- [ ] **Backend gap, not yet resolved**: `POST /payments` assumes the caller already has the *customer's* BioFinance session (it requires a customer bearer token and identifies the BioID from that token). BioPOS's actual job per PRD §32 is different — the merchant creates a payment request *before* any customer is identified, and the customer authenticates separately (their own device, or the same terminal) to fulfill it. That needs either:
  - a new "payment request" concept the backend can create unauthenticated (merchant-only) and later attach a `bio_id` to once a customer authenticates against it, or
  - `Transaction.bio_id` becoming nullable until claimed.
  Nothing here is wired to the backend yet — `biopos/lib/features/payment/payment_providers.dart` is local mock state only, matching how `mobile/` started in Phase 1. A real merchant-auth endpoint (JWT scoped to `merchants`/`merchant_devices`, not `users`) doesn't exist yet either.

## Phase 6 — End-to-End Demonstration
- [ ] Full path: customer biometric → BioID → BioRouter → Daraja → M-PESA → merchant confirmation → customer transaction history

## Not in MVP (do not build yet)
National biometric database · government identity integration · physical biometric cards · custom fingerprint hardware · real bank integrations · real Airtel integration · cross-bank settlement · customer fund custody · lending · insurance · investments · cryptocurrency · AI financial advisor · nationwide deployment.

## Success criteria (§47)

The project succeeds technically when: a user creates a BioID → authenticates via device biometrics → sees connected balances → sets M-PESA as preferred provider → a merchant creates a payment request → BioFinance identifies the user → BioRouter selects M-PESA → the Daraja adapter initiates the sandbox transaction → the backend receives the callback → the transaction reaches `COMPLETED` → the merchant sees "PAYMENT SUCCESSFUL" → the customer sees it in their transaction history.
