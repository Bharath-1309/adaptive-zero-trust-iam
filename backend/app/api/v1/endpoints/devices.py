from typing import Annotated
import uuid

from fastapi import (
    APIRouter,
    Cookie,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.repositories.device_repository import DeviceRepository
from app.schemas.device import DeviceRegistration, DeviceResponse
from app.security.authorization import (
    get_current_db_user,
    require_permission,
)
from app.services.device_service import DeviceService


router = APIRouter(
    prefix="/devices",
    tags=["Device Recognition"],
)

DEVICE_COOKIE_NAME = "zt_device_token"
DEVICE_COOKIE_PATH = "/api/v1"
DEVICE_COOKIE_MAX_AGE = 60 * 60 * 24 * 365


def get_device_service(db: Session) -> DeviceService:
    return DeviceService(DeviceRepository(db))


@router.post(
    "/register",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_device(
    data: DeviceRegistration,
    request: Request,
    response: Response,
    current_user: Annotated[
        User,
        Depends(get_current_db_user),
    ],
    db: Annotated[Session, Depends(get_db)],
):
    user_agent = request.headers.get("user-agent", "")

    device, token = get_device_service(db).register_device(
        user_id=current_user.id,
        device_name=data.device_name,
        operating_system=None,
        browser=user_agent[:100] or None,
    )

    db.commit()
    db.refresh(device)

    response.delete_cookie(
        key=DEVICE_COOKIE_NAME,
        path=DEVICE_COOKIE_PATH,
    )

    response.set_cookie(
        key=DEVICE_COOKIE_NAME,
        value=token,
        max_age=DEVICE_COOKIE_MAX_AGE,
        httponly=True,
        secure=True,
        samesite="lax",
        path=DEVICE_COOKIE_PATH,
    )

    return device


@router.get("/recognize")
def recognize_device(
    current_user: Annotated[
        User,
        Depends(get_current_db_user),
    ],
    db: Annotated[Session, Depends(get_db)],
    device_token: Annotated[
        str | None,
        Cookie(alias=DEVICE_COOKIE_NAME),
    ] = None,
):
    if not device_token:
        return {
            "recognized": False,
            "trusted": False,
            "message": "No registered device token was provided.",
        }

    device = get_device_service(db).identify_device(
        user_id=current_user.id,
        token=device_token,
    )

    if device is None:
        return {
            "recognized": False,
            "trusted": False,
            "message": "Device is unknown, inactive or revoked.",
        }

    db.commit()

    return {
        "recognized": True,
        "trusted": device.is_trusted,
        "device_id": str(device.id),
        "device_name": device.device_name,
        "message": "Device successfully recognized.",
    }


@router.get(
    "/",
    response_model=list[DeviceResponse],
)
def list_devices(
    current_user: Annotated[
        User,
        Depends(get_current_db_user),
    ],
    db: Annotated[Session, Depends(get_db)],
):
    return get_device_service(db).get_user_devices(
        current_user.id
    )


@router.delete("/{device_id}")
def revoke_device(
    device_id: uuid.UUID,
    current_user: Annotated[
        User,
        Depends(get_current_db_user),
    ],
    db: Annotated[Session, Depends(get_db)],
):
    service = get_device_service(db)

    revoked = service.revoke_device(
        user_id=current_user.id,
        device_id=device_id,
    )

    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found or already revoked.",
        )

    db.commit()

    return {
        "success": True,
        "device_id": str(device_id),
        "message": "Device successfully revoked.",
    }


@router.patch("/{device_id}/trust")
def update_device_trust(
    device_id: uuid.UUID,
    is_trusted: bool,
    current_user: Annotated[
        User,
        Depends(require_permission("devices:trust")),
    ],
    db: Annotated[Session, Depends(get_db)],
):
    service = get_device_service(db)

    updated = service.set_device_trust(
        user_id=current_user.id,
        device_id=device_id,
        is_trusted=is_trusted,
    )

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found or inactive.",
        )

    db.commit()

    return {
        "success": True,
        "device_id": str(device_id),
        "is_trusted": is_trusted,
        "message": "Device trust status updated.",
    }