"""Remove Twilio fields, rename provider_message_sid to provider_message_id, add last_inbound_whatsapp_at

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
Create Date: 2026-09-28 13:57:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e3f4a5b6c7d8'
down_revision = 'd2e3f4a5b6c7'
branch_labels = None
depends_on = None

def upgrade():
    # User model changes
    with op.batch_alter_table('user', schema=None) as batch_op:
        try:
            batch_op.drop_column('whatsapp_joined')
        except Exception:
            pass
        try:
            batch_op.add_column(sa.Column('last_inbound_whatsapp_at', sa.DateTime(), nullable=True))
        except Exception:
            pass

    # NotificationLog model changes
    with op.batch_alter_table('notification_log', schema=None) as batch_op:
        try:
            batch_op.alter_column('provider_message_sid', new_column_name='provider_message_id', existing_type=sa.String(length=255))
        except Exception:
            batch_op.add_column(sa.Column('provider_message_id', sa.String(length=255), nullable=True))

def downgrade():
    with op.batch_alter_table('notification_log', schema=None) as batch_op:
        try:
            batch_op.alter_column('provider_message_id', new_column_name='provider_message_sid', existing_type=sa.String(length=255))
        except Exception:
            pass

    with op.batch_alter_table('user', schema=None) as batch_op:
        try:
            batch_op.drop_column('last_inbound_whatsapp_at')
        except Exception:
            pass
        try:
            batch_op.add_column(sa.Column('whatsapp_joined', sa.Boolean(), server_default='0', nullable=False))
        except Exception:
            pass
