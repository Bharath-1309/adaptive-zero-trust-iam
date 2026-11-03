import uuid

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.device import Device
from app.models.login_event import LoginEvent
from app.models.user import User
from app.repositories.login_event_repository import LoginEventRepository


def run_tests():
    db = SessionLocal()

    try:
        repository = LoginEventRepository(db)

        # Create temporary test user.
        user = User(
            keycloak_subject=f"login-test-{uuid.uuid4()}",
            email=f"login-test-{uuid.uuid4()}@example.com",
            full_name="Login Event Test",
        )

        db.add(user)
        db.flush()

        # Create temporary device.
        device = Device(
            user_id=user.id,
            device_name="Login Test Device",
            operating_system="Windows",
            browser="Chrome",
            device_token_hash=uuid.uuid4().hex
            + uuid.uuid4().hex,
        )

        db.add(device)
        db.flush()

        print("PASS: Test user and device creation")

        # Create successful login event.
        success_event = LoginEvent(
            user_id=user.id,
            device_id=device.id,
            event_type="LOGIN_SUCCESS",
            success=True,
            user_agent="Test Browser",
        )

        repository.add(success_event)
        repository.flush()

        print("PASS: Successful login event creation")

        # Create failed login event.
        failure_event = LoginEvent(
            user_id=user.id,
            device_id=device.id,
            event_type="LOGIN_FAILURE",
            success=False,
            failure_reason="Invalid credentials",
        )

        repository.add(failure_event)
        repository.flush()

        print("PASS: Failed login event creation")

        # Retrieve event by UUID.
        retrieved = repository.get_by_id(success_event.id)

        assert retrieved is not None
        assert retrieved.event_type == "LOGIN_SUCCESS"

        print("PASS: Login event lookup by UUID")

        # Retrieve events by user.
        user_events = repository.get_user_events(user.id)

        assert len(user_events) == 2
        assert all(event.user_id == user.id for event in user_events)

        print("PASS: User login event retrieval")

        # Retrieve events by device.
        device_events = repository.get_device_events(device.id)

        assert len(device_events) == 2
        assert all(event.device_id == device.id for event in device_events)

        print("PASS: Device login event retrieval")

        # Retrieve events by event type.
        failed_events = repository.get_by_event_type("LOGIN_FAILURE")

        assert any(event.id == failure_event.id for event in failed_events)

        print("PASS: Event type filtering")

        # Verify pagination.
        first_page = repository.get_user_events(
            user.id,
            offset=0,
            limit=1,
        )

        assert len(first_page) == 1

        print("PASS: Login event pagination")

        # Verify repository does not expose update/delete methods.
        assert not hasattr(repository, "update")
        assert not hasattr(repository, "delete")

        print("PASS: No update/delete repository methods")

        # Roll back test data.
        db.rollback()

        remaining = db.scalar(
            select(LoginEvent).where(
                LoginEvent.id == success_event.id
            )
        )

        assert remaining is None

        print("PASS: Test transaction rolled back")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    run_tests()