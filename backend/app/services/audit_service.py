from typing import Any
import uuid

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.repositories.audit_log_repository import AuditLogRepository


class AuditService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = AuditLogRepository(db)

    def record_event(
        self,
        event_type: str,
        action: str,
        resource_type: str,
        outcome: str,
        actor_user_id: uuid.UUID | None = None,
        resource_id: str | None = None,
        request_id: uuid.UUID | None = None,
        details: dict[str, Any] | None = None,
        city: str | None = None,
        region: str | None = None,
        country: str | None = None,
        location_source: str | None = None,
    ) -> AuditLog:

        event_details = dict(details or {})

        if any(
            value is not None
            for value in (city, region, country, location_source)
        ):
            event_details["location"] = {
                "city": city,
                "region": region,
                "country": country,
                "source": location_source,
            }

        audit_event = AuditLog(
            actor_user_id=actor_user_id,
            event_type=event_type,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome,
            request_id=request_id,
            details=event_details,
        )

        self.repository.add(audit_event)
        self.repository.flush()

        return audit_event