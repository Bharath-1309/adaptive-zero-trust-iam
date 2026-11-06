import time


def parse_acr_level(acr: object) -> int:
    """
    Convert a Keycloak `acr` claim into a numeric level.

    Keycloak issues "0" (SSO session, no fresh login), "1" (password)
    and "2" (password + OTP) in this project. Anything that is not a
    clean non-negative integer string is treated as level 0, so an
    unexpected value never grants extra trust (fail closed).
    """

    if not isinstance(acr, str):
        return 0

    acr = acr.strip()

    if not acr.isascii() or not acr.isdigit():
        return 0

    return int(acr)


def is_step_up_satisfied(
    token_claims: dict | None,
    required_level: int,
    max_age_seconds: int,
    now: float | None = None,
) -> bool:
    """
    True only when the token proves a recent authentication at or
    above the required level.

    - `acr` must reach the required level.
    - `auth_time` (when the user last actually logged in) must exist
      and be recent. A missing or malformed value means NOT satisfied.
    """

    if not token_claims:
        return False

    if parse_acr_level(token_claims.get("acr")) < required_level:
        return False

    auth_time = token_claims.get("auth_time")

    if isinstance(auth_time, bool) or not isinstance(
        auth_time, (int, float)
    ):
        return False

    current = time.time() if now is None else now
    age = current - auth_time

    # Reject future-dated values as well as stale ones.
    return 0 <= age <= max_age_seconds