from dataclasses import dataclass, replace
from typing import Mapping, Optional

from opscontrol.models import Draft

SUPPORTED_CHANNELS = {"email", "sms"}

# Sentinel used by apply_customer_profile to identify the default values
_DEFAULT_GREETING = "Hello,"
_DEFAULT_SIGNOFF = "OpsControl Operations"


@dataclass(frozen=True)
class CustomerProfile:
    customer_id: str
    preferred_channel: str = "email"
    greeting: str = _DEFAULT_GREETING
    signoff: str = _DEFAULT_SIGNOFF
    tone: str = "concise"

    def __post_init__(self) -> None:
        if not self.customer_id.strip():
            raise ValueError("customer_id cannot be empty")

        if self.preferred_channel not in SUPPORTED_CHANNELS:
            allowed = ", ".join(sorted(SUPPORTED_CHANNELS))
            raise ValueError(
                f"unsupported preferred channel '{self.preferred_channel}'; "
                f"expected: {allowed}"
            )


DEFAULT_PROFILE = CustomerProfile(customer_id="default")


def resolve_customer_profile(
    customer_id: str | None,
    profiles: Mapping[str, "CustomerProfile"] | None = None,
) -> "CustomerProfile":
    """Resolve a profile while preserving a safe default."""
    if not customer_id or not profiles:
        return DEFAULT_PROFILE

    return profiles.get(customer_id, DEFAULT_PROFILE)


def apply_customer_profile(
    draft: Draft,
    profile: CustomerProfile,
) -> Draft:
    """Return a profile-adjusted copy without mutating the original draft.

    Replaces the greeting and signoff by scanning for the sentinel defaults.
    If the draft was composed with a custom greeting/signoff (e.g., a previous
    profile was already applied), this function is a no-op for those parts.
    """
    body = draft.email_body

    # Replace greeting only when the default sentinel is present at the start
    if body.startswith(_DEFAULT_GREETING) and profile.greeting != _DEFAULT_GREETING:
        body = profile.greeting + body[len(_DEFAULT_GREETING):]

    # Replace signoff only when the default sentinel is present at the end
    if body.endswith(_DEFAULT_SIGNOFF) and profile.signoff != _DEFAULT_SIGNOFF:
        body = body[: -len(_DEFAULT_SIGNOFF)] + profile.signoff

    return replace(draft, email_body=body)
