# BioFinance — API Spec (v1)

Base path: `/api/v1`. All authenticated endpoints require a bearer access token (short-lived JWT + refresh token, §37). FastAPI serves interactive docs at `/docs` once the app is running — this file is the human-readable index; keep both in sync as endpoints stop being stubs.

## Auth
| Method | Path | Purpose | Status |
|---|---|---|---|
| POST | `/auth/register` | create user + issue BioID | stub |
| POST | `/auth/login` | issue access + refresh token | stub |
| POST | `/auth/refresh` | rotate access token | stub |

## BioID
| Method | Path | Purpose | Status |
|---|---|---|---|
| POST | `/bioid` | issue a BioID for the current user | stub |
| GET | `/bioid` | fetch current user's BioID | stub |
| POST | `/bioid/lock` | lock the BioID (fraud/lost device) | stub |

## Providers
| Method | Path | Purpose | Status |
|---|---|---|---|
| GET | `/providers` | list connected providers | stub |
| POST | `/providers/connect` | connect a provider (real or mock) | stub |
| DELETE | `/providers/{id}` | disconnect a provider | stub |

## Balances
| Method | Path | Purpose | Status |
|---|---|---|---|
| GET | `/balances` | aggregated balance across connected providers | stub |

## Routing
| Method | Path | Purpose | Status |
|---|---|---|---|
| GET | `/routing-policy` | current routing policy | stub |
| PUT | `/routing-policy` | update mode / primary / fallback | stub |

## Payments
| Method | Path | Purpose | Status |
|---|---|---|---|
| POST | `/payments` | create a payment (requires `Idempotency-Key`) | stub |
| GET | `/payments/{id}` | payment status | stub |
| POST | `/payments/{id}/cancel` | cancel a pending payment | stub |

## Transactions
| Method | Path | Purpose | Status |
|---|---|---|---|
| GET | `/transactions` | list transaction history | stub |
| GET | `/transactions/{id}` | transaction detail incl. payment attempts | stub |

## Daraja
| Method | Path | Purpose | Status |
|---|---|---|---|
| POST | `/providers/daraja/callback` | Safaricom webhook — authoritative status update (§31) | stub |

## Idempotency

Every `POST /payments` must include a client-generated idempotency key (header `Idempotency-Key`, e.g. `TX-20260824-000001`). A repeated request with the same key returns the existing transaction rather than creating a new one (§28).

## Errors

Standard FastAPI validation errors (422) for bad input. Domain errors return a JSON body `{"error": "<code>", "message": "<human readable>"}` with an appropriate 4xx/5xx status — the exact error-code table gets filled in as each service is implemented (Phase 2+).
