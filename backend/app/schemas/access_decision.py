from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AccessDecisionRequest(BaseModel):
    action: str = Field(
        min_length=1,
        max_length=150,
    )

    resource: str = Field(
        min_length=1,
        max_length=255,
    )


class AccessDecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    request_id: UUID
    parent_decision_id: UUID | None
    user_id: UUID
    risk_assessment_id: UUID | None
    action: str
    resource: str
    decision: str
    risk_score: Decimal | None
    policy_snapshot: dict
    reason: str
    evaluated_at: datetime