"""drop tailored_resume_pdf_path

Revision ID: a1b2c3d4e5f6
Revises: e42ae4f71494
Create Date: 2026-09-26 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'e42ae4f71494'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('applications', 'tailored_resume_pdf_path')


def downgrade() -> None:
    op.add_column('applications', sa.Column('tailored_resume_pdf_path', sa.String(), nullable=True))
