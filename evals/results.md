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