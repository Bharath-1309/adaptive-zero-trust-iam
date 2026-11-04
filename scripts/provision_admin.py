import argparse
import sys

from sqlalchemy.exc import SQLAlchemyError

from app.db.session import SessionLocal
from app.models.permission import Permission
from app.models.role import Role
from app.repositories.permission_repository import PermissionRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository


ADMIN_ROLE = "admin"

ADMIN_PERMISSIONS = [
    "roles:read",
    "roles:write",
    "permissions:read",
    "permissions:write",
    "admin:manage",
]


def provision_admin(email: str) -> None:
    db = SessionLocal()

    try:
        user_repository = UserRepository(db)
        role_repository = RoleRepository(db)
        permission_repository = PermissionRepository(db)

        # Find the existing application user.
        user = user_repository.get_by_email(email)

        if user is None:
            raise ValueError(
                "No application user exists with this email."
            )

        if not user.is_active:
            raise ValueError(
                "Cannot provision an inactive user."
            )

        # Create or retrieve the administrator role.
        admin_role = role_repository.get_by_name(ADMIN_ROLE)

        if admin_role is None:
            admin_role = Role(
                name=ADMIN_ROLE,
                description="Platform administrator role.",
            )
            role_repository.add(admin_role)
            role_repository.flush()

        # Create or retrieve the administrator permissions.
        for permission_name in ADMIN_PERMISSIONS:
            permission = permission_repository.get_by_name(
                permission_name
            )

            if permission is None:
                permission = Permission(
                    name=permission_name,
                    description=(
                        f"Administrative permission: "
                        f"{permission_name}"
                    ),
                )
                permission_repository.add(permission)
                permission_repository.flush()

            permission_repository.assign_permission_to_role(
                admin_role,
                permission,
            )

        # Assign administrator role to the verified local user.
        role_repository.assign_role_to_user(
            user,
            admin_role,
        )

        db.commit()

        print("SUCCESS: Administrator provisioned.")
        print(f"User: {user.email}")
        print(f"Role: {admin_role.name}")
        print("Permissions:")

        for permission_name in ADMIN_PERMISSIONS:
            print(f"  - {permission_name}")

    except (ValueError, SQLAlchemyError) as exc:
        db.rollback()
        print(f"FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)

    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Provision an initial IAM administrator."
    )

    parser.add_argument(
        "--email",
        required=True,
        help="Email of the existing application user.",
    )

    parser.add_argument(
        "--confirm-email",
        required=True,
        help="Repeat the email to confirm the provisioning target.",
    )

    args = parser.parse_args()

    email = args.email.strip()

    if email != args.confirm_email.strip():
        parser.error("Email confirmation does not match.")

    provision_admin(email)


if __name__ == "__main__":
    main()