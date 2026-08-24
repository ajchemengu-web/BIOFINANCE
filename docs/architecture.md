# BioFinance — Architecture

## What this is

BioFinance is a provider-independent financial identity and payment-orchestration layer. It does not custody funds and does not replace banks or mobile-money providers — it sits above them, giving a user one biometric-enabled interface (**BioID**) to view balances across providers (**BioWallet**) and route a payment to whichever connected provider their policy selects (**BioRouter**).

The prototype phase uses simulated providers plus one real integration (Safaricom Daraja 3.0 sandbox) to prove the architecture without holding customer funds or requiring a payment-service-provider license.

## Component diagram

```
                         ┌───────────────┐
                         │ Flutter App   │
                         └───────┬───────┘
                                 │ HTTPS
                                 ▼
                       ┌──────────────────┐
                       │ Python FastAPI   │
                       │      API         │
                       └────────┬─────────┘
                                │
                 ┌──────────────┼──────────────┐
                 ▼              ▼              ▼
             BioID Service  BioRouter     Transaction
                              Service        Service
                 │              │              │
                 └──────────────┼──────────────┘
                                │
                                ▼
                         Provider Layer
                                │
                  ┌─────────────┼─────────────┐
                  ▼             ▼             ▼
             DarajaAdapter   MockBank      MockAirtel
                  │
                  ▼
             Daraja Sandbox → M-PESA
                                │
                                ▼
                         PostgreSQL
```

## The non-negotiable rule

**BioFinance must remain provider-agnostic.** Daraja is the first payment rail, not the foundation. Every provider — real or mock — implements the same `PaymentProvider` interface (`app/providers/base.py`):

```python
class PaymentProvider:
    async def get_balance(self, account_id): ...
    async def initiate_payment(self, request): ...
    async def get_payment_status(self, transaction_id): ...
    async def refund_payment(self, transaction_id): ...
```

`BioRouter` talks only to this interface, never to a concrete provider SDK. Adding a bank later means writing one new adapter class, not touching BioRouter.

## Layers

| Layer | Responsibility | Location |
|---|---|---|
| Flutter App | UI, local biometric auth via device secure hardware, never uploads raw biometric data | `mobile/` |
| FastAPI API | HTTP boundary, auth, request validation | `backend/app/api/` |
| Services | BioID issuance, routing decisions, payment lifecycle, transaction bookkeeping | `backend/app/services/` |
| Provider Layer | Uniform interface over real/mock financial providers | `backend/app/providers/` |
| PostgreSQL | Source of truth for users, BioIDs, providers, routing policy, transactions, audit log | self-hosted / Render Postgres |

## Deployment target

Backend deploys to **Render** as a Python web service (see `render.yaml`). Render's managed Postgres is the initial database — no Supabase/Firebase, no managed-DB vendor lock-in beyond "it's Postgres." Local dev points `DATABASE_URL` at the same instance or a locally installed Postgres.

## What this is NOT (yet)

No customer fund custody, no real bank/Airtel integration, no lending/insurance/investment products, no national biometric database. See `docs/roadmap.md` §"Not in MVP" for the full exclusion list. The system is a technology prototype, not a licensed financial service — the National Payment System Act would require PSP authorization before any production deployment that touches real customer funds.
