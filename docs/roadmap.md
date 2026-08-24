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
- [ ] Authentication screens (mock)
- [ ] Dashboard (mock balances)
- [ ] Provider connection UI (mock)
- [ ] Routing policy UI (mock)
- [ ] Transaction history UI (mock)
Uses mock/local data — no backend calls required yet.

## Phase 2 — PostgreSQL + FastAPI
- [ ] Real `DATABASE_URL` provisioned (Render Postgres or local)
- [ ] Alembic migrations applied
- [ ] Flutter → FastAPI → PostgreSQL wired end-to-end
- [ ] Hardcoded/mock financial data removed from the Flutter app

## Phase 3 — BioRouter
- [ ] Primary provider routing
- [ ] Fallback provider routing
- [ ] Transaction state machine implemented in `transaction_service.py`
- [ ] Idempotency enforced on `POST /payments`

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
