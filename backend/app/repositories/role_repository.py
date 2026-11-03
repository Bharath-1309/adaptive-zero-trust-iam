import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.role import Role
from app.models.user import User


class RoleRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, role_id: uuid.UUID) -> Role | None:
        statement = select(Role).where(Role.id == role_id)

        return self.db.scalar(statement)

    def get_by_name(self, name: str) -> Role | None:
        statement = select(Role).where(Role.name == name)

        return self.db.scalar(statement)

    def get_all(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Role]:
        statement = (
            select(Role)
            .order_by(Role.name.asc())
            .offset(offset)
            .limit(limit)
        )

        return list(self.db.scalars(statement).all())

    def get_user_roles(self, user_id: uuid.UUID) -> list[Role]:
        statement = (
            select(Role)
            .join(Role.users)
            .where(User.id == user_id)
            .order_by(Role.name.asc())
        )

        return list(self.db.scalars(statement).all())

    def get_role_with_permissions(
        self,
        role_id: uuid.UUID,
    ) -> Role | None:
        statement = (
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.id == role_id)
        )

        return self.db.scalar(statement)

    def add(self, role: Role) -> Role:
        self.db.add(role)

        return role

    def assign_role_to_user(
        self,
        user: User,
        role: Role,
    ) -> None:
        if all(existing_role.id != role.id for existing_role in user.roles):
            user.roles.append(role)

    def remove_role_from_user(
        self,
        user: User,
        role: Role,
    ) -> None:
        user.roles = [
            existing_role
            for existing_role in user.roles
            if existing_role.id != role.id
        ]

    def flush(self) -> None:
        self.db.flush()