"""Add CANCELLED_BY_ADMIN to AuctionStatus

Revision ID: 52bb9fb82d4f
Revises: 
Create Date: 2025-07-14 01:01:45.711660

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '52bb9fb82d4f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    # This will remove the value from the enum. This is not a standard feature of enums in all databases,
    # so this might fail. It's generally better to not remove enum values.
    op.execute("ALTER TYPE auctionstatus RENAME TO auctionstatus_old")
    op.execute("CREATE TYPE auctionstatus AS ENUM('PENDING_APPROVAL', 'ACTIVE', 'CLOSED', 'CANCELLED')")
    op.execute((
        "ALTER TABLE auction_items ALTER COLUMN status TYPE auctionstatus USING "
        "status::text::auctionstatus"
    ))
    op.execute("DROP TYPE auctionstatus_old")
