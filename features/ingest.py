from collections.abc import Iterable, Mapping
from typing import Any, Optional

from opscontrol.config import Settings
from opscontrol.models import ExceptionRecord
from opscontrol.pipeline import process_message
from opscontrol.store import Desk

ALLOWED_CHANNELS = {"edi", "email", "sms", "webhook"}


def normalize_channel(channel: str) -> str:
    normalized = channel.strip().lower()
    if normalized not in ALLOWED_CHANNELS:
        allowed = ", ".join(sorted(ALLOWED_CHANNELS))
        raise ValueError(f"unsupported channel '{channel}'; expected one of: {allowed}")
    return normalized


def ingest_message(
    raw: str,
    channel: str,
    desk: Desk,
    settings: Settings,
    metadata: Optional[Mapping[str, Any]] = None,
) -> Optional[ExceptionRecord]:
    """Validate and ingest one operational message.

    Returns the created exception record, or ``None`` when the normalized
    message is a duplicate.
    """
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("raw message must be a non-empty string")

    normalized_channel = normalize_channel(channel)
    record = process_message(raw.strip(), normalized_channel, desk, settings)

    if record is not None and metadata:
        desk.log(
            "info",
            "source_metadata_attached",
            id=record.id,
            source=metadata.get("source", "-"),
        )

    return record


def ingest_batch(
    messages: Iterable[Mapping[str, Any]],
    desk: Desk,
    settings: Settings,
) -> list[Optional[ExceptionRecord]]:
    """Ingest an iterable of raw message dictionaries."""
    results: list[Optional[ExceptionRecord]] = []

    for message in messages:
        if "raw" not in message or "channel" not in message:
            raise ValueError("each message must contain 'raw' and 'channel'")

        results.append(
            ingest_message(
                raw=message["raw"],
                channel=message["channel"],
                desk=desk,
                settings=settings,
                metadata=message.get("metadata"),
            )
        )

    return results
