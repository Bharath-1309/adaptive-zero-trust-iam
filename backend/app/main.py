from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.security.dependencies import get_current_user


app = FastAPI(
    title="Adaptive Zero Trust IAM",
    description=(
        "Adaptive Zero Trust Identity and Access Management "
        "with Geolocation-Based Risk Assessment"
    ),
    version="1.0.0",
)


# Allow requests from the React development server.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["Authorization"],
)


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "application": "Adaptive Zero Trust IAM",
    }


@app.get("/auth/me", tags=["Authentication"])
def get_authenticated_user(
    current_user: Annotated[
        dict,
        Depends(get_current_user),
    ],
):
    return {
        "authenticated": True,
        "subject": current_user.get("sub"),
        "username": current_user.get("preferred_username"),
        "email": current_user.get("email"),
        "authentication_level": current_user.get("acr"),
        "audience": current_user.get("aud"),
    }