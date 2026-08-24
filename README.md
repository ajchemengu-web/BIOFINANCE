# BioFinance

Biometric financial identity and payment-orchestration platform. BioFinance doesn't custody funds or replace banks/mobile-money providers — it gives a user one biometric-enabled identity (**BioID**) to view balances across connected providers (**BioWallet**) and route a payment to whichever provider their policy selects (**BioRouter**), authorizing through the real provider (starting with Safaricom Daraja 3.0 sandbox / M-PESA in Kenya).

See [`docs/architecture.md`](docs/architecture.md) for the full system design, [`docs/roadmap.md`](docs/roadmap.md) for what's built vs. planned, and the other docs in `docs/` for schema, API spec, and security model.

## Stack

- **Mobile**: Flutter / Dart, Riverpod for state management (`mobile/`)
- **Backend**: Python, FastAPI (`backend/`)
- **Database**: PostgreSQL (self-hosted or Render-managed — no Supabase/Firebase)
- **First payment rail**: Safaricom Daraja 3.0 sandbox
- **Backend hosting**: [Render](https://render.com) (`render.yaml`)

## Status

Phase 0 (architecture + scaffold) — see [`docs/roadmap.md`](docs/roadmap.md). Most API endpoints currently return `501 Not Implemented` with a note on which phase implements them; the routing, models, and provider-abstraction skeleton are in place and tested.

## Backend — run locally

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate        # .venv\Scripts\Activate.ps1 on PowerShell
pip install -r requirements.txt
cp .env.example .env          # fill in DATABASE_URL once you have a Postgres instance
uvicorn app.main:app --reload
```

`GET http://localhost:8000/health` should return `{"status": "ok"}` — this works without a real database. `alembic upgrade head` requires a real `DATABASE_URL` in `.env` (Render Postgres or a local instance) and hasn't been run yet in this repo.

Run tests: `pytest` from `backend/`.

## Mobile — run locally

```bash
cd mobile
flutter pub get
flutter run
```

`flutter analyze` and `flutter test` both pass on the current scaffold.

## Deploying the backend to Render

1. Push this repo to a Git remote (GitHub) — not done yet, this repo is currently local-only.
2. In the Render dashboard, create a new Blueprint from `render.yaml`, or a Web Service pointed at `backend/` with build command `pip install -r requirements.txt` and start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
3. Provision a Render Postgres instance and set `DATABASE_URL` on the web service to its connection string.
4. Set the `DARAJA_*` environment variables from your Safaricom developer account (sandbox credentials to start).

## Not in MVP scope

Real bank/Airtel integrations, customer fund custody, lending, insurance, investments, a national biometric database. Full exclusion list in [`docs/roadmap.md`](docs/roadmap.md).
