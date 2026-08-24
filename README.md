# BioFinance

Biometric financial identity and payment-orchestration platform. BioFinance doesn't custody funds or replace banks/mobile-money providers — it gives a user one biometric-enabled identity (**BioID**) to view balances across connected providers (**BioWallet**) and route a payment to whichever provider their policy selects (**BioRouter**), authorizing through the real provider (starting with Safaricom Daraja 3.0 sandbox / M-PESA in Kenya).

See [`docs/architecture.md`](docs/architecture.md) for the full system design, [`docs/roadmap.md`](docs/roadmap.md) for what's built vs. planned, and the other docs in `docs/` for schema, API spec, and security model.

## Stack

- **Mobile**: Flutter / Dart, Riverpod for state management (`mobile/` — customer app, `biopos/` — merchant terminal app)
- **Backend**: Python, FastAPI (`backend/`)
- **Database**: PostgreSQL (self-hosted or Render-managed — no Supabase/Firebase)
- **First payment rail**: Safaricom Daraja 3.0 sandbox
- **Backend hosting**: [Render](https://render.com) (`render.yaml`)

## Status

Phases 0–3 done: architecture, a real PostgreSQL-backed API, BioRouter (primary/fallback routing, idempotency, transaction state machine), and the customer-facing Flutter app (`mobile/`) wired end-to-end to that live backend (login, BioID, provider connect/disconnect, routing policy, balances, payments, transaction history all hit real endpoints — no mock state left).

Phase 4 (Daraja) is coded but **not yet verified against a real sandbox** — no Safaricom developer credentials were available to test against. `DarajaProvider` (STK push, status query, callback handling) is covered by tests against a mocked HTTP transport instead; MPESA payments automatically switch from the mock provider to real Daraja the moment `DARAJA_CONSUMER_KEY`/`SECRET`/`SHORTCODE` are set in `.env`. See [`docs/roadmap.md`](docs/roadmap.md) for what's needed to actually verify it (a Safaricom developer account + a public callback URL — sandbox rejects localhost).

Phase 5 (BioPOS, `biopos/`) is scaffolded — merchant sign-in, amount entry, waiting-for-customer, and receipt screens. The backend gap this needed is now resolved: `POST /payments/request` lets a merchant open a payment request with no customer attached yet, and `POST /payments/{id}/claim` lets a customer (in their own `mobile/` session) fulfill it, routing through the same BioRouter path as a normal payment. `biopos/` itself still runs on local mock state, though — it isn't wired to call these endpoints yet. See [`docs/roadmap.md`](docs/roadmap.md) Phase 5 for what's left (wiring BioPOS, real merchant auth, a request/customer pairing mechanism).

## Backend — run locally

PostgreSQL 17 is installed locally (via `winget install PostgreSQL.PostgreSQL.17`) with superuser `postgres` / password `postgres`, database `biofinance`.

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate        # .venv\Scripts\Activate.ps1 on PowerShell
pip install -r requirements.txt
cp .env.example .env          # already points at postgres:postgres@localhost:5432/biofinance
alembic upgrade head
uvicorn app.main:app --reload
```

`GET http://localhost:8000/health` returns `{"status": "ok"}`. Run tests: `pytest` from `backend/` — 28 tests: the customer-initiated payment flow end-to-end (register → connect providers → route a payment → fall back on decline → idempotent replay → transaction history), the merchant-initiated flow (open a request → claim it → routes the same way → double-claim rejected), the BioRouter fallback algorithm in isolation, the Daraja provider against a mocked HTTP transport (`respx`), and the Daraja callback handler — all against the real database except the mocked-transport one.

Notes:
- `requirements.txt` pins `bcrypt<4.1` — `passlib` 1.7.4 (last released 2020) breaks against bcrypt 4.1+, which dropped the `__about__` attribute passlib's backend detection relies on.
- The async DB engine uses `NullPool` (`backend/app/db/database.py`) rather than connection pooling — a pooled connection is bound to whichever event loop first used it, and this app has repeatedly ended up with more than one in play across test tooling (FastAPI's `TestClient`, pytest-asyncio). Correctness over pooling performance; revisit if connection-per-request overhead ever actually matters at this app's traffic level.

## Mobile — run locally

```bash
cd mobile
flutter pub get
flutter run
```

Points at `http://localhost:8000/api/v1` by default (override with `--dart-define=API_BASE_URL=...`), so the backend needs to be running first — see above.

`flutter analyze` is clean. `flutter test` runs two suites: a basic widget test with no backend dependency, and `payment_flow_test.dart`, which drives the real app (login → connect a provider → set routing policy → pay → view history) against the live backend over real HTTP — **start `uvicorn` first**, or this one fails with connection errors. It deliberately opts out of Flutter's test-network sandbox (`HttpOverrides.global = null`) and runs the whole flow inside one `tester.runAsync` block; see the comments in that file if you're extending it — mixing real async I/O with `flutter_test`'s fake clock is easy to get subtly wrong (multiple real network calls fired outside `runAsync`, or split across separate `runAsync` calls, just hang forever on the next `pumpAndSettle`).

## BioPOS — run locally

```bash
cd biopos
flutter pub get
flutter run
```

Local mock state only right now — no backend connection (see Status above). `flutter analyze` is clean; `flutter test` covers the full mock flow (sign in → request payment → simulate customer authentication → receipt → new transaction).

## Deploying the backend to Render

1. Repo is on GitHub at [github.com/ajchemengu-web/BIOFINANCE](https://github.com/ajchemengu-web/BIOFINANCE).
2. In the Render dashboard, create a new Blueprint from `render.yaml`, or a Web Service pointed at `backend/` with build command `pip install -r requirements.txt` and start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
3. Provision a Render Postgres instance and set `DATABASE_URL` on the web service to its connection string.
4. Set the `DARAJA_*` environment variables from your Safaricom developer account (sandbox credentials to start), including `DARAJA_CALLBACK_BASE_URL` set to this service's own public URL.

## Not in MVP scope

Real bank/Airtel integrations, customer fund custody, lending, insurance, investments, a national biometric database. Full exclusion list in [`docs/roadmap.md`](docs/roadmap.md).
