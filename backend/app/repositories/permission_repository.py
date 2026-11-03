import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.permission import Permission
from app.models.role import Role


class PermissionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        permission_id: uuid.UUID,
    ) -> Permission | None:
        statement = select(Permission).where(
            Permission.id == permission_id
        )

        return self.db.scalar(statement)

    def get_by_name(self, name: str) -> Permission | None:
        statement = select(Permission).where(
            Permission.name == name
        )

        return self.db.scalar(statement)

    def get_all(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Permission]:
        statement = (
            select(Permission)
            .order_by(Permission.name.asc())
            .offset(offset)
            .limit(limit)
        )

        return list(self.db.scalars(statement).all())

    def get_role_permissions(
        self,
        role_id: uuid.UUID,
    ) -> list[Permission]:
        statement = (
            select(Permission)
            .join(Permission.roles)
            .where(Role.id == role_id)
            .order_by(Permission.name.asc())
        )

        return list(self.db.scalars(statement).all())

    def get_permission_with_roles(
        self,
        permission_id: uuid.UUID,
    ) -> Permission | None:
        statement = (
            select(Permission)
            .options(selectinload(Permission.roles))
            .where(Permission.id == permission_id)
        )

        return self.db.scalar(statement)

    def add(self, permission: Permission) -> Permission:
        self.db.add(permission)

        return permission

    def assign_permission_to_role(
        self,
        role: Role,
        permission: Permission,
    ) -> None:
        if all(
            existing_permission.id != permission.id
            for existing_permission in role.permissions
        ):
            role.permissions.append(permission)

    def remove_permission_from_role(
        self,
        role: Role,
        permission: Permission,
    ) -> None:
        role.permissions = [
            existing_permission
            for existing_permission in role.permissions
            if existing_permission.id != permission.id
        ]

    def flush(self) -> None:
        self.db.flush()