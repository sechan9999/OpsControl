import hashlib
import json
from dataclasses import dataclass
from typing import List


ROLES = ["Operator", "Supervisor", "Auditor"]


@dataclass(frozen=True)
class UserRolePermissions:
    role: str
    can_approve_standard: bool
    can_approve_high_value_red: bool
    can_dismiss: bool
    can_execute_tenders: bool
    can_export_audit_logs: bool


ROLE_PERMISSIONS = {
    "Operator": UserRolePermissions(
        role="Operator", can_approve_standard=True, can_approve_high_value_red=False,
        can_dismiss=True, can_execute_tenders=True, can_export_audit_logs=False,
    ),
    "Supervisor": UserRolePermissions(
        role="Supervisor", can_approve_standard=True, can_approve_high_value_red=True,
        can_dismiss=True, can_execute_tenders=True, can_export_audit_logs=True,
    ),
    "Auditor": UserRolePermissions(
        role="Auditor", can_approve_standard=False, can_approve_high_value_red=False,
        can_dismiss=False, can_execute_tenders=False, can_export_audit_logs=True,
    ),
}


def get_role_permissions(role: str) -> UserRolePermissions:
    return ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS["Operator"])


def can_user_approve_record(role: str, tier: str, affected_value: float) -> bool:
    perms = get_role_permissions(role)
    if not perms.can_approve_standard:
        return False
    if tier == "red" and affected_value >= 10000.0:
        return perms.can_approve_high_value_red
    return True


def export_soc2_audit_logs_json(logs: List[str]) -> str:
    """Generate SOC2 WORM compliant audit log export in JSON format with SHA-256 cryptographic hash chaining."""
    blocks = []
    prev_hash = "0" * 64
    for idx, log_line in enumerate(logs):
        payload = f"{idx}:{prev_hash}:{log_line}"
        block_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        blocks.append({
            "index": idx,
            "previous_hash": prev_hash,
            "block_hash": block_hash,
            "event": log_line,
        })
        prev_hash = block_hash

    export_payload = {
        "export_standard": "SOC2_WORM_V1",
        "crypto_schema": "SHA-256_HASH_CHAIN",
        "total_events": len(logs),
        "worm_root_hash": prev_hash,
        "logs": logs,
        "hash_chain": blocks,
    }
    return json.dumps(export_payload, indent=2)


def verify_soc2_audit_chain(json_str: str) -> bool:
    """Verify cryptographic integrity of SOC2 WORM audit log export payload."""
    try:
        data = json.loads(json_str)
        logs = data.get("logs", [])
        chain = data.get("hash_chain", [])
        if len(logs) != len(chain):
            return False
        prev_hash = "0" * 64
        for idx, block in enumerate(chain):
            if logs[idx] != block["event"]:
                return False
            if block["previous_hash"] != prev_hash:
                return False
            expected_hash = hashlib.sha256(f"{idx}:{prev_hash}:{block['event']}".encode("utf-8")).hexdigest()
            if block["block_hash"] != expected_hash:
                return False
            prev_hash = expected_hash
        return data.get("worm_root_hash") == prev_hash
    except Exception:
        return False

