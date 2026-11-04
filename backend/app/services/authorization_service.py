import uuid

from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository


class AuthorizationService:
    def __init__(
        self,
        user_repository: UserRepository,
        role_repository: RoleRepository,
    ):
        self.user_repository = user_repository
        self.role_repository = role_repository

    def get_user_permissions(
        self,
        user_id: uuid.UUID,
    ) -> set[str]:
        user = self.user_repository.get_by_id(user_id)

        if user is None:
            raise LookupError("User not found.")

        if not user.is_active:
            raise PermissionError("Inactive user access denied.")

        roles = self.role_repository.get_user_roles(user_id)

        permissions = set()

        for role in roles:
            for permission in role.permissions:
                permissions.add(permission.name)

        return permissions

    def has_permission(
        self,
        user_id: uuid.UUID,
        permission_name: str,
    ) -> bool:
        if not permission_name or not permission_name.strip():
            return False

        permissions = self.get_user_permissions(user_id)

        return permission_name in permissions

    def require_permission(
        self,
        user_id: uuid.UUID,
        permission_name: str,
    ) -> None:
        if not self.has_permission(user_id, permission_name):
            raise PermissionError(
                f"Required permission '{permission_name}' is missing."
            )