import uuid

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.privileged_access_grant import PrivilegedAccessGrant
from app.models.privileged_access_request import PrivilegedAccessRequest


class PrivilegedAccessRepository:
    def __init__(self, db: Session):
        self.db = db

    # --------------------------------------------------
    # PRIVILEGED ACCESS REQUESTS
    # --------------------------------------------------

    def get_request_by_id(
        self,
        request_id: uuid.UUID,
    ) -> PrivilegedAccessRequest | None:
        statement = select(PrivilegedAccessRequest).where(
            PrivilegedAccessRequest.id == request_id
        )
        return self.db.scalar(statement)

    def get_user_requests(
        self,
        user_id: uuid.UUID,
        offset: int = 0,
        limit: int = 100,
    ) -> list[PrivilegedAccessRequest]:
        statement = (
            select(PrivilegedAccessRequest)
            .where(PrivilegedAccessRequest.user_id == user_id)
            .order_by(PrivilegedAccessRequest.requested_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def get_pending_requests(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> list[PrivilegedAccessRequest]:
        statement = (
            select(PrivilegedAccessRequest)
            .where(PrivilegedAccessRequest.status == "PENDING")
            .order_by(PrivilegedAccessRequest.requested_at.asc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def add_request(
        self,
        request: PrivilegedAccessRequest,
    ) -> PrivilegedAccessRequest:
        self.db.add(request)
        return request

    def review_request(
        self,
        request_id: uuid.UUID,
        reviewer_id: uuid.UUID,
        status: str,
        approval_reason: str,
    ) -> bool:
        if status not in {"APPROVED", "DENIED"}:
            raise ValueError("Review status must be APPROVED or DENIED.")

        statement = (
            update(PrivilegedAccessRequest)
            .where(
                PrivilegedAccessRequest.id == request_id,
                PrivilegedAccessRequest.status == "PENDING",
                PrivilegedAccessRequest.user_id != reviewer_id,
            )
            .values(
                status=status,
                approved_by_user_id=reviewer_id,
                approval_reason=approval_reason,
                reviewed_at=func.now(),
            )
            .execution_options(synchronize_session=False)
        )

        result = self.db.execute(statement)
        return result.rowcount == 1

    # --------------------------------------------------
    # PRIVILEGED ACCESS GRANTS
    # --------------------------------------------------

    def get_grant_by_id(
        self,
        grant_id: uuid.UUID,
    ) -> PrivilegedAccessGrant | None:
        statement = select(PrivilegedAccessGrant).where(
            PrivilegedAccessGrant.id == grant_id
        )
        return self.db.scalar(statement)

    def get_grant_by_request(
        self,
        request_id: uuid.UUID,
    ) -> PrivilegedAccessGrant | None:
        statement = select(PrivilegedAccessGrant).where(
            PrivilegedAccessGrant.request_id == request_id
        )
        return self.db.scalar(statement)

    def get_user_grants(
        self,
        user_id: uuid.UUID,
        offset: int = 0,
        limit: int = 100,
    ) -> list[PrivilegedAccessGrant]:
        statement = (
            select(PrivilegedAccessGrant)
            .where(PrivilegedAccessGrant.user_id == user_id)
            .order_by(PrivilegedAccessGrant.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def get_active_grants(
        self,
        user_id: uuid.UUID,
    ) -> list[PrivilegedAccessGrant]:
        statement = (
            select(PrivilegedAccessGrant)
            .where(
                PrivilegedAccessGrant.user_id == user_id,
                PrivilegedAccessGrant.status == "ACTIVE",
                PrivilegedAccessGrant.starts_at <= func.now(),
                PrivilegedAccessGrant.expires_at > func.now(),
            )
            .order_by(PrivilegedAccessGrant.expires_at.asc())
        )
        return list(self.db.scalars(statement).all())

    def add_grant(
        self,
        grant: PrivilegedAccessGrant,
    ) -> PrivilegedAccessGrant:
        self.db.add(grant)
        return grant

    def revoke_grant(
        self,
        grant_id: uuid.UUID,
        reason: str,
    ) -> bool:
        statement = (
            update(PrivilegedAccessGrant)
            .where(
                PrivilegedAccessGrant.id == grant_id,
                PrivilegedAccessGrant.status == "ACTIVE",
                PrivilegedAccessGrant.expires_at > func.now(),
            )
            .values(
                status="REVOKED",
                revoked_at=func.now(),
                revocation_reason=reason,
            )
            .execution_options(synchronize_session=False)
        )

        result = self.db.execute(statement)
        return result.rowcount == 1

    def expire_grants(self) -> int:
        statement = (
            update(PrivilegedAccessGrant)
            .where(
                PrivilegedAccessGrant.status == "ACTIVE",
                PrivilegedAccessGrant.expires_at <= func.now(),
            )
            .values(status="EXPIRED")
            .execution_options(synchronize_session=False)
        )

        result = self.db.execute(statement)
        return result.rowcount

    def flush(self) -> None:
        self.db.flush()