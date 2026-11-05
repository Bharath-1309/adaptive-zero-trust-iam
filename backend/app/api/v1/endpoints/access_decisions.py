from typing import Annotated

from fastapi import (
    APIRouter,
    Cookie,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.access_decision import (
    AccessDecisionRequest,
    AccessDecisionResponse,
)
from app.security.authorization import get_current_db_user
from app.services.access_decision_service import (
    AccessDecisionService,
)


router = APIRouter(
    prefix="/access-decisions",
    tags=["Zero Trust Access Decisions"],
)


@router.post(
    "/evaluate",
    response_model=AccessDecisionResponse,
    status_code=status.HTTP_200_OK,
)
def evaluate_access(
    request: AccessDecisionRequest,
    current_user: Annotated[
        User,
        Depends(get_current_db_user),
    ],
    db: Annotated[
        Session,
        Depends(get_db),
    ],
    device_token: Annotated[
        str | None,
        Cookie(alias="zt_device_token"),
    ] = None,
):
    service = AccessDecisionService(db)

    try:
        decision = service.evaluate(
            current_user=current_user,
            action=request.action,
            resource_name=request.resource,
            device_token=device_token,
        )

        db.commit()
        db.refresh(decision)

        return decision

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except SQLAlchemyError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to complete access evaluation.",
        ) from exc

    except Exception:
        db.rollback()
        raise