import json
from pathlib import Path

from src.rag.retriever import retrieve_sop_context

GOLDEN = Path("evals/golden_set.jsonl")
K = 2
FP_THRESHOLD = 0.65


def ranked_files(evidence):
    files = []
    for row in evidence:
        name = row["source_file"]
        if name not in files:
            files.append(name)
    return files


def main():
    rows = [json.loads(line) for line in GOLDEN.read_text().splitlines() if line.strip()]
    positives = [r for r in rows if not r["negative"]]
    negatives = [r for r in rows if r["negative"]]

    hits1 = hits2 = mrr_sum = 0.0
    misses = []
    for row in positives:
        _, evidence = retrieve_sop_context(row["query"], k=K)
        ranked = ranked_files(evidence)
        expected = row["expected_sop"]
        if ranked and ranked[0] == expected:
            hits1 += 1
        if expected in ranked[:K]:
            hits2 += 1
        if expected in ranked:
            mrr_sum += 1.0 / (ranked.index(expected) + 1)
        else:
            misses.append((row["id"], expected, ranked[:K]))

    n = len(positives)
    fp = 0
    for row in negatives:
        _, evidence = retrieve_sop_context(row["query"], k=K)
        top = evidence[0]["relevance_score"] if evidence else 0.0
        if top >= FP_THRESHOLD:
            fp += 1

    print(f"positives={n}  hit@1={hits1/n:.3f}  hit@2={hits2/n:.3f}  MRR={mrr_sum/n:.3f}")
    print(f"negatives={len(negatives)}  false_positive_rate@{FP_THRESHOLD}={fp/len(negatives):.3f}")
    print("misses:")
    for item in misses:
        print(" ", item)


if __name__ == "__main__":
    main()
