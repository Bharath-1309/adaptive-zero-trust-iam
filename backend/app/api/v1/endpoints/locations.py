from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.repositories.location_observation_repository import (
    LocationObservationRepository,
)
from app.schemas.location import (
    BrowserGPSCreate,
    LocationObservationResponse,
)
from app.schemas.location import (
    BrowserGPSCreate,
    LocationObservationResponse,
    LocationPermissionEventCreate,
)
from app.security.authorization import get_current_db_user
from app.services.location_observation_service import (
    LocationObservationService,
)


router = APIRouter(
    prefix="/locations",
    tags=["Geolocation and Location Intelligence"],
)


@router.post(
    "/observe-ip",
    response_model=LocationObservationResponse | None,
)
def observe_ip_location(
    request: Request,
    current_user: Annotated[
        User,
        Depends(get_current_db_user),
    ],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Determine approximate location using the request's direct
    client IP. Forwarded headers are not trusted.
    """

    if request.client is None:
        return None

    service = LocationObservationService(db)

    observation = service.record_ip_location(
        user_id=current_user.id,
        ip_address=request.client.host,
    )

    if observation is None:
        return None

    db.commit()
    db.refresh(observation)

    return observation


@router.post(
    "/browser-gps",
    response_model=LocationObservationResponse,
    status_code=201,
)
def observe_browser_gps(
    data: BrowserGPSCreate,
    current_user: Annotated[
        User,
        Depends(get_current_db_user),
    ],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Record browser GPS coordinates only with explicit consent.
    """

    service = LocationObservationService(db)

    try:
        observation = service.record_browser_gps(
            user_id=current_user.id,
            latitude=data.latitude,
            longitude=data.longitude,
            accuracy_meters=data.accuracy_meters,
            consent_granted=data.consent_granted,
        )

        db.commit()
        db.refresh(observation)

        return observation

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.get(
    "/history",
    response_model=list[LocationObservationResponse],
)
def get_location_history(
    current_user: Annotated[
        User,
        Depends(get_current_db_user),
    ],
    db: Annotated[Session, Depends(get_db)],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """
    Retrieve only the authenticated user's location history.
    """

    repository = LocationObservationRepository(db)

    return repository.get_user_observations(
        user_id=current_user.id,
        offset=offset,
        limit=limit,
    )

@router.post("/permission-event", status_code=201)
def record_location_permission_event(
    data: LocationPermissionEventCreate,
    current_user: Annotated[
        User,
        Depends(get_current_db_user),
    ],
    db: Annotated[Session, Depends(get_db)],
):
    service = LocationObservationService(db)

    try:
        service.record_location_permission_event(
            user_id=current_user.id,
            outcome=data.outcome,
            reason=data.reason,
        )

        db.commit()

        return {
            "recorded": True,
            "outcome": data.outcome,
        }

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc