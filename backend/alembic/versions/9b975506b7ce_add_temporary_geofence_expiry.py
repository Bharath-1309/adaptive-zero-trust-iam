"""add temporary geofence expiry

Revision ID: 9b975506b7ce
Revises: daf8520afc68
Create Date: 2026-11-04 16:43:18.433610

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9b975506b7ce"
down_revision: Union[str, Sequence[str], None] = "daf8520afc68"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "office_geofences",
        sa.Column(
            "location_type",
            sa.String(length=20),
            server_default="PERMANENT",
            nullable=False,
        ),
    )

    op.add_column(
        "office_geofences",
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.create_check_constraint(
        "ck_office_geofences_location_type",
        "office_geofences",
        "location_type IN ('PERMANENT', 'TEMPORARY')",
    )

    op.create_check_constraint(
        "ck_office_geofences_expiry",
        "office_geofences",
        """
        (location_type = 'PERMANENT' AND expires_at IS NULL)
        OR
        (location_type = 'TEMPORARY' AND expires_at IS NOT NULL)
        """,
    )

    op.create_index(
        "ix_office_geofences_active_expiry",
        "office_geofences",
        ["is_active", "expires_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_office_geofences_active_expiry",
        table_name="office_geofences",
    )

    op.drop_constraint(
        "ck_office_geofences_expiry",
        "office_geofences",
        type_="check",
    )

    op.drop_constraint(
        "ck_office_geofences_location_type",
        "office_geofences",
        type_="check",
    )

    op.drop_column("office_geofences", "expires_at")
    op.drop_column("office_geofences", "location_type")