# BioFinance — Database Schema (PostgreSQL)

All monetary columns use `NUMERIC(14,2)` — never floating point. All primary keys are UUIDs. All tables carry `created_at` (and `updated_at` where the row is mutable).

## Entities

### users
Core account record.
| column | type | notes |
|---|---|---|
| id | uuid, pk | |
| email | text, unique | |
| password_hash | text | bcrypt |
| full_name | text | |
| status | text | `ACTIVE`, `SUSPENDED`, `LOCKED` |
| created_at | timestamptz | |

### bio_ids
One-to-one with `users`. The provider-independent identity (e.g. `BF-8X7K29`). Never a phone number, account number, or raw biometric.
| column | type | notes |
|---|---|---|
| id | uuid, pk | |
| user_id | uuid, fk → users, unique | |
| code | text, unique | display identifier, internally generated |
| status | text | `ACTIVE`, `LOCKED` |
| created_at | timestamptz | |

### devices
Devices authorized to authenticate on behalf of a user (device binding, §37).
| column | type | notes |
|---|---|---|
| id | uuid, pk | |
| user_id | uuid, fk → users | |
| device_identifier | text | |
| public_key | text | for hardware-backed signature verification, future use |
| status | text | `ACTIVE`, `REVOKED` |
| created_at | timestamptz | |

### provider_connections
A user's link to one financial provider (real or mock).
| column | type | notes |
|---|---|---|
| id | uuid, pk | |
| user_id | uuid, fk → users | |
| provider_code | text | `MPESA`, `EQUITY`, `AIRTEL`, ... |
| status | text | `CONNECTED`, `DISCONNECTED` |
| created_at | timestamptz | |

### provider_accounts
The underlying account at the provider, referenced by `provider_connections`. Kept separate so one connection can expose multiple accounts later.
| column | type | notes |
|---|---|---|
| id | uuid, pk | |
| provider_connection_id | uuid, fk → provider_connections | |
| external_account_ref | text | opaque reference, never exposed raw in logs |
| currency | text | `KES` |
| created_at | timestamptz | |

### routing_policies
One per user. Drives BioRouter (§22-23).
| column | type | notes |
|---|---|---|
| id | uuid, pk | |
| user_id | uuid, fk → users, unique | |
| mode | text | `PRIMARY`, `PRIORITY`, `AUTOMATIC`, `MANUAL` |
| primary_provider_id | uuid, fk → provider_connections, nullable | |
| fallback_provider_id | uuid, fk → provider_connections, nullable | |
| created_at | timestamptz | |
| updated_at | timestamptz | |

### merchants
| column | type | notes |
|---|---|---|
| id | uuid, pk | |
| business_name | text | |
| merchant_code | text, unique | |
| status | text | `ACTIVE`, `SUSPENDED` |
| created_at | timestamptz | |

### merchant_devices
Only registered merchant devices may initiate production payment requests (§33).
| column | type | notes |
|---|---|---|
| id | uuid, pk | |
| merchant_id | uuid, fk → merchants | |
| device_identifier | text | |
| status | text | `ACTIVE`, `REVOKED` |
| created_at | timestamptz | |

### transactions
| column | type | notes |
|---|---|---|
| id | uuid, pk | |
| bio_id | uuid, fk → bio_ids, **nullable** | null until claimed — BioPOS-created requests (§32) have no customer yet; `POST /payments/{id}/claim` attaches one |
| merchant_id | uuid, fk → merchants | |
| amount | numeric(14,2) | |
| currency | text | `KES` |
| status | text | see state machine below |
| selected_provider | text, nullable | resolved by BioRouter |
| idempotency_key | text, unique | required on creation (§28) |
| created_at | timestamptz | |
| updated_at | timestamptz | |
| completed_at | timestamptz, nullable | |

### payment_attempts
One transaction can have multiple attempts across providers (fallback routing, §27).
| column | type | notes |
|---|---|---|
| id | uuid, pk | |
| transaction_id | uuid, fk → transactions | |
| provider_code | text | |
| result | text | `SUCCESS`, `DECLINED`, `TIMEOUT`, `ERROR` |
| provider_reference | text, nullable | Daraja `CheckoutRequestID` etc. |
| created_at | timestamptz | |

### audit_events
Append-only security/event log (§39).
| column | type | notes |
|---|---|---|
| id | uuid, pk | |
| user_id | uuid, fk → users, nullable | |
| event_type | text | `LOGIN_SUCCESS`, `BIOMETRIC_FAILED`, `PAYMENT_COMPLETED`, ... |
| metadata | jsonb | no raw secrets, no raw biometric data |
| created_at | timestamptz | |

### notifications
| column | type | notes |
|---|---|---|
| id | uuid, pk | |
| user_id | uuid, fk → users | |
| type | text | |
| payload | jsonb | |
| read_at | timestamptz, nullable | |
| created_at | timestamptz | |

## Relationships

```
User
 ├── BioID (1:1)
 ├── Devices (1:N)
 ├── ProviderConnections (1:N)
 │      └── ProviderAccount (1:N)
 ├── RoutingPolicy (1:1)
 └── Transactions (via BioID, 1:N)
        └── PaymentAttempts (1:N)
```

## Transaction state machine

```
CREATED → AUTHENTICATION_PENDING → AUTHENTICATED → ROUTING
        → AUTHORIZATION_PENDING → PROCESSING → COMPLETED
```
Failure states: `AUTHENTICATION_FAILED`, `DECLINED`, `INSUFFICIENT_FUNDS`, `PROVIDER_UNAVAILABLE`, `TIMEOUT`, `CANCELLED`, `FAILED`, `REVERSED`, `REFUNDED`.

Two entry points, per PRD §42/§32:
- **Customer-initiated** (`mobile/`, `PaymentService.create_payment`): the customer's own app has already run biometric auth client-side before calling `POST /payments`, so the row is created with `bio_id` set and jumps straight to `AUTHENTICATED`.
- **Merchant-initiated** (`biopos/`, `PaymentService.create_payment_request` + `claim_payment_request`): the merchant terminal has no customer to attach yet, so the row is created with `bio_id = NULL` and sits in `AUTHENTICATION_PENDING` until `POST /payments/{id}/claim` (called from the claiming customer's own session) attaches a `bio_id` and transitions it to `AUTHENTICATED`. Both paths converge from there — same routing, same state machine onward.

`AUTHORIZATION_PENDING` also covers an async provider's in-flight request (Daraja's STK push — see `docs/architecture.md`): the transaction stays there until the callback webhook resolves it, not resolved synchronously like the mock providers.

Migrations are managed with Alembic (`backend/app/db/migrations/`) — `0001` creates all tables above, `0002` makes `transactions.bio_id` nullable for the merchant-initiated path.
