from src.agent.incident_agent import IncidentAgent
from src.schemas import AlarmPayload, IncidentNotificationDraft


def test_process_alarm_uses_injected_client(monkeypatch):
    monkeypatch.setattr(
        "src.agent.incident_agent.get_circuit_details",
        lambda circuit_id: {
            "circuit_id": circuit_id,
            "client_name": "Goldman & Sachs Trading",
            "client_tier": "Tier-1",
            "contracted_sla_hours": 4,
            "origin_location": "LA",
            "dest_location": "Tokyo",
        },
    )
    monkeypatch.setattr(
        "src.agent.incident_agent.retrieve_sop_context",
        lambda query, k=2: ("SOP: dispatch a splicing crew", []),
    )

    class FakeCompletions:
        def create(self, **kwargs):
            return IncidentNotificationDraft(
                incident_id="INC-FAKE",
                client_name="Goldman & Sachs Trading",
                circuit_id="IEPL-9021-LAX-TYO",
                severity="P1_CRITICAL",
                root_cause_category="Physical Fiber Cut",
                mitigation_action_taken="Dispatched a splicing crew",
                estimated_restoration_time="Updates follow the scheduled cadence.",
                next_update_window_minutes=60,
                notification_email_body="Test",
            )

    class FakeClient:
        def __init__(self):
            self.chat = type("Chat", (), {"completions": FakeCompletions()})()

    agent = IncidentAgent(client=FakeClient())

    alarm = AlarmPayload(
        incident_id="INC-FAKE",
        circuit_id="IEPL-9021-LAX-TYO",
        alarm_type="FIBER_CUT",
        raw_symptom="OTDR indicates a fiber break",
        detected_at="2026-10-08T16:00:00Z",
    )
    draft, circuit, context, checks = agent.process_alarm(alarm)
    assert draft.client_name == "Goldman & Sachs Trading"
    assert checks["tenant_isolation_passed"] is True
