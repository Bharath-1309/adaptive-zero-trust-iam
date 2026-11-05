from datetime import datetime, timezone
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.travel_authorization import TravelAuthorization


class TravelAuthorizationRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        authorization_id: uuid.UUID,
    ) -> TravelAuthorization | None:
        return self.db.scalar(
            select(TravelAuthorization).where(
                TravelAuthorization.id == authorization_id
            )
        )

    def get_user_authorizations(
        self,
        user_id: uuid.UUID,
    ) -> list[TravelAuthorization]:
        return list(
            self.db.scalars(
                select(TravelAuthorization)
                .where(TravelAuthorization.user_id == user_id)
                .order_by(TravelAuthorization.requested_at.desc())
            ).all()
        )

    def get_pending_authorizations(
        self,
    ) -> list[TravelAuthorization]:
        return list(
            self.db.scalars(
                select(TravelAuthorization)
                .where(TravelAuthorization.status == "PENDING")
                .order_by(TravelAuthorization.requested_at.asc())
            ).all()
        )

    def get_active_authorization(
        self,
        user_id: uuid.UUID,
        current_time: datetime | None = None,
    ) -> TravelAuthorization | None:
        if current_time is None:
            current_time = datetime.now(timezone.utc)

        return self.db.scalar(
            select(TravelAuthorization)
            .where(
                TravelAuthorization.user_id == user_id,
                TravelAuthorization.status == "APPROVED",
                TravelAuthorization.starts_at <= current_time,
                TravelAuthorization.expires_at > current_time,
            )
            .order_by(TravelAuthorization.expires_at.desc())
        )

    def add(
        self,
        authorization: TravelAuthorization,
    ) -> TravelAuthorization:
        self.db.add(authorization)
        self.db.flush()
        return authorization

    def review(
        self,
        authorization: TravelAuthorization,
        reviewer_id: uuid.UUID,
        status: str,
        reason: str | None = None,
    ) -> TravelAuthorization:
        authorization.status = status
        authorization.approved_by_user_id = reviewer_id
        authorization.approval_reason = reason
        authorization.reviewed_at = datetime.now(timezone.utc)

        self.db.flush()
        return authorization

    def revoke(
        self,
        authorization: TravelAuthorization,
        reason: str,
    ) -> TravelAuthorization:
        authorization.status = "REVOKED"
        authorization.revoked_at = datetime.now(timezone.utc)
        authorization.revocation_reason = reason

        self.db.flush()
        return authorization

    def get_expired_authorizations(
        self,
        current_time: datetime | None = None,
    ) -> list[TravelAuthorization]:
        if current_time is None:
            current_time = datetime.now(timezone.utc)

        return list(
            self.db.scalars(
                select(TravelAuthorization).where(
                    TravelAuthorization.status == "APPROVED",
                    TravelAuthorization.expires_at <= current_time,
                )
            ).all()
        )

    def expire_authorizations(
        self,
        current_time: datetime | None = None,
    ) -> int:
        expired = self.get_expired_authorizations(current_time)

        for authorization in expired:
            authorization.status = "EXPIRED"

        self.db.flush()
        return len(expired)