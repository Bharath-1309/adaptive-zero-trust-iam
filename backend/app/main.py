from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import permissions, roles
from app.security.dependencies import get_current_user
from app.security.authorization import get_current_db_user
from app.models.user import User
from app.api.v1.endpoints import policies
from app.api.v1.endpoints import devices
from app.api.v1.endpoints import locations
from app.api.v1.endpoints import audit_logs
from app.api.v1.endpoints import risk_assessments
from app.api.v1.endpoints import office_geofences
from app.api.v1.endpoints import resource_definitions
from app.api.v1.endpoints import access_decisions
from app.api.v1.endpoints import travel_authorizations

app = FastAPI(
    title="Adaptive Zero Trust IAM",
    description=(
        "Adaptive Zero Trust Identity and Access Management "
        "with Geolocation-Based Risk Assessment"
    ),
    version="1.0.0",
    swagger_ui_init_oauth={
        "clientId": "adaptive-iam-frontend",
        "usePkceWithAuthorizationCodeGrant": True,
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
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

app.include_router(
    locations.router,
    prefix="/api/v1"
)

app.include_router(
    audit_logs.router,
    prefix="/api/v1",
)

app.include_router(
    risk_assessments.router,
    prefix="/api/v1",
)

app.include_router(
    office_geofences.router,
    prefix="/api/v1",
)

app.include_router(
    resource_definitions.router,
    prefix="/api/v1",
)

app.include_router(
    access_decisions.router,
    prefix="/api/v1",
)

app.include_router(
    travel_authorizations.router,
    prefix="/api/v1",
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