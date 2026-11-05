import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, audit_id: uuid.UUID) -> AuditLog | None:
        statement = select(AuditLog).where(
            AuditLog.id == audit_id
        )
        return self.db.scalar(statement)

    def get_by_actor(
        self,
        actor_user_id: uuid.UUID,
        offset: int = 0,
        limit: int = 100,
    ) -> list[AuditLog]:
        statement = (
            select(AuditLog)
            .where(AuditLog.actor_user_id == actor_user_id)
            .order_by(AuditLog.occurred_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def get_by_event_type(
        self,
        event_type: str,
        offset: int = 0,
        limit: int = 100,
    ) -> list[AuditLog]:
        statement = (
            select(AuditLog)
            .where(AuditLog.event_type == event_type)
            .order_by(AuditLog.occurred_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def get_by_action(
        self,
        action: str,
        offset: int = 0,
        limit: int = 100,
    ) -> list[AuditLog]:
        statement = (
            select(AuditLog)
            .where(AuditLog.action == action)
            .order_by(AuditLog.occurred_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def get_all(
        self,
        offset: int = 0,
        limit: int = 50,
        event_type: str | None = None,
        outcome: str | None = None,
    ) -> list[AuditLog]:

        statement = select(AuditLog)

        if event_type:
            statement = statement.where(
                AuditLog.event_type == event_type
            )

        if outcome:
            statement = statement.where(
                AuditLog.outcome == outcome
            )

        statement = (
            statement
            .order_by(AuditLog.occurred_at.desc())
            .offset(offset)
            .limit(limit)
        )

        return list(self.db.scalars(statement).all())

    def get_by_outcome(
        self,
        outcome: str,
        offset: int = 0,
        limit: int = 100,
    ) -> list[AuditLog]:
        statement = (
            select(AuditLog)
            .where(AuditLog.outcome == outcome)
            .order_by(AuditLog.occurred_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def get_by_request_id(
        self,
        request_id: uuid.UUID,
    ) -> list[AuditLog]:
        statement = (
            select(AuditLog)
            .where(AuditLog.request_id == request_id)
            .order_by(AuditLog.occurred_at.asc())
        )
        return list(self.db.scalars(statement).all())

    def get_by_date_range(
        self,
        start_time: datetime,
        end_time: datetime,
        offset: int = 0,
        limit: int = 100,
    ) -> list[AuditLog]:
        if start_time >= end_time:
            raise ValueError("Start time must be earlier than end time.")

        statement = (
            select(AuditLog)
            .where(
                AuditLog.occurred_at >= start_time,
                AuditLog.occurred_at < end_time,
            )
            .order_by(AuditLog.occurred_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def add(self, audit_log: AuditLog) -> AuditLog:
        self.db.add(audit_log)
        return audit_log

    def flush(self) -> None:
        self.db.flush()