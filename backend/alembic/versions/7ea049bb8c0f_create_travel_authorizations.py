"""create travel authorizations

Revision ID: 7ea049bb8c0f
Revises: 671e6e3ebe1e
Create Date: 2026-11-04 17:40:32.363274

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7ea049bb8c0f"
down_revision: Union[str, Sequence[str], None] = "671e6e3ebe1e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table(
        "travel_authorizations",

        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("destination", sa.String(200), nullable=False),
        sa.Column("justification", sa.Text(), nullable=False),
        sa.Column(
            "starts_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(20),
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column("approved_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("approval_reason", sa.Text(), nullable=True),
        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revocation_reason", sa.Text(), nullable=True),

        sa.CheckConstraint(
            "status IN ('PENDING', 'APPROVED', 'DENIED', 'REVOKED', 'EXPIRED')",
            name="ck_travel_authorizations_status",
        ),

        sa.CheckConstraint(
            "expires_at > starts_at",
            name="ck_travel_authorizations_expiry",
        ),

        sa.CheckConstraint(
            "length(trim(destination)) > 0",
            name="ck_travel_authorizations_destination",
        ),

        sa.CheckConstraint(
            "length(trim(justification)) > 0",
            name="ck_travel_authorizations_justification",
        ),

        sa.CheckConstraint(
            "approved_by_user_id IS NULL OR approved_by_user_id != user_id",
            name="ck_travel_authorizations_no_self_approval",
        ),

        sa.CheckConstraint(
            """
            (
                status IN ('APPROVED', 'DENIED')
                AND approved_by_user_id IS NOT NULL
                AND reviewed_at IS NOT NULL
            )
            OR
            (
                status NOT IN ('APPROVED', 'DENIED')
            )
            """,
            name="ck_travel_authorizations_review_tracking",
        ),

        sa.CheckConstraint(
            """
            (
                status = 'REVOKED'
                AND revoked_at IS NOT NULL
                AND revocation_reason IS NOT NULL
                AND length(trim(revocation_reason)) > 0
            )
            OR
            (
                status != 'REVOKED'
                AND revoked_at IS NULL
                AND revocation_reason IS NULL
            )
            """,
            name="ck_travel_authorizations_revocation",
        ),

        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),

        sa.ForeignKeyConstraint(
            ["approved_by_user_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),

        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_travel_authorizations_user_id",
        "travel_authorizations",
        ["user_id"],
        unique=False,
    )

    op.create_index(
        "ix_travel_authorizations_status",
        "travel_authorizations",
        ["status"],
        unique=False,
    )

    op.create_index(
        "ix_travel_authorizations_expires_at",
        "travel_authorizations",
        ["expires_at"],
        unique=False,
    )


def downgrade() -> None:

    op.drop_index(
        "ix_travel_authorizations_expires_at",
        table_name="travel_authorizations",
    )

    op.drop_index(
        "ix_travel_authorizations_status",
        table_name="travel_authorizations",
    )

    op.drop_index(
        "ix_travel_authorizations_user_id",
        table_name="travel_authorizations",
    )

    op.drop_table("travel_authorizations")