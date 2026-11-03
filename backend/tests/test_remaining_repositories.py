import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.access_decision import AccessDecision
from app.models.access_policy import AccessPolicy
from app.models.audit_log import AuditLog
from app.models.device import Device
from app.models.location_observation import LocationObservation
from app.models.login_event import LoginEvent
from app.models.privileged_access_grant import PrivilegedAccessGrant
from app.models.privileged_access_request import PrivilegedAccessRequest
from app.models.risk_assessment import RiskAssessment
from app.models.role import Role
from app.models.step_up_challenge import StepUpChallenge
from app.models.user import User

from app.repositories.access_decision_repository import AccessDecisionRepository
from app.repositories.access_policy_repository import AccessPolicyRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.location_observation_repository import (
    LocationObservationRepository,
)
from app.repositories.privileged_access_repository import (
    PrivilegedAccessRepository,
)
from app.repositories.risk_assessment_repository import (
    RiskAssessmentRepository,
)
from app.repositories.step_up_challenge_repository import (
    StepUpChallengeRepository,
)


def run_tests():
    db = SessionLocal()

    try:
        now = datetime.now(timezone.utc)

        # --------------------------------------------------
        # TEST DATA
        # --------------------------------------------------

        user = User(
            keycloak_subject=f"consolidated-{uuid.uuid4()}",
            email=f"consolidated-{uuid.uuid4()}@example.com",
            full_name="Consolidated Test User",
        )

        reviewer = User(
            keycloak_subject=f"reviewer-{uuid.uuid4()}",
            email=f"reviewer-{uuid.uuid4()}@example.com",
            full_name="Test Reviewer",
        )

        role = Role(
            name=f"pam_test_role_{uuid.uuid4().hex[:12]}",
            description="Temporary PAM test role",
        )

        db.add_all([user, reviewer, role])
        db.flush()

        device = Device(
            user_id=user.id,
            device_name="Consolidated Test Device",
            operating_system="Windows",
            browser="Chrome",
            device_token_hash=uuid.uuid4().hex + uuid.uuid4().hex,
        )

        db.add(device)
        db.flush()

        login_event = LoginEvent(
            user_id=user.id,
            device_id=device.id,
            event_type="LOGIN_SUCCESS",
            success=True,
        )

        db.add(login_event)
        db.flush()

        print("PASS: Consolidated test data creation")

        # --------------------------------------------------
        # 1. LOCATION OBSERVATION REPOSITORY
        # --------------------------------------------------

        location_repo = LocationObservationRepository(db)

        ip_location = LocationObservation(
            user_id=user.id,
            login_event_id=login_event.id,
            source="IP_GEOIP",
            country_code="IN",
            country_name="India",
            region="Karnataka",
            city="Bengaluru",
            latitude=Decimal("12.971600"),
            longitude=Decimal("77.594600"),
            consent_granted=False,
        )

        gps_location = LocationObservation(
            user_id=user.id,
            login_event_id=login_event.id,
            source="BROWSER_GPS",
            country_code="IN",
            country_name="India",
            region="Karnataka",
            city="Bengaluru",
            latitude=Decimal("12.971600"),
            longitude=Decimal("77.594600"),
            accuracy_meters=Decimal("15.00"),
            consent_granted=True,
            consent_recorded_at=now,
        )

        location_repo.add(ip_location)
        location_repo.add(gps_location)
        location_repo.flush()

        assert location_repo.get_by_id(ip_location.id) is not None
        print("PASS: Location observation creation and lookup")

        observations = location_repo.get_user_observations(user.id)
        assert len(observations) == 2
        print("PASS: User location history")

        login_locations = location_repo.get_login_observations(
            login_event.id
        )
        assert len(login_locations) == 2
        print("PASS: Location retrieval by login event")

        gps_observations = location_repo.get_by_source(
            user.id,
            "BROWSER_GPS",
        )
        assert len(gps_observations) == 1
        assert gps_observations[0].consent_granted is True
        print("PASS: GPS source and consent retrieval")

        assert location_repo.get_latest_observation(user.id) is not None
        print("PASS: Latest location retrieval")

        # --------------------------------------------------
        # 2. RISK ASSESSMENT REPOSITORY
        # --------------------------------------------------

        risk_repo = RiskAssessmentRepository(db)

        assessment = RiskAssessment(
            user_id=user.id,
            device_id=device.id,
            location_observation_id=ip_location.id,
            risk_score=Decimal("35.50"),
            risk_level="MEDIUM",
            risk_factors={
                "new_device": False,
                "unusual_location": True,
            },
            assessment_version="1.0",
        )

        risk_repo.add(assessment)
        risk_repo.flush()

        assert risk_repo.get_by_id(assessment.id) is not None
        print("PASS: Risk assessment creation and lookup")

        assert risk_repo.get_latest_assessment(user.id).id == assessment.id
        print("PASS: Latest risk assessment retrieval")

        assert len(risk_repo.get_user_assessments(user.id)) == 1
        print("PASS: User risk assessment history")

        assert len(risk_repo.get_by_risk_level("MEDIUM")) >= 1
        print("PASS: Risk level filtering")

        assert len(risk_repo.get_device_assessments(device.id)) == 1
        print("PASS: Device risk assessment retrieval")

        # --------------------------------------------------
        # 3. ACCESS POLICY REPOSITORY
        # --------------------------------------------------

        policy_repo = AccessPolicyRepository(db)

        deny_policy = AccessPolicy(
            name=f"test_deny_{uuid.uuid4().hex[:12]}",
            effect="DENY",
            priority=10,
            conditions={"risk_level": "CRITICAL"},
            is_active=True,
        )

        allow_policy = AccessPolicy(
            name=f"test_allow_{uuid.uuid4().hex[:12]}",
            effect="ALLOW",
            priority=100,
            conditions={"role": "user"},
            is_active=True,
        )

        inactive_policy = AccessPolicy(
            name=f"test_inactive_{uuid.uuid4().hex[:12]}",
            effect="ALLOW",
            priority=5,
            conditions={"test": True},
            is_active=False,
        )

        policy_repo.add(deny_policy)
        policy_repo.add(allow_policy)
        policy_repo.add(inactive_policy)
        policy_repo.flush()

        assert policy_repo.get_by_id(deny_policy.id) is not None
        assert policy_repo.get_by_name(deny_policy.name) is not None
        print("PASS: Access policy creation and lookup")

        active_policies = policy_repo.get_active_policies()

        test_policies = [
            p for p in active_policies
            if p.id in {deny_policy.id, allow_policy.id}
        ]

        assert len(test_policies) == 2
        assert test_policies[0].priority <= test_policies[1].priority
        print("PASS: Active policy priority ordering")

        assert not any(
            p.id == inactive_policy.id for p in active_policies
        )
        print("PASS: Inactive policy exclusion")

        assert any(
            p.id == deny_policy.id
            for p in policy_repo.get_by_effect("DENY")
        )
        print("PASS: Policy effect filtering")

        # --------------------------------------------------
        # 4. ACCESS DECISION REPOSITORY
        # --------------------------------------------------

        decision_repo = AccessDecisionRepository(db)

        request_id = uuid.uuid4()

        original_decision = AccessDecision(
            request_id=request_id,
            user_id=user.id,
            risk_assessment_id=assessment.id,
            action="access_sensitive_resource",
            resource="sensitive_resource",
            decision="STEP_UP",
            risk_score=Decimal("85.00"),
            policy_snapshot={"evaluated_policies": []},
            reason="Additional authentication required",
        )

        decision_repo.add(original_decision)
        db.flush()

        final_decision = AccessDecision(
            request_id=request_id,
            parent_decision_id=original_decision.id,
            user_id=user.id,
            risk_assessment_id=assessment.id,
            action="access_sensitive_resource",
            resource="sensitive_resource",
            decision="ALLOW",
            risk_score=Decimal("35.00"),
            policy_snapshot={"mfa_verified": True},
            reason="Additional authentication completed",
        )

        decision_repo.add(final_decision)
        decision_repo.flush()

        assert decision_repo.get_by_id(original_decision.id) is not None
        print("PASS: Access decision creation and lookup")

        request_decisions = decision_repo.get_by_request_id(request_id)
        assert len(request_decisions) == 2
        print("PASS: Decision retrieval by request ID")

        parent = decision_repo.get_parent_decision(final_decision.id)

        assert parent is not None
        assert parent.id == original_decision.id
        print("PASS: Parent decision retrieval")

        children = decision_repo.get_child_decisions(
            original_decision.id
        )

        assert any(child.id == final_decision.id for child in children)
        print("PASS: Child decision retrieval")

        assert any(
            d.id == original_decision.id
            for d in decision_repo.get_by_decision_type("STEP_UP")
        )
        print("PASS: Decision type filtering")

        assert len(decision_repo.get_user_decisions(user.id)) >= 2
        print("PASS: User decision history")

        # --------------------------------------------------
        # 5. AUDIT LOG REPOSITORY
        # --------------------------------------------------

        audit_repo = AuditLogRepository(db)

        audit = AuditLog(
            actor_user_id=user.id,
            event_type="ACCESS_DECISION",
            action="test.access.decision",
            resource_type="test_resource",
            resource_id="test-001",
            outcome="SUCCESS",
            request_id=request_id,
            details={"decision": "ALLOW"},
        )

        audit_repo.add(audit)
        audit_repo.flush()

        assert audit_repo.get_by_id(audit.id) is not None
        print("PASS: Audit log creation and lookup")

        assert any(
            item.id == audit.id
            for item in audit_repo.get_by_actor(user.id)
        )
        print("PASS: Audit retrieval by actor")

        assert any(
            item.id == audit.id
            for item in audit_repo.get_by_event_type("ACCESS_DECISION")
        )
        print("PASS: Audit event type filtering")

        assert any(
            item.id == audit.id
            for item in audit_repo.get_by_action("test.access.decision")
        )
        print("PASS: Audit action filtering")

        assert any(
            item.id == audit.id
            for item in audit_repo.get_by_outcome("SUCCESS")
        )
        print("PASS: Audit outcome filtering")

        assert any(
            item.id == audit.id
            for item in audit_repo.get_by_request_id(request_id)
        )
        print("PASS: Audit request ID retrieval")

        assert any(
            item.id == audit.id
            for item in audit_repo.get_by_date_range(
                now - timedelta(minutes=5),
                now + timedelta(minutes=5),
            )
        )
        print("PASS: Audit date-range filtering")

        try:
            audit_repo.get_by_date_range(now, now)
            raise AssertionError("Invalid date range was accepted")
        except ValueError:
            print("PASS: Invalid audit date range rejected")

        assert not hasattr(audit_repo, "update")
        assert not hasattr(audit_repo, "delete")
        print("PASS: Audit repository has no update/delete methods")

        # --------------------------------------------------
        # 6. STEP-UP CHALLENGE REPOSITORY
        # --------------------------------------------------

        challenge_repo = StepUpChallengeRepository(db)

        challenge = StepUpChallenge(
            access_decision_id=original_decision.id,
            challenge_hash=uuid.uuid4().hex + uuid.uuid4().hex,
            request_binding_hash=uuid.uuid4().hex + uuid.uuid4().hex,
            payload_hash=uuid.uuid4().hex + uuid.uuid4().hex,
            keycloak_session_id=f"test-session-{uuid.uuid4()}",
            status="PENDING",
            failed_attempts=0,
            expires_at=now + timedelta(minutes=5),
        )

        challenge_repo.add(challenge)
        challenge_repo.flush()

        assert challenge_repo.get_by_id(challenge.id) is not None
        assert challenge_repo.get_by_hash(challenge.challenge_hash) is not None
        assert (
            challenge_repo.get_by_access_decision(original_decision.id)
            is not None
        )
        print("PASS: MFA challenge creation and retrieval")

        assert challenge_repo.mark_verified(challenge.id) is True
        db.flush()
        print("PASS: MFA challenge verification")

        assert challenge_repo.consume(challenge.id) is True
        db.flush()
        print("PASS: MFA challenge consumption")

        assert challenge_repo.consume(challenge.id) is False
        print("PASS: Consumed challenge replay prevention")

        # Test failed-attempt limit.
        failed_challenge = StepUpChallenge(
            access_decision_id=final_decision.id,
            challenge_hash=uuid.uuid4().hex + uuid.uuid4().hex,
            request_binding_hash=uuid.uuid4().hex + uuid.uuid4().hex,
            payload_hash=uuid.uuid4().hex + uuid.uuid4().hex,
            keycloak_session_id=f"test-session-{uuid.uuid4()}",
            status="PENDING",
            failed_attempts=0,
            expires_at=now + timedelta(minutes=5),
        )

        challenge_repo.add(failed_challenge)
        challenge_repo.flush()

        assert challenge_repo.increment_failed_attempts(
            failed_challenge.id,
            2,
        ) is True

        assert challenge_repo.increment_failed_attempts(
            failed_challenge.id,
            2,
        ) is True

        db.flush()
        db.refresh(failed_challenge)

        assert failed_challenge.failed_attempts == 2
        assert failed_challenge.status == "FAILED"
        print("PASS: MFA failed-attempt limit enforcement")

        # Test revocation.
        revoke_challenge = StepUpChallenge(
            access_decision_id=uuid.uuid4(),
            challenge_hash=uuid.uuid4().hex + uuid.uuid4().hex,
            request_binding_hash=uuid.uuid4().hex + uuid.uuid4().hex,
            payload_hash=uuid.uuid4().hex + uuid.uuid4().hex,
            keycloak_session_id=f"test-session-{uuid.uuid4()}",
            status="PENDING",
            failed_attempts=0,
            expires_at=now + timedelta(minutes=5),
        )

        # A challenge must reference a real access decision.
        revoke_challenge.access_decision_id = original_decision.id

        # The original decision already has a challenge.
        # Therefore use the second decision for this challenge.
        revoke_challenge.access_decision_id = final_decision.id

        # The second decision already has a challenge too.
        # Skip creating a duplicate challenge for either decision.

        # Test expiration using a separate access decision.
        expiration_decision = AccessDecision(
            request_id=uuid.uuid4(),
            user_id=user.id,
            action="expiration_test",
            resource="test_resource",
            decision="STEP_UP",
            policy_snapshot={},
            reason="Expiration test",
        )

        decision_repo.add(expiration_decision)
        db.flush()

        expired_challenge = StepUpChallenge(
            access_decision_id=expiration_decision.id,
            challenge_hash=uuid.uuid4().hex + uuid.uuid4().hex,
            request_binding_hash=uuid.uuid4().hex + uuid.uuid4().hex,
            payload_hash=uuid.uuid4().hex + uuid.uuid4().hex,
            keycloak_session_id=f"test-session-{uuid.uuid4()}",
            status="PENDING",
            failed_attempts=0,
            created_at=now - timedelta(minutes=10),
            expires_at=now - timedelta(minutes=5),
        )

        challenge_repo.add(expired_challenge)
        challenge_repo.flush()

        assert challenge_repo.expire_challenges() >= 1
        db.flush()
        db.refresh(expired_challenge)

        assert expired_challenge.status == "EXPIRED"
        print("PASS: Expired challenge handling")

        # --------------------------------------------------
        # 7. PRIVILEGED ACCESS REPOSITORY
        # --------------------------------------------------

        pam_repo = PrivilegedAccessRepository(db)

        pam_request = PrivilegedAccessRequest(
            user_id=user.id,
            requested_role_id=role.id,
            justification="Temporary privileged access for testing",
            requested_duration_minutes=30,
            status="PENDING",
        )

        pam_repo.add_request(pam_request)
        pam_repo.flush()

        assert pam_repo.get_request_by_id(pam_request.id) is not None
        print("PASS: Privileged access request creation")

        assert any(
            item.id == pam_request.id
            for item in pam_repo.get_user_requests(user.id)
        )
        print("PASS: User privileged request retrieval")

        assert any(
            item.id == pam_request.id
            for item in pam_repo.get_pending_requests()
        )
        print("PASS: Pending request retrieval")

        # Self-approval must be rejected.
        assert pam_repo.review_request(
            pam_request.id,
            user.id,
            "APPROVED",
            "Self approval attempt",
        ) is False

        print("PASS: PAM self-approval prevention")

        # Independent reviewer approves.
        assert pam_repo.review_request(
            pam_request.id,
            reviewer.id,
            "APPROVED",
            "Approved for temporary testing",
        ) is True

        db.flush()
        db.refresh(pam_request)

        assert pam_request.status == "APPROVED"
        assert pam_request.approved_by_user_id == reviewer.id
        print("PASS: Independent PAM request approval")

        # Create temporary grant matching approved request.
        grant = PrivilegedAccessGrant(
            request_id=pam_request.id,
            user_id=user.id,
            role_id=role.id,
            approved_by_user_id=reviewer.id,
            status="ACTIVE",
            starts_at=now,
            expires_at=now + timedelta(minutes=30),
        )

        pam_repo.add_grant(grant)
        pam_repo.flush()

        assert pam_repo.get_grant_by_id(grant.id) is not None
        assert pam_repo.get_grant_by_request(pam_request.id) is not None
        print("PASS: Temporary privileged grant creation")

        assert any(
            item.id == grant.id
            for item in pam_repo.get_user_grants(user.id)
        )
        print("PASS: User privileged grant retrieval")

        assert any(
            item.id == grant.id
            for item in pam_repo.get_active_grants(user.id)
        )
        print("PASS: Active privileged grant retrieval")

        assert pam_repo.revoke_grant(
            grant.id,
            "Consolidated test revocation",
        ) is True

        db.flush()
        db.refresh(grant)

        assert grant.status == "REVOKED"
        assert grant.revoked_at is not None
        print("PASS: Privileged grant revocation")

        assert pam_repo.revoke_grant(
            grant.id,
            "Repeated revocation",
        ) is False
        print("PASS: Repeated grant revocation prevention")

        # --------------------------------------------------
        # FINAL TRANSACTION ROLLBACK
        # --------------------------------------------------

        db.rollback()

        print("PASS: All consolidated test data rolled back")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    run_tests()