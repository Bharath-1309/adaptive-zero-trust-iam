import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Integer,
    JSON,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AccessPolicy(Base):
    __tablename__ = "access_policies"

    __table_args__ = (
        CheckConstraint(
            "effect IN ('ALLOW', 'DENY')",
            name="ck_access_policies_effect",
        ),
        CheckConstraint(
            "priority >= 0",
            name="ck_access_policies_priority",
        ),
        CheckConstraint(
            "length(trim(name)) > 0",
            name="ck_access_policies_name_not_empty",
        ),
        CheckConstraint(
            "json_typeof(conditions) = 'object'",
            name="ck_access_policies_conditions_object",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    effect: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
        index=True,
    )

    conditions: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )