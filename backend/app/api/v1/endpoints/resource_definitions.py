import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.resource_definition_repository import (
    ResourceDefinitionRepository,
)
from app.schemas.resource_definition import (
    ResourceDefinitionCreate,
    ResourceDefinitionResponse,
    ResourceDefinitionUpdate,
)
from app.security.authorization import require_permission
from app.services.resource_definition_service import (
    ResourceDefinitionService,
)


router = APIRouter(
    prefix="/resource-definitions",
    tags=["Resource Definitions"],
)


def get_resource_service(
    db: Session,
) -> ResourceDefinitionService:
    return ResourceDefinitionService(
        ResourceDefinitionRepository(db)
    )


@router.post(
    "/",
    response_model=ResourceDefinitionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_resource(
    data: ResourceDefinitionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("admin:manage")),
):
    try:
        service = get_resource_service(db)
        resource = service.create_resource(data)

        db.commit()
        db.refresh(resource)

        return resource

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Resource conflicts with an existing database record.",
        )


@router.get(
    "/",
    response_model=list[ResourceDefinitionResponse],
)
def list_resources(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("admin:manage")),
):
    service = get_resource_service(db)

    return service.get_all_resources(
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{resource_id}",
    response_model=ResourceDefinitionResponse,
)
def get_resource(
    resource_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("admin:manage")),
):
    try:
        return get_resource_service(db).get_resource(resource_id)

    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.patch(
    "/{resource_id}",
    response_model=ResourceDefinitionResponse,
)
def update_resource(
    resource_id: uuid.UUID,
    data: ResourceDefinitionUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("admin:manage")),
):
    try:
        service = get_resource_service(db)
        resource = service.update_resource(resource_id, data)

        db.commit()
        db.refresh(resource)

        return resource

    except LookupError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Resource conflicts with an existing database record.",
        )