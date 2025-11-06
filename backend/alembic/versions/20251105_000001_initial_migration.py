"""initial migration

Revision ID: 20251105_000001
Revises:
Create Date: 2025-11-05 00:00:01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql, mysql

# revision identifiers, used by Alembic.
revision: str = '20251105_000001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


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


def get_inet_column():
    """Get INET column type based on database dialect"""
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        return postgresql.INET()
    else:
        # MySQL uses VARCHAR(45) for IP addresses (IPv6 compatible)
        return sa.String(45)


def get_json_column_with_default():
    """Get JSON column with default value (PostgreSQL only supports defaults)"""
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        return get_json_column(), '[]'
    else:
        # MySQL doesn't support defaults for JSON columns
        return get_json_column(), None


def upgrade() -> None:
    """创建所有表"""

    # 创建用户表
    op.create_table(
        'users',
        sa.Column('id', get_uuid_column(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=True),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='user'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 创建服务器表
    json_col, json_default = get_json_column_with_default()
    op.create_table(
        'servers',
        sa.Column('id', get_uuid_column(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('host', sa.String(length=255), nullable=False),
        sa.Column('port', sa.Integer(), nullable=False, server_default='22'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner_id', get_uuid_column(), nullable=False),
        sa.Column('ssh_username', sa.String(length=100), nullable=True),
        sa.Column('ssh_password_encrypted', sa.Text(), nullable=True),
        sa.Column('ssh_key_encrypted', sa.Text(), nullable=True),
        sa.Column('tags', json_col, nullable=True, server_default=json_default),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='unknown'),
        sa.Column('last_checked_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_servers_name'), 'servers', ['name'], unique=False)
    op.create_index(op.f('ix_servers_owner_id'), 'servers', ['owner_id'], unique=False)
    op.create_index(op.f('ix_servers_status'), 'servers', ['status'], unique=False)

    # 创建服务器监控数据表
    op.create_table(
        'server_metrics',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('server_id', get_uuid_column(), nullable=False),
        sa.Column('cpu_usage_percent', sa.Float(), nullable=True),
        sa.Column('cpu_cores', sa.Integer(), nullable=True),
        sa.Column('memory_total_mb', sa.BigInteger(), nullable=True),
        sa.Column('memory_used_mb', sa.BigInteger(), nullable=True),
        sa.Column('memory_usage_percent', sa.Float(), nullable=True),
        sa.Column('disk_total_gb', sa.BigInteger(), nullable=True),
        sa.Column('disk_used_gb', sa.BigInteger(), nullable=True),
        sa.Column('disk_usage_percent', sa.Float(), nullable=True),
        sa.Column('network_bytes_sent', sa.BigInteger(), nullable=True),
        sa.Column('network_bytes_recv', sa.BigInteger(), nullable=True),
        sa.Column('uptime_seconds', sa.BigInteger(), nullable=True),
        sa.Column('load_average', get_json_column(), nullable=True),
        sa.Column('collected_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['server_id'], ['servers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_server_metrics_server_id'), 'server_metrics', ['server_id'], unique=False)
    op.create_index(op.f('ix_server_metrics_collected_at'), 'server_metrics', ['collected_at'], unique=False)

    # 创建用户服务器权限表
    op.create_table(
        'user_server_permissions',
        sa.Column('id', get_uuid_column(), nullable=False),
        sa.Column('user_id', get_uuid_column(), nullable=False),
        sa.Column('server_id', get_uuid_column(), nullable=False),
        sa.Column('permission', sa.String(length=20), nullable=False),
        sa.Column('granted_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('granted_by', get_uuid_column(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['server_id'], ['servers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['granted_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'server_id', name='uq_user_server')
    )
    op.create_index(op.f('ix_user_server_permissions_user_id'), 'user_server_permissions', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_server_permissions_server_id'), 'user_server_permissions', ['server_id'], unique=False)

    # 创建聊天历史表
    op.create_table(
        'chat_history',
        sa.Column('id', get_uuid_column(), nullable=False),
        sa.Column('user_id', get_uuid_column(), nullable=False),
        sa.Column('server_id', get_uuid_column(), nullable=True),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', get_json_column(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['server_id'], ['servers.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_history_user_id'), 'chat_history', ['user_id'], unique=False)
    op.create_index(op.f('ix_chat_history_server_id'), 'chat_history', ['server_id'], unique=False)
    op.create_index(op.f('ix_chat_history_created_at'), 'chat_history', ['created_at'], unique=False)

    # 创建审计日志表
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', get_uuid_column(), nullable=True),
        sa.Column('server_id', get_uuid_column(), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=True),
        sa.Column('details', get_json_column(), nullable=True),
        sa.Column('ip_address', get_inet_column(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['server_id'], ['servers.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_server_id'), 'audit_logs', ['server_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_resource_type'), 'audit_logs', ['resource_type'], unique=False)
    op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'], unique=False)


def downgrade() -> None:
    """删除所有表"""
    op.drop_table('audit_logs')
    op.drop_table('chat_history')
    op.drop_table('user_server_permissions')
    op.drop_table('server_metrics')
    op.drop_table('servers')
    op.drop_table('users')
