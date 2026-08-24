# BioFinance — API Spec (v1)

Base path: `/api/v1`. All authenticated endpoints require a bearer access token (short-lived JWT + refresh token, §37). FastAPI serves interactive docs at `/docs` once the app is running — this file is the human-readable index; keep both in sync as endpoints stop being stubs.

## Auth
| Method | Path | Purpose | Status |
|---|---|---|---|
| POST | `/auth/register` | create user + issue BioID | done |
| POST | `/auth/login` | issue access + refresh token | done |
| POST | `/auth/refresh` | rotate access token | done |

## BioID
| Method | Path | Purpose | Status |
|---|---|---|---|
| POST | `/bioid` | issue a BioID for the current user (idempotent) | done |
| GET | `/bioid` | fetch current user's BioID | done |
| POST | `/bioid/lock` | lock the BioID (fraud/lost device) | done |

## Providers
| Method | Path | Purpose | Status |
|---|---|---|---|
| GET | `/providers` | list connected providers | done |
| POST | `/providers/connect` | connect a provider (real or mock) | done |
| DELETE | `/providers/{id}` | disconnect a provider | done |

## Balances
| Method | Path | Purpose | Status |
|---|---|---|---|
| GET | `/balances` | aggregated balance across connected providers | done |

## Routing
| Method | Path | Purpose | Status |
|---|---|---|---|
| GET | `/routing-policy` | current routing policy (creates a default on first read) | done |
| PUT | `/routing-policy` | update mode / primary / fallback | done |

## Payments
| Method | Path | Purpose | Status |
|---|---|---|---|
| POST | `/payments` | customer-initiated (`mobile/`): create + route a payment via BioRouter, authenticated, requires `Idempotency-Key` | done |
| POST | `/payments/request` | merchant-initiated (`biopos/`): open a payment request with no customer yet, unauthenticated (no merchant-auth endpoint exists — see `docs/roadmap.md` Phase 5), requires `Idempotency-Key` | done |
| POST | `/payments/{id}/claim` | a customer, authenticated in their own session, fulfills a merchant's request — attaches their BioID and routes it | done |
| GET | `/payments/{id}` | payment/request status — unauthenticated on purpose, so `biopos/` can poll it | done |
| POST | `/payments/{id}/cancel` | cancel a pending payment | done |

## Transactions
| Method | Path | Purpose | Status |
|---|---|---|---|
| GET | `/transactions` | list transaction history incl. payment attempts | done |
| GET | `/transactions/{id}` | transaction detail incl. payment attempts | done |

## Merchants
| Method | Path | Purpose | Status |
|---|---|---|---|
| POST | `/merchants` | register a merchant (not in original PRD spec — added so payments have something real to target before BioPOS exists in Phase 5) | done |
| GET | `/merchants/{id}` | merchant detail | done |

## Daraja
| Method | Path | Purpose | Status |
|---|---|---|---|
| POST | `/providers/daraja/callback` | Safaricom webhook — authoritative status update (§31) | done, unauthenticated (Safaricom calls it directly) — not yet verified against a real sandbox callback, see `docs/roadmap.md` Phase 4 |

All "done" endpoints are backed by real PostgreSQL via SQLAlchemy — see `backend/app/services/`. MPESA payments route to the real `DarajaProvider` automatically once Daraja credentials are configured (`backend/app/providers/registry.py`); other providers, and MPESA without credentials configured, use the in-memory mock providers.

## Idempotency

Every `POST /payments` and `POST /payments/request` must include a client-generated idempotency key (header `Idempotency-Key`, e.g. `TX-20260824-000001`). A repeated request with the same key returns the existing transaction rather than creating a new one (§28).

## Errors

Standard FastAPI validation errors (422) for bad input. Domain errors return FastAPI's default shape, `{"detail": "<human readable message>"}`, with an appropriate 4xx status — e.g. `POST /payments/{id}/claim` returns 404 if the request doesn't exist, 409 if it's already been claimed or isn't awaiting a customer.
