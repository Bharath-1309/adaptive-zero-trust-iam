import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    LargeBinary,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    __table_args__ = (
        CheckConstraint(
            "length(trim(event_type)) > 0",
            name="ck_audit_logs_event_type_not_empty",
        ),
        CheckConstraint(
            "length(trim(action)) > 0",
            name="ck_audit_logs_action_not_empty",
        ),
        CheckConstraint(
            "length(trim(resource_type)) > 0",
            name="ck_audit_logs_resource_type_not_empty",
        ),
        CheckConstraint(
            "length(trim(outcome)) > 0",
            name="ck_audit_logs_outcome_not_empty",
        ),
        CheckConstraint(
            "json_typeof(details) = 'object'",
            name="ck_audit_logs_details_object",
        ),
        CheckConstraint(
            "("
            "ip_ciphertext IS NULL "
            "AND ip_hmac IS NULL "
            "AND ip_key_version IS NULL"
            ") OR ("
            "ip_ciphertext IS NOT NULL "
            "AND ip_hmac IS NOT NULL "
            "AND ip_key_version IS NOT NULL"
            ")",
            name="ck_audit_logs_ip_fields_consistent",
        ),
        CheckConstraint(
            "ip_key_version IS NULL OR ip_key_version > 0",
            name="ck_audit_logs_ip_key_version",
        ),
        Index(
            "ix_audit_logs_actor_occurred",
            "actor_user_id",
            "occurred_at",
        ),
        Index(
            "ix_audit_logs_event_occurred",
            "event_type",
            "occurred_at",
        ),
        Index(
            "ix_audit_logs_ip_hmac",
            "ip_hmac",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    action: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    resource_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    resource_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    outcome: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    request_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True,
        index=True,
    )

    details: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    ip_ciphertext: Mapped[bytes | None] = mapped_column(
        LargeBinary,
        nullable=True,
    )

    ip_hmac: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    ip_key_version: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    actor = relationship("User")