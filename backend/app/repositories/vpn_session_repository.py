import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.vpn_session import VPNSession


class VPNSessionRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        session_id: uuid.UUID,
    ) -> VPNSession | None:
        return self.db.scalar(
            select(VPNSession).where(
                VPNSession.id == session_id
            )
        )

    def get_active_session(
        self,
        user_id: uuid.UUID,
        device_id: uuid.UUID,
    ) -> VPNSession | None:
        current_time = datetime.now(timezone.utc)

        return self.db.scalar(
            select(VPNSession)
            .where(
                VPNSession.user_id == user_id,
                VPNSession.device_id == device_id,
                VPNSession.status == "ACTIVE",
                VPNSession.started_at <= current_time,
                VPNSession.expires_at > current_time,
            )
            .order_by(VPNSession.expires_at.desc())
        )

    def add(self, vpn_session: VPNSession) -> VPNSession:
        self.db.add(vpn_session)
        self.db.flush()
        return vpn_session

    def revoke(
        self,
        vpn_session: VPNSession,
    ) -> VPNSession:
        vpn_session.status = "REVOKED"
        self.db.flush()
        return vpn_session

    def expire_sessions(self) -> int:
        current_time = datetime.now(timezone.utc)

        sessions = self.db.scalars(
            select(VPNSession).where(
                VPNSession.status == "ACTIVE",
                VPNSession.expires_at <= current_time,
            )
        ).all()

        for vpn_session in sessions:
            vpn_session.status = "EXPIRED"

        self.db.flush()
        return len(sessions)