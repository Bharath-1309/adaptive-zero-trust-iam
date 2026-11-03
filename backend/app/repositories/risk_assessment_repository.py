import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.risk_assessment import RiskAssessment


class RiskAssessmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        assessment_id: uuid.UUID,
    ) -> RiskAssessment | None:
        statement = select(RiskAssessment).where(
            RiskAssessment.id == assessment_id
        )
        return self.db.scalar(statement)

    def get_user_assessments(
        self,
        user_id: uuid.UUID,
        offset: int = 0,
        limit: int = 100,
    ) -> list[RiskAssessment]:
        statement = (
            select(RiskAssessment)
            .where(RiskAssessment.user_id == user_id)
            .order_by(RiskAssessment.assessed_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def get_latest_assessment(
        self,
        user_id: uuid.UUID,
    ) -> RiskAssessment | None:
        statement = (
            select(RiskAssessment)
            .where(RiskAssessment.user_id == user_id)
            .order_by(RiskAssessment.assessed_at.desc())
            .limit(1)
        )
        return self.db.scalar(statement)

    def get_by_risk_level(
        self,
        risk_level: str,
        offset: int = 0,
        limit: int = 100,
    ) -> list[RiskAssessment]:
        statement = (
            select(RiskAssessment)
            .where(RiskAssessment.risk_level == risk_level)
            .order_by(RiskAssessment.assessed_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def get_device_assessments(
        self,
        device_id: uuid.UUID,
        offset: int = 0,
        limit: int = 100,
    ) -> list[RiskAssessment]:
        statement = (
            select(RiskAssessment)
            .where(RiskAssessment.device_id == device_id)
            .order_by(RiskAssessment.assessed_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def add(self, assessment: RiskAssessment) -> RiskAssessment:
        self.db.add(assessment)
        return assessment

    def flush(self) -> None:
        self.db.flush()