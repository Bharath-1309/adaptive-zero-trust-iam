import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class StepUpChallenge(Base):
    __tablename__ = "step_up_challenges"

    __table_args__ = (
        CheckConstraint(
            "status IN "
            "('PENDING', 'VERIFIED', 'CONSUMED', "
            "'EXPIRED', 'FAILED', 'REVOKED')",
            name="ck_step_up_challenges_status",
        ),
        CheckConstraint(
            "failed_attempts >= 0",
            name="ck_step_up_challenges_failed_attempts",
        ),
        CheckConstraint(
            "challenge_hash ~ '^[0-9a-f]{64}$'",
            name="ck_step_up_challenges_hash_format",
        ),
        CheckConstraint(
            "request_binding_hash ~ '^[0-9a-f]{64}$'",
            name="ck_step_up_challenges_request_hash_format",
        ),
        CheckConstraint(
            "payload_hash ~ '^[0-9a-f]{64}$'",
            name="ck_step_up_challenges_payload_hash_format",
        ),
        CheckConstraint(
            "length(trim(keycloak_session_id)) > 0",
            name="ck_step_up_challenges_session_not_empty",
        ),
        CheckConstraint(
            "expires_at > created_at",
            name="ck_step_up_challenges_expiration",
        ),
        CheckConstraint(
            "("
            "status NOT IN ('VERIFIED', 'CONSUMED') "
            "OR verified_at IS NOT NULL"
            ")",
            name="ck_step_up_challenges_verified_timestamp",
        ),
        CheckConstraint(
            "("
            "status = 'CONSUMED' AND consumed_at IS NOT NULL"
            ") OR ("
            "status != 'CONSUMED' AND consumed_at IS NULL"
            ")",
            name="ck_step_up_challenges_consumed_timestamp",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    access_decision_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("access_decisions.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
    )

    challenge_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
    )

    request_binding_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    payload_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    keycloak_session_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDING",
        index=True,
    )

    failed_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    access_decision = relationship("AccessDecision")