import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    LargeBinary,
    SmallInteger,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class LoginEvent(Base):
    __tablename__ = "login_events"

    __table_args__ = (
        CheckConstraint(
            "event_type IN "
            "('LOGIN_SUCCESS', 'LOGIN_FAILURE', "
            "'LOGOUT', 'TOKEN_REFRESH', 'MFA_SUCCESS', "
            "'MFA_FAILURE', 'SESSION_EXPIRED')",
            name="ck_login_events_event_type",
        ),
        CheckConstraint(
            "("
            "ip_address_encrypted IS NULL "
            "AND ip_address_hash IS NULL "
            "AND ip_key_version IS NULL"
            ") OR ("
            "ip_address_encrypted IS NOT NULL "
            "AND ip_address_hash IS NOT NULL "
            "AND ip_key_version IS NOT NULL"
            ")",
            name="ck_login_events_ip_fields_consistent",
        ),
        CheckConstraint(
            "ip_address_hash IS NULL OR "
            "ip_address_hash ~ '^[0-9a-f]{64}$'",
            name="ck_login_events_ip_hash_format",
        ),
        CheckConstraint(
            "ip_key_version IS NULL OR ip_key_version > 0",
            name="ck_login_events_ip_key_version",
        ),
        CheckConstraint(
            "("
            "success = true AND failure_reason IS NULL"
            ") OR ("
            "success = false"
            ")",
            name="ck_login_events_failure_reason",
        ),
        CheckConstraint(
            "failure_reason IS NULL OR "
            "length(trim(failure_reason)) > 0",
            name="ck_login_events_failure_reason_not_empty",
        ),
        Index(
            "ix_login_events_user_occurred",
            "user_id",
            "occurred_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )

    device_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("devices.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    success: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    failure_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    ip_address_encrypted: Mapped[bytes | None] = mapped_column(
        LargeBinary,
        nullable=True,
    )

    ip_address_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )

    ip_key_version: Mapped[int | None] = mapped_column(
        SmallInteger,
        nullable=True,
    )

    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    user = relationship("User")
    device = relationship("Device")