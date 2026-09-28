"""add analytics fields to models

Revision ID: c1f2e3d4a5b6
Revises: ba4fdcf50e5d
Create Date: 2026-09-28 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c1f2e3d4a5b6'
down_revision = 'ba4fdcf50e5d'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('order', schema=None) as batch_op:
        batch_op.add_column(sa.Column('confirmed_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('cancelled_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('delivered_at', sa.DateTime(), nullable=True))

    with op.batch_alter_table('transaction', schema=None) as batch_op:
        batch_op.add_column(sa.Column('payment_method', sa.String(length=50), nullable=True))

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_active_at', sa.DateTime(), nullable=True))

    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=True))

def downgrade():
    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.drop_column('created_at')

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('last_active_at')

    with op.batch_alter_table('transaction', schema=None) as batch_op:
        batch_op.drop_column('payment_method')

    with op.batch_alter_table('order', schema=None) as batch_op:
        batch_op.drop_column('delivered_at')
        batch_op.drop_column('cancelled_at')
        batch_op.drop_column('confirmed_at')
