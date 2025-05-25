"""add role to dispatchers

Revision ID: bf64362c324c
Revises: 7c7d2985bb21
Create Date: 2025-05-24 13:33:19.619127

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "bf64362c324c"
down_revision: Union[str, None] = "7c7d2985bb21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Add role column if it doesn't exist
    try:
        op.add_column("dispatchers", sa.Column("role", sa.String(255), nullable=True))
        print("Added role column to dispatchers table")
    except Exception as e:
        print(f"Role column might already exist: {e}")

    # Update existing records to have 'dispatcher' role by default
    try:
        connection = op.get_bind()
        connection.execute(
            "UPDATE dispatchers SET role = 'dispatcher' WHERE role IS NULL"
        )
        print("Updated existing records with dispatcher role")
    except Exception as e:
        print(f"Error updating existing records: {e}")


def downgrade():
    # Remove role column
    try:
        op.drop_column("dispatchers", "role")
    except Exception as e:
        print(f"Error dropping role column: {e}")
