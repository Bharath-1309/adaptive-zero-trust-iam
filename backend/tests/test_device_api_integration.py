import uuid

from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.models.user import User
from app.security.dependencies import get_current_user


ADMIN_SUBJECT = "2bde334f-7433-455b-b024-4ce7d18ac3a7"
ADMIN_EMAIL = "bharath.test@example.com"

TEST_SUBJECT = f"device-api-test-{uuid.uuid4()}"
TEST_EMAIL = f"device-api-test-{uuid.uuid4()}@example.com"


def run_tests():
    passed = 0
    test_user_id = None
    registered_device_id = None

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
        "name": "Device API Test User",
    }

    try:
        with TestClient(
            app,
            base_url="https://testserver",
        ) as client:

            # 1. Unauthenticated request
            app.dependency_overrides.pop(
                get_current_user,
                None,
            )

            response = client.get("/api/v1/devices/")

            check(
                response.status_code == 401,
                "Unauthenticated device listing rejected",
            )

            # 2. Authenticate as ordinary user
            app.dependency_overrides[get_current_user] = (
                lambda: test_claims
            )

            # 3. Register a device
            response = client.post(
                "/api/v1/devices/register",
                json={
                    "device_name": "Integration Test Device",
                },
                headers={
                    "user-agent": "Device Integration Test",
                },
            )

            check(
                response.status_code == 201,
                "Authenticated user can register a device",
            )

            device = response.json()
            registered_device_id = device["id"]

            check(
                device["is_active"] is True
                and device["is_trusted"] is False,
                "New device is active and untrusted",
            )

            # 4. Verify token cookie
            cookie = response.headers.get("set-cookie", "")

            check(
                "zt_device_token=" in cookie,
                "Device token issued through cookie",
            )

            check(
                "httponly" in cookie.lower()
                and "secure" in cookie.lower(),
                "Device cookie has HttpOnly and Secure attributes",
            )

            check(
                "zt_device_token" not in response.text,
                "Raw device token is not exposed in response body",
            )

            # 5. Recognize device
            response = client.get(
                "/api/v1/devices/recognize"
            )

            check(
                response.status_code == 200
                and response.json()["recognized"] is True,
                "Registered device successfully recognized",
            )

            # 6. List devices
            response = client.get("/api/v1/devices/")

            check(
                response.status_code == 200
                and any(
                    item["id"] == registered_device_id
                    for item in response.json()
                ),
                "User can list their registered devices",
            )

            # 7. Ordinary user cannot grant device trust
            response = client.patch(
                f"/api/v1/devices/{registered_device_id}/trust",
                params={"is_trusted": "true"},
            )

            check(
                response.status_code == 403,
                "User without devices:trust permission cannot grant trust",
            )

            # 8. Authenticate as administrator
            app.dependency_overrides[get_current_user] = (
                lambda: admin_claims
            )

            response = client.patch(
                f"/api/v1/devices/{registered_device_id}/trust",
                params={"is_trusted": "true"},
            )

            check(
                response.status_code == 404,
                "Administrator cannot modify another user's device",
            )

            # 9. Authenticate as device owner
            app.dependency_overrides[get_current_user] = (
                lambda: test_claims
            )

            # 10. Recognize device without cookie
            client.cookies.delete("zt_device_token")

            response = client.get(
                "/api/v1/devices/recognize"
            )

            check(
                response.status_code == 200
                and response.json()["recognized"] is False,
                "Device recognition fails safely without cookie",
            )

            # 11. Revoke device
            response = client.delete(
                f"/api/v1/devices/{registered_device_id}"
            )

            check(
                response.status_code == 200
                and response.json()["success"] is True,
                "Device owner can revoke their device",
            )

            # 12. Verify revoked device is inactive
            db = SessionLocal()

            try:
                device_record = db.execute(
                    __import__("sqlalchemy").select(
                        __import__("app.models.device", fromlist=["Device"]).Device
                    ).where(
                        __import__("app.models.device", fromlist=["Device"]).Device.id
                        == uuid.UUID(registered_device_id)
                    )
                ).scalar_one()

                check(
                    device_record.is_active is False
                    and device_record.is_trusted is False,
                    "Revoked device is inactive and untrusted",
                )

            finally:
                db.close()

            # 13. Recognize revoked device using original cookie.
            # The cookie was deleted from the client, so supply an
            # invalidated token to verify rejection separately.
            response = client.get(
                "/api/v1/devices/recognize",
                cookies={"zt_device_token": "revoked-device-token"},
            )

            check(
                response.status_code == 200
                and response.json()["recognized"] is False,
                "Unknown device token rejected",
            )

            # 14. Repeated revocation
            response = client.delete(
                f"/api/v1/devices/{registered_device_id}"
            )

            check(
                response.status_code == 404,
                "Repeated device revocation rejected",
            )

            # 15. Invalid device UUID
            response = client.delete(
                "/api/v1/devices/not-a-valid-uuid"
            )

            check(
                response.status_code == 422,
                "Invalid device UUID rejected",
            )

            # 16. Invalid device registration
            response = client.post(
                "/api/v1/devices/register",
                json={"device_name": ""},
            )

            check(
                response.status_code == 422,
                "Empty device name rejected",
            )

            # Capture the test user's ID for cleanup.
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
                    test_user_id = test_user.id
                    test_user.is_active = False
                    db.commit()

            finally:
                db.close()

        print(f"\nDEVICE API TESTS: {passed}/16 PASSED")

    finally:
        app.dependency_overrides.pop(
            get_current_user,
            None,
        )

        # Keep the temporary account inactive.
        if test_user_id is not None:
            db = SessionLocal()

            try:
                user = db.get(User, test_user_id)

                if user is not None:
                    user.is_active = False
                    db.commit()

            finally:
                db.close()


if __name__ == "__main__":
    run_tests()