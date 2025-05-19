# alembic/versions/002_add_dispatchers_table.py
"""Add dispatchers table

Revision ID: 002
Revises: 001
Create Date: 2025-05-19 00:00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    # Create dispatchers table
    op.create_table(
        "dispatchers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("telegram_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Add dispatcher_id column to the loads table
    op.add_column("loads", sa.Column("dispatcher_id", sa.Integer(), nullable=True))

    # Add foreign key constraint
    op.create_foreign_key(
        "fk_loads_dispatcher_id",
        "loads",
        "dispatchers",
        ["dispatcher_id"],
        ["id"],
    )


def downgrade():
    # Remove foreign key constraint first
    op.drop_constraint("fk_loads_dispatcher_id", "loads", type_="foreignkey")

    # Remove dispatcher_id column from loads table
    op.drop_column("loads", "dispatcher_id")

    # Drop dispatchers table
    op.drop_table("dispatchers")
