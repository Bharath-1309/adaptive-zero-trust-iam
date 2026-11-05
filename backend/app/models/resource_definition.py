import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ResourceDefinition(Base):
    __tablename__ = "resource_definitions"

    __table_args__ = (
        CheckConstraint(
            "length(trim(name)) > 0",
            name="ck_resource_definitions_name_not_empty",
        ),
        CheckConstraint(
            "length(trim(required_permission)) > 0",
            name="ck_resource_definitions_permission_not_empty",
        ),
        CheckConstraint(
            """
            access_policy IN (
                'OFFICE_ONLY',
                'REMOTE_ALLOWED',
                'TRAVEL_ALLOWED',
                'VPN_REQUIRED'
            )
            """,
            name="ck_resource_definitions_access_policy",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    required_permission: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    access_policy: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="REMOTE_ALLOWED",
        server_default="REMOTE_ALLOWED",
    )

    # Retained temporarily for backward compatibility.
    requires_office_location: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
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