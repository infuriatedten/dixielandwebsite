"""Manual update of ConversationStatus enum

Revision ID: 20fdc741e25f
Revises: 52bb9fb82d4f
Create Date: 2025-07-14 13:11:22.535087

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20fdc741e25f'
down_revision = '52bb9fb82d4f'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE conversations ALTER COLUMN status TYPE VARCHAR(255)")
    op.execute("DROP TYPE conversationstatus")
    op.execute("CREATE TYPE conversationstatus AS ENUM ('OPEN', 'CLOSED_BY_USER', 'CLOSED_BY_ADMIN')")
    op.execute("ALTER TABLE conversations ALTER COLUMN status TYPE conversationstatus USING status::conversationstatus")


def downgrade():
    op.execute("ALTER TABLE conversations ALTER COLUMN status TYPE VARCHAR(255)")
    op.execute("DROP TYPE conversationstatus")
    op.execute("CREATE TYPE conversationstatus AS ENUM ('open', 'closed')")
    op.execute("ALTER TABLE conversations ALTER COLUMN status TYPE conversationstatus USING status::conversationstatus")
