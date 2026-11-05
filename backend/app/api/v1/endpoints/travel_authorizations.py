from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.security.authorization import (
    get_current_db_user,
    require_permission,
)
from app.schemas.travel_authorization import (
    TravelAuthorizationCreate,
    TravelAuthorizationReview,
    TravelAuthorizationRevoke,
    TravelAuthorizationResponse,
)
from app.services.travel_authorization_service import (
    TravelAuthorizationService,
)


router = APIRouter(
    prefix="/travel-authorizations",
    tags=["Travel Authorizations"],
)


CurrentUser = Annotated[
    User,
    Depends(get_current_db_user),
]


@router.post(
    "/",
    response_model=TravelAuthorizationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_travel_request(
    data: TravelAuthorizationCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    service = TravelAuthorizationService(db)

    try:
        authorization = service.create_request(
            user_id=current_user.id,
            data=data,
        )

        db.commit()
        db.refresh(authorization)

        return authorization

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Travel authorization request conflicts with database constraints.",
        ) from exc


@router.get(
    "/me",
    response_model=list[TravelAuthorizationResponse],
)
def get_my_travel_requests(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    service = TravelAuthorizationService(db)

    try:
        return service.get_user_requests(current_user.id)

    except Exception:
        db.rollback()
        raise


@router.get(
    "/pending",
    response_model=list[TravelAuthorizationResponse],
)
def get_pending_travel_requests(
    current_user=Depends(require_permission("admin:manage")),
    db: Session = Depends(get_db),
):
    service = TravelAuthorizationService(db)

    try:
        return service.get_pending_requests()

    except Exception:
        db.rollback()
        raise


@router.patch(
    "/{authorization_id}/review",
    response_model=TravelAuthorizationResponse,
)
def review_travel_request(
    authorization_id: UUID,
    data: TravelAuthorizationReview,
    current_user=Depends(require_permission("admin:manage")),
    db: Session = Depends(get_db),
):
    service = TravelAuthorizationService(db)

    try:
        authorization = service.review_request(
            authorization_id=authorization_id,
            reviewer_id=current_user.id,
            status=data.status,
            reason=data.reason,
        )

        db.commit()
        db.refresh(authorization)

        return authorization

    except ValueError as exc:
        db.rollback()

        status_code = (
            status.HTTP_404_NOT_FOUND
            if "not found" in str(exc).lower()
            else status.HTTP_400_BAD_REQUEST
        )

        raise HTTPException(
            status_code=status_code,
            detail=str(exc),
        ) from exc

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Travel authorization review conflicts with database constraints.",
        ) from exc


@router.post(
    "/{authorization_id}/revoke",
    response_model=TravelAuthorizationResponse,
)
def revoke_travel_request(
    authorization_id: UUID,
    data: TravelAuthorizationRevoke,
    current_user=Depends(require_permission("admin:manage")),
    db: Session = Depends(get_db),
):
    service = TravelAuthorizationService(db)

    try:
        authorization = service.revoke_request(
            authorization_id=authorization_id,
            reviewer_id=current_user.id,
            reason=data.reason,
        )

        db.commit()
        db.refresh(authorization)

        return authorization

    except ValueError as exc:
        db.rollback()

        status_code = (
            status.HTTP_404_NOT_FOUND
            if "not found" in str(exc).lower()
            else status.HTTP_400_BAD_REQUEST
        )

        raise HTTPException(
            status_code=status_code,
            detail=str(exc),
        ) from exc

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Travel authorization revocation conflicts with database constraints.",
        ) from exc