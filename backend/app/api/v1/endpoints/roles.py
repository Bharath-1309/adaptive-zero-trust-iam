from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.role import RoleCreate, RoleResponse
from app.security.authorization import require_permission
from app.services.role_service import RoleService


router = APIRouter(prefix="/roles", tags=["Role Management"])


@router.post(
    "/",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_role(
    data: RoleCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_permission("roles:write")),
    ],
):
    service = RoleService(
        RoleRepository(db),
        UserRepository(db),
    )

    try:
        role = service.create_role(
            data.name,
            data.description,
        )
        db.commit()
        db.refresh(role)
        return role

    except ValueError as exc:
        db.rollback()
        raise HTTPException(409, str(exc))

    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Role already exists.")


@router.get("/", response_model=list[RoleResponse])
def list_roles(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_permission("roles:read")),
    ],
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
):
    service = RoleService(
        RoleRepository(db),
        UserRepository(db),
    )

    return service.get_all_roles(offset, limit)


@router.post(
    "/{role_id}/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def assign_role(
    role_id: UUID,
    user_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_permission("roles:write")),
    ],
):
    service = RoleService(
        RoleRepository(db),
        UserRepository(db),
    )

    try:
        service.assign_role(user_id, role_id)
        db.commit()

    except LookupError as exc:
        db.rollback()
        raise HTTPException(404, str(exc))

    except PermissionError as exc:
        db.rollback()
        raise HTTPException(403, str(exc))


@router.delete(
    "/{role_id}/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_role(
    role_id: UUID,
    user_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_permission("roles:write")),
    ],
):
    service = RoleService(
        RoleRepository(db),
        UserRepository(db),
    )

    try:
        service.remove_role(user_id, role_id)
        db.commit()

    except LookupError as exc:
        db.rollback()
        raise HTTPException(404, str(exc))