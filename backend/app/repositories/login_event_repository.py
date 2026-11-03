import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.login_event import LoginEvent


class LoginEventRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, event_id: uuid.UUID) -> LoginEvent | None:
        statement = select(LoginEvent).where(
            LoginEvent.id == event_id
        )
        return self.db.scalar(statement)

    def get_user_events(
        self,
        user_id: uuid.UUID,
        offset: int = 0,
        limit: int = 100,
    ) -> list[LoginEvent]:
        statement = (
            select(LoginEvent)
            .where(LoginEvent.user_id == user_id)
            .order_by(LoginEvent.occurred_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def get_device_events(
        self,
        device_id: uuid.UUID,
        offset: int = 0,
        limit: int = 100,
    ) -> list[LoginEvent]:
        statement = (
            select(LoginEvent)
            .where(LoginEvent.device_id == device_id)
            .order_by(LoginEvent.occurred_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def get_by_event_type(
        self,
        event_type: str,
        offset: int = 0,
        limit: int = 100,
    ) -> list[LoginEvent]:
        statement = (
            select(LoginEvent)
            .where(LoginEvent.event_type == event_type)
            .order_by(LoginEvent.occurred_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def add(self, event: LoginEvent) -> LoginEvent:
        self.db.add(event)
        return event

    def flush(self) -> None:
        self.db.flush()