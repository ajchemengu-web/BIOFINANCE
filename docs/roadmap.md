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
- [ ] `DarajaAdapter` implements `PaymentProvider` fully (auth, STK push, status, callback)
- [ ] BioRouter → DarajaAdapter → Daraja Sandbox path working
- [ ] Callback webhook treated as the authoritative state transition (not the initial request)

## Phase 5 — BioPOS
- [ ] New Flutter app (merchant-facing) — not scaffolded yet, starts here
- [ ] Merchant authentication
- [ ] Payment request creation + status polling
- [ ] Receipt screen

## Phase 6 — End-to-End Demonstration
- [ ] Full path: customer biometric → BioID → BioRouter → Daraja → M-PESA → merchant confirmation → customer transaction history

## Not in MVP (do not build yet)
National biometric database · government identity integration · physical biometric cards · custom fingerprint hardware · real bank integrations · real Airtel integration · cross-bank settlement · customer fund custody · lending · insurance · investments · cryptocurrency · AI financial advisor · nationwide deployment.

## Success criteria (§47)

The project succeeds technically when: a user creates a BioID → authenticates via device biometrics → sees connected balances → sets M-PESA as preferred provider → a merchant creates a payment request → BioFinance identifies the user → BioRouter selects M-PESA → the Daraja adapter initiates the sandbox transaction → the backend receives the callback → the transaction reaches `COMPLETED` → the merchant sees "PAYMENT SUCCESSFUL" → the customer sees it in their transaction history.
