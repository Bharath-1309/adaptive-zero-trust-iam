import math
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.models.location_observation import LocationObservation
from app.models.office_geofence import OfficeGeofence


class GeofenceEvaluator:

    EARTH_RADIUS_METERS = 6_371_000
    MAX_LOCATION_AGE_MINUTES = 5

    @staticmethod
    def calculate_distance(
        latitude1: float,
        longitude1: float,
        latitude2: float,
        longitude2: float,
    ) -> float:

        lat1 = math.radians(latitude1)
        lon1 = math.radians(longitude1)

        lat2 = math.radians(latitude2)
        lon2 = math.radians(longitude2)

        delta_lat = lat2 - lat1
        delta_lon = lon2 - lon1

        a = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1)
            * math.cos(lat2)
            * math.sin(delta_lon / 2) ** 2
        )

        a = min(1.0, max(0.0, a))

        central_angle = 2 * math.atan2(
            math.sqrt(a),
            math.sqrt(1 - a),
        )

        return GeofenceEvaluator.EARTH_RADIUS_METERS * central_angle

    def evaluate(
        self,
        location: LocationObservation | None,
        geofence: OfficeGeofence,
    ) -> dict:

        if not geofence.is_active:
            return {
                "status": "UNAVAILABLE",
                "reason": "Office geofence is inactive.",
                "distance_meters": None,
            }

        if location is None:
            return {
                "status": "UNAVAILABLE",
                "reason": "No location observation is available.",
                "distance_meters": None,
            }

        if location.source != "BROWSER_GPS":
            return {
                "status": "UNAVAILABLE",
                "reason": "Browser GPS verification is required.",
                "distance_meters": None,
            }

        if not location.consent_granted:
            return {
                "status": "UNAVAILABLE",
                "reason": "Location consent was not granted.",
                "distance_meters": None,
            }

        if (
            location.latitude is None
            or location.longitude is None
            or location.accuracy_meters is None
        ):
            return {
                "status": "UNAVAILABLE",
                "reason": "GPS coordinates or accuracy are missing.",
                "distance_meters": None,
            }

        observed_at = location.observed_at

        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(
                tzinfo=timezone.utc
            )

        current_time = datetime.now(timezone.utc)

        if (
            current_time - observed_at
            > timedelta(minutes=self.MAX_LOCATION_AGE_MINUTES)
        ):
            return {
                "status": "UNAVAILABLE",
                "reason": "GPS observation is too old.",
                "distance_meters": None,
            }

        accuracy = float(location.accuracy_meters)
        maximum_accuracy = float(geofence.max_accuracy_meters)

        if accuracy <= 0 or accuracy > maximum_accuracy:
            return {
                "status": "UNAVAILABLE",
                "reason": "GPS accuracy is insufficient.",
                "distance_meters": None,
            }

        distance = self.calculate_distance(
            float(location.latitude),
            float(location.longitude),
            float(geofence.latitude),
            float(geofence.longitude),
        )

        radius = float(geofence.radius_meters)

        # Only classify as INSIDE when the entire reported
        # accuracy range fits within the permitted radius.
        if distance + accuracy <= radius:
            result = "INSIDE"
            reason = "Location is confidently inside the office boundary."

        elif distance - accuracy > radius:
            result = "OUTSIDE"
            reason = "Location is confidently outside the office boundary."

        else:
            result = "UNCERTAIN"
            reason = "GPS accuracy overlaps the office boundary."

        return {
            "status": result,
            "reason": reason,
            "distance_meters": round(distance, 2),
            "accuracy_meters": round(accuracy, 2),
            "radius_meters": radius,
        }