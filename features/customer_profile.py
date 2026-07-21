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
    recipient: str = ""
    extra_note: str = ""

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

BUILTIN_PROFILES = {
    "NovaPharm": CustomerProfile(
        customer_id="NovaPharm",
        preferred_channel="email",
        greeting="Hello NovaPharm Logistics,",
        signoff="OpsControl QA & Regulatory Ops",
        tone="formal",
        recipient="To: ops@novapharm.example",
        extra_note="[QA Compliance Ref: QA-PHARMA-2026]",
    ),
    "Atlanta Retail": CustomerProfile(
        customer_id="Atlanta Retail",
        preferred_channel="email",
        greeting="Hello Atlanta Retail Ops,",
        signoff="OpsControl Freight Ops",
        tone="concise",
        recipient="To: logistics@atlantaretail.example",
    ),
}


def resolve_customer_profile(
    customer_id: str | None,
    profiles: Mapping[str, "CustomerProfile"] | None = None,
) -> "CustomerProfile":
    """Resolve a profile while preserving a safe default."""
    if not customer_id:
        return DEFAULT_PROFILE

    if profiles and customer_id in profiles:
        return profiles[customer_id]

    if customer_id in BUILTIN_PROFILES:
        return BUILTIN_PROFILES[customer_id]

    return DEFAULT_PROFILE


def apply_customer_profile(
    draft: Draft,
    profile: CustomerProfile,
) -> Draft:
    """Return a profile-adjusted copy without mutating the original draft."""
    body = draft.email_body

    # Prepend recipient header if set and not present
    if profile.recipient and not body.startswith("To:"):
        body = f"{profile.recipient}\n\n{body}"

    # Replace greeting only when default or matching sentinel is present at line 1 after To:
    if profile.greeting and profile.greeting != _DEFAULT_GREETING:
        if _DEFAULT_GREETING in body:
            body = body.replace(_DEFAULT_GREETING, profile.greeting, 1)

    # Replace signoff only when default sentinel is present at the end
    if profile.signoff and profile.signoff != _DEFAULT_SIGNOFF:
        if body.endswith(_DEFAULT_SIGNOFF):
            body = body[: -len(_DEFAULT_SIGNOFF)] + profile.signoff

    if profile.extra_note and profile.extra_note not in body:
        lines = body.rsplit("\n\n", 1)
        if len(lines) == 2:
            body = f"{lines[0]}\n\n{profile.extra_note}\n\n{lines[1]}"
        else:
            body = f"{body}\n\n{profile.extra_note}"

    return replace(draft, email_body=body)
