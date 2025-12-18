"""merge multiple heads

Revision ID: 934fe898031f
Revises: 0bd32e7f333a, ed108538e974
Create Date: 2025-12-18 08:50:19.558907

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '934fe898031f'
down_revision: Union[str, Sequence[str], None] = ('0bd32e7f333a', 'ed108538e974')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
