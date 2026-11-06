import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.access_decision import AccessDecision
from app.models.user import User

from app.repositories.access_decision_repository import (
    AccessDecisionRepository,
)
from app.repositories.access_policy_repository import (
    AccessPolicyRepository,
)
from app.repositories.device_repository import DeviceRepository
from app.repositories.location_observation_repository import (
    LocationObservationRepository,
)
from app.repositories.office_geofence_repository import (
    OfficeGeofenceRepository,
)
from app.repositories.resource_definition_repository import (
    ResourceDefinitionRepository,
)
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.repositories.travel_authorization_repository import (
    TravelAuthorizationRepository,
)

from app.security.assurance import (
    is_step_up_satisfied,
    parse_acr_level,
)
from app.services.abac_service import ABACService
from app.services.audit_service import AuditService
from app.services.authorization_service import AuthorizationService
from app.services.device_service import DeviceService
from app.services.geofence_evaluator import GeofenceEvaluator
from app.services.risk_assessment_service import RiskAssessmentService
from app.services.vpn_verification_service import (
    VPNVerificationService,
)


class AccessDecisionService:

    def __init__(self, db: Session):
        self.db = db

        self.decision_repository = AccessDecisionRepository(db)
        self.resource_repository = ResourceDefinitionRepository(db)
        self.user_repository = UserRepository(db)
        self.role_repository = RoleRepository(db)
        self.device_repository = DeviceRepository(db)
        self.location_repository = LocationObservationRepository(db)
        self.geofence_repository = OfficeGeofenceRepository(db)
        self.policy_repository = AccessPolicyRepository(db)

        self.travel_authorization_repository = (
            TravelAuthorizationRepository(db)
        )

        self.authorization_service = AuthorizationService(
            user_repository=self.user_repository,
            role_repository=self.role_repository,
        )

        self.device_service = DeviceService(
            self.device_repository
        )

        self.vpn_verification_service = VPNVerificationService(db)

        self.risk_service = RiskAssessmentService(db)

        self.abac_service = ABACService(
            self.policy_repository
        )

        self.geofence_evaluator = GeofenceEvaluator()
        self.audit_service = AuditService(db)
        
        # Authentication level of the current request's token, recorded
        # on every decision (including early DENY results).
        self._token_acr: int | None = None

    def evaluate(
        self,
        current_user: User,
        action: str,
        resource_name: str,
        device_token: str | None = None,
        token_claims: dict | None = None,
    ) -> AccessDecision:

        request_id = uuid.uuid4()
        
        self._token_acr = parse_acr_level(
            (token_claims or {}).get("acr")
        )

        action = action.strip()
        resource_name = resource_name.strip()

        if not action or not resource_name:
            raise ValueError("Action and resource are required.")

        # User verification.
        if not current_user.is_active:
            return self._save_decision(
                request_id=request_id,
                user=current_user,
                action=action,
                resource=resource_name,
                decision="DENY",
                reason="User account is inactive.",
            )

        # Resource verification.
        resource = self.resource_repository.get_by_name(
            resource_name
        )

        if resource is None or not resource.is_active:
            return self._save_decision(
                request_id=request_id,
                user=current_user,
                action=action,
                resource=resource_name,
                decision="DENY",
                reason="Resource does not exist or is inactive.",
            )

        # RBAC verification.
        try:
            permissions = (
                self.authorization_service.get_user_permissions(
                    current_user.id
                )
            )

        except (LookupError, PermissionError):
            return self._save_decision(
                request_id=request_id,
                user=current_user,
                action=action,
                resource=resource_name,
                decision="DENY",
                reason="User authorization failed.",
            )

        if resource.required_permission not in permissions:
            return self._save_decision(
                request_id=request_id,
                user=current_user,
                action=action,
                resource=resource_name,
                decision="DENY",
                reason="Required RBAC permission is missing.",
            )

        # Device verification.
        device = None
        device_status = "UNKNOWN"

        if device_token:
            token_hash = self.device_service.hash_device_token(
                device_token
            )

            stored_device = (
                self.device_repository.get_by_token_hash(
                    token_hash
                )
            )

            if stored_device is not None:

                if stored_device.user_id != current_user.id:
                    return self._save_decision(
                        request_id=request_id,
                        user=current_user,
                        action=action,
                        resource=resource_name,
                        decision="DENY",
                        reason="Device identity does not match the user.",
                    )

                if not stored_device.is_active:
                    return self._save_decision(
                        request_id=request_id,
                        user=current_user,
                        action=action,
                        resource=resource_name,
                        decision="DENY",
                        reason="Device has been revoked or deactivated.",
                    )

                device = self.device_service.identify_device(
                    current_user.id,
                    device_token,
                )

                device_status = (
                    "TRUSTED"
                    if device and device.is_trusted
                    else "UNTRUSTED"
                )

        # Latest location observation.
        location = (
            self.location_repository.get_latest_observation(
                current_user.id
            )
        )

        # Fresh risk assessment.
        risk_assessment = self.risk_service.assess(
            user_id=current_user.id,
            device_id=device.id if device else None,
            location_observation_id=location.id if location else None,
        )

        risk_score = Decimal(str(risk_assessment.risk_score))
        risk_level = risk_assessment.risk_level

        # Resource access policy evaluation.
        access_policy = resource.access_policy

        geofence_results = []
        office_verified = False
        travel_authorization_verified = False
        corporate_vpn_verified = False

        # OFFICE ONLY.
        if access_policy == "OFFICE_ONLY":

            geofences = (
                self.geofence_repository.get_active_geofences()
            )

            if not geofences:
                return self._save_decision(
                    request_id=request_id,
                    user=current_user,
                    action=action,
                    resource=resource_name,
                    decision="DENY",
                    reason="No active company office geofence is configured.",
                    risk_assessment=risk_assessment,
                    extra_snapshot={
                        "access_policy": access_policy,
                        "office_verified": False,
                    },
                )

            for geofence in geofences:

                result = self.geofence_evaluator.evaluate(
                    location=location,
                    geofence=geofence,
                )

                geofence_results.append({
                    "office": geofence.name,
                    "status": result["status"],
                    "reason": result["reason"],
                })

            office_verified = any(
                result["status"] == "INSIDE"
                for result in geofence_results
            )

            if not office_verified:
                return self._save_decision(
                    request_id=request_id,
                    user=current_user,
                    action=action,
                    resource=resource_name,
                    decision="DENY",
                    reason="Office-premises verification failed.",
                    risk_assessment=risk_assessment,
                    extra_snapshot={
                        "access_policy": access_policy,
                        "office_verified": False,
                        "geofence_results": geofence_results,
                    },
                )

        # REMOTE ACCESS.
        elif access_policy == "REMOTE_ALLOWED":

            office_verified = False

        # TRAVEL ACCESS.
        elif access_policy == "TRAVEL_ALLOWED":

            travel_authorization = (
                self.travel_authorization_repository
                .get_active_authorization(current_user.id)
            )

            if travel_authorization is None:
                return self._save_decision(
                    request_id=request_id,
                    user=current_user,
                    action=action,
                    resource=resource_name,
                    decision="DENY",
                    reason=(
                        "No valid approved travel authorization exists."
                    ),
                    risk_assessment=risk_assessment,
                    extra_snapshot={
                        "access_policy": access_policy,
                        "travel_authorization_verified": False,
                    },
                )

            travel_authorization_verified = True

        # CORPORATE VPN ACCESS.
        elif access_policy == "VPN_REQUIRED":

            vpn_verified = (
                device_status == "TRUSTED"
                and self.vpn_verification_service.verify_session(
                    user_id=current_user.id,
                    device_id=device.id if device else None,
                )
            )

            if not vpn_verified:
                return self._save_decision(
                    request_id=request_id,
                    user=current_user,
                    action=action,
                    resource=resource_name,
                    decision="DENY",
                    reason=(
                        "A verified corporate VPN session "
                        "on a trusted device is required."
                    ),
                    risk_assessment=risk_assessment,
                    extra_snapshot={
                        "access_policy": access_policy,
                        "corporate_vpn_verified": False,
                        "device_status": device_status,
                    },
                )

            corporate_vpn_verified = True

        else:

            return self._save_decision(
                request_id=request_id,
                user=current_user,
                action=action,
                resource=resource_name,
                decision="DENY",
                reason="Unsupported resource access policy.",
                risk_assessment=risk_assessment,
                extra_snapshot={
                    "access_policy": access_policy,
                },
            )

        # ABAC evaluation.
        roles = self.role_repository.get_user_roles(
            current_user.id
        )

        abac_context = {
            "subject": {
                "user_id": str(current_user.id),
                "email": current_user.email,
                "is_active": current_user.is_active,
                "roles": [role.name for role in roles],
                "permissions": sorted(permissions),
            },
            "resource": {
                "name": resource.name,
                "access_policy": access_policy,
                "requires_office_location": (
                    access_policy == "OFFICE_ONLY"
                ),
            },
            "action": {
                "name": action,
            },
            "environment": {
                "device_status": device_status,
                "risk_score": float(risk_score),
                "risk_level": risk_level,
                "location_source": (
                    location.source if location else "UNKNOWN"
                ),
                "access_policy": access_policy,
                "office_verified": office_verified,
                "travel_authorization_verified": (
                    travel_authorization_verified
                ),
                "corporate_vpn_verified": corporate_vpn_verified,
            },
        }

        abac_result = self.abac_service.evaluate(
            abac_context
        )

        if not abac_result.allowed:
            return self._save_decision(
                request_id=request_id,
                user=current_user,
                action=action,
                resource=resource_name,
                decision="DENY",
                reason=abac_result.reason,
                risk_assessment=risk_assessment,
                extra_snapshot={
                    "matched_policies": list(
                        abac_result.matched_policies
                    ),
                    "geofence_results": geofence_results,
                    "access_policy": access_policy,
                    "office_verified": office_verified,
                    "travel_authorization_verified": (
                        travel_authorization_verified
                    ),
                    "corporate_vpn_verified": corporate_vpn_verified,
                },
            )

        # Authentication strength proven by the verified token.
        token_acr_level = parse_acr_level(
            (token_claims or {}).get("acr")
        )

        step_up_satisfied = is_step_up_satisfied(
            token_claims=token_claims,
            required_level=settings.STEP_UP_REQUIRED_ACR,
            max_age_seconds=settings.STEP_UP_MAX_AGE_SECONDS,
        )

        required_acr = None

        # Adaptive risk and device decisions.
        if risk_level == "CRITICAL" or risk_score >= 80:

            # Critical risk is never overridden by MFA.
            decision = "DENY"
            reason = "Critical security risk detected."

        elif (
            risk_level == "HIGH"
            or risk_score >= 60
            or device_status != "TRUSTED"
        ):

            if step_up_satisfied:
                decision = "ALLOW"
                reason = (
                    "Step-up authentication completed; "
                    "all Zero Trust security checks passed."
                )
            else:
                decision = "STEP_UP"
                required_acr = str(settings.STEP_UP_REQUIRED_ACR)

                if token_acr_level >= settings.STEP_UP_REQUIRED_ACR:
                    reason = (
                        "Previous MFA has expired; "
                        "fresh step-up authentication is required."
                    )
                else:
                    reason = (
                        "Additional authentication or device "
                        "verification is required."
                    )

        else:

            decision = "ALLOW"
            reason = "All Zero Trust security checks passed."

        return self._save_decision(
            request_id=request_id,
            user=current_user,
            action=action,
            resource=resource_name,
            decision=decision,
            reason=reason,
            risk_assessment=risk_assessment,
            extra_snapshot={
                "device_status": device_status,
                "risk_level": risk_level,
                "risk_score": float(risk_score),
                "matched_policies": list(
                    abac_result.matched_policies
                ),
                "geofence_results": geofence_results,
                "access_policy": access_policy,
                "office_verified": office_verified,
                "travel_authorization_verified": (
                    travel_authorization_verified
                ),
                "corporate_vpn_verified": corporate_vpn_verified,
                "token_acr": token_acr_level,
                "step_up_satisfied": step_up_satisfied,
                "required_acr": required_acr,
            },
        )

    def _save_decision(
        self,
        request_id: uuid.UUID,
        user: User,
        action: str,
        resource: str,
        decision: str,
        reason: str,
        risk_assessment=None,
        extra_snapshot: dict | None = None,
    ) -> AccessDecision:

        snapshot = dict(extra_snapshot or {})
        snapshot.setdefault("token_acr", self._token_acr)

        access_decision = AccessDecision(
            request_id=request_id,
            user_id=user.id,
            risk_assessment_id=(
                risk_assessment.id
                if risk_assessment is not None
                else None
            ),
            action=action,
            resource=resource,
            decision=decision,
            risk_score=(
                risk_assessment.risk_score
                if risk_assessment is not None
                else None
            ),
            policy_snapshot=snapshot,
            reason=reason,
        )

        self.decision_repository.add(access_decision)
        self.decision_repository.flush()

        # Retrieve the latest available location observation.
        location = self.location_repository.get_latest_observation(
            user.id
        )

        self.audit_service.record_event(
            event_type="ACCESS_DECISION_EVALUATED",
            action=action,
            resource_type="RESOURCE",
            resource_id=resource,
            outcome=decision,
            actor_user_id=user.id,
            request_id=request_id,
            details={
                "decision_id": str(access_decision.id),
                "reason": reason,
                "required_acr": snapshot.get("required_acr"),
                "token_acr": snapshot.get("token_acr"),
                "risk_score": (
                    float(risk_assessment.risk_score)
                    if risk_assessment is not None
                    else None
                ),
                "location_observation_id": (
                    str(location.id)
                    if location is not None
                    else None
                ),
                "location_accuracy_meters": (
                    float(location.accuracy_meters)
                    if location is not None
                    and location.accuracy_meters is not None
                    else None
                ),
            },
            city=location.city if location else None,
            region=location.region if location else None,
            country=location.country_name if location else None,
            location_source=location.source if location else None,
        )

        return access_decision