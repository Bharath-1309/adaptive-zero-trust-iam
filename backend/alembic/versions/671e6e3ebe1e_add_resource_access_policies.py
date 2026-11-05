"""add resource access policies

Revision ID: 671e6e3ebe1e
Revises: 9b975506b7ce
Create Date: 2026-11-04 17:01:22.850991

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "671e6e3ebe1e"
down_revision: Union[str, Sequence[str], None] = "9b975506b7ce"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the new access policy column.
    op.add_column(
        "resource_definitions",
        sa.Column(
            "access_policy",
            sa.String(length=30),
            server_default="REMOTE_ALLOWED",
            nullable=False,
        ),
    )

    # Preserve existing office-only resource configurations.
    op.execute(
        """
        UPDATE resource_definitions
        SET access_policy = 'OFFICE_ONLY'
        WHERE requires_office_location = TRUE
        """
    )

    # Restrict access policies to supported values.
    op.create_check_constraint(
        "ck_resource_definitions_access_policy",
        "resource_definitions",
        """
        access_policy IN (
            'OFFICE_ONLY',
            'REMOTE_ALLOWED',
            'TRAVEL_ALLOWED',
            'VPN_REQUIRED'
        )
        """,
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_resource_definitions_access_policy",
        "resource_definitions",
        type_="check",
    )

    op.drop_column(
        "resource_definitions",
        "access_policy",
    )