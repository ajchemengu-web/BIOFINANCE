# BioFinance

Biometric financial identity and payment-orchestration platform. BioFinance doesn't custody funds or replace banks/mobile-money providers — it gives a user one biometric-enabled identity (**BioID**) to view balances across connected providers (**BioWallet**) and route a payment to whichever provider their policy selects (**BioRouter**), authorizing through the real provider (starting with Safaricom Daraja 3.0 sandbox / M-PESA in Kenya).

See [`docs/architecture.md`](docs/architecture.md) for the full system design, [`docs/roadmap.md`](docs/roadmap.md) for what's built vs. planned, and the other docs in `docs/` for schema, API spec, and security model.

## Stack

- **Mobile**: Flutter / Dart, Riverpod for state management (`mobile/` — customer app, `biopos/` — merchant terminal app)
- **Backend**: Python, FastAPI (`backend/`)
- **Database**: PostgreSQL (self-hosted or Render-managed — no Supabase/Firebase)
- **First payment rail**: Safaricom Daraja 3.0 sandbox
- **Backend hosting**: [Render](https://render.com) (`render.yaml`)
- **Frontend hosting**: [Vercel](https://vercel.com) (`mobile/vercel.json`, `biopos/vercel.json`) — static Flutter web builds, each importable directly from this GitHub repo

## Status

Phases 0–3 done: architecture, a real PostgreSQL-backed API, BioRouter (primary/fallback routing, idempotency, transaction state machine), and the customer-facing Flutter app (`mobile/`) wired end-to-end to that live backend (login, BioID, provider connect/disconnect, routing policy, balances, payments, transaction history all hit real endpoints — no mock state left).

Phase 4 (Daraja) is coded but **not yet verified against a real sandbox** — no Safaricom developer credentials were available to test against. `DarajaProvider` (STK push, status query, callback handling) is covered by tests against a mocked HTTP transport instead; MPESA payments automatically switch from the mock provider to real Daraja the moment `DARAJA_CONSUMER_KEY`/`SECRET`/`SHORTCODE` are set in `.env`. See [`docs/roadmap.md`](docs/roadmap.md) for what's needed to actually verify it (a Safaricom developer account + a public callback URL — sandbox rejects localhost).

Phase 5 (BioPOS, `biopos/`) — backend is now fully real, both layers: `POST /merchants/register`/`login` issue a merchant-scoped JWT distinct from a customer's, and `POST /payments/request` requires it plus a `Device-Identifier` header naming a device that merchant registered via `POST /merchant-devices/register` (403 otherwise) — `POST /payments/{id}/cancel` requires merchant auth too, ownership-checked. `biopos/` itself is **not yet wired to any of this** — it still does the old "sign-in creates a fresh `Merchant` row, no real login, no device registration" thing and would need updating to actually work against the current API (deliberately deferred, no laptop to verify Flutter changes against right now). Also still open, of BioFinance ID push pairing: the Flutter side (receiving the push, a BioFinance-ID-entry screen). The push-pairing backend (targeted requests, the `claim` ownership check, the FCM push send, `GET /payments/pending`, rate limiting) is done. See [`docs/roadmap.md`](docs/roadmap.md) Phase 5.

Phase 7 (international provider catalog) is built: which financial providers exist and can be connected is now a database table (`provider_catalog`), not a hardcoded list — `GET /provider-catalog` serves it, `POST /providers/connect` validates against it, and `mobile/`'s provider-selection screen renders it. Adding a provider anywhere in the world is a catalog row (plus a real adapter and an actual integration agreement once it's more than a demo); no BioRouter or payment-service code changes needed. See [`docs/roadmap.md`](docs/roadmap.md) Phase 7 for what this does and doesn't cover.

Phase 6 (end-to-end demonstration) is done **at the backend level**: `backend/scripts/demo_end_to_end.py` runs the full PRD §47 story — BioID issuance, provider connection, routing policy, merchant registration + device registration, BioFinance ID push pairing to identify the customer, BioRouter, the transaction reaching `COMPLETED`, and it showing up in the customer's history — against a real running backend and real Postgres (`python -m scripts.demo_end_to_end`, or see it run automatically in `backend/tests/test_end_to_end_demo.py`). It is **not** the full literal Phase 6: MPESA routes to the mock provider (no real Daraja sandbox), nothing is actually deployed, and no Flutter app participates. See [`docs/roadmap.md`](docs/roadmap.md) Phase 6 for exactly what is and isn't proven.

Phase 8 (audit logging) is built: `audit_events` existed since the very first migration but nothing wrote to it until now — `app/services/audit_service.py` wires the documented minimum event set (logins, device registration and removal, provider connect/disconnect, routing changes, the full payment lifecycle including the async Daraja-callback path, BioID locking) into the operations that already existed, each event staged in the same DB transaction as the thing it's auditing. `DELETE /devices/{id}` and `DELETE /merchant-devices/{id}` let a customer or merchant revoke a device — the merchant side has real teeth (a revoked POS terminal immediately fails the device check on `POST /payments/request`), not just bookkeeping. `SUSPICIOUS_TRANSACTION` fires after 3 payment failures for one user in 10 minutes (a fixed rule, not behavioral modeling), and `GET /audit-events` lets a user read their own trail (self-scoped only — no admin/role concept exists to gate a broader view). Not done: `BIOMETRIC_SUCCESS`/`BIOMETRIC_FAILED` and repeated-biometric-failure detection — no backend signal exists, biometric auth is entirely client-side, and a client self-report would contradict the security model's own trust boundary. See [`docs/roadmap.md`](docs/roadmap.md) Phase 8.

Phase 9 (transaction limits) is built: a per-transaction cap (`MAX_TRANSACTION_AMOUNT`, default 150,000 KES) is now enforced on both payment-creation paths — 400 over the limit. Per-transaction only, not daily/aggregate. See [`docs/roadmap.md`](docs/roadmap.md) Phase 9 and `docs/security-model.md` "Fraud protection (MVP scope)" for what else in that section is and isn't covered yet.

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

`GET http://localhost:8000/health` returns `{"status": "ok"}`. Run tests: `pytest` from `backend/` — 94 tests covering, roughly by file: the customer-initiated payment flow end-to-end (`test_payment_flow.py`), the merchant-initiated flow authenticated as both the merchant and the device throughout plus BioFinance ID push pairing and rate limiting (`test_biopos_payment_flow.py`), merchant register/login/`me` and its token type being rejected by customer endpoints and vice versa (`test_merchant_auth.py`), merchant device registration, revocation, and enforcement (`test_merchant_devices.py`), the Phase 6 end-to-end demonstration (`test_end_to_end_demo.py`, also runnable standalone — see below), audit logging landing rows for the documented event set plus `SUSPICIOUS_TRANSACTION` (fires at 3 failures, not 2) and `GET /audit-events` returning only the caller's own rows (`test_audit_service.py`), the per-transaction amount cap on both payment-creation paths (`test_transaction_limits.py`), the BioRouter fallback algorithm in isolation (`test_router_service.py`), the Daraja provider against a mocked HTTP transport and its callback handler (`test_daraja_provider.py`, `test_daraja_callback.py`), customer device registration and revocation (`test_devices.py`), the FCM push service unit + wiring tests (`test_push_service.py`), the sliding-window rate limiter in isolation (`test_rate_limit.py`), and the provider catalog (`test_provider_catalog.py`) — all against the real database except the mocked-HTTP-transport and pure-Python ones.

Run the Phase 6 demo narrated, against this running server: `python -m scripts.demo_end_to_end` (from `backend/`, with `uvicorn` already running — see [`docs/roadmap.md`](docs/roadmap.md) Phase 6 for what it does and doesn't prove).

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

Points at `http://localhost:8000/api/v1` by default (override with `--dart-define=API_BASE_URL=...`) — start the backend first.

`flutter analyze` is clean. `flutter test` drives the real UI against the live backend: sign in creates a merchant, requesting a payment opens a real request, then — playing "a customer on their own device" via raw HTTP, since claiming is `mobile/`'s job, not BioPOS's — registers a customer, connects M-PESA, sets it as primary, and claims the request; confirms BioPOS's polling picks it up and shows the receipt. Same `runAsync` + `HttpOverrides.global = null` requirements as `mobile/`'s test, plus one more lesson this one surfaced: a plain `pump()` rebuilds the tree but doesn't advance the fake animation clock, so a `Navigator.push`'s page-transition needs an explicit `pump(duration)` too, or the new screen's `State` gets constructed but nothing can find its widgets yet.

## Deploying — Render (backend) + Vercel (frontends)

Backend needs a persistent process and a real Postgres connection, which is what Render is for; the two Flutter web builds are static output, which is what Vercel is for. Deploy in this order — the frontend needs the backend's URL, and (optionally) the backend needs the frontend's URL back for CORS.

**1. Backend on Render**
1. In the [Render dashboard](https://dashboard.render.com), create a new Blueprint from this repo — it'll pick up `render.yaml` automatically (Web Service rooted at `backend/`, build/pre-deploy/start commands, and the env var list already declared).
2. Provision a Render Postgres instance (or use any other reachable Postgres) and set `DATABASE_URL` on the web service to its connection string. `preDeployCommand: alembic upgrade head` in `render.yaml` runs migrations automatically on every deploy.
3. Leave `DARAJA_*` and `CORS_ALLOWED_ORIGINS` unset for now (defaults: Daraja mock provider, CORS wide open) — come back to them after steps 2 and 3 below.
4. Note the service's URL, e.g. `https://biofinance-api.onrender.com` — the frontends need `<that URL>/api/v1` as `API_BASE_URL`.

**2. Frontend(s) on Vercel** — repeat per app you want live (`mobile/`, `biopos/`, or both — each needs its own Vercel project since Vercel projects map to one root directory):
1. In the [Vercel dashboard](https://vercel.com/new), import this GitHub repo.
2. Set **Root Directory** to `mobile` (or `biopos`) — Vercel finds that folder's `vercel.json` (build command clones the Flutter SDK, since Vercel's build image doesn't have Flutter preinstalled — a standard pattern for this, not Vercel-specific tooling — then runs `flutter build web`).
3. Set **Framework Preset** to "Other" — there's no `package.json` here for Vercel to auto-detect against.
4. Add an environment variable **`API_BASE_URL`** = `https://<your-render-service>.onrender.com/api/v1` (from step 1.4). The build command reads this and bakes it into the web build via `--dart-define`.
5. Deploy. Note the resulting `*.vercel.app` URL(s).

**3. Back on Render** — tighten CORS now that you know the frontend URL(s): set `CORS_ALLOWED_ORIGINS` to a comma-separated list of your Vercel URLs (e.g. `https://biofinance-mobile.vercel.app,https://biofinance-biopos.vercel.app`) instead of leaving it at the default `*`.

**4. Daraja** (optional, once you have Safaricom sandbox credentials): set `DARAJA_CONSUMER_KEY`/`SECRET`/`SHORTCODE`/`PASSKEY` and `DARAJA_CALLBACK_BASE_URL` to the Render service's own URL from step 1.4 — MPESA payments switch from the mock provider to real Daraja automatically, no redeploy-time code change needed.

None of this has actually been deployed yet — the config above (`render.yaml`, `mobile/vercel.json`, `biopos/vercel.json`) is prepared and ready to import, but importing/provisioning happens in your own Render and Vercel accounts.

## Not in MVP scope

Real bank/Airtel integrations, customer fund custody, lending, insurance, investments, a national biometric database. Full exclusion list in [`docs/roadmap.md`](docs/roadmap.md).
