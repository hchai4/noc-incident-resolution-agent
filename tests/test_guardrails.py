import pytest

from src.agent.guardrails import GuardrailViolation, apply_guardrails
from src.schemas import AlarmPayload, IncidentNotificationDraft


def _alarm() -> AlarmPayload:
    return AlarmPayload(
        incident_id="INC-GUARD-1",
        circuit_id="IEPL-9021-LAX-TYO",
        alarm_type="FIBER_CUT",
        raw_symptom="OTDR indicates a fiber break",
        detected_at="2026-10-07T18:00:00Z",
    )


def _circuit() -> dict:
    return {
        "circuit_id": "IEPL-9021-LAX-TYO",
        "client_name": "Goldman & Sachs Trading",
        "contracted_sla_hours": 4,
    }


def _draft(**overrides) -> IncidentNotificationDraft:
    fields = {
        "incident_id": "INC-GUARD-1",
        "client_name": "Goldman & Sachs Trading",
        "circuit_id": "IEPL-9021-LAX-TYO",
        "severity": "P1_CRITICAL",
        "root_cause_category": "Physical Fiber Cut",
        "mitigation_action_taken": "Dispatched a splicing crew",
        "estimated_restoration_time": "Updates will follow the scheduled cadence.",
        "next_update_window_minutes": 60,
        "notification_email_body": "Test notification",
    }
    fields.update(overrides)
    return IncidentNotificationDraft(**fields)


def test_tenant_mismatch_fails_closed():
    draft = _draft(client_name="Acme Retail Wholesale")
    with pytest.raises(GuardrailViolation):
        apply_guardrails(draft, _alarm(), _circuit())


def test_sla_window_is_clamped_in_python():
    draft = _draft(next_update_window_minutes=9999)
    validated, checks = apply_guardrails(draft, _alarm(), _circuit())

    assert validated.next_update_window_minutes == 240
    assert checks["sla_compliance_passed"] is True
    assert checks["auto_remediated"] is True
    assert checks["tenant_isolation_passed"] is True
