import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        statement = select(User).where(User.id == user_id)

        return self.db.scalar(statement)

    def get_by_keycloak_subject(
        self,
        keycloak_subject: str,
    ) -> User | None:
        statement = select(User).where(
            User.keycloak_subject == keycloak_subject
        )

        return self.db.scalar(statement)

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)

        return self.db.scalar(statement)

    def get_all(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> list[User]:
        statement = (
            select(User)
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        return list(self.db.scalars(statement).all())

    def get_active_users(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> list[User]:
        statement = (
            select(User)
            .where(User.is_active.is_(True))
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        return list(self.db.scalars(statement).all())

    def add(self, user: User) -> User:
        self.db.add(user)

        return user

    def flush(self) -> None:
        self.db.flush()