"""merge heads 95ce0a157b2c and d60d2547506d

Revision ID: e67b72c65124
Revises: 95ce0a157b2c, d60d2547506d
Create Date: 2025-07-09 11:30:57.670039

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e67b72c65124'
down_revision = ('95ce0a157b2c', 'd60d2547506d')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
