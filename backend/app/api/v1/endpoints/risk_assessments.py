from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.repositories.device_repository import DeviceRepository
from app.repositories.location_observation_repository import (
    LocationObservationRepository,
)
from app.schemas.risk_assessment import RiskAssessmentResponse
from app.security.authorization import get_current_db_user
from app.services.device_service import DeviceService
from app.services.risk_assessment_service import RiskAssessmentService


router = APIRouter(
    prefix="/risk-assessments",
    tags=["Adaptive Risk Assessment"],
)


@router.post(
    "/evaluate",
    response_model=RiskAssessmentResponse,
)
def evaluate_risk(
    current_user: Annotated[
        User,
        Depends(get_current_db_user),
    ],
    db: Annotated[Session, Depends(get_db)],
    device_token: Annotated[
        str | None,
        Cookie(alias="zt_device_token"),
    ] = None,
):
    device = None

    if device_token:
        device = DeviceService(
            DeviceRepository(db)
        ).identify_device(
            user_id=current_user.id,
            token=device_token,
        )

    location = LocationObservationRepository(
        db
    ).get_latest_observation(current_user.id)

    service = RiskAssessmentService(db)

    try:
        assessment = service.assess(
            user_id=current_user.id,
            device_id=device.id if device else None,
            location_observation_id=location.id if location else None,
        )

        db.commit()
        db.refresh(assessment)

        return assessment

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc