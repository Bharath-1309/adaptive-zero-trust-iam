import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Device(Base):
    __tablename__ = "devices"

    __table_args__ = (
        CheckConstraint(
            "length(trim(device_name)) > 0",
            name="ck_devices_name_not_empty",
        ),
        CheckConstraint(
            "device_token_hash ~ '^[0-9a-f]{64}$'",
            name="ck_devices_token_hash_format",
        ),
        CheckConstraint(
            "is_active OR NOT is_trusted",
            name="ck_devices_inactive_not_trusted",
        ),
        CheckConstraint(
            "("
            "is_active = true AND revoked_at IS NULL"
            ") OR ("
            "is_active = false AND revoked_at IS NOT NULL"
            ")",
            name="ck_devices_revocation_consistency",
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

    device_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    operating_system: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    browser: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    device_token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
    )

    is_trusted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user = relationship("User")