from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import permissions, roles
from app.security.dependencies import get_current_user
from app.security.authorization import get_current_db_user
from app.models.user import User
from app.api.v1.endpoints import policies
from app.api.v1.endpoints import devices

app = FastAPI(
    title="Adaptive Zero Trust IAM",
    description=(
        "Adaptive Zero Trust Identity and Access Management "
        "with Geolocation-Based Risk Assessment"
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(
    roles.router,
    prefix="/api/v1",
)

app.include_router(
    permissions.router,
    prefix="/api/v1",
)

app.include_router(
    policies.router,
    prefix="/api/v1"
)

app.include_router(
    devices.router,
    prefix="/api/v1"
)

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "application": "Adaptive Zero Trust IAM",
    }


@app.get("/auth/me")
def read_current_user(
    current_user: Annotated[
        User,
        Depends(get_current_db_user),
    ],
):
    return {
        "authenticated": True,
        "id": str(current_user.id),
        "keycloak_subject": current_user.keycloak_subject,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
        "roles": [
            role.name for role in current_user.roles
        ],
    }