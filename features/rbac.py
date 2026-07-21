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
    """Generate SOC2 WORM compliant audit log export in JSON format."""
    export_payload = {
        "export_standard": "SOC2_WORM_V1",
        "total_events": len(logs),
        "logs": logs,
    }
    return json.dumps(export_payload, indent=2)
