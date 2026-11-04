import uuid

from app.db.session import SessionLocal
from app.models.user import User
from app.repositories.device_repository import DeviceRepository
from app.services.device_service import DeviceService


def run_tests():
    db = SessionLocal()

    try:
        repository = DeviceRepository(db)
        service = DeviceService(repository)

        # Create two temporary users.
        user1 = User(
            keycloak_subject=f"device-service-{uuid.uuid4()}",
            email=f"device-service-{uuid.uuid4()}@example.com",
            full_name="Device Service User 1",
        )

        user2 = User(
            keycloak_subject=f"device-service-{uuid.uuid4()}",
            email=f"device-service-{uuid.uuid4()}@example.com",
            full_name="Device Service User 2",
        )

        db.add_all([user1, user2])
        db.flush()

        # 1. Register a device.
        device, raw_token = service.register_device(
            user_id=user1.id,
            device_name="Test Windows Device",
            operating_system="Windows",
            browser="Chrome",
        )

        assert device.id is not None
        assert device.is_active is True
        assert device.is_trusted is False
        print("PASS: Device registration")

        # 2. Verify raw token is not stored.
        expected_hash = service.hash_device_token(raw_token)

        assert device.device_token_hash == expected_hash
        assert device.device_token_hash != raw_token
        print("PASS: Only token hash is stored")

        # 3. Verify token generation produces unique tokens.
        another_token = service.generate_device_token()

        assert another_token != raw_token
        print("PASS: Unique device token generation")

        # 4. Recognize device using valid token.
        recognized = service.identify_device(
            user_id=user1.id,
            token=raw_token,
        )

        assert recognized is not None
        assert recognized.id == device.id
        print("PASS: Valid device recognition")

        # 5. Reject empty token.
        assert service.identify_device(
            user_id=user1.id,
            token="",
        ) is None
        print("PASS: Empty token rejected")

        # 6. Reject oversized token.
        assert service.identify_device(
            user_id=user1.id,
            token="A" * 513,
        ) is None
        print("PASS: Oversized token rejected")

        # 7. Reject invalid token.
        assert service.identify_device(
            user_id=user1.id,
            token="invalid-device-token",
        ) is None
        print("PASS: Invalid token rejected")

        # 8. Reject recognition by another user.
        assert service.identify_device(
            user_id=user2.id,
            token=raw_token,
        ) is None
        print("PASS: Cross-user device recognition rejected")

        # 9. List user's devices.
        devices = service.get_user_devices(user1.id)

        assert any(item.id == device.id for item in devices)
        print("PASS: User device listing")

        # 10. Trust the device.
        assert service.set_device_trust(
            user_id=user1.id,
            device_id=device.id,
            is_trusted=True,
        ) is True

        db.flush()
        db.refresh(device)

        assert device.is_trusted is True
        print("PASS: Device trust enabled")

        # 11. Untrust the device.
        assert service.set_device_trust(
            user_id=user1.id,
            device_id=device.id,
            is_trusted=False,
        ) is True

        db.flush()
        db.refresh(device)

        assert device.is_trusted is False
        print("PASS: Device trust disabled")

        # 12. Reject trust modification by another user.
        assert service.set_device_trust(
            user_id=user2.id,
            device_id=device.id,
            is_trusted=True,
        ) is False
        print("PASS: Cross-user trust modification rejected")

        # 13. Reject revocation by another user.
        assert service.revoke_device(
            user_id=user2.id,
            device_id=device.id,
        ) is False
        print("PASS: Cross-user revocation rejected")

        # 14. Revoke device.
        assert service.revoke_device(
            user_id=user1.id,
            device_id=device.id,
        ) is True

        db.flush()
        db.refresh(device)

        assert device.is_active is False
        assert device.is_trusted is False
        assert device.revoked_at is not None
        print("PASS: Device revocation")

        # 15. Reject recognition after revocation.
        assert service.identify_device(
            user_id=user1.id,
            token=raw_token,
        ) is None
        print("PASS: Revoked device recognition rejected")

        # 16. Reject repeated revocation.
        assert service.revoke_device(
            user_id=user1.id,
            device_id=device.id,
        ) is False
        print("PASS: Repeated revocation rejected")

        # 17. Reject trust modification after revocation.
        assert service.set_device_trust(
            user_id=user1.id,
            device_id=device.id,
            is_trusted=True,
        ) is False
        print("PASS: Revoked device cannot be trusted")

        db.rollback()
        print("\nPASS: All device service tests completed.")
        print("PASS: Test transaction rolled back.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    run_tests()