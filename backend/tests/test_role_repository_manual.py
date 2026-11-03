import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal
from app.models.role import Role
from app.models.user import User
from app.repositories.role_repository import RoleRepository


def test_role_repository():
    db = SessionLocal()

    try:
        repository = RoleRepository(db)

        user = User(
            keycloak_subject=f"role-test-{uuid.uuid4()}",
            email=f"role-test-{uuid.uuid4()}@example.com",
            full_name="Role Repository Test User",
            is_active=True,
        )

        role = Role(
            name=f"repository-test-{uuid.uuid4()}",
            description="Temporary repository test role",
        )

        db.add(user)
        repository.add(role)
        repository.flush()

        print("PASS: User and role creation")

        found_by_id = repository.get_by_id(role.id)
        assert found_by_id is not None
        assert found_by_id.id == role.id
        print("PASS: Role lookup by UUID")

        found_by_name = repository.get_by_name(role.name)
        assert found_by_name is not None
        assert found_by_name.id == role.id
        print("PASS: Role lookup by name")

        all_roles = repository.get_all(offset=0, limit=100)
        assert any(item.id == role.id for item in all_roles)
        print("PASS: Role listing and pagination")

        repository.assign_role_to_user(user, role)
        repository.flush()

        user_roles = repository.get_user_roles(user.id)
        assert any(item.id == role.id for item in user_roles)
        print("PASS: Role assignment and retrieval")

        # Confirm duplicate assignment does not create another relationship.
        repository.assign_role_to_user(user, role)
        repository.flush()

        assert len([item for item in user.roles if item.id == role.id]) == 1
        print("PASS: Duplicate role assignment prevention")

        repository.remove_role_from_user(user, role)
        repository.flush()

        user_roles = repository.get_user_roles(user.id)
        assert all(item.id != role.id for item in user_roles)
        print("PASS: Role removal")

        db.rollback()
        print("PASS: Test transaction rolled back")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    test_role_repository()