import uuid

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.step_up_challenge import StepUpChallenge


class StepUpChallengeRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        challenge_id: uuid.UUID,
    ) -> StepUpChallenge | None:
        statement = select(StepUpChallenge).where(
            StepUpChallenge.id == challenge_id
        )
        return self.db.scalar(statement)

    def get_by_hash(self, challenge_hash: str) -> StepUpChallenge | None:
        statement = select(StepUpChallenge).where(
            StepUpChallenge.challenge_hash == challenge_hash
        )
        return self.db.scalar(statement)

    def get_by_access_decision(
        self,
        access_decision_id: uuid.UUID,
    ) -> StepUpChallenge | None:
        statement = select(StepUpChallenge).where(
            StepUpChallenge.access_decision_id == access_decision_id
        )
        return self.db.scalar(statement)

    def add(self, challenge: StepUpChallenge) -> StepUpChallenge:
        self.db.add(challenge)
        return challenge

    def mark_verified(self, challenge_id: uuid.UUID) -> bool:
        statement = (
            update(StepUpChallenge)
            .where(
                StepUpChallenge.id == challenge_id,
                StepUpChallenge.status == "PENDING",
                StepUpChallenge.expires_at > func.now(),
            )
            .values(
                status="VERIFIED",
                verified_at=func.now(),
            )
            .execution_options(synchronize_session=False)
        )

        result = self.db.execute(statement)
        return result.rowcount == 1

    def consume(self, challenge_id: uuid.UUID) -> bool:
        statement = (
            update(StepUpChallenge)
            .where(
                StepUpChallenge.id == challenge_id,
                StepUpChallenge.status == "VERIFIED",
                StepUpChallenge.expires_at > func.now(),
                StepUpChallenge.consumed_at.is_(None),
            )
            .values(
                status="CONSUMED",
                consumed_at=func.now(),
            )
            .execution_options(synchronize_session=False)
        )

        result = self.db.execute(statement)
        return result.rowcount == 1

    def increment_failed_attempts(
        self,
        challenge_id: uuid.UUID,
        max_attempts: int,
    ) -> bool:
        if max_attempts < 1:
            raise ValueError("Maximum attempts must be at least 1.")

        statement = (
            update(StepUpChallenge)
            .where(
                StepUpChallenge.id == challenge_id,
                StepUpChallenge.status == "PENDING",
                StepUpChallenge.expires_at > func.now(),
            )
            .values(
                failed_attempts=StepUpChallenge.failed_attempts + 1,
            )
            .returning(StepUpChallenge.failed_attempts)
            .execution_options(synchronize_session=False)
        )

        failed_attempts = self.db.execute(
            statement
        ).scalar_one_or_none()

        if failed_attempts is None:
            return False

        if failed_attempts >= max_attempts:
            failure_statement = (
                update(StepUpChallenge)
                .where(
                    StepUpChallenge.id == challenge_id,
                    StepUpChallenge.status == "PENDING",
                )
                .values(status="FAILED")
                .execution_options(synchronize_session=False)
            )

            self.db.execute(failure_statement)

        return True

    def expire_challenges(self) -> int:
        statement = (
            update(StepUpChallenge)
            .where(
                StepUpChallenge.status.in_(["PENDING", "VERIFIED"]),
                StepUpChallenge.expires_at <= func.now(),
            )
            .values(status="EXPIRED")
            .execution_options(synchronize_session=False)
        )

        result = self.db.execute(statement)
        return result.rowcount

    def revoke(self, challenge_id: uuid.UUID) -> bool:
        statement = (
            update(StepUpChallenge)
            .where(
                StepUpChallenge.id == challenge_id,
                StepUpChallenge.status.in_(["PENDING", "VERIFIED"]),
            )
            .values(status="REVOKED")
            .execution_options(synchronize_session=False)
        )

        result = self.db.execute(statement)
        return result.rowcount == 1

    def flush(self) -> None:
        self.db.flush()