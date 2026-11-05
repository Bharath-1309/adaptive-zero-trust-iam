import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class OfficeGeofence(Base):
    __tablename__ = "office_geofences"

    __table_args__ = (
        CheckConstraint(
            "length(trim(name)) > 0",
            name="ck_office_geofences_name_not_empty",
        ),
        CheckConstraint(
            "latitude BETWEEN -90 AND 90",
            name="ck_office_geofences_latitude",
        ),
        CheckConstraint(
            "longitude BETWEEN -180 AND 180",
            name="ck_office_geofences_longitude",
        ),
        CheckConstraint(
            "radius_meters > 0",
            name="ck_office_geofences_radius_positive",
        ),
        CheckConstraint(
            "max_accuracy_meters > 0",
            name="ck_office_geofences_accuracy_positive",
        ),
        CheckConstraint(
            "location_type IN ('PERMANENT', 'TEMPORARY')",
            name="ck_office_geofences_location_type",
        ),
        CheckConstraint(
            """
            (location_type = 'PERMANENT' AND expires_at IS NULL)
            OR
            (location_type = 'TEMPORARY' AND expires_at IS NOT NULL)
            """,
            name="ck_office_geofences_expiry",
        ),
        Index(
            "ix_office_geofences_active_expiry",
            "is_active",
            "expires_at",
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

    latitude: Mapped[Decimal] = mapped_column(
        Numeric(9, 6),
        nullable=False,
    )

    longitude: Mapped[Decimal] = mapped_column(
        Numeric(9, 6),
        nullable=False,
    )

    radius_meters: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=100,
    )

    max_accuracy_meters: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=100,
    )

    location_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PERMANENT",
        server_default="PERMANENT",
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
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

    created_by = relationship("User")