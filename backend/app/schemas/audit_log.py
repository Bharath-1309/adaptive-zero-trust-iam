from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: UUID
    actor_user_id: UUID | None
    actor_email: str | None
    actor_name: str | None

    event_type: str
    action: str
    resource_type: str
    resource_id: str | None
    outcome: str

    city: str | None
    region: str | None
    country: str | None
    location_source: str | None

    occurred_at: datetime