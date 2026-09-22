"""merchants.email + password_hash — real merchant authentication
(docs/roadmap.md Phase 5, docs/security-model.md "Merchant-side integrity").

Nullable, not backfilled: a merchant row created before this migration
(via the old unauthenticated POST /merchants) has no credential and simply
can't log in — that's expected, not a data-loss concern, since nothing
depended on merchants having a login before now and this app has never
been deployed anywhere real (README).

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-22

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("merchants", sa.Column("email", sa.String, nullable=True))
    op.add_column("merchants", sa.Column("password_hash", sa.String, nullable=True))
    op.create_unique_constraint("uq_merchants_email", "merchants", ["email"])


def downgrade() -> None:
    op.drop_constraint("uq_merchants_email", "merchants", type_="unique")
    op.drop_column("merchants", "password_hash")
    op.drop_column("merchants", "email")
