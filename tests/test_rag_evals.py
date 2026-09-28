import pytest
from dotenv import load_dotenv
from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import FaithfulnessMetric, HallucinationMetric

from src.schemas import AlarmPayload
from src.agent.incident_agent import IncidentAgent

load_dotenv()


@pytest.fixture(scope="module")
def agent():
    return IncidentAgent(model_name="gpt-4o-mini")


def test_fiber_cut_rag_faithfulness_and_hallucination(agent):
    """
    Evaluates that the notification email generated for a Tier-1 Metro Fiber Cut
    strictly reflects facts in the retrieved SOP and introduces zero hallucinated ETAs.
    """
    # 1. Arrange: Define the operational alarm
    alarm = AlarmPayload(
        incident_id="INC-EVAL-101",
        circuit_id="IEPL-9021-LAX-TYO",
        alarm_type="FIBER_CUT",
        raw_symptom="OTDR reflection indicates physical fiber break at KM marker 34.2",
        detected_at="2026-09-28T14:00:00Z"
    )

    # 2. Act: Execute the complete Agent pipeline
    draft, circuit, sop_context, guardrail_report = agent.process_alarm(alarm)

    # 3. Format context for DeepEval (expects List[str])
    # FaithfulnessMetric judges RAG grounding against retrieved SOP chunks.
    # HallucinationMetric requires `context` (not retrieval_context) and should
    # include every authorized fact: SOP plus telemetry/alarm ground truth.
    retrieval_context = [sop_context]
    factual_context = [
        sop_context,
        (
            f"Incident ID: {alarm.incident_id}. "
            f"Circuit ID: {alarm.circuit_id}. "
            f"Client: {circuit['client_name']}. "
            f"Route: {circuit['origin_location']} -> {circuit['dest_location']}. "
            f"Client Tier: {circuit['client_tier']}. "
            f"Contracted SLA Hours: {circuit['contracted_sla_hours']}. "
            f"Contact: {circuit['contact_email']}. "
            f"Alarm: {alarm.alarm_type}. "
            f"Symptom: {alarm.raw_symptom}. "
            f"Detected At: {alarm.detected_at}."
        ),
    ]

    # Construct the formal LLM Test Case
    test_case = LLMTestCase(
        input=f"{alarm.alarm_type}: {alarm.raw_symptom} on circuit {alarm.circuit_id}",
        actual_output=draft.notification_email_body,
        retrieval_context=retrieval_context,
        context=factual_context,
    )

    # 4. Metric 1: Faithfulness Metric
    # Verifies every technical assertion in actual_output is directly inferable from the SOP
    faithfulness_metric = FaithfulnessMetric(
        threshold=0.85,
        model="gpt-4o-mini",
        include_reason=True
    )
    faithfulness_metric.measure(test_case)

    print(f"\n[EVAL REPORT] Faithfulness Score: {faithfulness_metric.score:.4f}")
    print(f"[EVAL REPORT] Faithfulness Reason: {faithfulness_metric.reason}")

    # 5. Metric 2: Hallucination Metric
    # Score is now "factual alignment" (1.0 = no hallucination).
    # DeepEval flipped HallucinationMetric: 1.0 = no hallucination, threshold is a minimum.
    # 0.85 is the equivalent of the old "at most 15% contradictory claims" bar.
    hallucination_metric = HallucinationMetric(
        threshold=0.85,
        model="gpt-4o-mini",
        include_reason=True
    )
    hallucination_metric.measure(test_case)

    print(f"[EVAL REPORT] Hallucination Score: {hallucination_metric.score:.4f}")
    print(f"[EVAL REPORT] Hallucination Reason: {hallucination_metric.reason}")

    # 6. Metric 3: Deterministic Contractual Guardrails
    assert guardrail_report["tenant_isolation_passed"] is True, "Tenant isolation violated."
    assert guardrail_report["sla_compliance_passed"] is True, "SLA update window violated."

    # 7. Assert via DeepEval Test Runner
    assert faithfulness_metric.is_successful(), (
        f"Faithfulness score {faithfulness_metric.score} below threshold 0.85. Reason: {faithfulness_metric.reason}"
    )
    assert hallucination_metric.is_successful(), (
        f"Hallucination score {hallucination_metric.score} below threshold 0.85. Reason: {hallucination_metric.reason}"
    )


def test_bgp_route_leak_rag_faithfulness(agent):
    """
    Evaluates that BGP routing incidents correctly cite mitigation steps
    without hallucinating unauthorized network configuration changes.
    """
    alarm = AlarmPayload(
        incident_id="INC-EVAL-202",
        circuit_id="DIA-4410-SFO-JFK",
        alarm_type="BGP_LEAK",
        raw_symptom="Unauthorized prefix leak detected from upstream peer AS64512",
        detected_at="2026-09-28T14:15:00Z"
    )

    draft, circuit, sop_context, guardrail_report = agent.process_alarm(alarm)

    test_case = LLMTestCase(
        input=f"{alarm.alarm_type}: {alarm.raw_symptom}",
        actual_output=draft.notification_email_body,
        retrieval_context=[sop_context]
    )

    faithfulness_metric = FaithfulnessMetric(
        threshold=0.85,
        model="gpt-4o-mini",
        include_reason=True
    )
    faithfulness_metric.measure(test_case)

    print(f"\n[EVAL REPORT] BGP Faithfulness Score: {faithfulness_metric.score:.4f}")
    print(f"[EVAL REPORT] BGP Faithfulness Reason: {faithfulness_metric.reason}")

    assert faithfulness_metric.is_successful(), (
        f"BGP Faithfulness score {faithfulness_metric.score} below threshold 0.85. Reason: {faithfulness_metric.reason}"
    )