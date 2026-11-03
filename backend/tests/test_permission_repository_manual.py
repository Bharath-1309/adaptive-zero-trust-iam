import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal
from app.models.permission import Permission
from app.models.role import Role
from app.repositories.permission_repository import PermissionRepository


def test_permission_repository():
    db = SessionLocal()

    try:
        repository = PermissionRepository(db)

        role = Role(
            name=f"permission-test-{uuid.uuid4()}",
            description="Temporary permission repository test role",
        )

        permission = Permission(
            name=f"repository-test:{uuid.uuid4()}",
            description="Temporary repository test permission",
        )

        db.add(role)
        repository.add(permission)
        repository.flush()

        print("PASS: Role and permission creation")

        found_by_id = repository.get_by_id(permission.id)
        assert found_by_id is not None
        assert found_by_id.id == permission.id
        print("PASS: Permission lookup by UUID")

        found_by_name = repository.get_by_name(permission.name)
        assert found_by_name is not None
        assert found_by_name.id == permission.id
        print("PASS: Permission lookup by name")

        all_permissions = repository.get_all(
            offset=0,
            limit=100,
        )
        assert any(
            item.id == permission.id for item in all_permissions
        )
        print("PASS: Permission listing and pagination")

        repository.assign_permission_to_role(role, permission)
        repository.flush()

        role_permissions = repository.get_role_permissions(role.id)
        assert any(
            item.id == permission.id for item in role_permissions
        )
        print("PASS: Permission assignment and retrieval")

        repository.assign_permission_to_role(role, permission)
        repository.flush()

        assert len(
            [
                item
                for item in role.permissions
                if item.id == permission.id
            ]
        ) == 1
        print("PASS: Duplicate permission assignment prevention")

        permission_with_roles = repository.get_permission_with_roles(
            permission.id
        )
        assert permission_with_roles is not None
        assert any(
            item.id == role.id
            for item in permission_with_roles.roles
        )
        print("PASS: Permission retrieval with roles")

        repository.remove_permission_from_role(role, permission)
        repository.flush()

        role_permissions = repository.get_role_permissions(role.id)
        assert all(
            item.id != permission.id for item in role_permissions
        )
        print("PASS: Permission removal")

        db.rollback()
        print("PASS: Test transaction rolled back")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    test_permission_repository()