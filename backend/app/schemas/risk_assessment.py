from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RiskAssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    device_id: UUID | None
    location_observation_id: UUID | None
    risk_score: Decimal
    risk_level: str
    risk_factors: dict
    assessment_version: str
    assessed_at: datetime