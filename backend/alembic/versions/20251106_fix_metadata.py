"""Fix ChatHistory metadata column name

Revision ID: 20251106_fix_metadata
Revises: 20251105_000001
Create Date: 2025-11-06

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251106_fix_metadata'
down_revision = '20251105_000001'
branch_labels = None
depends_on = None


def get_uuid_column():
    """Get UUID column type based on database dialect"""
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        return postgresql.UUID(as_uuid=True)
    else:
        # MySQL and others use CHAR(36)
        return sa.CHAR(36)


def get_json_column():
    """Get JSON column type based on database dialect"""
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        return postgresql.JSONB(astext_type=sa.Text())
    else:
        # MySQL uses JSON
        return sa.JSON()


def upgrade() -> None:
    # Rename metadata column to extra_data
    op.alter_column('chat_history', 'metadata',
                    new_column_name='extra_data',
                    existing_type=get_json_column(),
                    existing_nullable=True)

    # Add conversation_id column
    op.add_column('chat_history',
                  sa.Column('conversation_id',
                           get_uuid_column(),
                           nullable=True))

    # Add index for conversation_id
    op.create_index('ix_chat_history_conversation_id',
                   'chat_history',
                   ['conversation_id'],
                   unique=False)


def downgrade() -> None:
    # Remove index
    op.drop_index('ix_chat_history_conversation_id', table_name='chat_history')

    # Remove conversation_id column
    op.drop_column('chat_history', 'conversation_id')

    # Rename extra_data back to metadata
    op.alter_column('chat_history', 'extra_data',
                    new_column_name='metadata',
                    existing_type=get_json_column(),
                    existing_nullable=True)
