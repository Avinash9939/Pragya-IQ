"""add_featured_to_datasetstatus

Revision ID: 52d8400ac986
Revises: 83ecd605f138
Create Date: 2026-07-12 14:03:58.452395

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '52d8400ac986'
down_revision: Union[str, Sequence[str], None] = '83ecd605f138'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # PostgreSQL supports ALTER TYPE ... ADD VALUE since V9.1+, and IF NOT EXISTS since V16+
        op.execute("ALTER TYPE datasetstatus ADD VALUE IF NOT EXISTS 'FEATURED'")


def downgrade() -> None:
    """Downgrade schema."""
    # Postgres doesn't easily support dropping an enum value without dropping/recreating the enum type.
    # We leave this as a pass because removing 'FEATURED' from the Type registry is not critical.
    pass

