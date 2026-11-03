import hashlib
import uuid

from app.db.session import SessionLocal
from app.models.device import Device
from app.models.user import User
from app.repositories.device_repository import DeviceRepository


def run_tests():
    db = SessionLocal()

    try:
        repository = DeviceRepository(db)

        # Create a temporary test user.
        user = User(
            keycloak_subject=f"device-test-{uuid.uuid4()}",
            email=f"device-test-{uuid.uuid4()}@example.com",
            full_name="Device Repository Test",
        )

        db.add(user)
        db.flush()

        # Generate a SHA-256 hash for a temporary device token.
        raw_token = str(uuid.uuid4())
        token_hash = hashlib.sha256(
            raw_token.encode("utf-8")
        ).hexdigest()

        device = Device(
            user_id=user.id,
            device_name="Test Windows Device",
            operating_system="Windows",
            browser="Chrome",
            device_token_hash=token_hash,
        )

        repository.add(device)
        repository.flush()

        print("PASS: Device creation")

        # Lookup by device ID.
        assert repository.get_by_id(device.id) is not None
        print("PASS: Device lookup by UUID")

        # Lookup by token hash.
        assert repository.get_by_token_hash(token_hash) is not None
        print("PASS: Device lookup by token hash")

        # Retrieve devices belonging to the user.
        devices = repository.get_user_devices(user.id)
        assert any(item.id == device.id for item in devices)
        print("PASS: User device retrieval")

        # Retrieve active devices.
        active_devices = repository.get_active_devices(user.id)
        assert any(item.id == device.id for item in active_devices)
        print("PASS: Active device retrieval")

        # Update last-seen timestamp.
        assert repository.update_last_seen(device.id) is True
        db.flush()
        db.refresh(device)

        assert device.last_seen_at is not None
        print("PASS: Device last-seen update")

        # Mark device as trusted.
        assert repository.set_trusted(device.id, True) is True
        db.flush()
        db.refresh(device)

        assert device.is_trusted is True
        print("PASS: Device trust update")

        # Revoke device.
        assert repository.revoke(device.id) is True
        db.flush()
        db.refresh(device)

        assert device.is_active is False
        assert device.is_trusted is False
        assert device.revoked_at is not None
        print("PASS: Device revocation")

        # Revoked devices cannot be trusted again.
        assert repository.set_trusted(device.id, True) is False
        print("PASS: Revoked device cannot be trusted")

        # Revoked devices cannot have last-seen updated.
        assert repository.update_last_seen(device.id) is False
        print("PASS: Revoked device cannot update last-seen")

        # Roll back all test data.
        db.rollback()
        print("PASS: Test transaction rolled back")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    run_tests()