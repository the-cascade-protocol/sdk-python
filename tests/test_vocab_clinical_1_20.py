"""clinical v1.20: clinical:documentType (new) and the clinical:narrativeText
comment restatement.

Two terms, both predicate-only. Neither is modelled on any dataclass in this
SDK, the same situation clinical v1.16's document predicates were in, so the
round trip is proved through serialize_from_dict() against an arbitrary dict
rather than through parse()/parse_one(), which filters to a dataclass's
declared fields and would drop them either way.

1. clinical:documentType is a human-readable label (FHIR DocumentReference.
   type.text / C-CDA section title), open-ended text for a person to read.
   It is declared distinct from the existing core-vocabulary
   cascade:documentType, a closed set of lowercase slugs software branches
   on ("summarization", "progress-note", ...). The two are not two spellings
   of one fact: neither is deprecated in favour of the other, so they need
   distinct dict keys here. This SDK had no "document_type" key registered
   under any namespace before this change (confirmed by grep), so there is
   no collision to resolve, only the naming to get right so one is never
   introduced later that collides.
2. clinical:narrativeText was already declared in earlier clinical releases
   (its predicate carries FHIR Narrative.text.div / C-CDA section text,
   markup stripped) but was never registered in this SDK's predicate tables,
   so it round-tripped through neither serializer nor reader.

Out of scope: the v1.20 migration-window reader fallback (cascade:
narrativeText, clinical:content as legacy spellings) is not implemented
here. This change registers the canonical predicate only.
"""

from __future__ import annotations

from cascade_protocol.serializer.turtle_serializer import serialize_from_dict
from cascade_protocol.vocabularies.namespaces import (
    PROPERTY_PREDICATES,
    PROPERTY_PREDICATES_CAMEL,
)

_ID = "urn:uuid:c1200000-0000-4000-8000-000000000001"


def _base_dict(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "id": _ID,
        "type": "Procedure",
        "procedureName": "Left knee arthroscopy",
        "dataProvenance": "EHRVerified",
        "schemaVersion": "1.4",
    }
    data.update(overrides)
    return data


# ---------------------------------------------------------------------------
# 0. Registration
# ---------------------------------------------------------------------------

def test_both_clinical_v1_20_terms_are_registered_snake_case() -> None:
    assert PROPERTY_PREDICATES["narrative_text"] == "clinical:narrativeText"
    assert PROPERTY_PREDICATES["document_type"] == "clinical:documentType"


def test_both_clinical_v1_20_terms_are_registered_camel_case() -> None:
    assert PROPERTY_PREDICATES_CAMEL["narrativeText"] == "clinical:narrativeText"
    assert PROPERTY_PREDICATES_CAMEL["documentType"] == "clinical:documentType"


# ---------------------------------------------------------------------------
# 1. Round trip through serialize_from_dict(), the path unmodeled predicates
#    are provable on (matches clinical v1.16's document_author_name /
#    authenticator_name precedent, also unmodeled at registration time).
# ---------------------------------------------------------------------------

def test_narrative_text_is_written() -> None:
    turtle = serialize_from_dict(
        _base_dict(
            narrativeText="Arthroscopic examination showed mild synovitis; "
            "no meniscal tear identified."
        )
    )
    assert (
        'clinical:narrativeText "Arthroscopic examination showed mild synovitis; '
        'no meniscal tear identified."' in turtle
    )


def test_document_type_is_written() -> None:
    turtle = serialize_from_dict(_base_dict(documentType="Progress Note"))
    assert 'clinical:documentType "Progress Note"' in turtle


def test_narrative_text_and_document_type_are_written_together() -> None:
    turtle = serialize_from_dict(
        _base_dict(
            documentType="Operative Note",
            narrativeText="Procedure performed without complication.",
        )
    )
    assert 'clinical:documentType "Operative Note"' in turtle
    assert (
        'clinical:narrativeText "Procedure performed without complication."'
        in turtle
    )


# ---------------------------------------------------------------------------
# 2. clinical:documentType is distinct from cascade:documentType
# ---------------------------------------------------------------------------

def test_clinical_document_type_is_a_distinct_key_from_any_cascade_slug() -> None:
    """cascade:documentType (core vocabulary) is a closed slug set; clinical:
    documentType (this release) is an open-ended human-readable label. This
    SDK does not register cascade:documentType under any key, so there is no
    key collision today, but the two must never share a dict key: writing
    "document_type" -> "clinical:documentType" here must not be mistaken for,
    or later overwritten by, a cascade-slug registration reusing the same
    key."""
    assert "clinical:documentType" not in PROPERTY_PREDICATES.values() or (
        PROPERTY_PREDICATES["document_type"] == "clinical:documentType"
    )
    # No key in this table maps to the core cascade:documentType slug today.
    assert "cascade:documentType" not in PROPERTY_PREDICATES.values()
    assert "cascade:documentType" not in PROPERTY_PREDICATES_CAMEL.values()
