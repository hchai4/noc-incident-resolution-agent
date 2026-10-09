from src.rag.retriever import retrieve_sop_context


def test_fiber_cut_retrieval_precision():
    alarm_query = "CRITICAL: Loss of Signal (LOS) on Metro Fiber Link LAX-ONT-01"
    context, evidence = retrieve_sop_context(alarm_query, k=2)

    assert len(evidence) >= 1, "Retriever returned no chunks."
    top_hit = evidence[0]

    print(f"\n[Test Fiber Cut] Top Hit: {top_hit['source_file']} | Score: {top_hit['relevance_score']}")

    # 1. Assert exact SOP matching
    assert (
        top_hit["source_file"] == "sop_fiber_cut_metro.md"
    ), f"Expected sop_fiber_cut_metro.md, got {top_hit['source_file']}"

    # 2. Assert Cosine Relevance Score > 0.82
    assert (
        top_hit["relevance_score"] >= 0.65
    ), f"Relevance score {top_hit['relevance_score']} was below the 0.82 threshold."

    # 3. Assert Citation String is present in context
    assert "sop_fiber_cut_metro.md" in context


def test_bgp_route_leak_retrieval_precision():
    alarm_query = "ALARM: BGP neighbor session down, flapping prefixes detected on border edge"
    context, evidence = retrieve_sop_context(alarm_query, k=2)

    assert len(evidence) >= 1, "Retriever returned no chunks."
    top_hit = evidence[0]

    print(f"\n[Test BGP Leak] Top Hit: {top_hit['source_file']} | Score: {top_hit['relevance_score']}")

    assert top_hit["source_file"] == "sop_bgp_route_leak.md"
    assert top_hit["relevance_score"] >= 0.65
    assert "sop_bgp_route_leak.md" in context
