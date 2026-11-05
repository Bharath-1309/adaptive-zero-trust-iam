from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.office_geofence import OfficeGeofence
from app.repositories.office_geofence_repository import (
    OfficeGeofenceRepository,
)
from app.schemas.office_geofence import (
    OfficeGeofenceCreate,
    OfficeGeofenceUpdate,
    OfficeGeofenceResponse,
)
from app.security.authorization import require_permission
from app.services.office_geofence_service import (
    OfficeGeofenceService,
)

router = APIRouter(
    prefix="/office-geofences",
    tags=["Office Geofences"],
)

AdminUser = Annotated[
    object,
    Depends(require_permission("admin:manage")),
]


def get_service(db: Session) -> OfficeGeofenceService:
    repository = OfficeGeofenceRepository(db)
    return OfficeGeofenceService(repository)


@router.post(
    "/",
    response_model=OfficeGeofenceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_office_geofence(
    data: OfficeGeofenceCreate,
    current_user=Depends(require_permission("admin:manage")),
    db: Session = Depends(get_db),
):
    service = get_service(db)

    try:
        geofence = service.create_geofence(
            name=data.name,
            latitude=data.latitude,
            longitude=data.longitude,
            radius_meters=data.radius_meters,
            max_accuracy_meters=data.max_accuracy_meters,
            created_by_user_id=current_user.id,
            location_type=data.location_type,
            expires_at=data.expires_at,
        )

        db.commit()
        db.refresh(geofence)

        return geofence

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Office geofence conflicts with existing data.",
        )


@router.get(
    "/",
    response_model=list[OfficeGeofenceResponse],
)
def get_office_geofences(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    current_user=Depends(require_permission("admin:manage")),
    db: Session = Depends(get_db),
):
    service = get_service(db)

    return service.get_all_geofences(
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{geofence_id}",
    response_model=OfficeGeofenceResponse,
)
def get_office_geofence(
    geofence_id: UUID,
    current_user=Depends(require_permission("admin:manage")),
    db: Session = Depends(get_db),
):
    service = get_service(db)

    try:
        return service.get_geofence(geofence_id)

    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.patch(
    "/{geofence_id}",
    response_model=OfficeGeofenceResponse,
)
def update_office_geofence(
    geofence_id: UUID,
    data: OfficeGeofenceUpdate,
    current_user=Depends(require_permission("admin:manage")),
    db: Session = Depends(get_db),
):
    service = get_service(db)

    try:
        geofence = service.update_geofence(
            geofence_id=geofence_id,
            updates=data.model_dump(exclude_unset=True),
        )

        db.commit()
        db.refresh(geofence)

        return geofence

    except LookupError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Office geofence conflicts with existing data.",
        )


@router.post(
    "/{geofence_id}/deactivate",
    response_model=OfficeGeofenceResponse,
)
def deactivate_office_geofence(
    geofence_id: UUID,
    current_user=Depends(require_permission("admin:manage")),
    db: Session = Depends(get_db),
):
    service = get_service(db)

    try:
        geofence = service.deactivate_geofence(geofence_id)

        db.commit()
        db.refresh(geofence)

        return geofence

    except LookupError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )