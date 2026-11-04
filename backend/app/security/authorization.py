from typing import Annotated, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.services.authorization_service import AuthorizationService
from app.security.dependencies import get_current_user


def get_current_db_user(
    token_payload: Annotated[
        dict,
        Depends(get_current_user),
    ],
    db: Annotated[
        Session,
        Depends(get_db),
    ],
) -> User:

    keycloak_subject = token_payload.get("sub")
    email = token_payload.get("email")

    if (
        not isinstance(keycloak_subject, str)
        or not keycloak_subject.strip()
        or not isinstance(email, str)
        or not email.strip()
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Required identity claims are missing.",
        )

    user_repository = UserRepository(db)

    user = user_repository.get_by_keycloak_subject(
        keycloak_subject
    )

    if user is None:
        # Prevent an existing local account from being
        # silently linked to a different Keycloak identity.
        existing_email_user = user_repository.get_by_email(email)

        if existing_email_user is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email is already associated with another identity.",
            )

        full_name = (
            token_payload.get("name")
            or token_payload.get("preferred_username")
            or email.split("@")[0]
        )

        if not isinstance(full_name, str) or not full_name.strip():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user identity information.",
            )

        user = User(
            keycloak_subject=keycloak_subject,
            email=email,
            full_name=full_name.strip(),
            is_active=True,
        )

        try:
            user_repository.add(user)
            user_repository.flush()
            db.commit()
            db.refresh(user)

        except IntegrityError:
            db.rollback()

            # Handle a concurrent first-login request.
            user = user_repository.get_by_keycloak_subject(
                keycloak_subject
            )

            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Unable to provision application user.",
                )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    return user


def require_permission(
    permission_name: str,
) -> Callable:

    def permission_checker(
        current_user: Annotated[
            User,
            Depends(get_current_db_user),
        ],
        db: Annotated[
            Session,
            Depends(get_db),
        ],
    ) -> User:

        authorization_service = AuthorizationService(
            user_repository=UserRepository(db),
            role_repository=RoleRepository(db),
        )

        try:
            authorization_service.require_permission(
                current_user.id,
                permission_name,
            )

        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )

        except LookupError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User authorization failed.",
            )

        return current_user

    return permission_checker