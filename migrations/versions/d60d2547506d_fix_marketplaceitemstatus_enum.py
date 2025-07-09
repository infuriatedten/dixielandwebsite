"""fix marketplaceitemstatus enum

Revision ID: d60d2547506d
Revises: ac3035b2c955
Create Date: 2025-07-09 00:00:00.000000

"""
from alembic import op

revision = 'd60d2547506d'
down_revision = 'ac3035b2c955'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE TYPE marketplaceitemstatus_new AS ENUM ('AVAILABLE', 'SOLD_PENDING', 'SOLD_OUT', 'CANCELLED')")
    op.execute("""
        ALTER TABLE marketplace_listings
        ALTER COLUMN status TYPE marketplaceitemstatus_new
        USING status::text::marketplaceitemstatus_new
    """)
    op.execute("DROP TYPE marketplaceitemstatus")
    op.execute("ALTER TYPE marketplaceitemstatus_new RENAME TO marketplaceitemstatus")


def downgrade():
    op.execute("CREATE TYPE marketplaceitemstatus_old AS ENUM ('AVAILABLE', 'SOLD_PENDIN..', 'SOLD_OUT', 'CANCELLED')")
    op.execute("""
        ALTER TABLE marketplace_listings
        ALTER COLUMN status TYPE marketplaceitemstatus_old
        USING status::text::marketplaceitemstatus_old
    """)
    op.execute("DROP TYPE marketplaceitemstatus")
    op.execute("ALTER TYPE marketplaceitemstatus_old RENAME TO marketplaceitemstatus")
