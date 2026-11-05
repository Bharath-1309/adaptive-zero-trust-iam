import uuid

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.risk_assessment import RiskAssessment
from app.repositories.device_repository import DeviceRepository
from app.repositories.location_observation_repository import (
    LocationObservationRepository,
)
from app.repositories.risk_assessment_repository import (
    RiskAssessmentRepository,
)


class RiskAssessmentService:

    ASSESSMENT_VERSION = "1.0"

    def __init__(self, db: Session):
        self.db = db

        self.risk_repository = RiskAssessmentRepository(db)
        self.device_repository = DeviceRepository(db)
        self.location_repository = LocationObservationRepository(db)

    @staticmethod
    def _get_risk_level(score: int) -> str:
        if score < 30:
            return "LOW"
        if score < 60:
            return "MEDIUM"
        if score < 80:
            return "HIGH"
        return "CRITICAL"

    @staticmethod
    def _evaluate_device(device) -> tuple[int, dict]:

        if device is None:
            return 25, {
                "risk": "MEDIUM",
                "reason": "Device identity could not be verified.",
            }

        if not device.is_active:
            return 100, {
                "risk": "CRITICAL",
                "reason": "Device is revoked or inactive.",
            }

        if not device.is_trusted:
            return 25, {
                "risk": "MEDIUM",
                "reason": "Device is registered but not trusted.",
            }

        return 0, {
            "risk": "LOW",
            "reason": "Device is active and trusted.",
        }

    @staticmethod
    def _evaluate_location(location) -> tuple[int, dict]:

        if location is None:
            return 40, {
                "risk": "HIGH",
                "reason": "No location observation is available.",
            }

        now = datetime.now(timezone.utc)

        observed_at = location.observed_at

        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=timezone.utc)

        age = now - observed_at

        if age > timedelta(minutes=15):
            return 30, {
                "risk": "HIGH",
                "reason": "Location observation is older than 15 minutes.",
            }

        if location.source == "IP_GEOIP":
            return 25, {
                "risk": "MEDIUM",
                "reason": "IP geolocation provides approximate location only.",
            }

        if location.source != "BROWSER_GPS":
            return 40, {
                "risk": "HIGH",
                "reason": "Location source is not recognized.",
            }

        if not location.consent_granted:
            return 40, {
                "risk": "HIGH",
                "reason": "GPS consent was not recorded.",
            }

        if location.accuracy_meters is None:
            return 35, {
                "risk": "HIGH",
                "reason": "GPS accuracy information is unavailable.",
            }

        accuracy = float(location.accuracy_meters)

        if accuracy <= 100:
            return 0, {
                "risk": "LOW",
                "reason": "GPS location has good accuracy.",
            }

        if accuracy <= 500:
            return 15, {
                "risk": "MEDIUM",
                "reason": "GPS location has moderate accuracy.",
            }

        return 30, {
            "risk": "HIGH",
            "reason": "GPS location accuracy is poor.",
        }

    def assess(
        self,
        user_id: uuid.UUID,
        device_id: uuid.UUID | None = None,
        location_observation_id: uuid.UUID | None = None,
    ) -> RiskAssessment:

        device = None
        location = None

        if device_id is not None:
            device = self.device_repository.get_by_id(device_id)

            if device is None or device.user_id != user_id:
                raise ValueError(
                    "Device does not belong to the specified user."
                )

        if location_observation_id is not None:
            location = self.location_repository.get_by_id(
                location_observation_id
            )

            if location is None or location.user_id != user_id:
                raise ValueError(
                    "Location observation does not belong to the specified user."
                )

        device_score, device_factor = self._evaluate_device(device)

        location_score, location_factor = self._evaluate_location(
            location
        )

        # Initial contextual scoring.
        # Maximum score is capped at 100.
        risk_score = min(
            100,
            device_score + location_score,
        )

        risk_level = self._get_risk_level(risk_score)

        risk_factors = {
            "device": device_factor,
            "location": location_factor,
            "scoring": {
                "device_score": device_score,
                "location_score": location_score,
                "maximum_score": 100,
                "method": "Deterministic contextual risk scoring",
            },
        }

        assessment = RiskAssessment(
            user_id=user_id,
            device_id=device.id if device else None,
            location_observation_id=location.id if location else None,
            risk_score=Decimal(str(risk_score)),
            risk_level=risk_level,
            risk_factors=risk_factors,
            assessment_version=self.ASSESSMENT_VERSION,
        )

        self.risk_repository.add(assessment)
        self.risk_repository.flush()

        return assessment