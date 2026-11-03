import jwt

from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError

from app.core.config import settings


# Keycloak public signing keys.
# PyJWKClient caches keys and supports signing-key rotation.
jwks_client = PyJWKClient(
    settings.keycloak_jwks_url,
    cache_keys=True,
)


def decode_access_token(token: str) -> dict:
    """
    Verify and decode a Keycloak access token.

    Validates:
    - JWT signature
    - Issuer
    - Audience
    - Expiration
    - Required identity claims
    - Authentication level claim
    """

    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.KEYCLOAK_API_CLIENT_ID,
            issuer=settings.keycloak_issuer,
            options={
                "require": [
                    "exp",
                    "iss",
                    "sub",
                    "aud",
                    "acr",
                ],
            },
        )

        # Ensure the authentication level is represented as a string.
        if not isinstance(payload.get("acr"), str):
            raise InvalidTokenError(
                "Invalid authentication level claim."
            )

        return payload

    except InvalidTokenError:
        raise