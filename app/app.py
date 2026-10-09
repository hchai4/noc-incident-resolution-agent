import sys
from pathlib import Path

# streamlit run app/app.py puts `app/` on sys.path, not the repo root.
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import datetime

import streamlit as st
from dotenv import load_dotenv
from src.agent.guardrails import GuardrailViolation
from src.agent.incident_agent import IncidentAgent
from src.schemas import AlarmPayload
from src.telemetry_db import get_circuit_details, get_db_connection
from ulid import ULID

load_dotenv()

# Page configuration
st.set_page_config(page_title="NOC Incident Copilot | Enterprise Dispatch", page_icon="📡", layout="wide")

# Custom Styling for enterprise look
st.markdown(
    """
<style>
    .metric-box {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 10px;
    }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource
def load_agent():
    return IncidentAgent(model_name="gpt-4o-mini")


agent = load_agent()


def fetch_all_circuits():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT circuit_id, client_name, client_tier, contracted_sla_hours FROM circuits")
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


# Header
st.title("📡 NOC Incident Resolution & Dispatch Copilot")
st.caption("Grounded enterprise RAG | Human-in-the-loop dispatch")
st.divider()

# Layout: 3 Columns
col_left, col_center, col_right = st.columns([1.1, 2.0, 1.1])

# ==============================================================================
# LEFT PANEL: Real-Time Telemetry & Incoming Network Alarm
# ==============================================================================
with col_left:
    st.subheader("1. Incoming Telemetry Alert")

    circuits = fetch_all_circuits()
    circuit_options = {f"{c['circuit_id']} ({c['client_name']})": c["circuit_id"] for c in circuits}
    selected_label = st.selectbox("Select Target Circuit Alert:", list(circuit_options.keys()))
    selected_circuit_id = circuit_options[selected_label]

    circuit_data = get_circuit_details(selected_circuit_id)
    if circuit_data is None:
        st.error(f"Circuit {selected_circuit_id} was not found in telemetry.")
        st.stop()

    st.markdown(
        f"""
        <div class="metric-box">
            <b>Client:</b> {circuit_data['client_name']}<br>
            <b>Tier:</b> {circuit_data['client_tier']}<br>
            <b>Contracted SLA:</b> {circuit_data['contracted_sla_hours']} Hours<br>
            <b>Route:</b> {circuit_data['origin_location']} ➔ {circuit_data['dest_location']}
        </div>
        """,
        unsafe_allow_html=True,
    )

    alarm_type = st.selectbox("Simulated Anomaly Event:", ["FIBER_CUT", "BGP_LEAK", "POWER_FAIL", "DDOS"])

    symptom_defaults = {
        "FIBER_CUT": "OTDR reflection indicates physical fiber conduit break at KM 34.2",
        "BGP_LEAK": "Peer AS-Path flapping, unauthorized route prefixes announced on edge",
        "POWER_FAIL": "Mains utility grid failure, automatic transfer switch engaged generator",
        "DDOS": "Volumetric ingress saturation exceeding 65 Gbps targeting client subnet",
    }

    raw_symptom = st.text_area("Raw Sensor Telemetry:", value=symptom_defaults[alarm_type], height=100)

    generate_btn = st.button("Generate incident draft", type="primary", width="stretch")

# State initialization
if "draft_result" not in st.session_state:
    st.session_state.draft_result = None
if "guardrail_error" not in st.session_state:
    st.session_state.guardrail_error = None

# Trigger Agent Execution
if generate_btn:
    with st.spinner("Executing RAG retrieval and structured drafting..."):
        current_time = datetime.datetime.now(datetime.UTC).isoformat()
        alarm = AlarmPayload(
            incident_id=f"INC-{ULID()}",
            circuit_id=selected_circuit_id,
            alarm_type=alarm_type,
            raw_symptom=raw_symptom,
            detected_at=current_time,
        )
        try:
            draft, circuit, sop_context, guardrails = agent.process_alarm(alarm)
        except GuardrailViolation as exc:
            st.session_state.draft_result = None
            st.session_state.guardrail_error = str(exc)
        else:
            st.session_state.guardrail_error = None
            st.session_state.draft_result = {
                "draft": draft,
                "circuit": circuit,
                "sop_context": sop_context,
                "guardrails": guardrails,
                "alarm": alarm,
            }

# ==============================================================================
# CENTER PANEL: Knowledge Citations & Generated Draft
# ==============================================================================
with col_center:
    st.subheader("2. Grounded Incident Response Draft")

    if st.session_state.guardrail_error:
        st.error(st.session_state.guardrail_error)
        st.caption("No customer email was drafted.")
    elif st.session_state.draft_result:
        res = st.session_state.draft_result
        draft = res["draft"]

        with st.expander("View retrieved runbook citations", expanded=False):
            st.markdown(res["sop_context"])

        st.markdown(f"**Ticket:** `{draft.incident_id}` | **Severity:** `{draft.severity}`")
        st.markdown(f"**Identified root cause:** {draft.root_cause_category}")
        st.markdown(f"**Technical mitigation taken:** {draft.mitigation_action_taken}")

        st.markdown("### Customer notification email")
        st.text_area(
            "Review and edit the draft before marking it reviewed:",
            value=draft.notification_email_body,
            height=260,
        )

        reviewed = st.button("Mark reviewed (no email is sent)", type="primary", width="stretch")
        if reviewed:
            st.success(
                f"Marked reviewed in this session. No email was sent to {res['circuit']['contact_email']}."
            )
    else:
        st.info("Select a circuit alarm on the left and click **Generate incident draft**.")

# ==============================================================================
# RIGHT PANEL: Quality Badges & Evaluation Scorecard
# ==============================================================================
with col_right:
    st.subheader("3. Production Safety Guardrails")

    if st.session_state.guardrail_error:
        st.markdown("**Tenant isolation**")
        st.badge("Failed", icon=":material/close:", color="red")
        st.caption(st.session_state.guardrail_error)
        st.markdown("**SLA cadence**")
        st.badge("Not evaluated", icon=":material/remove:", color="gray")
    elif st.session_state.draft_result:
        res = st.session_state.draft_result
        draft = res["draft"]
        checks = res["guardrails"]
        max_minutes = res["circuit"]["contracted_sla_hours"] * 60

        st.markdown("**Tenant isolation**")
        if checks["tenant_isolation_passed"]:
            st.badge("Passed", icon=":material/check:", color="green")
        else:
            st.badge("Failed", icon=":material/close:", color="red")
        st.caption(f"Target match: {draft.client_name} ({draft.circuit_id})")

        st.markdown("**SLA cadence**")
        if checks.get("auto_remediated"):
            st.badge("Passed (clamped)", icon=":material/warning:", color="orange")
            st.caption(
                f"Next update every {draft.next_update_window_minutes} mins. "
                f"Window was clamped to the {max_minutes}-minute SLA limit."
            )
        elif checks["sla_compliance_passed"]:
            st.badge("Passed", icon=":material/check:", color="green")
            st.caption(
                f"Next update every {draft.next_update_window_minutes} mins "
                f"(allowed: <= {max_minutes} mins)."
            )
        else:
            st.badge("Failed", icon=":material/close:", color="red")
            st.caption(f"Allowed window is <= {max_minutes} mins.")

        st.divider()
        st.markdown("**Evaluation**")
        st.caption(
            "Faithfulness and hallucination are measured offline in "
            "`tests/test_rag_evals.py` (DeepEval, threshold 0.85). "
            "This console does not show a live score."
        )
    else:
        st.caption("Awaiting a draft to show guardrail results.")
