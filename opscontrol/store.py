import hashlib
import json
import re
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .models import Assessment, Draft, ExceptionRecord, MitigationAction, TriageResult

TIER_ORDER = {"red": 0, "orange": 1, "green": 2}


SCHEMA_VERSION = 2


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def normalize_hash(raw: str) -> str:
    return hashlib.sha256(re.sub(r"\s+", " ", raw.strip().lower()).encode()).hexdigest()


class Desk:
    """Exception desk state, optionally persisted between Streamlit reruns."""

    def __init__(self):
        self._hashes: set[str] = set()
        self.exceptions: dict[int, ExceptionRecord] = {}
        self.logs: list[str] = []
        self.counters = {"ingested": 0, "duplicates": 0, "sent": 0, "dismissed": 0}
        self.adaptive_thresholds: dict[str, float] = {}
        self.feedback_dataset: list[dict] = []
        self._next_msg = 0
        self._next_exc = 0

    def adjust_threshold(self, exception_type: str, delta: float) -> float:
        current = self.adaptive_thresholds.get(exception_type, 0.0)
        new_val = max(-0.15, min(0.15, current + delta))
        self.adaptive_thresholds[exception_type] = round(new_val, 2)
        return self.adaptive_thresholds[exception_type]

    def log(self, level: str, event: str, **kw) -> None:
        rest = " ".join(f"{k}={v}" for k, v in kw.items())
        self.logs.insert(0, f"{_now()} {level.upper():<7} {event} {rest}".rstrip())
        if len(self.logs) > 400:
            self.logs.insert(
                0,
                f"{_now()} WARNING log_truncated kept=400 dropped={len(self.logs) - 400}",
            )
            del self.logs[400:]

    def seen_or_add(self, raw: str) -> bool:
        message_hash = normalize_hash(raw)
        if message_hash in self._hashes:
            return True
        self._hashes.add(message_hash)
        return False

    def add_exception(self, raw: str, channel: str, triage: TriageResult) -> ExceptionRecord:
        self._next_msg += 1
        self._next_exc += 1
        record = ExceptionRecord(
            id=self._next_exc, message_id=self._next_msg, raw=raw, channel=channel,
            triage=triage, created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )
        self.exceptions[record.id] = record
        return record

    def set_status(self, exc_id: int, status: str) -> None:
        record = self.exceptions[exc_id]
        if record.status in ("sent", "dismissed"):
            raise ValueError(f"exception {exc_id} is terminal ({record.status})")
        record.status = status
        if status == "sent":
            self.counters["sent"] += 1
        if status == "dismissed":
            self.counters["dismissed"] += 1

    def save_assessment(self, exc_id: int, assessment: Assessment) -> None:
        self.exceptions[exc_id].assessment = assessment

    def save_draft(self, exc_id: int, draft: Draft) -> None:
        self.exceptions[exc_id].draft = draft

    def sorted_open(self) -> list[ExceptionRecord]:
        open_records = [record for record in self.exceptions.values()
                        if record.status not in ("sent", "dismissed")]
        return sorted(open_records, key=lambda record: (
            TIER_ORDER[record.tier], -record.triage.severity, record.created_at))

    def by_status(self, status: str) -> list[ExceptionRecord]:
        return [record for record in self.exceptions.values() if record.status == status]

    def metrics(self) -> dict:
        by_status = {}
        for record in self.exceptions.values():
            by_status[record.status] = by_status.get(record.status, 0) + 1
        risk = sum(record.assessment.affected_value for record in self.exceptions.values()
                   if record.assessment and record.status not in ("sent", "dismissed"))
        return {
            "ingested": self.counters["ingested"],
            "duplicates": self.counters["duplicates"],
            "ready": by_status.get("ready_for_approval", 0),
            "review": by_status.get("needs_human_review", 0),
            "sent": self.counters["sent"],
            "value_at_risk": risk,
        }

    @classmethod
    def load(cls, path: str | Path) -> "Desk":
        snapshot_path = Path(path)
        if not snapshot_path.exists():
            return cls()

        try:
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
            saved_version = snapshot.get("schema_version", 0)
            desk = cls()
            if saved_version != SCHEMA_VERSION:
                desk.log(
                    "warning",
                    "snapshot_version_mismatch",
                    saved=saved_version,
                    expected=SCHEMA_VERSION,
                )
            desk._hashes = set(snapshot["hashes"])
            desk.logs = list(snapshot["logs"])
            desk.counters = dict(snapshot["counters"])
            desk.adaptive_thresholds = dict(snapshot.get("adaptive_thresholds", {}))
            desk.feedback_dataset = list(snapshot.get("feedback_dataset", []))
            desk._next_msg = int(snapshot["next_msg"])
            desk._next_exc = int(snapshot["next_exc"])
            for serialized in snapshot["exceptions"]:
                serialized["triage"] = TriageResult(**serialized["triage"])
                if serialized["assessment"]:
                    a_dict = dict(serialized["assessment"])
                    actions_raw = a_dict.pop("mitigation_actions", [])
                    actions = [
                        item if isinstance(item, MitigationAction) else MitigationAction(**item)
                        for item in actions_raw
                    ]
                    serialized["assessment"] = Assessment(mitigation_actions=actions, **a_dict)
                if serialized["draft"]:
                    serialized["draft"] = Draft(**serialized["draft"])
                record = ExceptionRecord(**serialized)
                desk.exceptions[record.id] = record
            return desk
        except (KeyError, TypeError, ValueError, json.JSONDecodeError, OSError):
            return cls()

    def save(self, path: str | Path) -> None:
        snapshot_path = Path(path)
        snapshot = {
            "schema_version": SCHEMA_VERSION,
            "hashes": sorted(self._hashes),
            "exceptions": [asdict(record) for record in self.exceptions.values()],
            "logs": self.logs,
            "counters": self.counters,
            "adaptive_thresholds": self.adaptive_thresholds,
            "feedback_dataset": self.feedback_dataset,
            "next_msg": self._next_msg,
            "next_exc": self._next_exc,
        }
        snapshot_path.write_text(
            json.dumps(snapshot, indent=2, sort_keys=True), encoding="utf-8"
        )