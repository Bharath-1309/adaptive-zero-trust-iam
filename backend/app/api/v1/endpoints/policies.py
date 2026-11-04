import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.access_policy import AccessPolicy
from app.repositories.access_policy_repository import (
    AccessPolicyRepository,
)
from app.schemas.access_policy import (
    AccessPolicyCreate,
    AccessPolicyResponse,
    AccessPolicyUpdate,
)
from app.security.authorization import require_permission
from app.services.abac_service import (
    ABACService,
    PolicyConfigurationError,
)
from app.services.access_policy_service import AccessPolicyService


router = APIRouter(
    prefix="/policies",
    tags=["ABAC Policies"],
)


def get_policy_service(db: Session) -> AccessPolicyService:
    return AccessPolicyService(
        AccessPolicyRepository(db)
    )


@router.post(
    "/",
    response_model=AccessPolicyResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_policy(
    data: AccessPolicyCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("admin:manage")),
):
    try:
        ABACService.validate_policy_conditions(data.conditions)

        service = get_policy_service(db)
        policy = service.create_policy(data)

        db.commit()
        db.refresh(policy)

        return policy

    except PolicyConfigurationError as exc:
        db.rollback()
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        )

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Policy conflicts with an existing database record.",
        )


@router.get(
    "/",
    response_model=list[AccessPolicyResponse],
)
def list_policies(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("admin:manage")),
):
    return get_policy_service(db).get_all_policies(
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{policy_id}",
    response_model=AccessPolicyResponse,
)
def get_policy(
    policy_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("admin:manage")),
):
    try:
        return get_policy_service(db).get_policy(policy_id)

    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@router.patch(
    "/{policy_id}",
    response_model=AccessPolicyResponse,
)
def update_policy(
    policy_id: uuid.UUID,
    data: AccessPolicyUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("admin:manage")),
):
    try:
        updates = data.model_dump(exclude_unset=True)

        if "conditions" in updates and updates["conditions"] is not None:
            ABACService.validate_policy_conditions(
                updates["conditions"]
            )

        service = get_policy_service(db)
        policy = service.update_policy(policy_id, data)

        db.commit()
        db.refresh(policy)

        return policy

    except LookupError as exc:
        db.rollback()
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except PolicyConfigurationError as exc:
        db.rollback()
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        )

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Policy conflicts with an existing database record.",
        )


@router.delete(
    "/{policy_id}",
    response_model=AccessPolicyResponse,
)
def deactivate_policy(
    policy_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("admin:manage")),
):
    try:
        service = get_policy_service(db)
        policy = service.deactivate_policy(policy_id)

        db.commit()
        db.refresh(policy)

        return policy

    except LookupError as exc:
        db.rollback()
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )