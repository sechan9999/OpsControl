from dataclasses import dataclass, replace
from typing import Mapping

from opscontrol.models import Draft

SUPPORTED_CHANNELS = {"email", "sms"}


@dataclass(frozen=True)
class CustomerProfile:
    customer_id: str
    preferred_channel: str = "email"
    greeting: str = "Hello,"
    signoff: str = "OpsControl Operations"
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
    profiles: Mapping[str, CustomerProfile] | None = None,
) -> CustomerProfile:
    """Resolve a profile while preserving a safe default."""
    if not customer_id or not profiles:
        return DEFAULT_PROFILE

    return profiles.get(customer_id, DEFAULT_PROFILE)


def apply_customer_profile(
    draft: Draft,
    profile: CustomerProfile,
) -> Draft:
    """Return a profile-adjusted copy without mutating the original draft."""
    body = draft.email_body

    if body.startswith("Hello,"):
        body = body.replace("Hello,", profile.greeting, 1)

    default_signoff = "OpsControl Operations"
    if body.endswith(default_signoff):
        body = body[: -len(default_signoff)] + profile.signoff

    return replace(draft, email_body=body)
