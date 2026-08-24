"""transactions.bio_id nullable (merchant-initiated payment requests)

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("transactions", "bio_id", existing_type=sa.dialects.postgresql.UUID(as_uuid=True), nullable=True)


def downgrade() -> None:
    op.alter_column("transactions", "bio_id", existing_type=sa.dialects.postgresql.UUID(as_uuid=True), nullable=False)
