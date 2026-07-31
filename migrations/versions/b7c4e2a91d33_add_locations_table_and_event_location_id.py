"""add_locations_table_and_event_location_id

Revision ID: b7c4e2a91d33
Revises: 4e9300586112
Create Date: 2026-07-31 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from migrations.idempotency import column_exists, fk_exists, index_exists, table_exists

revision: str = "b7c4e2a91d33"
down_revision: Union[str, None] = "4e9300586112"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if not table_exists("locations"):
        op.create_table(
            "locations",
            sa.Column("id", sa.UUID(as_uuid=True), nullable=False),
            sa.Column("group_id", sa.UUID(as_uuid=True), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            # NUMERIC(9, 6) for both: 3 digits before the decimal keeps out-of-range
            # values inside the column type so the CHECK constraint below is the one
            # that rejects them, instead of a numeric overflow error.
            sa.Column("latitude", sa.Numeric(precision=9, scale=6), nullable=True),
            sa.Column("longitude", sa.Numeric(precision=9, scale=6), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_by", sa.String(length=255), nullable=False),
            sa.ForeignKeyConstraint(
                ["group_id"], ["author_groups.id"], ondelete="RESTRICT"
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.CheckConstraint(
                "latitude IS NULL OR (latitude >= -90 AND latitude <= 90)",
                name="ck_locations_latitude_range",
            ),
            sa.CheckConstraint(
                "longitude IS NULL OR (longitude >= -180 AND longitude <= 180)",
                name="ck_locations_longitude_range",
            ),
            sa.CheckConstraint(
                "(latitude IS NULL AND longitude IS NULL) "
                "OR (latitude IS NOT NULL AND longitude IS NOT NULL)",
                name="ck_locations_coordinates_paired",
            ),
        )

    if not index_exists("locations", "idx_locations_group_id"):
        op.create_index("idx_locations_group_id", "locations", ["group_id"])

    # Not unique: a group may legitimately have two places with the same name
    # (e.g. "Main Hall" at different centres).
    if not index_exists("locations", "idx_locations_group_id_name"):
        op.create_index(
            "idx_locations_group_id_name", "locations", ["group_id", "name"]
        )

    if not column_exists("events", "location_id"):
        op.add_column(
            "events",
            sa.Column("location_id", sa.UUID(as_uuid=True), nullable=True),
        )

    if not fk_exists("events", "fk_events_location_id"):
        op.create_foreign_key(
            "fk_events_location_id",
            "events",
            "locations",
            ["location_id"],
            ["id"],
            ondelete="RESTRICT",
        )

    if not index_exists("events", "idx_events_location_id"):
        op.create_index("idx_events_location_id", "events", ["location_id"])


def downgrade() -> None:
    op.drop_index("idx_events_location_id", table_name="events")
    op.drop_constraint("fk_events_location_id", "events", type_="foreignkey")
    op.drop_column("events", "location_id")

    op.drop_index("idx_locations_group_id_name", table_name="locations")
    op.drop_index("idx_locations_group_id", table_name="locations")
    op.drop_table("locations")
