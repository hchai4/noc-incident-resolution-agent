# Retrieval baseline (2026-10-21)

Corpus: 20 SOPs (4 distractors). Retriever: whole-document + alarm aliases, k=2. No hybrid, no rerank.

| Metric | Value |
|---|---|
| hit@1 | | 0.771
| hit@2 | | 0.914
| MRR | | 0.843
| false-positive rate @ 0.65 | | 0.000

Notes: BGP leak query `pos-05` retrieved `sop_bgp_session_flap.md` on 10/20 (score 0.8605). Do not change the indexer until 10/22.