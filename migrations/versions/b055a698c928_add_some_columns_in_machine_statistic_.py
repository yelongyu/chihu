"""add some columns in machine_statistic table

Revision ID: b055a698c928
Revises: e8b3861bce6b
Create Date: 2016-07-28 10:52:15.203727

"""

# revision identifiers, used by Alembic.
revision = 'b055a698c928'
down_revision = 'e8b3861bce6b'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('machine_statistic', sa.Column('company', sa.String(length=64), nullable=True))
    op.add_column('machine_statistic', sa.Column('openid', sa.String(length=64), nullable=True))
    op.add_column('machine_statistic', sa.Column('userpasswd', sa.String(length=64), nullable=True))
    op.add_column('machine_statistic', sa.Column('webkey', sa.String(length=64), nullable=True))
    op.add_column('machine_statistic', sa.Column('wlanpasswd', sa.String(length=64), nullable=True))
    op.add_column('machine_statistic', sa.Column('wlanssid', sa.String(length=64), nullable=True))
    op.alter_column('statistic_visitor', 'referred',
               existing_type=mysql.VARCHAR(collation=u'utf8_unicode_ci', length=128),
               nullable=True,
               existing_server_default=sa.text(u"''"))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('statistic_visitor', 'referred',
               existing_type=mysql.VARCHAR(collation=u'utf8_unicode_ci', length=128),
               nullable=False,
               existing_server_default=sa.text(u"''"))
    op.drop_column('machine_statistic', 'wlanssid')
    op.drop_column('machine_statistic', 'wlanpasswd')
    op.drop_column('machine_statistic', 'webkey')
    op.drop_column('machine_statistic', 'userpasswd')
    op.drop_column('machine_statistic', 'openid')
    op.drop_column('machine_statistic', 'company')
    ### end Alembic commands ###