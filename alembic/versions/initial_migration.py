"""Initial migration - Create all tables

Revision ID: 001_initial
Revises:
Create Date: 2025-05-24

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create facilities table
    op.create_table(
        "facilities",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("full_address", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create companies table
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("usdot", sa.Integer(), nullable=True),
        sa.Column("carrier_identifier", sa.String(length=255), nullable=True),
        sa.Column("mc", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create telegram_chats table
    op.create_table(
        "telegram_chats",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("group_name", sa.String(length=255), nullable=True),
        sa.Column("chat_token", sa.Integer(), nullable=True),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create dispatchers table
    op.create_table(
        "dispatchers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("telegram_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create drivers table
    op.create_table(
        "drivers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("chat_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["chat_id"],
            ["telegram_chats.id"],
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create loads table
    op.create_table(
        "loads",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("trip_id", sa.String(length=255), nullable=True),
        sa.Column("pickup_facility_id", sa.Integer(), nullable=True),
        sa.Column("dropoff_facility_id", sa.Integer(), nullable=True),
        sa.Column("pickup_facility_name", sa.String(length=255), nullable=True),
        sa.Column("dropoff_facility_name", sa.String(length=255), nullable=True),
        sa.Column("pickup_address", sa.String(length=255), nullable=True),
        sa.Column("dropoff_address", sa.String(length=255), nullable=True),
        sa.Column("pickup_full_address", sa.Text(), nullable=True),
        sa.Column("dropoff_full_address", sa.Text(), nullable=True),
        sa.Column("start_time", sa.DateTime(), nullable=False),
        sa.Column("end_time", sa.DateTime(), nullable=False),
        sa.Column("start_time_str", sa.String(length=50), nullable=True),
        sa.Column("end_time_str", sa.String(length=50), nullable=True),
        sa.Column("rate", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("rate_per_mile", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("distance", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("driver_id", sa.Integer(), nullable=True),
        sa.Column("assigned_driver", sa.String(length=255), nullable=True),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("dispatcher_id", sa.Integer(), nullable=True),
        sa.Column("is_team_load", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
        ),
        sa.ForeignKeyConstraint(
            ["dispatcher_id"],
            ["dispatchers.id"],
        ),
        sa.ForeignKeyConstraint(
            ["dropoff_facility_id"],
            ["facilities.id"],
        ),
        sa.ForeignKeyConstraint(
            ["driver_id"],
            ["drivers.id"],
        ),
        sa.ForeignKeyConstraint(
            ["pickup_facility_id"],
            ["facilities.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("trip_id"),
    )

    # Create legs table
    op.create_table(
        "legs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("leg_id", sa.String(length=255), nullable=True),
        sa.Column("load_id", sa.Integer(), nullable=True),
        sa.Column("pickup_facility_id", sa.Integer(), nullable=True),
        sa.Column("dropoff_facility_id", sa.Integer(), nullable=True),
        sa.Column("pickup_facility_name", sa.String(length=255), nullable=True),
        sa.Column("dropoff_facility_name", sa.String(length=255), nullable=True),
        sa.Column("pickup_address", sa.String(length=255), nullable=True),
        sa.Column("dropoff_address", sa.String(length=255), nullable=True),
        sa.Column("pickup_full_address", sa.Text(), nullable=True),
        sa.Column("dropoff_full_address", sa.Text(), nullable=True),
        sa.Column("pickup_time", sa.DateTime(), nullable=False),
        sa.Column("dropoff_time", sa.DateTime(), nullable=False),
        sa.Column("pickup_time_str", sa.String(length=50), nullable=True),
        sa.Column("dropoff_time_str", sa.String(length=50), nullable=True),
        sa.Column("fuel_sur_charge", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("distance", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("assigned_driver", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(
            ["dropoff_facility_id"],
            ["facilities.id"],
        ),
        sa.ForeignKeyConstraint(
            ["load_id"],
            ["loads.id"],
        ),
        sa.ForeignKeyConstraint(
            ["pickup_facility_id"],
            ["facilities.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("leg_id"),
    )

    # Create indexes for better performance
    op.create_index("ix_loads_trip_id", "loads", ["trip_id"])
    op.create_index("ix_loads_company_id", "loads", ["company_id"])
    op.create_index("ix_loads_driver_id", "loads", ["driver_id"])
    op.create_index("ix_loads_start_time", "loads", ["start_time"])
    op.create_index("ix_loads_end_time", "loads", ["end_time"])
    op.create_index("ix_loads_pickup_facility_id", "loads", ["pickup_facility_id"])
    op.create_index("ix_loads_dropoff_facility_id", "loads", ["dropoff_facility_id"])

    op.create_index("ix_legs_leg_id", "legs", ["leg_id"])
    op.create_index("ix_legs_load_id", "legs", ["load_id"])
    op.create_index("ix_legs_pickup_time", "legs", ["pickup_time"])
    op.create_index("ix_legs_dropoff_time", "legs", ["dropoff_time"])

    op.create_index("ix_facilities_name", "facilities", ["name"])
    op.create_index("ix_companies_name", "companies", ["name"])
    op.create_index("ix_companies_usdot", "companies", ["usdot"])
    op.create_index("ix_drivers_name", "drivers", ["name"])
    op.create_index("ix_drivers_company_id", "drivers", ["company_id"])


def downgrade():
    # Drop indexes first
    op.drop_index("ix_drivers_company_id", table_name="drivers")
    op.drop_index("ix_drivers_name", table_name="drivers")
    op.drop_index("ix_companies_usdot", table_name="companies")
    op.drop_index("ix_companies_name", table_name="companies")
    op.drop_index("ix_facilities_name", table_name="facilities")

    op.drop_index("ix_legs_dropoff_time", table_name="legs")
    op.drop_index("ix_legs_pickup_time", table_name="legs")
    op.drop_index("ix_legs_load_id", table_name="legs")
    op.drop_index("ix_legs_leg_id", table_name="legs")

    op.drop_index("ix_loads_dropoff_facility_id", table_name="loads")
    op.drop_index("ix_loads_pickup_facility_id", table_name="loads")
    op.drop_index("ix_loads_end_time", table_name="loads")
    op.drop_index("ix_loads_start_time", table_name="loads")
    op.drop_index("ix_loads_driver_id", table_name="loads")
    op.drop_index("ix_loads_company_id", table_name="loads")
    op.drop_index("ix_loads_trip_id", table_name="loads")

    # Drop tables in reverse order of creation (due to foreign key constraints)
    op.drop_table("legs")
    op.drop_table("loads")
    op.drop_table("drivers")
    op.drop_table("dispatchers")
    op.drop_table("telegram_chats")
    op.drop_table("companies")
    op.drop_table("facilities")
