import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.access_decision import AccessDecision


class AccessDecisionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        decision_id: uuid.UUID,
    ) -> AccessDecision | None:
        statement = select(AccessDecision).where(
            AccessDecision.id == decision_id
        )
        return self.db.scalar(statement)

    def get_by_request_id(
        self,
        request_id: uuid.UUID,
    ) -> list[AccessDecision]:
        statement = (
            select(AccessDecision)
            .where(AccessDecision.request_id == request_id)
            .order_by(AccessDecision.evaluated_at.asc())
        )
        return list(self.db.scalars(statement).all())

    def get_user_decisions(
        self,
        user_id: uuid.UUID,
        offset: int = 0,
        limit: int = 100,
    ) -> list[AccessDecision]:
        statement = (
            select(AccessDecision)
            .where(AccessDecision.user_id == user_id)
            .order_by(AccessDecision.evaluated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def get_by_decision_type(
        self,
        decision: str,
        offset: int = 0,
        limit: int = 100,
    ) -> list[AccessDecision]:
        statement = (
            select(AccessDecision)
            .where(AccessDecision.decision == decision)
            .order_by(AccessDecision.evaluated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def get_parent_decision(
        self,
        decision_id: uuid.UUID,
    ) -> AccessDecision | None:
        decision = self.get_by_id(decision_id)

        if decision is None:
            return None

        return decision.parent_decision

    def get_child_decisions(
        self,
        parent_decision_id: uuid.UUID,
    ) -> list[AccessDecision]:
        statement = (
            select(AccessDecision)
            .where(
                AccessDecision.parent_decision_id
                == parent_decision_id
            )
            .order_by(AccessDecision.evaluated_at.asc())
        )
        return list(self.db.scalars(statement).all())

    def add(self, decision: AccessDecision) -> AccessDecision:
        self.db.add(decision)
        return decision

    def flush(self) -> None:
        self.db.flush()