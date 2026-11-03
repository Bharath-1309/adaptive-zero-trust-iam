import uuid

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.device import Device


class DeviceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, device_id: uuid.UUID) -> Device | None:
        statement = select(Device).where(Device.id == device_id)
        return self.db.scalar(statement)

    def get_by_token_hash(self, token_hash: str) -> Device | None:
        statement = select(Device).where(
            Device.device_token_hash == token_hash
        )
        return self.db.scalar(statement)

    def get_user_devices(
        self,
        user_id: uuid.UUID,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Device]:
        statement = (
            select(Device)
            .where(Device.user_id == user_id)
            .order_by(
                Device.last_seen_at.desc().nullslast(),
                Device.created_at.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def get_active_devices(
        self,
        user_id: uuid.UUID,
    ) -> list[Device]:
        statement = (
            select(Device)
            .where(
                Device.user_id == user_id,
                Device.is_active.is_(True),
            )
            .order_by(Device.created_at.desc())
        )
        return list(self.db.scalars(statement).all())

    def add(self, device: Device) -> Device:
        self.db.add(device)
        return device

    def update_last_seen(self, device_id: uuid.UUID) -> bool:
        statement = (
            update(Device)
            .where(
                Device.id == device_id,
                Device.is_active.is_(True),
            )
            .values(last_seen_at=func.now())
        )
        result = self.db.execute(statement)
        return result.rowcount == 1

    def set_trusted(
        self,
        device_id: uuid.UUID,
        is_trusted: bool,
    ) -> bool:
        statement = (
            update(Device)
            .where(
                Device.id == device_id,
                Device.is_active.is_(True),
            )
            .values(is_trusted=is_trusted)
        )
        result = self.db.execute(statement)
        return result.rowcount == 1

    def revoke(self, device_id: uuid.UUID) -> bool:
        statement = (
            update(Device)
            .where(
                Device.id == device_id,
                Device.is_active.is_(True),
            )
            .values(
                is_active=False,
                is_trusted=False,
                revoked_at=func.now(),
            )
        )
        result = self.db.execute(statement)
        return result.rowcount == 1

    def flush(self) -> None:
        self.db.flush()