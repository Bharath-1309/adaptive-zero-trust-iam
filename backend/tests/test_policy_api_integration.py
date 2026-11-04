import uuid

from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.models.user import User
from app.security.dependencies import get_current_user
from app.repositories.access_policy_repository import (
    AccessPolicyRepository,
)
from app.services.abac_service import ABACService


ADMIN_SUBJECT = "2bde334f-7433-455b-b024-4ce7d18ac3a7"
ADMIN_EMAIL = "bharath.test@example.com"

TEST_SUBJECT = f"abac-test-{uuid.uuid4()}"
TEST_EMAIL = f"abac-test-{uuid.uuid4()}@example.com"

POLICY_NAME = f"integration-test-{uuid.uuid4()}"


def run_tests():

    passed = 0
    test_user = None

    def check(condition, message):
        nonlocal passed

        if not condition:
            raise AssertionError(message)

        passed += 1
        print(f"PASS: {message}")

    admin_claims = {
        "sub": ADMIN_SUBJECT,
        "email": ADMIN_EMAIL,
        "name": "Bharath Test",
    }

    test_claims = {
        "sub": TEST_SUBJECT,
        "email": TEST_EMAIL,
        "name": "ABAC Integration Test",
    }

    try:
        with TestClient(app) as client:

            # 1. Unauthenticated request
            app.dependency_overrides.pop(
                get_current_user,
                None,
            )

            response = client.get("/api/v1/policies/")

            check(
                response.status_code == 401,
                "Unauthenticated policy request rejected",
            )

            # 2. Authenticate as administrator
            app.dependency_overrides[get_current_user] = (
                lambda: admin_claims
            )

            response = client.post(
                "/api/v1/policies/",
                json={
                    "name": POLICY_NAME,
                    "description": "Temporary integration test policy",
                    "effect": "ALLOW",
                    "priority": 100,
                    "conditions": {
                        "subject": {
                            "is_active": {"eq": True}
                        }
                    },
                },
            )

            check(
                response.status_code == 201,
                "Administrator can create a policy",
            )

            policy = response.json()
            policy_id = policy["id"]

            check(
                policy["is_active"] is True,
                "New policy is active",
            )

            # 3. Retrieve policy
            response = client.get(
                f"/api/v1/policies/{policy_id}"
            )

            check(
                response.status_code == 200,
                "Administrator can retrieve a policy",
            )

            # 4. List policies
            response = client.get("/api/v1/policies/")

            check(
                any(item["id"] == policy_id for item in response.json()),
                "Policy appears in policy listing",
            )

            # 5. Duplicate policy name
            response = client.post(
                "/api/v1/policies/",
                json={
                    "name": POLICY_NAME,
                    "effect": "ALLOW",
                    "priority": 100,
                    "conditions": {
                        "subject": {
                            "is_active": {"eq": True}
                        }
                    },
                },
            )

            check(
                response.status_code == 409,
                "Duplicate policy name rejected",
            )

            # 6. Invalid policy conditions
            response = client.post(
                "/api/v1/policies/",
                json={
                    "name": f"invalid-{uuid.uuid4()}",
                    "effect": "ALLOW",
                    "priority": 100,
                    "conditions": {
                        "subject": {
                            "is_active": {
                                "unsupported_operator": True
                            }
                        }
                    },
                },
            )

            check(
                response.status_code == 422,
                "Invalid policy conditions rejected",
            )

            # 7. Update policy
            response = client.patch(
                f"/api/v1/policies/{policy_id}",
                json={
                    "priority": 50,
                    "description": "Updated integration test policy",
                },
            )

            check(
                response.status_code == 200
                and response.json()["priority"] == 50,
                "Administrator can update a policy",
            )

            # 8. Deactivate policy
            response = client.delete(
                f"/api/v1/policies/{policy_id}"
            )

            check(
                response.status_code == 200
                and response.json()["is_active"] is False,
                "Policy deactivation works",
            )

            # 9. Verify inactive policy is excluded
            db = SessionLocal()

            try:
                repository = AccessPolicyRepository(db)
                active_policies = repository.get_active_policies()

                check(
                    all(
                        str(item.id) != policy_id
                        for item in active_policies
                    ),
                    "Inactive policy excluded from evaluation",
                )

            finally:
                db.close()

            # 10. Test user without admin permissions
            app.dependency_overrides[get_current_user] = (
                lambda: test_claims
            )

            response = client.get("/api/v1/policies/")

            check(
                response.status_code == 403,
                "User without admin permission denied",
            )

            db = SessionLocal()

            try:
                test_user = (
                    db.query(User)
                    .filter(
                        User.keycloak_subject == TEST_SUBJECT
                    )
                    .first()
                )

                if test_user is not None:
                    test_user.is_active = False
                    db.commit()

            finally:
                db.close()

        print(f"\nPOLICY API TESTS: {passed}/10 PASSED")

    finally:
        app.dependency_overrides.pop(
            get_current_user,
            None,
        )

        if test_user is not None:
            db = SessionLocal()
            try:
                user = db.get(User, test_user.id)
                if user is not None:
                    user.is_active = False
                    db.commit()
            finally:
                db.close()


if __name__ == "__main__":
    run_tests()