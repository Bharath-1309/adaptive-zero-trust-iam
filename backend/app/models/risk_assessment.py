import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    JSON,
    Numeric,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    __table_args__ = (
        CheckConstraint(
            "risk_score >= 0 AND risk_score <= 100",
            name="ck_risk_assessments_score_range",
        ),
        CheckConstraint(
            "risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')",
            name="ck_risk_assessments_level",
        ),
        CheckConstraint(
            "json_typeof(risk_factors) = 'object'",
            name="ck_risk_assessments_factors_object",
        ),
        CheckConstraint(
            "length(trim(assessment_version)) > 0",
            name="ck_risk_assessments_version_not_empty",
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

    device_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("devices.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    location_observation_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("location_observations.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    risk_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )

    risk_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    risk_factors: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    assessment_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    assessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    user = relationship("User")
    device = relationship("Device")
    location_observation = relationship("LocationObservation")
