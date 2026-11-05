from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.vpn_session_repository import (
    VPNSessionRepository,
)


class VPNVerificationService:

    def __init__(self, db: Session):
        self.repository = VPNSessionRepository(db)

    def verify_session(
        self,
        user_id: UUID,
        device_id: UUID | None,
    ) -> bool:
        """
        Verify that the user has an active VPN session
        associated with the specified device.

        A database session alone does not prove that it
        originated from a genuine corporate VPN gateway.
        Trusted gateway integration is required before
        sessions can be created and accepted.
        """

        if device_id is None:
            return False

        session = self.repository.get_active_session(
            user_id=user_id,
            device_id=device_id,
        )

        return session is not None