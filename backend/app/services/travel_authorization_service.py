from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.travel_authorization import TravelAuthorization
from app.repositories.travel_authorization_repository import (
    TravelAuthorizationRepository,
)
from app.schemas.travel_authorization import TravelAuthorizationCreate
from app.services.audit_service import AuditService


class TravelAuthorizationService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = TravelAuthorizationRepository(db)
        self.audit_service = AuditService(db)

    def create_request(
        self,
        user_id: UUID,
        data: TravelAuthorizationCreate,
    ) -> TravelAuthorization:

        current_time = datetime.now(timezone.utc)

        if data.starts_at < current_time:
            raise ValueError("Travel start time cannot be in the past.")

        if data.expires_at <= data.starts_at:
            raise ValueError("Travel expiry must be after the start time.")

        authorization = TravelAuthorization(
            user_id=user_id,
            destination=data.destination,
            justification=data.justification,
            starts_at=data.starts_at,
            expires_at=data.expires_at,
            status="PENDING",
        )

        authorization = self.repository.add(authorization)

        self.audit_service.record_event(
            event_type="TRAVEL_AUTHORIZATION_CREATED",
            action="CREATE",
            resource_type="TRAVEL_AUTHORIZATION",
            resource_id=str(authorization.id),
            outcome="SUCCESS",
            actor_user_id=user_id,
            details={
                "destination": authorization.destination,
                "justification": authorization.justification,
                "starts_at": authorization.starts_at.isoformat(),
                "expires_at": authorization.expires_at.isoformat(),
                "status": authorization.status,
            },
        )

        return authorization

    def get_request(
        self,
        authorization_id: UUID,
    ) -> TravelAuthorization | None:

        return self.repository.get_by_id(authorization_id)

    def get_user_requests(
        self,
        user_id: UUID,
    ) -> list[TravelAuthorization]:

        self.expire_authorizations()
        return self.repository.get_user_authorizations(user_id)

    def get_pending_requests(self) -> list[TravelAuthorization]:

        self.expire_authorizations()
        return self.repository.get_pending_authorizations()

    def review_request(
        self,
        authorization_id: UUID,
        reviewer_id: UUID,
        status: str,
        reason: str,
    ) -> TravelAuthorization:

        authorization = self.repository.get_by_id(authorization_id)

        if authorization is None:
            raise ValueError("Travel authorization request not found.")

        if authorization.status != "PENDING":
            raise ValueError("Only pending requests can be reviewed.")

        if authorization.user_id == reviewer_id:
            raise ValueError("Users cannot review their own travel requests.")

        if status not in {"APPROVED", "DENIED"}:
            raise ValueError("Invalid review status.")

        if not reason.strip():
            raise ValueError("A review reason is required.")

        if status == "APPROVED":
            current_time = datetime.now(timezone.utc)

            if authorization.expires_at <= current_time:
                raise ValueError(
                    "Cannot approve a travel request that has already expired."
                )

        authorization = self.repository.review(
            authorization=authorization,
            reviewer_id=reviewer_id,
            status=status,
            reason=reason.strip(),
        )

        event_type = (
            "TRAVEL_AUTHORIZATION_APPROVED"
            if status == "APPROVED"
            else "TRAVEL_AUTHORIZATION_DENIED"
        )

        self.audit_service.record_event(
            event_type=event_type,
            action="REVIEW",
            resource_type="TRAVEL_AUTHORIZATION",
            resource_id=str(authorization.id),
            outcome="SUCCESS",
            actor_user_id=reviewer_id,
            details={
                "applicant_user_id": str(authorization.user_id),
                "reviewer_user_id": str(reviewer_id),
                "destination": authorization.destination,
                "status": authorization.status,
                "reason": reason.strip(),
            },
        )

        return authorization

    def revoke_request(
        self,
        authorization_id: UUID,
        reviewer_id: UUID,
        reason: str,
    ) -> TravelAuthorization:

        authorization = self.repository.get_by_id(authorization_id)

        if authorization is None:
            raise ValueError("Travel authorization request not found.")

        if authorization.status != "APPROVED":
            raise ValueError(
                "Only approved travel authorizations can be revoked."
            )

        if not reason.strip():
            raise ValueError("A revocation reason is required.")

        authorization = self.repository.revoke(
            authorization=authorization,
            reason=reason.strip(),
        )

        self.audit_service.record_event(
            event_type="TRAVEL_AUTHORIZATION_REVOKED",
            action="REVOKE",
            resource_type="TRAVEL_AUTHORIZATION",
            resource_id=str(authorization.id),
            outcome="SUCCESS",
            actor_user_id=reviewer_id,
            details={
                "applicant_user_id": str(authorization.user_id),
                "revoked_by_user_id": str(reviewer_id),
                "destination": authorization.destination,
                "status": authorization.status,
                "reason": reason.strip(),
            },
        )

        return authorization

    def expire_authorizations(self) -> int:

        expired_authorizations = (
            self.repository.get_expired_authorizations()
        )

        if not expired_authorizations:
            return 0

        expired_count = self.repository.expire_authorizations()

        for authorization in expired_authorizations:
            self.audit_service.record_event(
                event_type="TRAVEL_AUTHORIZATION_EXPIRED",
                action="EXPIRE",
                resource_type="TRAVEL_AUTHORIZATION",
                resource_id=str(authorization.id),
                outcome="SUCCESS",
                actor_user_id=None,
                details={
                    "applicant_user_id": str(authorization.user_id),
                    "destination": authorization.destination,
                    "status": "EXPIRED",
                    "expires_at": authorization.expires_at.isoformat(),
                },
            )

        return expired_count