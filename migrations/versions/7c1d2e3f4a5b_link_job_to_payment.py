"""link job posting to the payment that funds it

Revision ID: 7c1d2e3f4a5b
Revises: 402eaeacc7e9
Create Date: 2026-10-10 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7c1d2e3f4a5b'
down_revision = '402eaeacc7e9'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('jobposting', schema=None) as batch_op:
        batch_op.add_column(sa.Column('post_payid', sa.Integer(), nullable=True))
        batch_op.create_unique_constraint('uq_jobposting_post_payid', ['post_payid'])
        batch_op.create_foreign_key('fk_jobposting_post_payid', 'payment', ['post_payid'], ['pay_id'])

    with op.batch_alter_table('payment', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_payment_pay_ref', ['pay_ref'])


def downgrade():
    with op.batch_alter_table('payment', schema=None) as batch_op:
        batch_op.drop_constraint('uq_payment_pay_ref', type_='unique')

    with op.batch_alter_table('jobposting', schema=None) as batch_op:
        batch_op.drop_constraint('fk_jobposting_post_payid', type_='foreignkey')
        batch_op.drop_constraint('uq_jobposting_post_payid', type_='unique')
        batch_op.drop_column('post_payid')
