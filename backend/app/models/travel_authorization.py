import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TravelAuthorization(Base):

    __tablename__ = "travel_authorizations"

    __table_args__ = (
        CheckConstraint(
            "status IN "
            "('PENDING', 'APPROVED', 'DENIED', 'REVOKED', 'EXPIRED')",
            name="ck_travel_authorizations_status",
        ),
        CheckConstraint(
            "expires_at > starts_at",
            name="ck_travel_authorizations_expiry",
        ),
        CheckConstraint(
            "length(trim(destination)) > 0",
            name="ck_travel_authorizations_destination",
        ),
        CheckConstraint(
            "length(trim(justification)) > 0",
            name="ck_travel_authorizations_justification",
        ),
        CheckConstraint(
            "approved_by_user_id IS NULL OR "
            "approved_by_user_id != user_id",
            name="ck_travel_authorizations_no_self_approval",
        ),
        CheckConstraint(
            "("
            "status IN ('APPROVED', 'DENIED') "
            "AND approved_by_user_id IS NOT NULL "
            "AND reviewed_at IS NOT NULL"
            ") OR ("
            "status NOT IN ('APPROVED', 'DENIED')"
            ")",
            name="ck_travel_authorizations_review_tracking",
        ),
        CheckConstraint(
            "("
            "status = 'REVOKED' "
            "AND revoked_at IS NOT NULL "
            "AND revocation_reason IS NOT NULL "
            "AND length(trim(revocation_reason)) > 0"
            ") OR ("
            "status != 'REVOKED' "
            "AND revoked_at IS NULL "
            "AND revocation_reason IS NULL"
            ")",
            name="ck_travel_authorizations_revocation",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    destination: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    justification: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDING",
        server_default="PENDING",
        index=True,
    )

    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )

    approval_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    revocation_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    user = relationship(
        "User",
        foreign_keys=[user_id],
    )

    approved_by = relationship(
        "User",
        foreign_keys=[approved_by_user_id],
    )