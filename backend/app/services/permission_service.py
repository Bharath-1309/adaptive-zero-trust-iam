import uuid

from app.models.permission import Permission
from app.repositories.permission_repository import PermissionRepository
from app.repositories.role_repository import RoleRepository


class PermissionService:
    def __init__(
        self,
        permission_repository: PermissionRepository,
        role_repository: RoleRepository,
    ):
        self.permission_repository = permission_repository
        self.role_repository = role_repository

    def create_permission(
        self,
        name: str,
        description: str | None = None,
    ) -> Permission:
        name = name.strip()

        if not name:
            raise ValueError("Permission name cannot be empty.")

        if self.permission_repository.get_by_name(name):
            raise ValueError("Permission already exists.")

        permission = Permission(
            name=name,
            description=description,
        )

        self.permission_repository.add(permission)
        self.permission_repository.flush()

        return permission

    def get_permission(
        self,
        permission_id: uuid.UUID,
    ) -> Permission:
        permission = self.permission_repository.get_by_id(
            permission_id
        )

        if permission is None:
            raise LookupError("Permission not found.")

        return permission

    def get_all_permissions(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Permission]:
        if offset < 0 or limit < 1 or limit > 100:
            raise ValueError("Invalid pagination parameters.")

        return self.permission_repository.get_all(
            offset,
            limit,
        )

    def assign_permission(
        self,
        role_id: uuid.UUID,
        permission_id: uuid.UUID,
    ) -> None:
        role = self.role_repository.get_by_id(role_id)

        if role is None:
            raise LookupError("Role not found.")

        permission = self.get_permission(permission_id)

        self.permission_repository.assign_permission_to_role(
            role,
            permission,
        )

        self.permission_repository.flush()

    def remove_permission(
        self,
        role_id: uuid.UUID,
        permission_id: uuid.UUID,
    ) -> None:
        role = self.role_repository.get_by_id(role_id)

        if role is None:
            raise LookupError("Role not found.")

        permission = self.get_permission(permission_id)

        self.permission_repository.remove_permission_from_role(
            role,
            permission,
        )

        self.permission_repository.flush()

    def get_role_permissions(
        self,
        role_id: uuid.UUID,
    ) -> list[Permission]:
        role = self.role_repository.get_by_id(role_id)

        if role is None:
            raise LookupError("Role not found.")

        return self.permission_repository.get_role_permissions(
            role_id
        )