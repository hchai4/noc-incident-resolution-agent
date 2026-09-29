# NOC Incident Resolution Agent

A grounded RAG copilot for network operations. It turns an incoming circuit alarm into an SLA-compliant customer incident draft, using SQL telemetry as ground truth, SOP runbooks as retrieval context, and deterministic guardrails before anything is shown to an operator.

The Streamlit UI is a human-in-the-loop (HITL) dispatch console: operators pick a circuit and alarm, review citations and the draft email, then confirm dispatch.

## How it works

```
AlarmPayload
    │
    ├─ 1. Telemetry context injection
    │     SQLite lookup by circuit_id → client, tier, contracted SLA, route
    │
    ├─ 2. SOP retrieval (RAG)
    │     ChromaDB similarity search over NOC runbooks (k=2) with citations
    │
    ├─ 3. Constrained generation
    │     gpt-4o-mini via Instructor → IncidentNotificationDraft (Pydantic)
    │
    └─ 4. Guardrail gate
          Tenant isolation (fail hard) + SLA update-window clamp (auto-remediate)
```

The agent must not invent a restoration ETA. If field confirmation is missing, it schedules the next update within the customer's contracted window instead.

## Project layout

```
app/app.py                      Streamlit HITL console
src/schemas.py                  AlarmPayload + IncidentNotificationDraft
src/telemetry_db.py             SQLite circuit catalog (seed + lookup)
src/rag/indexer.py              Embed SOP runbooks into ChromaDB
src/rag/retriever.py            Cited SOP retrieval
src/agent/incident_agent.py     End-to-end drafting pipeline
src/agent/guardrails.py         Tenant isolation + SLA compliance
data/noc_runbooks/              Markdown SOP source files
data/circuits_telemetry.db      Generated SQLite DB (after seed)
data/chroma_db/                 Generated vector index (after index)
tests/                          Scenario, retrieval, and DeepEval tests
```

## Sample circuits

| Circuit ID | Client | Tier | SLA (hours) |
|---|---|---|---|
| `IEPL-9021-LAX-TYO` | Goldman & Sachs Trading | Tier-1 | 4 |
| `DIA-4410-SFO-JFK` | Stripe Cloud Platform | Tier-1 | 2 |
| `METRO-3301-ORD-CHI` | Midwest Logistics Corp | Tier-2 | 6 |
| `IPLC-8812-LON-FRA` | Acme Retail Wholesale | Tier-3 | 8 |

Supported alarm types in the UI: `FIBER_CUT`, `BGP_LEAK`, `POWER_FAIL`, `DDOS`.

SOP corpus:

- `sop_fiber_cut_metro.md`
- `sop_bgp_route_leak.md`
- `sop_power_outage_datacenter.md`
- `sop_ddos_mitigation.md`
- `sop_sla_communication_policy.md`

## Prerequisites

- Python 3.12+
- An OpenAI API key (`OPENAI_API_KEY`) for embeddings (`text-embedding-3-small`) and drafting (`gpt-4o-mini`)

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install instructor   # used by src/agent/incident_agent.py, not listed in requirements.txt
```

Create a `.env` in the repo root:

```bash
OPENAI_API_KEY=sk-...
```

Optional overrides:

| Variable | Default | Purpose |
|---|---|---|
| `TELEMETRY_DB_PATH` | `data/circuits_telemetry.db` | Circuit SQLite path |
| `RUNBOOKS_DIR` | `data/noc_runbooks` | SOP markdown directory |
| `CHROMA_PERSIST_DIR` | `data/chroma_db` | Chroma persist directory |

Seed telemetry and build the vector index (from the repo root):

```bash
python -m src.telemetry_db
python -m src.rag.indexer
```

## Run the console

```bash
streamlit run app/app.py
```

Opens at [http://localhost:8501](http://localhost:8501).

1. Select a circuit alarm and anomaly type.
2. Generate an incident draft (RAG + structured LLM output).
3. Review retrieved runbook citations, edit the customer email, and dispatch.

## Tests

```bash
pytest -s -v tests/test_retrieval.py      # SOP hit + relevance
pytest -s -v tests/test_agent_scenarios.py  # fiber / BGP / power scenarios + guardrails
pytest -s -v tests/test_rag_evals.py      # DeepEval faithfulness / hallucination
```

`pytest.ini` sets `pythonpath = .` so `src.*` imports resolve from the repo root.

DeepEval thresholds in `tests/test_rag_evals.py`:

- Faithfulness ≥ 0.85
- Hallucination (factual alignment) ≥ 0.85

Those eval tests call the live model and consume OpenAI quota.

## Guardrails

Implemented in `src/agent/guardrails.py`:

- **Tenant isolation** — draft `client_name` / `circuit_id` must match the alarm and the SQL row. Mismatch raises `GuardrailViolation`.
- **SLA cadence** — `next_update_window_minutes` must be ≤ `contracted_sla_hours * 60`. If not, the value is clamped and marked `auto_remediated`.
