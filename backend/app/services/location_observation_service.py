from datetime import datetime, timezone
from decimal import Decimal
from math import isfinite
import uuid

from sqlalchemy.orm import Session

from app.models.location_observation import LocationObservation
from app.repositories.location_observation_repository import (
    LocationObservationRepository,
)
from app.services.audit_service import AuditService
from app.services.geolocation_service import GeolocationService
from app.services.reverse_geocoding_service import (
    ReverseGeocodingService,
)


class LocationObservationService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = LocationObservationRepository(db)
        self.audit_service = AuditService(db)
        self.reverse_geocoder = ReverseGeocodingService()

    def record_location_permission_event(
        self,
        user_id: uuid.UUID,
        outcome: str,
        reason: str | None = None,
    ) -> None:

        event_mapping = {
            "GRANTED": (
                "BROWSER_LOCATION_PERMISSION_GRANTED",
                "SUCCESS",
            ),
            "DENIED": (
                "BROWSER_LOCATION_PERMISSION_DENIED",
                "DENIED",
            ),
            "UNAVAILABLE": (
                "BROWSER_LOCATION_UNAVAILABLE",
                "UNAVAILABLE",
            ),
        }

        if outcome not in event_mapping:
            raise ValueError("Invalid location permission outcome.")

        event_type, audit_outcome = event_mapping[outcome]

        self.audit_service.record_event(
            actor_user_id=user_id,
            event_type=event_type,
            action="location.browser_permission",
            resource_type="location_permission",
            outcome=audit_outcome,
            details={
                "permission_outcome": outcome,
                "reason": reason,
                "location_source": "BROWSER_GPS",
            },
        )    

    def record_ip_location(
        self,
        user_id: uuid.UUID,
        ip_address: str,
        login_event_id: uuid.UUID | None = None,
    ) -> LocationObservation | None:

        try:
            with GeolocationService() as geolocation:
                location = geolocation.lookup(ip_address)

        except (ValueError, RuntimeError, OSError):
            return None

        if location is None:
            return None

        observation = LocationObservation(
            user_id=user_id,
            login_event_id=login_event_id,
            source="IP_GEOIP",
            country_code=location.get("country_code"),
            country_name=location.get("country_name"),
            region=location.get("region"),
            city=location.get("city"),
            latitude=location.get("latitude"),
            longitude=location.get("longitude"),
            accuracy_meters=location.get("accuracy_meters"),
            consent_granted=False,
            consent_recorded_at=None,
        )

        self.repository.add(observation)
        self.repository.flush()

        self.audit_service.record_event(
            actor_user_id=user_id,
            event_type="IP_LOCATION_OBSERVED",
            action="location.ip_observed",
            resource_type="location_observation",
            resource_id=str(observation.id),
            outcome="SUCCESS",
            details={
                "city": observation.city,
                "region": observation.region,
                "country": observation.country_name,
                "country_code": observation.country_code,
                "location_source": "IP_GEOIP",
                "location_observation_id": str(observation.id),
            },
        )

        return observation

    def record_browser_gps(
        self,
        user_id: uuid.UUID,
        latitude: float,
        longitude: float,
        accuracy_meters: float,
        consent_granted: bool,
        login_event_id: uuid.UUID | None = None,
    ) -> LocationObservation:

        if consent_granted is not True:
            raise ValueError(
                "Explicit location consent is required."
            )

        values = [latitude, longitude, accuracy_meters]

        if not all(isfinite(value) for value in values):
            raise ValueError(
                "GPS values must be finite numbers."
            )

        if not -90 <= latitude <= 90:
            raise ValueError(
                "Latitude must be between -90 and 90."
            )

        if not -180 <= longitude <= 180:
            raise ValueError(
                "Longitude must be between -180 and 180."
            )

        if accuracy_meters < 0:
            raise ValueError(
                "GPS accuracy cannot be negative."
            )

        location_details = self.reverse_geocoder.reverse_lookup(
            latitude,
            longitude,
        )

        location_details = location_details or {}

        observation = LocationObservation(
            user_id=user_id,
            login_event_id=login_event_id,
            source="BROWSER_GPS",
            country_code=location_details.get("country_code"),
            country_name=location_details.get("country_name"),
            region=location_details.get("region"),
            city=location_details.get("city"),
            latitude=Decimal(str(latitude)),
            longitude=Decimal(str(longitude)),
            accuracy_meters=Decimal(str(accuracy_meters)),
            consent_granted=True,
            consent_recorded_at=datetime.now(timezone.utc),
        )

        self.repository.add(observation)
        self.repository.flush()

        self.audit_service.record_event(
            actor_user_id=user_id,
            event_type="BROWSER_LOCATION_CAPTURED",
            action="location.browser_gps_captured",
            resource_type="location_observation",
            resource_id=str(observation.id),
            outcome="SUCCESS",
            details={
                "city": observation.city,
                "region": observation.region,
                "country": observation.country_name,
                "country_code": observation.country_code,
                "location_source": "BROWSER_GPS",
                "accuracy_meters": float(accuracy_meters),
                "location_observation_id": str(observation.id),
                "reverse_geocoding_available": bool(
                    location_details
                ),
            },
        )

        return observation