import os
from typing import Any

import instructor
from dotenv import load_dotenv
from openai import OpenAI

from src.agent.guardrails import apply_guardrails
from src.rag.retriever import retrieve_sop_context
from src.schemas import AlarmPayload, IncidentNotificationDraft
from src.telemetry_db import get_circuit_details

load_dotenv()


class IncidentAgent:
    def __init__(self, model_name: str = "gpt-4o-mini", client=None):
        self.model_name = model_name
        if client is None:
            load_dotenv()
            api_key = os.environ["OPENAI_API_KEY"]
            client = instructor.from_openai(OpenAI(api_key=api_key))
        self.client = client

    def process_alarm(
        self, alarm: AlarmPayload
    ) -> tuple[IncidentNotificationDraft, dict[str, Any], str, dict[str, bool]]:
        """
        Executes end-to-end incident drafting:
        1. Telemetry Context Injection (SQL)
        2. SOP Runbook Retrieval (ChromaDB RAG)
        3. Constrained LLM Generation (Pydantic via Instructor)
        4. Deterministic guardrails
        Returns: (draft, circuit_metadata, retrieved_context, guardrail_report)
        """
        # Step 1: Structured Telemetry Lookup (Ground Truth)
        circuit = get_circuit_details(alarm.circuit_id)
        if not circuit:
            raise ValueError(f"Circuit {alarm.circuit_id} not found in telemetry database.")

        # Step 2: Unstructured SOP Knowledge Retrieval
        rag_query = f"{alarm.alarm_type}: {alarm.raw_symptom}"
        sop_context, raw_evidence = retrieve_sop_context(rag_query, k=2)

        # Step 3: Prompt Construction with Guardrailed Context
        system_prompt = f"""
You are the Lead NOC Incident Response Copilot for an enterprise telecom carrier.
Your responsibility is to draft professional, technical, and SLA-compliant customer outage notifications.

OPERATIONAL INSTRUCTIONS:
1. Base all technical mitigation steps solely on the provided SOP runbooks.
2. Comply strictly with client SLA terms:
   - Client Tier: {circuit['client_tier']}
   - Contracted SLA Window: {circuit['contracted_sla_hours']} Hours
3. ZERO-HALLUCINATION POLICY:
   - Do NOT invent or commit to an unconfirmed restoration time. If field technicians have not confirmed a fix, state that updates will be delivered according to the scheduled update cadence.
   - You must set 'next_update_window_minutes' to an interval LESS THAN OR EQUAL to the customer's SLA update requirement.
4. Format the final 'notification_email_body' with clean markdown, including:
   - Incident Ticket ID & Impacted Circuit
   - Current Physical Status
   - Technical Actions Taken by NOC
   - Next Scheduled Communication Time
"""

        user_content = f"""
INCOMING NETWORK TELEMETRY ALERT:
- Incident ID: {alarm.incident_id}
- Circuit ID: {alarm.circuit_id}
- Client Name: {circuit['client_name']}
- Endpoint Route: {circuit['origin_location']} -> {circuit['dest_location']}
- Alarm Event: {alarm.alarm_type}
- Symptom: {alarm.raw_symptom}
- Detected At: {alarm.detected_at}

RETRIEVED OPERATIONAL RUNBOOK (SOP):
{sop_context}

Draft the formal customer notification following the IncidentNotificationDraft schema.
"""

        # Step 4: Structured Output Inference
        raw_draft: IncidentNotificationDraft = self.client.chat.completions.create(
            model=self.model_name,
            response_model=IncidentNotificationDraft,
            max_retries=2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.1,
        )

        # Step 5: Deterministic Guardrail Gate & Remediation
        validated_draft, guardrail_report = apply_guardrails(raw_draft, alarm, circuit)

        return validated_draft, circuit, sop_context, guardrail_report
