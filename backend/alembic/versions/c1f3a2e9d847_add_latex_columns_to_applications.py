"""add latex columns to applications

Revision ID: c1f3a2e9d847
Revises: b4deff804b0e
Create Date: 2026-09-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'c1f3a2e9d847'
down_revision: Union[str, Sequence[str], None] = 'b4deff804b0e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('applications', sa.Column('tailored_resume_latex', sa.Text(), nullable=True))
    op.add_column('applications', sa.Column('tailored_resume_pdf_path', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('applications', 'tailored_resume_pdf_path')
    op.drop_column('applications', 'tailored_resume_latex')
