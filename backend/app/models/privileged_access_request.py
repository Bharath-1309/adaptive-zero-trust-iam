import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PrivilegedAccessRequest(Base):
    __tablename__ = "privileged_access_requests"

    __table_args__ = (
        CheckConstraint(
            "status IN "
            "('PENDING', 'APPROVED', 'DENIED', "
            "'CANCELLED', 'EXPIRED')",
            name="ck_privileged_access_requests_status",
        ),
        CheckConstraint(
            "requested_duration_minutes > 0",
            name="ck_privileged_access_requests_duration",
        ),
        CheckConstraint(
            "length(trim(justification)) > 0",
            name="ck_privileged_access_requests_justification",
        ),
        CheckConstraint(
            "approval_reason IS NULL OR "
            "length(trim(approval_reason)) > 0",
            name="ck_privileged_access_requests_approval_reason",
        ),
        CheckConstraint(
            "approved_by_user_id IS NULL OR "
            "approved_by_user_id != user_id",
            name="ck_privileged_access_requests_no_self_approval",
        ),
        CheckConstraint(
            "("
            "status IN ('APPROVED', 'DENIED') "
            "AND approved_by_user_id IS NOT NULL "
            "AND reviewed_at IS NOT NULL"
            ") OR ("
            "status NOT IN ('APPROVED', 'DENIED')"
            ")",
            name="ck_privileged_access_requests_review_tracking",
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

    requested_role_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
    )

    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )

    justification: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    requested_duration_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDING",
        index=True,
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

    user = relationship(
        "User",
        foreign_keys=[user_id],
    )

    requested_role = relationship("Role")

    approved_by = relationship(
        "User",
        foreign_keys=[approved_by_user_id],
    )