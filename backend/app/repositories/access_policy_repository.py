import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.access_policy import AccessPolicy


class AccessPolicyRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, policy_id: uuid.UUID) -> AccessPolicy | None:
        statement = select(AccessPolicy).where(
            AccessPolicy.id == policy_id
        )
        return self.db.scalar(statement)

    def get_by_name(self, name: str) -> AccessPolicy | None:
        statement = select(AccessPolicy).where(
            AccessPolicy.name == name
        )
        return self.db.scalar(statement)

    def get_all(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> list[AccessPolicy]:
        statement = (
            select(AccessPolicy)
            .order_by(
                AccessPolicy.priority.asc(),
                AccessPolicy.created_at.asc(),
                AccessPolicy.id.asc(),
            )
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def get_active_policies(self) -> list[AccessPolicy]:
        statement = (
            select(AccessPolicy)
            .where(AccessPolicy.is_active.is_(True))
            .order_by(
                AccessPolicy.priority.asc(),
                AccessPolicy.created_at.asc(),
                AccessPolicy.id.asc(),
            )
        )
        return list(self.db.scalars(statement).all())

    def get_by_effect(
        self,
        effect: str,
        active_only: bool = True,
    ) -> list[AccessPolicy]:
        statement = select(AccessPolicy).where(
            AccessPolicy.effect == effect
        )

        if active_only:
            statement = statement.where(
                AccessPolicy.is_active.is_(True)
            )

        statement = statement.order_by(
            AccessPolicy.priority.asc(),
            AccessPolicy.created_at.asc(),
            AccessPolicy.id.asc(),
        )

        return list(self.db.scalars(statement).all())

    def add(self, policy: AccessPolicy) -> AccessPolicy:
        self.db.add(policy)
        return policy

    def flush(self) -> None:
        self.db.flush()