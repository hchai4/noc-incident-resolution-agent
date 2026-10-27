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
    │     Header chunks + BM25, RRF shortlist, MiniLM rerank; abstain if CE < T
    │     Then small-to-big parent SOP (k=2 files), or empty → escalate
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
src/rag/indexer.py              Split SOPs on numbered headers; embed sections + aliases
src/rag/hybrid.py               BM25 over sections/aliases; RRF fuse with dense ranks
src/rag/rerank.py               Cross-encoder ms-marco-MiniLM-L-6-v2; RETRIEVAL_ABSTAIN_THRESHOLD
src/rag/retriever.py            Dense + BM25 RRF, MiniLM rerank, parent SOP or empty
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

After the 5→20 expansion, whole-document retrieval ranked a BGP leak query as `sop_bgp_session_flap.md`. Header chunks plus small-to-big (10/22) raised hit@1. Hybrid BM25 + RRF (10/23) fuses lexical ranks with dense ranks; on this set hit@1 did not beat 10/22. Cross-encoder rerank on the RRF shortlist (10/24) recovered hit@1 to 0.857. With `RETRIEVAL_ABSTAIN_THRESHOLD=0.5`, all ten negatives return no SOP; the agent then tells the LLM there is no matching runbook and to escalate.

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
| `RETRIEVAL_ABSTAIN_THRESHOLD` | `-9.0` | Drop retrieval when the top MiniLM logit is below T. Default is off. Use `0.5` after 10/24 calibration. Set it on the process, not only in `.env` (`rerank.py` reads it at import, before `load_dotenv`). |

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

## Evaluation (retrieval)

`evals/golden_set.jsonl` is the answer key: 45 alarm strings, 35 with one expected SOP and 10 negatives that must not look like a runbook incident. `evals/retrieval_metrics.py` sends each query through `retrieve_sop_context` (`k=2` parent files) and scores filename match. It does not draft mail and does not use DeepEval. Query embedding still needs `OPENAI_API_KEY`.

The indexer splits each runbook on numbered headers (`1. Scope & Symptoms`, …), embeds those sections plus alarm aliases, and stores the full SOP as `parent_text`. The retriever searches extra dense hits, ranks the same sections with BM25, fuses both lists with RRF (`1 / (60 + rank)`), then scores the top 8 files with `cross-encoder/ms-marco-MiniLM-L-6-v2` on `(query, parent SOP)`. Evidence `relevance_score` is that CE logit, not dense cosine — do not compare FP to the old 0.65 cutoff. If the top logit is below `RETRIEVAL_ABSTAIN_THRESHOLD`, retrieval returns empty and the drafter escalates. BM25 reads markdown from disk; rebuild Chroma only after indexer changes. First MiniLM run downloads weights from Hugging Face.

```bash
uv run python -m src.rag.indexer
PYTHONPATH=. uv run python evals/retrieval_metrics.py
RETRIEVAL_ABSTAIN_THRESHOLD=0.5 PYTHONPATH=. uv run python evals/retrieval_metrics.py
```

Numbers in `evals/results.md` (same 45 rows):

| Date | Retriever | hit@1 | hit@2 | MRR | FP |
|---|---|---|---|---|---|
| 2026-10-21 | Whole document + aliases | 0.771 | 0.914 | 0.843 | 0.000 @ 0.65 cosine |
| 2026-10-22 | Header sections + aliases, parent SOP | 0.800 | 0.971 | 0.886 | 0.000 @ 0.65 cosine |
| 2026-10-23 | Dense + BM25, RRF k=60 | 0.771 | 0.971 | 0.871 | 0.000 @ 0.65 cosine |
| 2026-10-24 | RRF + MiniLM rerank, T=-9 | 0.857 | 1.000 | 0.929 | n/a (CE logit; 7/10 neg abstain) |
| 2026-10-24 | Same + abstain T=0.5 | 0.857 | 0.971 | 0.914 | n/a (CE logit; 10/10 neg abstain) |

T=0.5 is from the CE lists: 34 positives ≥ 0.97, one at -0.45; leftover negatives at T=-9 scored -8.66, -8.21, -1.62. At T=0.5, `pos-12` (BGP leak) abstains, so hit@2 drops and that row is the only miss. `tests/test_retrieval.py` can still fail on the single BGP leak string. Quote the 45-row table, not that one assert.

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
