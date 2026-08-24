# BioFinance — Security Model

## Principles

- **Authenticate locally; don't collect raw biometric templates unnecessarily.** The Flutter app uses the device's native secure biometric system (Android Keystore / iOS Secure Enclave). Raw fingerprint/face data never leaves the device and is never sent to or stored by the backend.
- Kenya's Data Protection Act treats biometric data (including fingerprinting) as personal data — biometric privacy is an architectural requirement, not an optional feature.
- BioFinance never stores a fingerprint "as" the wallet. The chain is always: biometric → local device authentication success → BioID → routing decision → provider authorization. See `docs/architecture.md`.

## Authentication & sessions

- Password hashing: bcrypt (`passlib`).
- Session tokens: short-lived JWT access token + longer-lived refresh token. Access tokens are not stored server-side; refresh tokens can be revoked.
- Every sensitive operation is authorized server-side — the Flutter client is never trusted to self-report "biometric succeeded" without a corresponding server-verifiable session state.

## Secrets

- Daraja credentials (`DARAJA_CONSUMER_KEY`, `DARAJA_CONSUMER_SECRET`, `DARAJA_SHORTCODE`, `DARAJA_PASSKEY`, `DARAJA_ENVIRONMENT`) live only in backend environment configuration (`.env`, or Render's environment variable dashboard in production). Never in Flutter source, never committed to git, never stored in PostgreSQL.
- `.env` is gitignored; `.env.example` documents the required keys with placeholder values only.

## Device binding

- The `devices` table associates authorized devices with a user (`docs/database-schema.md`). Future hardening: hardware-backed key pair per device, cryptographic signature on transaction authorization instead of a bare "success" flag.

## Merchant-side integrity

- Only devices registered in `merchant_devices` may initiate production payment requests (§33 of the source PRD) — an unregistered device cannot pose as a merchant terminal.

## Fraud protection (MVP scope)

- Transaction limits, basic rate limiting, device verification, mandatory idempotency keys on payment creation, suspicious-transaction logging, repeated-biometric-failure detection.
- Explicitly deferred: behavioral anomaly detection, ML-based risk scoring, device fingerprinting beyond the basic `device_identifier`, merchant risk scoring.

## Audit logging

Append-only `audit_events` table. Minimum event set to implement as features land:

```
LOGIN_SUCCESS          LOGIN_FAILED
BIOMETRIC_SUCCESS      BIOMETRIC_FAILED
DEVICE_REGISTERED      DEVICE_REMOVED
PROVIDER_CONNECTED     PROVIDER_DISCONNECTED
ROUTING_CHANGED
PAYMENT_CREATED        PAYMENT_AUTHORIZED
PAYMENT_COMPLETED      PAYMENT_FAILED
BIOID_LOCKED
```

`metadata` (jsonb) on each event must never contain secrets or raw biometric data — reference IDs only.

## Regulatory posture

The prototype intentionally avoids positioning BioFinance as custodian of customer funds — no customer deposits, no production financial balances, sandbox/mock providers only. The National Payment System Act defines payment-service-provider activity broadly; before any deployment that touches real customer funds, the exact regulatory classification needs Kenyan legal/regulatory advice. This is a hard boundary for MVP scope, not a formality — see `docs/roadmap.md` "Not in MVP."
