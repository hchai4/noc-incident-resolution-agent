import datetime
import json
import re
import statistics
from pathlib import Path

from deepeval.metrics import FaithfulnessMetric, HallucinationMetric
from deepeval.test_case import LLMTestCase
from dotenv import load_dotenv
from src.agent.incident_agent import IncidentAgent
from src.rag.rerank import ABSTAIN_THRESHOLD
from src.schemas import AlarmPayload

load_dotenv()

SCENARIOS = Path("evals/faithfulness_scenarios.jsonl")
OUT = Path("evals/faithfulness_results.json")
JUDGE_MODEL = "gpt-4o-mini"
THRESHOLD = 0.85
CITATION = re.compile(r"CITATION: \[([^\]]+)\]")


def main():
    rows = [json.loads(line) for line in SCENARIOS.read_text().splitlines() if line.strip()]
    agent = IncidentAgent(model_name="gpt-4o-mini")
    measured_at = datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")
    results = []

    for row in rows:
        alarm = AlarmPayload(
            incident_id=f"INC-EVAL-{row['id'].upper()}",
            circuit_id=row["circuit_id"],
            alarm_type=row["alarm_type"],
            raw_symptom=row["raw_symptom"],
            detected_at=measured_at,
        )
        draft, circuit, sop_context, guardrails = agent.process_alarm(alarm)

        cited = CITATION.findall(sop_context)
        abstained = sop_context.startswith("NO MATCHING SOP")

        telemetry = (
            f"Incident ID: {alarm.incident_id}. Circuit ID: {alarm.circuit_id}. "
            f"Client: {circuit['client_name']}. Client Tier: {circuit['client_tier']}. "
            f"Contracted SLA Hours: {circuit['contracted_sla_hours']}. "
            f"Route: {circuit['origin_location']} -> {circuit['dest_location']}. "
            f"Alarm: {alarm.alarm_type}. Symptom: {alarm.raw_symptom}. Detected At: {alarm.detected_at}."
        )
        case = LLMTestCase(
            input=f"{alarm.alarm_type}: {alarm.raw_symptom} on circuit {alarm.circuit_id}",
            actual_output=draft.notification_email_body,
            retrieval_context=[sop_context],
            context=[sop_context, telemetry],
        )

        faith = FaithfulnessMetric(threshold=THRESHOLD, model=JUDGE_MODEL, include_reason=True)
        faith.measure(case)
        halluc = HallucinationMetric(threshold=THRESHOLD, model=JUDGE_MODEL, include_reason=True)
        halluc.measure(case)

        results.append(
            {
                "id": row["id"],
                "alarm_type": row["alarm_type"],
                "circuit_id": row["circuit_id"],
                "expected_sop": row["expected_sop"],
                "cited_files": cited,
                "abstained": abstained,
                "retrieval_correct": (
                    abstained if row["expect_abstain"] else (bool(cited) and cited[0] == row["expected_sop"])
                ),
                "faithfulness": round(float(faith.score), 3),
                "faithfulness_reason": faith.reason,
                "hallucination": round(float(halluc.score), 3),
                "hallucination_reason": halluc.reason,
                "tenant_isolation_passed": guardrails["tenant_isolation_passed"],
                "sla_compliance_passed": guardrails["sla_compliance_passed"],
                "next_update_window_minutes": draft.next_update_window_minutes,
            }
        )
        print(
            f"{row['id']:8} faith={faith.score:.2f} halluc={halluc.score:.2f} "
            f"cited={cited or 'ABSTAIN'} retrieval_ok={results[-1]['retrieval_correct']}"
        )

    scored = [r for r in results]
    report = {
        "measured_at": measured_at,
        "judge_model": JUDGE_MODEL,
        "threshold": THRESHOLD,
        "retrieval_abstain_threshold": ABSTAIN_THRESHOLD,
        "scenario_count": len(results),
        "summary": {
            "faithfulness_mean": round(statistics.mean(r["faithfulness"] for r in scored), 3),
            "faithfulness_min": min(r["faithfulness"] for r in scored),
            "hallucination_mean": round(statistics.mean(r["hallucination"] for r in scored), 3),
            "hallucination_min": min(r["hallucination"] for r in scored),
            "retrieval_correct": sum(r["retrieval_correct"] for r in scored),
            "guardrails_passed": sum(
                r["tenant_isolation_passed"] and r["sla_compliance_passed"] for r in scored
            ),
        },
        "scenarios": results,
    }
    OUT.write_text(json.dumps(report, indent=2) + "\n")

    print("\n| Scenario | Cited SOP | Faithfulness | Factual alignment | Guardrails |")
    print("|---|---|---|---|---|")
    for r in results:
        cited = r["cited_files"][0] if r["cited_files"] else "abstained"
        guard = "pass" if r["tenant_isolation_passed"] and r["sla_compliance_passed"] else "FAIL"
        print(
            f"| {r['alarm_type']} | `{cited}` | {r['faithfulness']:.2f} | {r['hallucination']:.2f} | {guard} |"
        )
    print(f"\nwrote {OUT}  (T={ABSTAIN_THRESHOLD}, judge={JUDGE_MODEL}, at {measured_at})")


if __name__ == "__main__":
    main()
