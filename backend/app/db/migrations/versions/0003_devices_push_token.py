"""devices.push_token + platform (BioFinance ID push pairing)

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-21

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("devices", sa.Column("push_token", sa.String, nullable=True))
    op.add_column("devices", sa.Column("platform", sa.String, nullable=True))


def downgrade() -> None:
    op.drop_column("devices", "platform")
    op.drop_column("devices", "push_token")
