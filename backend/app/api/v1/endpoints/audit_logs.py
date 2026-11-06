from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
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
    actor_user_id: UUID | None = Query(None),
    request_id: UUID | None = Query(None),
    occurred_after: datetime | None = Query(None),
    occurred_before: datetime | None = Query(None),
):
    if (
        occurred_after
        and occurred_before
        and occurred_after >= occurred_before
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="occurred_after must be earlier than occurred_before.",
        )

    repository = AuditLogRepository(db)

    audit_logs = repository.get_all(
        offset=offset,
        limit=limit,
        event_type=event_type,
        outcome=outcome,
        actor_user_id=actor_user_id,
        request_id=request_id,
        occurred_after=occurred_after,
        occurred_before=occurred_before,
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
                request_id=log.request_id,
                reason=details.get("reason"),
                risk_score=details.get("risk_score"),
                token_acr=details.get("token_acr"),
                required_acr=details.get("required_acr"),
                occurred_at=log.occurred_at,
            )
        )

    return results