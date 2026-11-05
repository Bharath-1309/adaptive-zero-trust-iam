import uuid
from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.office_geofence import OfficeGeofence


class OfficeGeofenceRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        geofence_id: uuid.UUID,
    ) -> OfficeGeofence | None:
        return self.db.get(OfficeGeofence, geofence_id)

    def get_by_name(
        self,
        name: str,
    ) -> OfficeGeofence | None:
        statement = select(OfficeGeofence).where(
            OfficeGeofence.name == name
        )

        return self.db.scalar(statement)

    def get_all(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> list[OfficeGeofence]:
        statement = (
            select(OfficeGeofence)
            .order_by(OfficeGeofence.name.asc())
            .offset(offset)
            .limit(limit)
        )

        return list(self.db.scalars(statement).all())

    def get_active_geofences(self) -> list[OfficeGeofence]:
        current_time = datetime.now(timezone.utc)

        statement = (
            select(OfficeGeofence)
            .where(
                OfficeGeofence.is_active.is_(True),
                or_(
                    OfficeGeofence.location_type == "PERMANENT",
                    (
                        (OfficeGeofence.location_type == "TEMPORARY")
                        & (OfficeGeofence.expires_at > current_time)
                    ),
                ),
            )
            .order_by(OfficeGeofence.name.asc())
        )

        return list(self.db.scalars(statement).all())

    def add(
        self,
        geofence: OfficeGeofence,
    ) -> OfficeGeofence:
        self.db.add(geofence)
        return geofence

    def flush(self) -> None:
        self.db.flush()