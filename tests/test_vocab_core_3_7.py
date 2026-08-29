"""core v3.7: a Pod can hold the documents its records point at.

Eight terms — ``cascade:Attachment`` plus seven properties — let a record point
at bytes stored beside the Turtle instead of at a URL that stops resolving.

What the tests here pin, in the order the release argues it:

1. The node is reached by an IRI edge, not embedded. FHIR permits bytes inline
   as base64; core v3.7 does not, because Turtle files in a Pod are
   parse-critical and an unbounded literal is paid for by every reader.
2. The three facts ``cascade:AttachmentShape`` requires at ``sh:Violation``:
   the path (nothing to open without it), the digest (nothing distinguishes the
   right bytes without it) and the ALGORITHM (without which the digest cannot be
   recomputed, and so is decorative).
3. The digest is lowercase hex because it is also the FILENAME. Base64 contains
   "/" and is case-sensitive, and two spellings of one digest defeat the
   deduplication content addressing exists to provide.
4. Media type splits across two severities: its FORM is a violation, its
   PRESENCE only a warning. Bytes with no stated type are awkward to render,
   not lost.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cascade_protocol import Attachment, LabResult, serialize, validate, validate_dict
from cascade_protocol.deserializer.turtle_parser import parse, parse_attachments
from cascade_protocol.vocabularies.namespaces import (
    PROPERTY_PREDICATES,
    PROPERTY_PREDICATES_CAMEL,
    TYPE_MAPPING,
    TYPE_TO_MAPPING_KEY,
    build_reverse_predicate_map,
)

# The real SHA-256 of the conformance fixture's synthetic payload, reused so
# these tests and the shared fixture agree on a reproducible digest rather than
# each inventing one.
_DIGEST = "8dd3c6b5f593b25cb9dc0094d67323d16c3bbc9584eda019726a38dd2cc7a471"

_FIXTURES = Path(__file__).resolve().parent.parent.parent / "conformance" / "fixtures"


def _attachment(**overrides: object) -> Attachment:
    data: dict[str, object] = {
        "id": "urn:uuid:a77a0307-0000-4000-8000-0000000000a1",
        "attachment_path": f"attachments/sha-256/{_DIGEST}",
        "content_hash": _DIGEST,
        "hash_algorithm": "sha-256",
        "attachment_media_type": "application/pdf",
        "byte_size": 184320,
        "attachment_title": "Comprehensive Metabolic Panel — signed report",
    }
    data.update(overrides)
    return Attachment(**data)  # type: ignore[arg-type]


def _attachment_dict(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "id": "urn:uuid:a77a0307-0000-4000-8000-0000000000a1",
        "type": "Attachment",
        "attachmentPath": f"attachments/sha-256/{_DIGEST}",
        "contentHash": _DIGEST,
        "hashAlgorithm": "sha-256",
        "attachmentMediaType": "application/pdf",
    }
    data.update(overrides)
    return data


# ---------------------------------------------------------------------------
# 1. Registration
# ---------------------------------------------------------------------------

def test_all_eight_core_v3_7_terms_are_registered() -> None:
    """The class plus its seven properties, in both key spellings."""
    assert TYPE_MAPPING[TYPE_TO_MAPPING_KEY["Attachment"]]["rdf_type"] == "cascade:Attachment"

    expected = {
        "has_attachment": "cascade:hasAttachment",
        "attachment_path": "cascade:attachmentPath",
        "attachment_media_type": "cascade:attachmentMediaType",
        "content_hash": "cascade:contentHash",
        "hash_algorithm": "cascade:hashAlgorithm",
        "byte_size": "cascade:byteSize",
        "attachment_title": "cascade:attachmentTitle",
    }
    for snake, pred in expected.items():
        assert PROPERTY_PREDICATES[snake] == pred

    camel = {
        "hasAttachment": "cascade:hasAttachment",
        "attachmentPath": "cascade:attachmentPath",
        "attachmentMediaType": "cascade:attachmentMediaType",
        "contentHash": "cascade:contentHash",
        "hashAlgorithm": "cascade:hashAlgorithm",
        "byteSize": "cascade:byteSize",
        "attachmentTitle": "cascade:attachmentTitle",
    }
    for key, pred in camel.items():
        assert PROPERTY_PREDICATES_CAMEL[key] == pred


def test_attachment_title_does_not_collide_with_the_manifest_title() -> None:
    """``title`` is already bound to dcterms:title by cascade:ExportManifest.

    The predicate registry is keyed on the Python field name, so an Attachment
    field spelled ``title`` would emit an attachment label as a Dublin Core
    dataset title. The vocabulary's own spelling is what keeps the two apart.
    """
    assert PROPERTY_PREDICATES["title"] == "dcterms:title"
    assert PROPERTY_PREDICATES["attachment_title"] == "cascade:attachmentTitle"
    assert {f.name for f in Attachment.__dataclass_fields__.values()}.isdisjoint({"title"})


# ---------------------------------------------------------------------------
# 2. The edge is an IRI, and the node is its own subject
# ---------------------------------------------------------------------------

def test_the_edge_is_a_repeated_iri_never_a_literal() -> None:
    """cascade:HasAttachmentEdgeShape asserts sh:nodeKind sh:IRI.

    The point of the IRI is that the record and the attachment can live in
    DIFFERENT files, which is how a Pod partitioned by record type stores them.
    A quoted literal would put the reference in a form nothing can resolve.
    """
    turtle = serialize(
        LabResult(
            id="urn:uuid:a77a0307-0000-4000-8000-000000000001",
            test_name="Comprehensive Metabolic Panel",
            data_provenance="EHRVerified",
            schema_version="1.4",
            has_attachment=[
                "urn:uuid:a77a0307-0000-4000-8000-0000000000a1",
                "urn:uuid:a77a0307-0000-4000-8000-0000000000a2",
            ],
        )
    )
    assert "cascade:hasAttachment <urn:uuid:a77a0307-0000-4000-8000-0000000000a1>" in turtle
    assert "cascade:hasAttachment <urn:uuid:a77a0307-0000-4000-8000-0000000000a2>" in turtle
    assert 'cascade:hasAttachment "' not in turtle


def test_the_edge_is_domain_free_so_it_lives_on_the_base_record() -> None:
    """core v3.7 leaves the domain unrestricted: any record that renders as a
    document may carry one. Restricting it to one class would be false."""
    from cascade_protocol.models.common import CascadeRecord

    assert "has_attachment" in CascadeRecord.__dataclass_fields__


def test_attachment_serializes_as_its_own_typed_subject() -> None:
    turtle = serialize(_attachment())
    assert "a cascade:Attachment" in turtle
    assert f'cascade:attachmentPath "attachments/sha-256/{_DIGEST}"' in turtle
    assert f'cascade:contentHash "{_DIGEST}"' in turtle
    assert 'cascade:hashAlgorithm "sha-256"' in turtle
    assert 'cascade:attachmentMediaType "application/pdf"' in turtle
    assert "cascade:byteSize 184320" in turtle


def test_attachment_round_trips(  ) -> None:
    """A serialize-only check would pass while the reader dropped everything."""
    turtle = serialize(_attachment())
    back = parse_attachments(turtle)
    assert len(back) == 1
    got = back[0]
    assert got.attachment_path == f"attachments/sha-256/{_DIGEST}"
    assert got.content_hash == _DIGEST
    assert got.hash_algorithm == "sha-256"
    assert got.attachment_media_type == "application/pdf"
    assert got.byte_size == 184320
    assert got.attachment_title == "Comprehensive Metabolic Panel — signed report"


def test_byte_size_reads_back_as_an_integer() -> None:
    """xsd:integer, so a consumer can compare sizes without parsing strings."""
    got = parse_attachments(serialize(_attachment(byte_size=7)))[0]
    assert got.byte_size == 7
    assert isinstance(got.byte_size, int)


def test_parse_does_not_return_an_empty_list_for_a_type_it_can_write() -> None:
    """The silent-empty-list defect CLAUDE.md records for other types.

    Returning [] rather than raising is worse than an error, because nothing
    reports it: a pod full of attachments reads as a pod with none.
    """
    records = parse(serialize(_attachment()), "Attachment")
    assert len(records) == 1
    assert isinstance(records[0], Attachment)


def test_the_edge_reads_back_as_a_list_of_iris() -> None:
    turtle = serialize(
        LabResult(
            id="urn:uuid:a77a0307-0000-4000-8000-000000000001",
            test_name="CMP",
            data_provenance="EHRVerified",
            schema_version="1.4",
            has_attachment=["urn:uuid:aaaa-1", "urn:uuid:aaaa-2"],
        )
    )
    lab = parse(turtle, "LabResultRecord")[0]
    assert lab.has_attachment == ["urn:uuid:aaaa-1", "urn:uuid:aaaa-2"]


# ---------------------------------------------------------------------------
# 3. The three violation-severity facts
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("missing", ["attachmentPath", "contentHash", "hashAlgorithm"])
def test_each_required_fact_is_required(missing: str) -> None:
    """Each buys something specific: somewhere to look, something to compare,
    and the means to recompute the comparison."""
    data = _attachment_dict()
    del data[missing]
    result = validate_dict(data)
    assert not result.is_valid
    assert any(missing in e for e in result.errors)


def test_the_algorithm_is_not_enumerated() -> None:
    """RFC 6920's registry grows. An enum would have to be revised to accept a
    stronger hash, which is the wrong direction for a property that exists so
    the algorithm CAN be replaced."""
    for algorithm in ("sha-256", "sha-512", "blake2b-256"):
        assert validate_dict(
            _attachment_dict(hashAlgorithm=algorithm, contentHash="a" * 64)
        ).is_valid


def test_an_uppercase_digest_is_rejected() -> None:
    """The digest is also the FILENAME. Two spellings of one digest defeat the
    deduplication that content addressing exists to provide, and case-folding
    is unsafe on a case-insensitive filesystem."""
    result = validate_dict(_attachment_dict(contentHash=_DIGEST.upper()))
    assert not result.is_valid
    assert any("contentHash" in e for e in result.errors)


def test_a_short_digest_is_rejected() -> None:
    assert not validate_dict(_attachment_dict(contentHash="abc123")).is_valid


@pytest.mark.parametrize(
    "path",
    [
        "/etc/passwd",                       # absolute: breaks when a Pod is copied
        "https://example.org/report.pdf",    # a URL, not a pod-relative path
        "attachments/../../etc/passwd",      # traversal: reads outside the Pod
        "../secrets",
    ],
)
def test_a_path_that_escapes_the_pod_is_rejected(path: str) -> None:
    result = validate_dict(_attachment_dict(attachmentPath=path))
    assert not result.is_valid
    assert any("attachmentPath" in e for e in result.errors)


def test_a_pod_relative_path_is_accepted() -> None:
    assert validate_dict(
        _attachment_dict(attachmentPath=f"attachments/sha-256/{_DIGEST}")
    ).is_valid


# ---------------------------------------------------------------------------
# 4. Media type: form is a violation, presence is only a warning
# ---------------------------------------------------------------------------

def test_a_missing_media_type_warns_but_does_not_invalidate() -> None:
    """Stored bytes with no stated type are awkward to render, not lost, so a
    missing one must not invalidate the record that points at them."""
    data = _attachment_dict()
    del data["attachmentMediaType"]
    result = validate_dict(data)
    assert result.is_valid
    assert any("media type" in w for w in result.warnings)


def test_a_malformed_media_type_is_a_violation() -> None:
    """A value that is not type/subtype is not a media type."""
    result = validate_dict(_attachment_dict(attachmentMediaType="pdf"))
    assert not result.is_valid
    assert any("attachmentMediaType" in e for e in result.errors)


def test_two_media_types_on_one_set_of_bytes_are_rejected() -> None:
    result = validate_dict(
        _attachment_dict(attachmentMediaType=["application/pdf", "text/html"])
    )
    assert not result.is_valid


def test_a_negative_byte_size_is_rejected() -> None:
    """Not a small file: a sign error at an import boundary."""
    assert not validate_dict(_attachment_dict(byteSize=-1)).is_valid


# ---------------------------------------------------------------------------
# 5. Against the shared conformance fixtures
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _FIXTURES.exists(), reason="conformance checkout not a sibling")
@pytest.mark.parametrize(
    "name,expected_valid",
    [
        ("attachment-linked-report.VALID.ttl", True),
        ("attachment-no-media-type.WARN.ttl", True),
        ("attachment-no-path.INVALID.ttl", False),
        ("attachment-no-content-hash.INVALID.ttl", False),
        ("attachment-no-hash-algorithm.INVALID.ttl", False),
        ("attachment-absolute-path.INVALID.ttl", False),
        ("attachment-parent-traversal-path.INVALID.ttl", False),
        ("attachment-uppercase-digest.INVALID.ttl", False),
    ],
)
def test_core_v3_7_conformance_fixtures(name: str, expected_valid: bool) -> None:
    turtle = (_FIXTURES / "core" / name).read_text(encoding="utf-8")
    assert validate(turtle).is_valid is expected_valid


@pytest.mark.skipif(not _FIXTURES.exists(), reason="conformance checkout not a sibling")
def test_the_canonical_fixture_reads_back_whole() -> None:
    """Reading the shared fixture, not our own output: a round trip through one
    serializer proves the two halves agree with each other, not with the spec."""
    turtle = (_FIXTURES / "core" / "attachment-linked-report.VALID.ttl").read_text(
        encoding="utf-8"
    )
    attachments = parse_attachments(turtle)
    assert len(attachments) == 1
    got = attachments[0]
    assert got.content_hash == _DIGEST
    assert got.hash_algorithm == "sha-256"
    assert got.attachment_media_type == "application/pdf"
    assert got.byte_size == 184320

    lab = parse(turtle, "LabResultRecord")[0]
    assert lab.has_attachment == ["urn:uuid:a77a0307-0000-4000-8000-0000000000a1"]
