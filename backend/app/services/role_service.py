import uuid

from app.models.role import Role
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository


class RoleService:
    def __init__(
        self,
        role_repository: RoleRepository,
        user_repository: UserRepository,
    ):
        self.role_repository = role_repository
        self.user_repository = user_repository

    def create_role(
        self,
        name: str,
        description: str | None = None,
    ) -> Role:
        name = name.strip()

        if not name:
            raise ValueError("Role name cannot be empty.")

        if self.role_repository.get_by_name(name):
            raise ValueError("Role already exists.")

        role = Role(
            name=name,
            description=description,
        )

        self.role_repository.add(role)
        self.role_repository.flush()

        return role

    def get_role(self, role_id: uuid.UUID) -> Role:
        role = self.role_repository.get_by_id(role_id)

        if role is None:
            raise LookupError("Role not found.")

        return role

    def get_all_roles(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Role]:
        if offset < 0 or limit < 1 or limit > 100:
            raise ValueError("Invalid pagination parameters.")

        return self.role_repository.get_all(offset, limit)

    def assign_role(
        self,
        user_id: uuid.UUID,
        role_id: uuid.UUID,
    ) -> None:
        user = self.user_repository.get_by_id(user_id)

        if user is None:
            raise LookupError("User not found.")

        if not user.is_active:
            raise PermissionError("Cannot assign roles to inactive users.")

        role = self.get_role(role_id)

        self.role_repository.assign_role_to_user(user, role)
        self.role_repository.flush()

    def remove_role(
        self,
        user_id: uuid.UUID,
        role_id: uuid.UUID,
    ) -> None:
        user = self.user_repository.get_by_id(user_id)

        if user is None:
            raise LookupError("User not found.")

        role = self.get_role(role_id)

        self.role_repository.remove_role_from_user(user, role)
        self.role_repository.flush()

    def get_user_roles(
        self,
        user_id: uuid.UUID,
    ) -> list[Role]:
        user = self.user_repository.get_by_id(user_id)

        if user is None:
            raise LookupError("User not found.")

        if not user.is_active:
            raise PermissionError("Inactive users cannot access roles.")

        return self.role_repository.get_user_roles(user_id)