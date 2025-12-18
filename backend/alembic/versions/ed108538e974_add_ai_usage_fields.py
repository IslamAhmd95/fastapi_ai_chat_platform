"""add ai usage fields

Revision ID: ed108538e974
Revises: 022f568cc330
Create Date: 2025-01-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'ed108538e974'
down_revision: Union[str, Sequence[str], None] = '022f568cc330'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add ai_requests_count column
    op.add_column('user', sa.Column('ai_requests_count', sa.Integer(), nullable=False, server_default='0'))
    
    # Add is_unlimited column
    op.add_column('user', sa.Column('is_unlimited', sa.Boolean(), nullable=False, server_default='false'))
    
    # Backfill ai_requests_count based on existing chat_history records
    # Use connection to execute raw SQL for compatibility
    connection = op.get_bind()
    connection.execute(text("""
        UPDATE "user" 
        SET ai_requests_count = (
            SELECT COUNT(*)
            FROM chat_history 
            WHERE chat_history.user_id = "user".id
        )
    """))
    connection.commit()


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('user', 'is_unlimited')
    op.drop_column('user', 'ai_requests_count')

