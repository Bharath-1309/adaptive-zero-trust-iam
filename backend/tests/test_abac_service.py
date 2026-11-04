from types import SimpleNamespace
from uuid import uuid4

from app.services.abac_service import (
    ABACService,
    PolicyConfigurationError,
)


class MockPolicyRepository:

    def __init__(self, policies):
        self.policies = policies

    def get_active_policies(self):
        return self.policies


def make_policy(name, effect, conditions, priority=100):
    return SimpleNamespace(
        id=uuid4(),
        name=name,
        effect=effect,
        conditions=conditions,
        priority=priority,
    )


def make_service(policies):
    return ABACService(
        MockPolicyRepository(policies)
    )


def test_matching_allow_policy():
    policy = make_policy(
        "allow_admin_read",
        "ALLOW",
        {
            "subject": {
                "roles": {"contains": "admin"}
            },
            "action": {
                "name": {"eq": "read"}
            },
        },
    )

    context = {
        "subject": {"roles": ["admin"]},
        "action": {"name": "read"},
    }

    result = make_service([policy]).evaluate(context)

    assert result.allowed is True
    assert result.effect == "ALLOW"


def test_non_matching_policy():
    policy = make_policy(
        "allow_admin_only",
        "ALLOW",
        {
            "subject": {
                "roles": {"contains": "admin"}
            }
        },
    )

    context = {
        "subject": {"roles": ["user"]}
    }

    result = make_service([policy]).evaluate(context)

    assert result.allowed is False
    assert result.effect == "DENY"


def test_default_deny():
    result = make_service([]).evaluate(
        {"subject": {"is_active": True}}
    )

    assert result.allowed is False
    assert result.effect == "DENY"
    assert "Default deny" in result.reason


def test_explicit_deny_overrides_allow():
    allow_policy = make_policy(
        "general_allow",
        "ALLOW",
        {"subject": {"is_active": {"eq": True}}},
        priority=1,
    )

    deny_policy = make_policy(
        "high_risk_deny",
        "DENY",
        {"environment": {"risk_level": {"eq": "HIGH"}}},
        priority=100,
    )

    context = {
        "subject": {"is_active": True},
        "environment": {"risk_level": "HIGH"},
    }

    result = make_service(
        [allow_policy, deny_policy]
    ).evaluate(context)

    assert result.allowed is False
    assert result.effect == "DENY"
    assert len(result.matched_policies) == 2


def test_missing_attribute_does_not_match():
    policy = make_policy(
        "trusted_device_only",
        "ALLOW",
        {
            "environment": {
                "device_trusted": {"eq": True}
            }
        },
    )

    result = make_service([policy]).evaluate(
        {"environment": {}}
    )

    assert result.allowed is False


def test_exists_operator():
    policy = make_policy(
        "location_required",
        "ALLOW",
        {
            "environment": {
                "country_code": {"exists": True}
            }
        },
    )

    result = make_service([policy]).evaluate(
        {"environment": {"country_code": "IN"}}
    )

    assert result.allowed is True


def test_numeric_comparison_operators():
    policy = make_policy(
        "risk_threshold",
        "ALLOW",
        {
            "environment": {
                "risk_score": {
                    "gte": 0,
                    "lte": 30,
                }
            }
        },
    )

    result = make_service([policy]).evaluate(
        {"environment": {"risk_score": 20}}
    )

    assert result.allowed is True


def test_in_operator():
    policy = make_policy(
        "allowed_countries",
        "ALLOW",
        {
            "environment": {
                "country_code": {
                    "in": ["IN", "US", "GB"]
                }
            }
        },
    )

    result = make_service([policy]).evaluate(
        {"environment": {"country_code": "IN"}}
    )

    assert result.allowed is True


def test_not_in_operator():
    policy = make_policy(
        "restricted_countries",
        "DENY",
        {
            "environment": {
                "country_code": {
                    "not_in": ["IN", "US"]
                }
            }
        },
    )

    result = make_service([policy]).evaluate(
        {"environment": {"country_code": "RU"}}
    )

    assert result.allowed is False
    assert result.effect == "DENY"


def test_invalid_operator_rejected():
    policy = make_policy(
        "invalid_policy",
        "ALLOW",
        {
            "subject": {
                "is_active": {"invalid_operator": True}
            }
        },
    )

    try:
        make_service([policy]).evaluate(
            {"subject": {"is_active": True}}
        )
    except PolicyConfigurationError:
        return

    raise AssertionError("Invalid operator was not rejected.")


def test_invalid_context_rejected():
    try:
        make_service([]).evaluate(
            {"unsupported": {}}
        )
    except ValueError:
        return

    raise AssertionError("Invalid context was not rejected.")


def run_tests():

    tests = [
        test_matching_allow_policy,
        test_non_matching_policy,
        test_default_deny,
        test_explicit_deny_overrides_allow,
        test_missing_attribute_does_not_match,
        test_exists_operator,
        test_numeric_comparison_operators,
        test_in_operator,
        test_not_in_operator,
        test_invalid_operator_rejected,
        test_invalid_context_rejected,
    ]

    passed = 0

    for test in tests:
        test()
        passed += 1
        print(f"PASS: {test.__name__}")

    print(f"\nABAC TEST RESULTS: {passed}/{len(tests)} PASSED")


if __name__ == "__main__":
    run_tests()