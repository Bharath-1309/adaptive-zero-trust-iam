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


class PrivilegedAccessGrant(Base):
    __tablename__ = "privileged_access_grants"

    __table_args__ = (
        CheckConstraint(
            "status IN ('ACTIVE', 'EXPIRED', 'REVOKED')",
            name="ck_privileged_access_grants_status",
        ),
        CheckConstraint(
            "expires_at > starts_at",
            name="ck_privileged_access_grants_expiry",
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
            name="ck_privileged_access_grants_revocation",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    request_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "privileged_access_requests.id",
            ondelete="RESTRICT",
        ),
        unique=True,
        nullable=False,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    role_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
    )

    approved_by_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ACTIVE",
        index=True,
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

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    revocation_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    request = relationship("PrivilegedAccessRequest")
    user = relationship("User", foreign_keys=[user_id])
    role = relationship("Role")

    approved_by = relationship(
        "User",
        foreign_keys=[approved_by_user_id],
    )