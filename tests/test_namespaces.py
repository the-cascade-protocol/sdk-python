"""Tests for the vocabulary namespace and predicate registries.

Covers the v1-draft batched sync additions (spec PENDING_DOWNSTREAM_SYNC rows
1-3): the evidence facet predicates, workbench:userSourceLabel, and the external
namespaces the notes substrate reuses (oa / ical / skos). Draft vocabularies are
NOT registered in VOCAB_VERSIONS until v1.0 graduation, but their namespaces and
predicates are registered here so terms round-trip and the reverse predicate map
resolves.
"""

from __future__ import annotations

from cascade_protocol.vocabularies.namespaces import (
    NAMESPACES,
    PROPERTY_PREDICATES,
    PROPERTY_PREDICATES_CAMEL,
    build_reverse_predicate_map,
)


def test_draft_namespaces_registered() -> None:
    assert NAMESPACES["evidence"] == "https://ns.cascadeprotocol.org/evidence/v1#"
    assert NAMESPACES["workbench"] == "https://ns.cascadeprotocol.org/workbench/v1#"
    assert NAMESPACES["oa"] == "http://www.w3.org/ns/oa#"
    assert NAMESPACES["ical"] == "http://www.w3.org/2002/12/cal/ical#"
    assert NAMESPACES["skos"] == "http://www.w3.org/2004/02/skos/core#"


def test_evidence_facet_predicates() -> None:
    for name in ("direction", "basis", "strength", "settled", "reason", "confidence"):
        assert PROPERTY_PREDICATES[name] == f"evidence:{name}"
        assert PROPERTY_PREDICATES_CAMEL[name] == f"evidence:{name}"


def test_workbench_user_source_label() -> None:
    assert PROPERTY_PREDICATES["user_source_label"] == "workbench:userSourceLabel"
    assert PROPERTY_PREDICATES_CAMEL["userSourceLabel"] == "workbench:userSourceLabel"


def test_draft_predicate_prefixes_resolve_in_reverse_map() -> None:
    """A predicate whose prefix is missing from NAMESPACES is silently dropped
    from the reverse map; assert the draft facet predicates survive."""
    reverse = build_reverse_predicate_map()
    assert reverse["https://ns.cascadeprotocol.org/evidence/v1#direction"] == "direction"
    assert (
        reverse["https://ns.cascadeprotocol.org/workbench/v1#userSourceLabel"]
        == "user_source_label"
    )
