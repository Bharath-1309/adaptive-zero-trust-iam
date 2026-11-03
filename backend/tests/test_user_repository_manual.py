import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal
from app.models.user import User
from app.repositories.user_repository import UserRepository


def test_user_repository():
    db = SessionLocal()
    test_user = None

    try:
        repository = UserRepository(db)

        test_user = User(
            keycloak_subject=f"repository-test-{uuid.uuid4()}",
            email=f"repository-test-{uuid.uuid4()}@example.com",
            full_name="Repository Test User",
            is_active=True,
        )

        repository.add(test_user)
        repository.flush()

        assert test_user.id is not None
        print("PASS: User creation")

        found_by_subject = repository.get_by_keycloak_subject(
            test_user.keycloak_subject
        )
        assert found_by_subject is not None
        assert found_by_subject.id == test_user.id
        print("PASS: Lookup by Keycloak subject")

        found_by_email = repository.get_by_email(test_user.email)
        assert found_by_email is not None
        assert found_by_email.id == test_user.id
        print("PASS: Lookup by email")

        found_by_id = repository.get_by_id(test_user.id)
        assert found_by_id is not None
        assert found_by_id.id == test_user.id
        print("PASS: Lookup by UUID")

        active_users = repository.get_active_users(
            offset=0,
            limit=100,
        )
        assert any(user.id == test_user.id for user in active_users)
        print("PASS: Active user retrieval")

        paginated_users = repository.get_all(
            offset=0,
            limit=1,
        )
        assert len(paginated_users) <= 1
        print("PASS: User pagination")

        db.rollback()
        print("PASS: Test transaction rolled back")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    test_user_repository()