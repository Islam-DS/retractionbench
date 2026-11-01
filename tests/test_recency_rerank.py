from retraction_bench.rag.recency_rerank import CandidateDocument, build_candidate_documents, rerank_by_recency


def _hit(pmid: str, score: float, corpus_role: str = "background", linked: str | None = None) -> dict:
    """A raw FAISS hit dict, shaped exactly like `corpus/embed_index.search`'s real output --
    including the fields a reranker must never use (`corpus_role`, `linked_source_registry_id`).
    """
    return {"pmid": pmid, "domain": "test-domain", "corpus_role": corpus_role, "linked_source_registry_id": linked, "score": score}


# --- forbidden-field inaccessibility (Phase 5's explicit requirement) ---


def test_candidate_document_has_no_attribute_for_any_forbidden_field() -> None:
    candidate = CandidateDocument(pmid="1", semantic_rank=1, semantic_score=0.9, pub_year=2020)
    for forbidden in ("corpus_role", "linked_source_registry_id", "domain", "title", "text", "item_id"):
        assert not hasattr(candidate, forbidden)


def test_build_candidate_documents_drops_corpus_role_and_linked_id_even_though_present_on_input() -> None:
    hits = [_hit("1", 0.9, corpus_role="superseding_evidence", linked="10.1/evidence-doi")]
    candidates = build_candidate_documents(hits, pub_year_lookup={"1": 2021})
    assert candidates == [CandidateDocument(pmid="1", semantic_rank=1, semantic_score=0.9, pub_year=2021)]
    # The dataclass physically has no slot for the forbidden fields -- not just "unused".
    assert not hasattr(candidates[0], "corpus_role")
    assert not hasattr(candidates[0], "linked_source_registry_id")


def test_build_candidate_documents_assigns_rank_positionally_not_from_the_hit() -> None:
    """Rank must come from the hit's position in the already-ordered list, never from any
    field on the hit dict itself (there is no such field on a real FAISS hit anyway)."""
    hits = [_hit("1", 0.5), _hit("2", 0.9), _hit("3", 0.1)]
    candidates = build_candidate_documents(hits, pub_year_lookup={})
    assert [c.semantic_rank for c in candidates] == [1, 2, 3]
    assert [c.pmid for c in candidates] == ["1", "2", "3"]


def test_missing_pub_year_resolves_to_none_not_a_guess() -> None:
    candidates = build_candidate_documents([_hit("1", 0.5)], pub_year_lookup={})
    assert candidates[0].pub_year is None


# --- determinism ---


def test_rerank_is_deterministic_across_repeated_calls() -> None:
    candidates = [
        CandidateDocument(pmid="a", semantic_rank=1, semantic_score=0.9, pub_year=2010),
        CandidateDocument(pmid="b", semantic_rank=2, semantic_score=0.8, pub_year=2022),
        CandidateDocument(pmid="c", semantic_rank=3, semantic_score=0.7, pub_year=None),
    ]
    first = rerank_by_recency(candidates)
    second = rerank_by_recency(candidates)
    assert first == second


# --- the frozen rule itself: year descending, missing last, semantic rank as tie-break ---


def test_more_recent_year_is_promoted_ahead_of_older_year() -> None:
    candidates = [
        CandidateDocument(pmid="old", semantic_rank=1, semantic_score=0.9, pub_year=2005),
        CandidateDocument(pmid="new", semantic_rank=2, semantic_score=0.1, pub_year=2024),
    ]
    result = rerank_by_recency(candidates)
    assert [c.pmid for c in result] == ["new", "old"]


def test_missing_year_sorts_after_every_present_year() -> None:
    candidates = [
        CandidateDocument(pmid="unknown", semantic_rank=1, semantic_score=0.99, pub_year=None),
        CandidateDocument(pmid="known", semantic_rank=2, semantic_score=0.01, pub_year=2001),
    ]
    result = rerank_by_recency(candidates)
    assert [c.pmid for c in result] == ["known", "unknown"]


def test_tied_year_breaks_by_original_semantic_rank_ascending() -> None:
    candidates = [
        CandidateDocument(pmid="rank3", semantic_rank=3, semantic_score=0.3, pub_year=2020),
        CandidateDocument(pmid="rank1", semantic_rank=1, semantic_score=0.9, pub_year=2020),
        CandidateDocument(pmid="rank2", semantic_rank=2, semantic_score=0.5, pub_year=2020),
    ]
    result = rerank_by_recency(candidates)
    assert [c.pmid for c in result] == ["rank1", "rank2", "rank3"]


def test_reranker_works_on_an_arbitrary_generic_pool_not_tied_to_any_benchmark_item() -> None:
    """The reranker must be usable for arbitrary future queries, not just the 15 replacement
    items -- demonstrated here with a pool that has no connection to any benchmark concept."""
    candidates = build_candidate_documents(
        [_hit(f"p{i}", score=1.0 / i) for i in range(1, 6)],
        pub_year_lookup={"p1": 1999, "p2": 2015, "p3": 2015, "p4": None, "p5": 2023},
    )
    result = rerank_by_recency(candidates)
    assert [c.pmid for c in result] == ["p5", "p2", "p3", "p1", "p4"]


def test_rerank_never_changes_the_set_of_documents_only_their_order() -> None:
    hits = [_hit(str(i), score=1.0 / i) for i in range(1, 11)]
    candidates = build_candidate_documents(hits, pub_year_lookup={str(i): 2000 + i for i in range(1, 11)})
    reranked = rerank_by_recency(candidates)
    assert {c.pmid for c in reranked} == {c.pmid for c in candidates}
    assert len(reranked) == len(candidates)
