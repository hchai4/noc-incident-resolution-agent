import pytest
from src.agent.incident_agent import IncidentAgent
from src.schemas import AlarmPayload


@pytest.fixture(scope="module")
def agent():
    return IncidentAgent()


def test_scenario_1_fiber_cut_tier1(agent):
    """Scenario 1: Goldman Sachs Tier-1 Fiber Cut (4-hour SLA)."""
    alarm = AlarmPayload(
        incident_id="INC-FIBER-991",
        circuit_id="IEPL-9021-LAX-TYO",
        alarm_type="FIBER_CUT",
        raw_symptom="OTDR indicates total loss of signal at KM 34.2 optical conduit shearing",
        detected_at="2026-09-25T10:15:00Z",
    )

    draft, circuit, context, checks = agent.process_alarm(alarm)

    # 1. Verify Grounding & Schema
    assert draft.incident_id == "INC-FIBER-991"
    assert draft.client_name == "Goldman & Sachs Trading"
    assert draft.circuit_id == "IEPL-9021-LAX-TYO"
    assert draft.severity == "P1_CRITICAL"

    # 2. Verify SOP-informed technical actions
    assert any(
        term in draft.mitigation_action_taken.lower()
        for term in ["splicing", "otdr", "fiber", "dispatch", "rerout"]
    )

    # 3. Verify Deterministic Guardrails
    assert checks["tenant_isolation_passed"] is True
    assert checks["sla_compliance_passed"] is True
    assert draft.next_update_window_minutes <= (circuit["contracted_sla_hours"] * 60)


def test_scenario_2_bgp_route_leak_tier1(agent):
    """Scenario 2: Stripe Cloud Tier-1 BGP Route Leak (2-hour SLA)."""
    alarm = AlarmPayload(
        incident_id="INC-BGP-442",
        circuit_id="DIA-4410-SFO-JFK",
        alarm_type="BGP_LEAK",
        raw_symptom="Peer AS-Path flapping, unauthorized prefix leak on transit edge router",
        detected_at="2026-09-25T11:00:00Z",
    )

    draft, circuit, context, checks = agent.process_alarm(alarm)

    assert draft.client_name == "Stripe Cloud Platform"
    assert "bgp" in draft.root_cause_category.lower()
    assert any(
        term in draft.mitigation_action_taken.lower()
        for term in ["filter", "shut", "divert", "prefix", "peer"]
    )
    assert checks["tenant_isolation_passed"] is True
    assert checks["sla_compliance_passed"] is True
    # Tier-1 BGP SLA requires frequent updates (<= 120 mins)
    assert draft.next_update_window_minutes <= 120


def test_scenario_3_power_failure_tier2(agent):
    """Scenario 3: Midwest Logistics Tier-2 Power Grid Failure (6-hour SLA)."""
    alarm = AlarmPayload(
        incident_id="INC-PWR-701",
        circuit_id="METRO-3301-ORD-CHI",
        alarm_type="POWER_FAIL",
        raw_symptom="Mains utility power loss at CHI1 PoP, automatic transfer switch engaged generator",
        detected_at="2026-09-25T11:30:00Z",
    )

    draft, circuit, context, checks = agent.process_alarm(alarm)

    assert draft.client_name == "Midwest Logistics Corp"
    assert any(
        term in draft.mitigation_action_taken.lower()
        for term in ["generator", "ats", "ups", "utility", "transfer"]
    )
    assert checks["tenant_isolation_passed"] is True
    assert checks["sla_compliance_passed"] is True
    assert draft.next_update_window_minutes <= 360
