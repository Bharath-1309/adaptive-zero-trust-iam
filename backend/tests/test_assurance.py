import pytest

from app.security.assurance import (
    is_step_up_satisfied,
    parse_acr_level,
)

NOW = 1_000_000.0


@pytest.mark.parametrize(
    "value, expected",
    [
        ("0", 0),
        ("1", 1),
        ("2", 2),
        (" 2 ", 2),
        (None, 0),
        (2, 0),
        ("", 0),
        ("two", 0),
        ("-1", 0),
        ("2.5", 0),
        ("\u0662", 0),
    ],
)
def test_parse_acr_level(value, expected):
    assert parse_acr_level(value) == expected


def satisfied(claims):
    return is_step_up_satisfied(
        claims, required_level=2, max_age_seconds=300, now=NOW
    )


def test_fresh_level_2_token_is_accepted():
    assert satisfied({"acr": "2", "auth_time": NOW - 60})


def test_level_1_token_is_rejected_downgrade_attempt():
    assert not satisfied({"acr": "1", "auth_time": NOW - 10})


def test_level_0_sso_token_is_rejected():
    assert not satisfied({"acr": "0", "auth_time": NOW - 10})


def test_stale_mfa_is_rejected():
    assert not satisfied({"acr": "2", "auth_time": NOW - 301})


def test_missing_auth_time_is_rejected():
    assert not satisfied({"acr": "2"})


def test_malformed_auth_time_is_rejected():
    assert not satisfied({"acr": "2", "auth_time": "now"})
    assert not satisfied({"acr": "2", "auth_time": True})


def test_future_auth_time_is_rejected():
    assert not satisfied({"acr": "2", "auth_time": NOW + 500})


def test_no_claims_is_rejected():
    assert not satisfied(None)
    assert not satisfied({})