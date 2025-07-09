"""merge heads 1ff4e33de83b and ea8eae891d90

Revision ID: ac3035b2c955
Revises: 1ff4e33de83b, ea8eae891d90
Create Date: 2025-07-09 11:25:15.515489

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ac3035b2c955'
down_revision = ('1ff4e33de83b', 'ea8eae891d90')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
