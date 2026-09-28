"""Add WhatsApp notification models and user preferences

Revision ID: d2e3f4a5b6c7
Revises: c1f2e3d4a5b6
Create Date: 2026-09-28 12:08:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd2e3f4a5b6c7'
down_revision = 'c1f2e3d4a5b6'
branch_labels = None
depends_on = None

def upgrade():
    # User notification columns
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('phone', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('whatsapp_opt_in', sa.Boolean(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('whatsapp_joined', sa.Boolean(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('notification_language', sa.String(length=10), server_default='en', nullable=False))

    # NotificationLog table
    op.create_table('notification_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('channel', sa.String(length=50), nullable=True, server_default='whatsapp'),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='queued'),
        sa.Column('provider_message_sid', sa.String(length=255), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Notification table
    op.create_table('notification',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=True, server_default='info'),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('notification')
    op.drop_table('notification_log')
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('notification_language')
        batch_op.drop_column('whatsapp_joined')
        batch_op.drop_column('whatsapp_opt_in')
        batch_op.drop_column('phone')
