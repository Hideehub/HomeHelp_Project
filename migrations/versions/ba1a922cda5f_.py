"""empty message

Revision ID: ba1a922cda5f
Revises: 78ad7befca9b
Create Date: 2025-02-20 05:37:24.452620

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ba1a922cda5f'
down_revision = '78ad7befca9b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('worker_recipient',
    sa.Column('recp_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('recp_workerid', sa.Integer(), nullable=False),
    sa.Column('recp_code', sa.String(length=100), nullable=False),
    sa.Column('recp_createdat', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['recp_workerid'], ['worker.worker_id'], ),
    sa.PrimaryKeyConstraint('recp_id'),
    sa.UniqueConstraint('recp_workerid')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('worker_recipient')
    # ### end Alembic commands ###
