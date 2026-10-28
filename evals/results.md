# Retrieval baseline (2026-10-21)

Corpus: 20 SOPs (4 distractors). Retriever: whole-document + alarm aliases, k=2. No hybrid, no rerank.

| Metric | Value |
|---|---|
| hit@1 | | 0.771
| hit@2 | | 0.914
| MRR | | 0.843
| false-positive rate @ 0.65 | | 0.000

Notes: BGP leak query `pos-05` retrieved `sop_bgp_session_flap.md` on 10/20 (score 0.8605). Do not change the indexer until 10/22.

# Header chunks + small-to-big (2026-10-22)
Same golden set. Embed numbered sections; return parent SOP. Aliases kept. No BM25, no rerank.
| Metric | Value |
|---|---|
| hit@1 | | 0.800
| hit@2 | | 0.971
| MRR | | 0.886
| false-positive rate @ 0.65 | | 0.000
Notes: paste the new `misses` list. If hit@1 did not beat 0.771, leave it. 10/23 is hybrid, not a silent revert.

# Hybrid BM25 + RRF (2026-10-23)

Same golden set. Dense header chunks + BM25 on sections/aliases, fused with RRF k=60. No cross-encoder.

| Metric | Value |
|---|---|
| hit@1 | | 0.771
| hit@2 | | 0.971
| MRR | | 0.871
| false-positive rate @ 0.65 | | 0.000

Notes: paste misses. Ranking is RRF; `relevance_score` in evidence is still dense cosine so FP@0.65 stays comparable.

# Cross-encoder rerank + abstain (2026-10-24)

Same golden set. RRF shortlist of 8 files, `ms-marco-MiniLM-L-6-v2` on (query, parent SOP). Evidence score is the CE logit, not dense cosine.

| Setting | hit@1 | hit@2 | MRR | FP |
|---|---|---|---|---|
| Rerank, abstain off (T=-9) | 0.857 | 1.000 | 0.929 | n/a |
| Rerank + abstain (T=0.5) | 0.857 | 0.971 | 0.914 | n/a |

Notes: T=0.5 from pos vs neg CE lists (34 positives ≥ 0.97, one -0.45). T=-9: misses empty; 7/10 negatives already abstain; remaining neg CE -8.66, -8.21, -1.62. T=0.5: all 10 negatives abstain; miss is `pos-12` `sop_bgp_route_leak.md` with empty evidence. Do not compare FP to cosine @ 0.65; an earlier print of 1.000 reused the last positive's evidence and was not ten false positives.


# Faithfulness eval (2026-10-26)

5 scenarios in `evals/faithfulness_scenarios.jsonl`, full agent (retrieval T=0.5 → gpt-4o-mini draft → guardrails).
Judge: DeepEval FaithfulnessMetric + HallucinationMetric on gpt-4o-mini, threshold 0.85. Raw JSON: `evals/faithfulness_results.json`.

| Scenario | Cited SOP | Faithfulness | Factual alignment | Guardrails |
|---|---|---|---|---|
| FIBER_CUT | `sop_fiber_cut_metro.md` | 0.88 | 0.50 | pass |
| BGP_LEAK | `sop_bgp_route_leak.md` | 1.00 | 0.50 | pass |
| POWER_FAIL | `sop_power_outage_datacenter.md` | 0.89 | 1.00 | pass |
| DDOS | `sop_ddos_mitigation.md` | 0.89 | 0.50 | pass |
| INFO | `abstained` | 0.80 | 0.50 | pass |

Summary: faithfulness mean 0.891 / min 0.800; factual alignment mean 0.600 / min 0.500; retrieval correct 5/5; guardrails 5/5.
Notes (judge reasons, from the JSON):
- FIBER_CUT 0.88: email implied updates continue until resolution; SOP only says every 60 minutes.
- POWER_FAIL 0.89: email said 45-minute updates; generator fail-over SOP says 15.
- DDOS 0.89: email repeated the alarm's 65 Gbps as the attack size against the SOP's 50 Gbps threshold.
- INFO 0.80: abstain email asserted "all circuits green"; context only said NO MATCHING SOP, escalate.
- Factual alignment 0.50 rows (fiber, bgp, ddos, abstain) cite omitted SLA / cadence facts, not invented ones. HallucinationMetric penalizes omission; faithfulness is the headline metric.
- Retrieval 5/5 and guardrails 5/5: none of the deviations are retrieval or guardrail failures. No prompt tuning done today.