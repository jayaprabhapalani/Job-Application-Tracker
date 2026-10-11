"""change embedding dimension to 384

Revision ID: d7e8f9a0b1c2
Revises: c1f3a2e9d847
Create Date: 2026-09-26 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision: str = 'd7e8f9a0b1c2'
down_revision: Union[str, Sequence[str], None] = 'c1f3a2e9d847'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'document_chunks', 'embedding',
        type_=Vector(384),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        'document_chunks', 'embedding',
        type_=Vector(1536),
        existing_nullable=True,
    )
