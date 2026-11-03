import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.location_observation import LocationObservation


class LocationObservationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        observation_id: uuid.UUID,
    ) -> LocationObservation | None:
        statement = select(LocationObservation).where(
            LocationObservation.id == observation_id
        )
        return self.db.scalar(statement)

    def get_user_observations(
        self,
        user_id: uuid.UUID,
        offset: int = 0,
        limit: int = 100,
    ) -> list[LocationObservation]:
        statement = (
            select(LocationObservation)
            .where(LocationObservation.user_id == user_id)
            .order_by(LocationObservation.observed_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def get_login_observations(
        self,
        login_event_id: uuid.UUID,
    ) -> list[LocationObservation]:
        statement = (
            select(LocationObservation)
            .where(
                LocationObservation.login_event_id == login_event_id
            )
            .order_by(LocationObservation.observed_at.desc())
        )
        return list(self.db.scalars(statement).all())

    def get_by_source(
        self,
        user_id: uuid.UUID,
        source: str,
        offset: int = 0,
        limit: int = 100,
    ) -> list[LocationObservation]:
        statement = (
            select(LocationObservation)
            .where(
                LocationObservation.user_id == user_id,
                LocationObservation.source == source,
            )
            .order_by(LocationObservation.observed_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def get_latest_observation(
        self,
        user_id: uuid.UUID,
    ) -> LocationObservation | None:
        statement = (
            select(LocationObservation)
            .where(LocationObservation.user_id == user_id)
            .order_by(LocationObservation.observed_at.desc())
            .limit(1)
        )
        return self.db.scalar(statement)

    def add(
        self,
        observation: LocationObservation,
    ) -> LocationObservation:
        self.db.add(observation)
        return observation

    def flush(self) -> None:
        self.db.flush()