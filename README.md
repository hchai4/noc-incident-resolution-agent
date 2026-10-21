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
data/noc_runbooks/              Markdown SOP source files (20; 4 are distractors)
data/circuits_telemetry.db      Generated SQLite DB (after seed)
data/chroma_db/                 Generated vector index (after index)
evals/golden_set.jsonl          45 labeled alarms (35 positive, 10 negative)
evals/retrieval_metrics.py      hit@1 / hit@2 / MRR / false-positive rate
evals/results.md                Retrieval baseline numbers
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

SOP corpus is 20 runbooks in `data/noc_runbooks/`. Four of them are near-neighbor distractors: long-haul fiber cut, planned fiber maintenance, BGP session flap, and application-layer attack. They share wording with metro fiber, BGP leak, and volumetric DDoS so dense retrieval can pick the wrong sibling.

| File | Role |
|---|---|
| `sop_fiber_cut_metro.md` | Metro LOS / OTDR |
| `sop_fiber_cut_longhaul.md` | Distractor for metro cut |
| `sop_fiber_planned_maintenance.md` | Distractor for metro cut |
| `sop_bgp_route_leak.md` | Unintended leak / hijack |
| `sop_bgp_session_flap.md` | Distractor for leak |
| `sop_ddos_mitigation.md` | Volumetric flood |
| `sop_application_layer_attack.md` | Distractor for volumetric DDoS |
| `sop_power_outage_datacenter.md` | Utility / UPS |
| `sop_generator_fail_over.md` | Diesel fail-to-start |
| `sop_cooling_failure.md` | CRAC / thermal |
| `sop_sla_communication_policy.md` | Tier cadence; no ETA hallucination |
| `sop_dns_resolver_outage.md` | Recursive DNS |
| `sop_ntp_clock_skew.md` | Time source |
| `sop_tls_certificate_expiry.md` | Handshake / chain |
| `sop_peering_congestion.md` | IX / peer utilization |
| `sop_transponder_failure.md` | Single wavelength, fiber plant up |
| `sop_ospf_adjacency_down.md` | IGP neighbor |
| `sop_mpls_lsp_down.md` | RSVP / LDP LSP |
| `sop_customer_cpe_down.md` | Last-mile CPE |
| `sop_ixp_port_down.md` | Exchange switch port |

After re-indexing the 20 files, `tests/test_retrieval.py` still ranks `sop_fiber_cut_metro.md` first for the metro LOS query (score 0.8602). The BGP leak query ranks `sop_bgp_session_flap.md` first (score 0.8605) instead of `sop_bgp_route_leak.md`. That miss is part of the 5→20 baseline; do not tune the retriever to hide it.

## Prerequisites

- Python 3.12+
- An OpenAI API key (`OPENAI_API_KEY`) for embeddings (`text-embedding-3-small`) and drafting (`gpt-4o-mini`)

## Setup

```bash
uv sync --all-groups
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

## Evaluation (retrieval baseline)

`evals/golden_set.jsonl` is the answer key: 45 alarm strings, 35 with one expected SOP and 10 negatives that must not look like a runbook incident. `evals/retrieval_metrics.py` sends each query through `retrieve_sop_context` (`k=2`) and scores filename match. It does not draft mail and does not use DeepEval. Query embedding still needs `OPENAI_API_KEY`.

From the repo root:

```bash
PYTHONPATH=. uv run python evals/retrieval_metrics.py
```

Baseline on 2026-10-21 (whole-document + alarm aliases, no hybrid, no rerank), also stored in `evals/results.md`:

| Metric | Value |
|---|---|
| hit@1 | 0.771 |
| hit@2 | 0.914 |
| MRR | 0.843 |
| false-positive rate @ 0.65 | 0.000 |

`tests/test_retrieval.py` can still fail on the single BGP leak string. The 45-row table is the number to quote, not that one assert.

## Tests

```bash
PYTHONPATH=. uv run python evals/retrieval_metrics.py  # 45-row retrieval baseline
pytest -s -v tests/test_retrieval.py      # SOP hit + relevance (BGP leak may fail after 5→20)
pytest -s -v tests/test_agent_scenarios.py  # fiber / BGP / power scenarios + guardrails
pytest -s -v tests/test_rag_evals.py      # DeepEval faithfulness / hallucination
```

`pytest.ini` sets `pythonpath = .` so `src.*` imports resolve from the repo root. The metrics script does not read `pytest.ini`; that is why `PYTHONPATH=.` is required.

DeepEval thresholds in `tests/test_rag_evals.py`:

- Faithfulness ≥ 0.85
- Hallucination (factual alignment) ≥ 0.85

Those eval tests call the live model and consume OpenAI quota.

## Guardrails

Implemented in `src/agent/guardrails.py`:

- **Tenant isolation** — draft `client_name` / `circuit_id` must match the alarm and the SQL row. Mismatch raises `GuardrailViolation`.
- **SLA cadence** — `next_update_window_minutes` must be ≤ `contracted_sla_hours * 60`. If not, the value is clamped and marked `auto_remediated`.
