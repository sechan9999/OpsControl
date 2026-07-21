import json
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
    """Validate and ingest one operational message."""
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


def parse_feed_drop_content(content_bytes: bytes, filename: str) -> list[dict]:
    """Parse raw uploaded bytes (.jsonl or .txt) into list of message dicts."""
    text = content_bytes.decode("utf-8", errors="replace")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    messages = []

    if filename.lower().endswith(".jsonl"):
        for line in lines:
            try:
                data = json.loads(line)
                if isinstance(data, dict) and "raw" in data:
                    messages.append({
                        "raw": str(data["raw"]),
                        "channel": str(data.get("channel", "edi")),
                        "metadata": data.get("metadata"),
                    })
            except json.JSONDecodeError:
                messages.append({"raw": line, "channel": "edi"})
    else:
        for line in lines:
            low = line.lower()
            if "status:" in low or "cntr" in low or "shpmt" in low:
                channel = "edi"
            elif "reefer alarm" in low or "sms" in low:
                channel = "sms"
            else:
                channel = "email"
            messages.append({"raw": line, "channel": channel})

    return messages
