"""empty message

Revision ID: c37df0e0d606
Revises: 46d3e0c8a806
Create Date: 2025-01-10 05:19:35.370950

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'c37df0e0d606'
down_revision = '46d3e0c8a806'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('employer', schema=None) as batch_op:
        batch_op.add_column(sa.Column('employer_status', sa.String(length=10), nullable=True))

    with op.batch_alter_table('worker', schema=None) as batch_op:
        batch_op.alter_column('worker_status',
               existing_type=mysql.ENUM('0', '1'),
               type_=sa.String(length=10),
               nullable=True,
               existing_server_default=sa.text("'0'"))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('worker', schema=None) as batch_op:
        batch_op.alter_column('worker_status',
               existing_type=sa.String(length=10),
               type_=mysql.ENUM('0', '1'),
               nullable=False,
               existing_server_default=sa.text("'0'"))

    with op.batch_alter_table('employer', schema=None) as batch_op:
        batch_op.drop_column('employer_status')

    # ### end Alembic commands ###
