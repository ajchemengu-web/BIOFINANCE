"""provider_catalog — the DB-backed source of truth for which financial
providers exist and can be connected, decoupled from the code-level
adapter registry (app/providers/registry.py). Adding a provider worldwide
becomes a catalog row instead of a code change; a real integration still
needs an adapter, but the catalog alone is enough to list and (via the
registry's generic mock fallback) demo-connect a provider before one
exists. See docs/architecture.md "Provider catalog".

Seeds the three providers already in use (MPESA, EQUITY, AIRTEL) as
Kenya/KES entries, and backfills a foreign key from
provider_connections.provider_code so the database itself rejects a
connection to a code the catalog doesn't know about — the same rule
POST /providers/connect already enforces at the API layer, now also
guaranteed at the data layer.

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-21

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

provider_catalog = sa.table(
    "provider_catalog",
    sa.column("code", sa.String),
    sa.column("display_name", sa.String),
    sa.column("country_code", sa.String),
    sa.column("currency", sa.String),
    sa.column("category", sa.String),
    sa.column("status", sa.String),
)


def upgrade() -> None:
    op.create_table(
        "provider_catalog",
        sa.Column("code", sa.String, primary_key=True),
        sa.Column("display_name", sa.String, nullable=False),
        sa.Column("country_code", sa.String, nullable=False),
        sa.Column("currency", sa.String, nullable=False),
        sa.Column("category", sa.String, nullable=False),
        sa.Column("status", sa.String, nullable=False, server_default="COMING_SOON"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.bulk_insert(
        provider_catalog,
        [
            {
                "code": "MPESA",
                "display_name": "M-PESA",
                "country_code": "KE",
                "currency": "KES",
                "category": "MOBILE_MONEY",
                "status": "AVAILABLE",
            },
            {
                "code": "EQUITY",
                "display_name": "Equity Bank",
                "country_code": "KE",
                "currency": "KES",
                "category": "BANK",
                "status": "AVAILABLE",
            },
            {
                "code": "AIRTEL",
                "display_name": "Airtel Money",
                "country_code": "KE",
                "currency": "KES",
                "category": "MOBILE_MONEY",
                "status": "AVAILABLE",
            },
        ],
    )

    op.create_foreign_key(
        "fk_provider_connections_provider_code_catalog",
        "provider_connections",
        "provider_catalog",
        ["provider_code"],
        ["code"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_provider_connections_provider_code_catalog", "provider_connections", type_="foreignkey"
    )
    op.drop_table("provider_catalog")
