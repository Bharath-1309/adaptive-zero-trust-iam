import hashlib
import secrets
import uuid

from app.models.device import Device
from app.repositories.device_repository import DeviceRepository


class DeviceService:

    def __init__(
        self,
        repository: DeviceRepository,
    ):
        self.repository = repository

    @staticmethod
    def generate_device_token() -> str:
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_device_token(token: str) -> str:
        return hashlib.sha256(
            token.encode("utf-8")
        ).hexdigest()

    def register_device(
        self,
        user_id: uuid.UUID,
        device_name: str,
        operating_system: str | None = None,
        browser: str | None = None,
    ) -> tuple[Device, str]:

        device_name = device_name.strip()

        if not device_name:
            raise ValueError("Device name cannot be empty.")

        token = self.generate_device_token()
        token_hash = self.hash_device_token(token)

        device = Device(
            user_id=user_id,
            device_name=device_name,
            operating_system=operating_system,
            browser=browser,
            device_token_hash=token_hash,
            is_trusted=False,
            is_active=True,
        )

        self.repository.add(device)
        self.repository.flush()

        return device, token

    def identify_device(
        self,
        user_id: uuid.UUID,
        token: str,
    ) -> Device | None:

        if not token or len(token) > 512:
            return None

        token_hash = self.hash_device_token(token)

        device = self.repository.get_by_token_hash(token_hash)

        if (
            device is None
            or device.user_id != user_id
            or not device.is_active
        ):
            return None

        self.repository.update_last_seen(device.id)
        self.repository.flush()

        return device

    def get_user_devices(
        self,
        user_id: uuid.UUID,
    ) -> list[Device]:

        return self.repository.get_user_devices(user_id)

    def revoke_device(
        self,
        user_id: uuid.UUID,
        device_id: uuid.UUID,
    ) -> bool:

        device = self.repository.get_by_id(device_id)

        if device is None or device.user_id != user_id:
            return False

        if not device.is_active:
            return False

        return self.repository.revoke(device_id)

    def set_device_trust(
        self,
        user_id: uuid.UUID,
        device_id: uuid.UUID,
        is_trusted: bool,
    ) -> bool:

        device = self.repository.get_by_id(device_id)

        if device is None or device.user_id != user_id:
            return False

        if not device.is_active:
            return False

        return self.repository.set_trusted(
            device_id=device_id,
            is_trusted=is_trusted,
        )