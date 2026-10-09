from typing import Any

from src.schemas import AlarmPayload, IncidentNotificationDraft


class GuardrailViolation(Exception):
    """Raised when an incident draft violates strict operational rules."""

    pass


def verify_sla_compliance(draft: IncidentNotificationDraft, contracted_sla_hours: int) -> bool:
    """
    Asserts that the scheduled update cadence is compliant with the customer SLA.
    For Tier-1/Tier-2 clients, updates must occur within contracted windows (in minutes).
    """
    max_allowed_update_window = contracted_sla_hours * 60
    return draft.next_update_window_minutes <= max_allowed_update_window


def verify_tenant_isolation(
    draft: IncidentNotificationDraft, alarm: AlarmPayload, circuit: dict[str, Any]
) -> bool:
    """
    Prevents cross-tenant data leakage by verifying that the drafted entities
    match both the trigger alarm and the database record.
    """
    matches_circuit = draft.circuit_id == alarm.circuit_id == circuit["circuit_id"]
    matches_client = draft.client_name == circuit["client_name"]
    return matches_circuit and matches_client


def apply_guardrails(
    draft: IncidentNotificationDraft, alarm: AlarmPayload, circuit: dict[str, Any]
) -> tuple[IncidentNotificationDraft, dict[str, bool]]:
    """
    Runs all deterministic verification checks and performs safe remediation.
    """
    checks = {"tenant_isolation_passed": False, "sla_compliance_passed": False, "auto_remediated": False}

    # 1. Check Tenant Isolation
    if not verify_tenant_isolation(draft, alarm, circuit):
        raise GuardrailViolation(
            f"Tenant Isolation Failed: Draft client ({draft.client_name}) or circuit ({draft.circuit_id}) "
            f"does not match ground-truth circuit {circuit['circuit_id']} ({circuit['client_name']})."
        )
    checks["tenant_isolation_passed"] = True

    # 2. Check SLA Compliance
    if verify_sla_compliance(draft, circuit["contracted_sla_hours"]):
        checks["sla_compliance_passed"] = True
    else:
        # Auto-remediation: Clamp update cadence to maximum legal boundary
        max_minutes = circuit["contracted_sla_hours"] * 60
        draft.next_update_window_minutes = min(draft.next_update_window_minutes, max_minutes)
        checks["sla_compliance_passed"] = True
        checks["auto_remediated"] = True

    return draft, checks
