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

Phase 5 (BioPOS, `biopos/`) is wired end-to-end: merchant sign-in creates a real `Merchant`, amount entry opens a real payment request (`POST /payments/request`), and the waiting screen polls the real backend (`GET /payments/{id}`) until a customer claims it from their own `mobile/` session (`POST /payments/{id}/claim`) — same BioRouter path as a normal payment. What's still open: real merchant authentication (`POST /merchants` is unauthenticated and creates a fresh row per sign-in — no login exists yet) and a pairing mechanism binding a specific customer to a specific terminal's request. See [`docs/roadmap.md`](docs/roadmap.md) Phase 5.

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
