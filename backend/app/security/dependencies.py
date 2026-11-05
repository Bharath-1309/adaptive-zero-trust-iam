from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer
from jwt.exceptions import InvalidTokenError, PyJWKClientError

from app.core.config import settings
from app.security.jwt import decode_access_token


oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=(
        f"{settings.keycloak_issuer}"
        "/protocol/openid-connect/auth"
    ),
    tokenUrl=(
        f"{settings.keycloak_issuer}"
        "/protocol/openid-connect/token"
    ),
    scopes={},
    auto_error=False,
)


def get_current_user(
    token: Annotated[
        str | None,
        Depends(oauth2_scheme),
    ],
) -> dict:

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials are required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return decode_access_token(token)

    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except PyJWKClientError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve authentication signing keys.",
        )