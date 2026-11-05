import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from app.models.office_geofence import OfficeGeofence
from app.repositories.office_geofence_repository import (
    OfficeGeofenceRepository,
)


class OfficeGeofenceService:

    def __init__(self, repository: OfficeGeofenceRepository):
        self.repository = repository

    @staticmethod
    def _to_decimal(value, field_name: str) -> Decimal:
        if isinstance(value, bool):
            raise ValueError(f"{field_name} must be a number.")

        try:
            result = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError(f"{field_name} must be a valid number.")

        if not result.is_finite():
            raise ValueError(f"{field_name} must be finite.")

        return result

    @staticmethod
    def _validate_location(
        location_type: str,
        expires_at: datetime | None,
    ) -> None:
        if location_type not in {"PERMANENT", "TEMPORARY"}:
            raise ValueError("Invalid location type.")

        if location_type == "PERMANENT" and expires_at is not None:
            raise ValueError("Permanent locations cannot have an expiry date.")

        if location_type == "TEMPORARY":
            if expires_at is None:
                raise ValueError("Temporary locations require an expiry date.")

            if expires_at.tzinfo is None:
                raise ValueError("Expiry date must include a timezone.")

            if expires_at <= datetime.now(timezone.utc):
                raise ValueError("Expiry date must be in the future.")

    @staticmethod
    def _validate_coordinates(latitude, longitude):
        if not Decimal("-90") <= latitude <= Decimal("90"):
            raise ValueError("Latitude must be between -90 and 90.")

        if not Decimal("-180") <= longitude <= Decimal("180"):
            raise ValueError("Longitude must be between -180 and 180.")

    @staticmethod
    def _validate_positive(value, field_name):
        if value <= 0:
            raise ValueError(f"{field_name} must be greater than zero.")

    def create_geofence(
        self,
        name: str,
        latitude,
        longitude,
        radius_meters,
        max_accuracy_meters,
        created_by_user_id: uuid.UUID | None = None,
        location_type: str = "PERMANENT",
        expires_at: datetime | None = None,
    ) -> OfficeGeofence:

        if not isinstance(name, str) or not name.strip():
            raise ValueError("Office name cannot be empty.")

        name = name.strip()

        if self.repository.get_by_name(name) is not None:
            raise ValueError("An office with this name already exists.")

        latitude = self._to_decimal(latitude, "Latitude")
        longitude = self._to_decimal(longitude, "Longitude")
        radius_meters = self._to_decimal(radius_meters, "Radius")
        max_accuracy_meters = self._to_decimal(
            max_accuracy_meters,
            "Maximum GPS accuracy",
        )

        self._validate_coordinates(latitude, longitude)
        self._validate_positive(radius_meters, "Radius")
        self._validate_positive(
            max_accuracy_meters,
            "Maximum GPS accuracy",
        )
        self._validate_location(location_type, expires_at)

        geofence = OfficeGeofence(
            name=name,
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters,
            max_accuracy_meters=max_accuracy_meters,
            location_type=location_type,
            expires_at=expires_at,
            is_active=True,
            created_by_user_id=created_by_user_id,
        )

        self.repository.add(geofence)
        self.repository.flush()

        return geofence

    def get_geofence(self, geofence_id: uuid.UUID) -> OfficeGeofence:
        geofence = self.repository.get_by_id(geofence_id)

        if geofence is None:
            raise LookupError("Office geofence not found.")

        return geofence

    def get_all_geofences(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> list[OfficeGeofence]:

        if offset < 0:
            raise ValueError("Offset cannot be negative.")

        if not 1 <= limit <= 100:
            raise ValueError("Limit must be between 1 and 100.")

        return self.repository.get_all(offset, limit)

    def update_geofence(
        self,
        geofence_id: uuid.UUID,
        updates: dict,
    ) -> OfficeGeofence:

        geofence = self.get_geofence(geofence_id)

        allowed_fields = {
            "name",
            "latitude",
            "longitude",
            "radius_meters",
            "max_accuracy_meters",
            "location_type",
            "expires_at",
            "is_active",
        }

        if not isinstance(updates, dict):
            raise ValueError("Updates must be provided as an object.")

        unknown_fields = set(updates) - allowed_fields

        if unknown_fields:
            raise ValueError("Unsupported geofence update fields.")

        if not updates:
            raise ValueError("At least one update is required.")

        candidate = {
            "name": geofence.name,
            "latitude": geofence.latitude,
            "longitude": geofence.longitude,
            "radius_meters": geofence.radius_meters,
            "max_accuracy_meters": geofence.max_accuracy_meters,
            "location_type": geofence.location_type,
            "expires_at": geofence.expires_at,
            "is_active": geofence.is_active,
        }

        candidate.update(updates)

        if not isinstance(candidate["name"], str):
            raise ValueError("Office name must be a string.")

        candidate["name"] = candidate["name"].strip()

        if not candidate["name"]:
            raise ValueError("Office name cannot be empty.")

        existing = self.repository.get_by_name(candidate["name"])

        if existing is not None and existing.id != geofence.id:
            raise ValueError("An office with this name already exists.")

        if not isinstance(candidate["is_active"], bool):
            raise ValueError("is_active must be a boolean.")

        candidate["latitude"] = self._to_decimal(
            candidate["latitude"], "Latitude"
        )
        candidate["longitude"] = self._to_decimal(
            candidate["longitude"], "Longitude"
        )
        candidate["radius_meters"] = self._to_decimal(
            candidate["radius_meters"], "Radius"
        )
        candidate["max_accuracy_meters"] = self._to_decimal(
            candidate["max_accuracy_meters"],
            "Maximum GPS accuracy",
        )

        self._validate_coordinates(
            candidate["latitude"],
            candidate["longitude"],
        )
        self._validate_positive(candidate["radius_meters"], "Radius")
        self._validate_positive(
            candidate["max_accuracy_meters"],
            "Maximum GPS accuracy",
        )
        self._validate_location(
            candidate["location_type"],
            candidate["expires_at"],
        )

        for field, value in candidate.items():
            setattr(geofence, field, value)

        self.repository.flush()

        return geofence

    def deactivate_geofence(
        self,
        geofence_id: uuid.UUID,
    ) -> OfficeGeofence:

        geofence = self.get_geofence(geofence_id)
        geofence.is_active = False

        self.repository.flush()

        return geofence