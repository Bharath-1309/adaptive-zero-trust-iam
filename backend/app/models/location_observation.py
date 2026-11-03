import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class LocationObservation(Base):
    __tablename__ = "location_observations"

    __table_args__ = (
        CheckConstraint(
            "source IN ('IP_GEOIP', 'BROWSER_GPS')",
            name="ck_location_observations_source",
        ),
        CheckConstraint(
            "latitude IS NULL OR latitude BETWEEN -90 AND 90",
            name="ck_location_observations_latitude",
        ),
        CheckConstraint(
            "longitude IS NULL OR longitude BETWEEN -180 AND 180",
            name="ck_location_observations_longitude",
        ),
        CheckConstraint(
            "accuracy_meters IS NULL OR accuracy_meters >= 0",
            name="ck_location_observations_accuracy",
        ),
        CheckConstraint(
            "country_code IS NULL OR country_code ~ '^[A-Z]{2}$'",
            name="ck_location_observations_country_code",
        ),
        CheckConstraint(
            "country_name IS NULL OR length(trim(country_name)) > 0",
            name="ck_location_observations_country_name",
        ),
        CheckConstraint(
            "region IS NULL OR length(trim(region)) > 0",
            name="ck_location_observations_region",
        ),
        CheckConstraint(
            "city IS NULL OR length(trim(city)) > 0",
            name="ck_location_observations_city",
        ),
        CheckConstraint(
            "("
            "source != 'BROWSER_GPS' "
            "OR (latitude IS NOT NULL "
            "AND longitude IS NOT NULL "
            "AND accuracy_meters IS NOT NULL)"
            ")",
            name="ck_location_observations_gps_coordinates",
        ),
        CheckConstraint(
            "("
            "source = 'IP_GEOIP' "
            "AND consent_granted = false "
            "AND consent_recorded_at IS NULL"
            ") OR ("
            "source = 'BROWSER_GPS' "
            "AND consent_granted = true "
            "AND consent_recorded_at IS NOT NULL"
            ")",
            name="ck_location_observations_consent",
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

    login_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("login_events.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    source: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    country_code: Mapped[str | None] = mapped_column(
        String(2),
        nullable=True,
    )

    country_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    region: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    city: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    latitude: Mapped[Decimal | None] = mapped_column(
        Numeric(9, 6),
        nullable=True,
    )

    longitude: Mapped[Decimal | None] = mapped_column(
        Numeric(9, 6),
        nullable=True,
    )

    accuracy_meters: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )

    consent_granted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    consent_recorded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    user = relationship("User")
    login_event = relationship("LoginEvent")