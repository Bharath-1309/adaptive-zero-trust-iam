from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.repositories.permission_repository import PermissionRepository
from app.repositories.role_repository import RoleRepository
from app.schemas.permission import (
    PermissionCreate,
    PermissionResponse,
)
from app.security.authorization import require_permission
from app.services.permission_service import PermissionService


router = APIRouter(
    prefix="/permissions",
    tags=["Permission Management"],
)


@router.post(
    "/",
    response_model=PermissionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_permission(
    data: PermissionCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_permission("permissions:write")),
    ],
):
    service = PermissionService(
        PermissionRepository(db),
        RoleRepository(db),
    )

    try:
        permission = service.create_permission(
            data.name,
            data.description,
        )
        db.commit()
        db.refresh(permission)
        return permission

    except ValueError as exc:
        db.rollback()
        raise HTTPException(409, str(exc))

    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Permission already exists.")


@router.get("/", response_model=list[PermissionResponse])
def list_permissions(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_permission("permissions:read")),
    ],
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
):
    service = PermissionService(
        PermissionRepository(db),
        RoleRepository(db),
    )

    return service.get_all_permissions(offset, limit)


@router.post(
    "/{permission_id}/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def assign_permission(
    permission_id: UUID,
    role_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_permission("permissions:write")),
    ],
):
    service = PermissionService(
        PermissionRepository(db),
        RoleRepository(db),
    )

    try:
        service.assign_permission(role_id, permission_id)
        db.commit()

    except LookupError as exc:
        db.rollback()
        raise HTTPException(404, str(exc))


@router.delete(
    "/{permission_id}/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_permission(
    permission_id: UUID,
    role_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_permission("permissions:write")),
    ],
):
    service = PermissionService(
        PermissionRepository(db),
        RoleRepository(db),
    )

    try:
        service.remove_permission(role_id, permission_id)
        db.commit()

    except LookupError as exc:
        db.rollback()
        raise HTTPException(404, str(exc))