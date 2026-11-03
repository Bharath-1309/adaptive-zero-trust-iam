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
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AccessDecision(Base):
    __tablename__ = "access_decisions"

    __table_args__ = (
        CheckConstraint(
            "decision IN ('ALLOW', 'STEP_UP', 'DENY')",
            name="ck_access_decisions_decision",
        ),
        CheckConstraint(
            "parent_decision_id IS NULL OR parent_decision_id != id",
            name="ck_access_decisions_no_self_parent",
        ),
        CheckConstraint(
            "risk_score IS NULL OR "
            "(risk_score >= 0 AND risk_score <= 100)",
            name="ck_access_decisions_risk_score_range",
        ),
        CheckConstraint(
            "json_typeof(policy_snapshot) = 'object'",
            name="ck_access_decisions_policy_snapshot_object",
        ),
        CheckConstraint(
            "length(trim(action)) > 0",
            name="ck_access_decisions_action_not_empty",
        ),
        CheckConstraint(
            "length(trim(resource)) > 0",
            name="ck_access_decisions_resource_not_empty",
        ),
        CheckConstraint(
            "length(trim(reason)) > 0",
            name="ck_access_decisions_reason_not_empty",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    request_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
        index=True,
    )

    parent_decision_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("access_decisions.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    risk_assessment_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("risk_assessments.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    action: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    resource: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    decision: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    risk_score: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    policy_snapshot: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    user = relationship("User")
    risk_assessment = relationship("RiskAssessment")

    parent_decision = relationship(
        "AccessDecision",
        remote_side="AccessDecision.id",
        foreign_keys=[parent_decision_id],
    )