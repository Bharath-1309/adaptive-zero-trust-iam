from dataclasses import dataclass
from typing import Any

from app.models.access_policy import AccessPolicy
from app.repositories.access_policy_repository import (
    AccessPolicyRepository,
)


ALLOWED_SECTIONS = {
    "subject",
    "resource",
    "action",
    "environment",
}

ALLOWED_OPERATORS = {
    "eq",
    "ne",
    "in",
    "not_in",
    "gt",
    "gte",
    "lt",
    "lte",
    "contains",
    "exists",
}


class PolicyConfigurationError(Exception):
    """Raised when an ABAC policy has an invalid structure."""


@dataclass(frozen=True)
class ABACEvaluationResult:
    allowed: bool
    effect: str
    reason: str
    matched_policies: tuple[dict[str, Any], ...]


class ABACService:

    @classmethod
    def validate_policy_conditions(
        cls,
        conditions: dict,
    ) -> None:

        if not isinstance(conditions, dict) or not conditions:
            raise PolicyConfigurationError(
                "Policy conditions must be a non-empty object."
            )

        if set(conditions) - ALLOWED_SECTIONS:
            raise PolicyConfigurationError(
                "Policy contains unsupported sections."
            )

        for section, attributes in conditions.items():

            if not isinstance(attributes, dict) or not attributes:
                raise PolicyConfigurationError(
                    f"Policy section '{section}' must contain conditions."
                )

            for attribute_path, operators in attributes.items():

                if (
                    not isinstance(attribute_path, str)
                    or not attribute_path.strip()
                    or any(not part.strip() for part in attribute_path.split("."))
                ):
                    raise PolicyConfigurationError(
                        "Invalid attribute path."
                    )

                if not isinstance(operators, dict) or not operators:
                    raise PolicyConfigurationError(
                        f"Invalid conditions for '{attribute_path}'."
                    )

                for operator, expected in operators.items():

                    if operator not in ALLOWED_OPERATORS:
                        raise PolicyConfigurationError(
                            f"Unsupported operator: {operator}"
                        )

                    if operator == "exists" and not isinstance(expected, bool):
                        raise PolicyConfigurationError(
                            "'exists' requires a boolean."
                        )

                    if operator in {"in", "not_in"} and not isinstance(
                        expected, (list, tuple, set, str)
                    ):
                        raise PolicyConfigurationError(
                            f"'{operator}' requires a collection."
                        )

    def __init__(
        self,
        policy_repository: AccessPolicyRepository,
    ):
        self.policy_repository = policy_repository

    @staticmethod
    def _get_attribute(
        attributes: dict,
        attribute_path: str,
    ) -> tuple[bool, Any]:

        current = attributes

        for part in attribute_path.split("."):
            if not isinstance(current, dict) or part not in current:
                return False, None

            current = current[part]

        return True, current

    @staticmethod
    def _compare(
        actual: Any,
        operator: str,
        expected: Any,
    ) -> bool:

        try:
            if operator in {"eq", "ne"}:
                if type(actual) is not type(expected):
                    return False

                return (
                    actual == expected
                    if operator == "eq"
                    else actual != expected
                )

            if operator in {"gt", "gte", "lt", "lte"}:

                if (
                    isinstance(actual, bool)
                    or isinstance(expected, bool)
                    or not isinstance(actual, (int, float))
                    or not isinstance(expected, (int, float))
                ):
                    return False

                if operator == "gt":
                    return actual > expected

                if operator == "gte":
                    return actual >= expected

                if operator == "lt":
                    return actual < expected

                return actual <= expected

            if operator == "in":
                return actual in expected

            if operator == "not_in":
                return actual not in expected

            if operator == "contains":
                if isinstance(actual, dict):
                    return expected in actual

                if isinstance(actual, (list, tuple, set, str)):
                    return expected in actual

                return False

            if operator == "exists":
                return actual is not None

        except (TypeError, ValueError):
            return False

        return False

    @classmethod
    def _evaluate_attribute_conditions(
        cls,
        attributes: dict,
        conditions: dict,
    ) -> bool:

        for attribute_path, operators in conditions.items():

            if not isinstance(attribute_path, str) or not attribute_path:
                raise PolicyConfigurationError(
                    "Invalid attribute path."
                )

            if not isinstance(operators, dict) or not operators:
                raise PolicyConfigurationError(
                    f"Invalid conditions for attribute: {attribute_path}"
                )

            exists, actual = cls._get_attribute(
                attributes,
                attribute_path,
            )

            for operator, expected in operators.items():

                if operator not in ALLOWED_OPERATORS:
                    raise PolicyConfigurationError(
                        f"Unsupported ABAC operator: {operator}"
                    )

                if operator == "exists":
                    if not isinstance(expected, bool):
                        raise PolicyConfigurationError(
                            "'exists' requires a boolean value."
                        )

                    if exists != expected:
                        return False

                    continue

                if not exists:
                    return False

                if operator in {"in", "not_in"} and not isinstance(
                    expected, (list, tuple, set, str)
                ):
                    raise PolicyConfigurationError(
                        f"Operator '{operator}' requires a collection."
                    )

                if not cls._compare(actual, operator, expected):
                    return False

        return True

    @classmethod
    def _policy_matches(
        cls,
        policy: AccessPolicy,
        context: dict,
    ) -> bool:

        conditions = policy.conditions

        if not isinstance(conditions, dict):
            raise PolicyConfigurationError(
                f"Policy '{policy.name}' conditions must be an object."
            )

        for section, section_conditions in conditions.items():

            if section not in ALLOWED_SECTIONS:
                raise PolicyConfigurationError(
                    f"Unsupported policy section: {section}"
                )

            if not isinstance(section_conditions, dict):
                raise PolicyConfigurationError(
                    f"Policy section '{section}' must be an object."
                )

            section_attributes = context.get(section, {})

            if not isinstance(section_attributes, dict):
                return False

            if not cls._evaluate_attribute_conditions(
                section_attributes,
                section_conditions,
            ):
                return False

        return True

    def evaluate(
        self,
        context: dict,
    ) -> ABACEvaluationResult:

        if not isinstance(context, dict):
            raise ValueError("ABAC context must be an object.")

        if set(context) - ALLOWED_SECTIONS:
            raise ValueError("ABAC context contains unsupported sections.")

        policies = self.policy_repository.get_active_policies()

        matched = []

        for policy in policies:

            if policy.effect not in {"ALLOW", "DENY"}:
                raise PolicyConfigurationError(
                    f"Invalid effect in policy '{policy.name}'."
                )

            if self._policy_matches(policy, context):
                matched.append(policy)

        matched_snapshot = tuple(
            {
                "id": str(policy.id),
                "name": policy.name,
                "effect": policy.effect,
                "priority": policy.priority,
                "conditions": policy.conditions,
            }
            for policy in matched
        )

        # Explicit DENY always takes precedence.
        deny_policies = [
            policy for policy in matched
            if policy.effect == "DENY"
        ]

        if deny_policies:
            return ABACEvaluationResult(
                allowed=False,
                effect="DENY",
                reason="An explicit DENY policy matched.",
                matched_policies=matched_snapshot,
            )

        allow_policies = [
            policy for policy in matched
            if policy.effect == "ALLOW"
        ]

        if allow_policies:
            return ABACEvaluationResult(
                allowed=True,
                effect="ALLOW",
                reason="At least one ALLOW policy matched and no DENY policy matched.",
                matched_policies=matched_snapshot,
            )

        return ABACEvaluationResult(
            allowed=False,
            effect="DENY",
            reason="No ABAC policy matched. Default deny applied.",
            matched_policies=matched_snapshot,
        )