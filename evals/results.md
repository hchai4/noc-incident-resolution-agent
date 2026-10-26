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