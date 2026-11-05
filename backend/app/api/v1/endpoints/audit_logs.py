from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.audit_log import AuditLogResponse
from app.security.authorization import require_permission


router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Logs"],
)


@router.get("/", response_model=list[AuditLogResponse])
def get_audit_logs(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_permission("audit:read")),
    ],
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    event_type: str | None = Query(None, min_length=1, max_length=100),
    outcome: str | None = Query(None, min_length=1, max_length=30),
):
    repository = AuditLogRepository(db)

    audit_logs = repository.get_all(
        offset=offset,
        limit=limit,
        event_type=event_type,
        outcome=outcome,
    )

    results = []

    for log in audit_logs:
        details = log.details or {}
        actor = log.actor

        results.append(
            AuditLogResponse(
                id=log.id,
                actor_user_id=log.actor_user_id,
                actor_email=actor.email if actor else None,
                actor_name=actor.full_name if actor else None,
                event_type=log.event_type,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                outcome=log.outcome,
                city=(
                    details.get("city")
                    or (details.get("location") or {}).get("city")
                ),
                region=(
                    details.get("region")
                    or (details.get("location") or {}).get("region")
                ),
                country=(
                    details.get("country")
                    or details.get("country_name")
                    or (details.get("location") or {}).get("country")
                ),
                location_source=(
                    details.get("location_source")
                    or (details.get("location") or {}).get("source")
                ),
                occurred_at=log.occurred_at,
            )
        )

    return results