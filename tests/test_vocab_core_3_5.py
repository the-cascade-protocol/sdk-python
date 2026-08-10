"""Tests for core v3.5 — ``cascade:sourceIdentity``, the ORIGIN axis.

core v3.5 separates three source questions that were being collapsed:

  ORIGIN     ``cascade:sourceIdentity``  which organization a record came from,
                                         as a canonical token that is the same
                                         whatever transport carried it. The only
                                         one of the three usable as a
                                         reconciliation key.
  LABEL      ``clinical:sourceEHR``      what to call that organization on screen.
  INGESTION  ``cascade:sourceSystem``    how and when the data entered the pod.

This SDK does not validate: it registers the predicate and carries the value.
The value form is a scheme-prefixed token, ``org:{slug}`` / ``ns:{namespace}``
/ ``transport:{label}``, and the slug normalization belongs to the producers
(the two converters in cascade-cli), not here. Reading a v3.5 pod without the
predicate registered would drop the property silently, which is the whole cost
of not carrying it.

Every value below is synthetic. The organization names are invented and the
hosts use the RFC 2606 ``.example`` reserved TLD.
"""

from __future__ import annotations

import pytest

from cascade_protocol import (
    Condition,
    LabResult,
    NAMESPACES,
    PROPERTY_PREDICATES,
    parse_one,
    serialize,
)
from cascade_protocol.vocabularies.namespaces import (
    PROPERTY_PREDICATES_CAMEL,
    build_reverse_predicate_map,
)


def _condition(**kwargs: object) -> Condition:
    base: dict[str, object] = dict(
        id="urn:uuid:c0000000-0000-4000-8000-000000000009",
        condition_name="Essential hypertension",
        status="active",
        data_provenance="ClinicalGenerated",
        schema_version="1.3",
    )
    base.update(kwargs)
    return Condition(**base)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Predicate registration
# ---------------------------------------------------------------------------

def test_source_identity_predicate_is_registered_in_both_spellings() -> None:
    assert PROPERTY_PREDICATES["source_identity"] == "cascade:sourceIdentity"
    assert PROPERTY_PREDICATES_CAMEL["sourceIdentity"] == "cascade:sourceIdentity"


def test_source_identity_resolves_in_the_reverse_map() -> None:
    """A predicate absent from the reverse map parses to nothing at all."""
    reverse = build_reverse_predicate_map()
    assert reverse[f"{NAMESPACES['cascade']}sourceIdentity"] == "source_identity"


# ---------------------------------------------------------------------------
# The field, on every record
# ---------------------------------------------------------------------------

def test_source_identity_is_available_on_any_record() -> None:
    """``rdfs:domain owl:Thing`` — it is not a per-class property.

    Carrying it on the base record is what makes a lab result and a condition
    from one organization comparable; putting it on a subset of the models
    would leave the rest of the pod unreconcilable for no stated reason.
    """
    from dataclasses import fields

    for cls in (Condition, LabResult):
        assert "source_identity" in {f.name for f in fields(cls)}


def test_source_identity_defaults_to_none_and_emits_nothing() -> None:
    """A pod written before v3.5 carries it nowhere, and must stay unchanged."""
    turtle = serialize(_condition())
    assert "sourceIdentity" not in turtle


@pytest.mark.parametrize(
    "value",
    [
        "org:meridian",
        "ns:https://fhir.meridianhealth.example/api/FHIR/R4",
        "transport:Apple Health export",
    ],
)
def test_each_declared_scheme_round_trips(value: str) -> None:
    turtle = serialize(_condition(source_identity=value))
    assert "cascade:sourceIdentity" in turtle

    parsed = parse_one(turtle, "ConditionRecord")
    assert parsed is not None
    assert isinstance(parsed, Condition)
    assert parsed.source_identity == value


def test_source_identity_is_a_plain_string_literal() -> None:
    """Not an IRI, not a typed literal: ``rdfs:range xsd:string``.

    A colon inside the value is part of the token, and emitting it unquoted
    would make ``org:meridian`` a CURIE against an undeclared prefix.
    """
    turtle = serialize(_condition(source_identity="org:meridian"))
    assert 'cascade:sourceIdentity "org:meridian"' in turtle
    assert "^^xsd:" not in turtle.split("cascade:sourceIdentity")[1].split(";")[0]


def test_no_validation_is_applied_to_the_value() -> None:
    """Deliberate: the SDK carries the value, the producers mint it.

    An unprefixed value is wrong per core v3.5, but rejecting it here would
    make this SDK the arbiter of a normalization it does not implement, and
    would drop data a producer already wrote.
    """
    from cascade_protocol import validate_dict

    result = validate_dict(
        {
            "id": "urn:uuid:c0000000-0000-4000-8000-000000000010",
            "type": "ConditionRecord",
            "conditionName": "Essential hypertension",
            "status": "active",
            "sourceIdentity": "meridian",
            "dataProvenance": "ClinicalGenerated",
            "schemaVersion": "1.3",
        }
    )
    assert result.is_valid


def test_camel_case_input_serializes_the_predicate() -> None:
    from cascade_protocol import serialize_from_dict

    turtle = serialize_from_dict(
        {
            "id": "urn:uuid:1ab00000-0000-4000-8000-000000000011",
            "type": "LabResultRecord",
            "testName": "Glucose",
            "sourceIdentity": "org:northgate",
            "dataProvenance": "ClinicalGenerated",
            "schemaVersion": "1.3",
        }
    )
    assert 'cascade:sourceIdentity "org:northgate"' in turtle


def test_two_transports_of_one_organization_carry_one_identity() -> None:
    """The property's entire purpose, stated as a test.

    Two records of the same organization that arrived through different
    ingestion batches agree on origin. Nothing in this SDK derives that: it is
    asserted by the producer and preserved here.
    """
    from_fhir = _condition(
        id="urn:uuid:c0000000-0000-4000-8000-00000000000a",
        source_identity="org:meridian",
        source_record_id="fhir-export-2026-08",
    )
    from_ccda = _condition(
        id="urn:uuid:c0000000-0000-4000-8000-00000000000b",
        source_identity="org:meridian",
        source_record_id="ccda-import-2026-08",
    )
    a = parse_one(serialize(from_fhir), "ConditionRecord")
    b = parse_one(serialize(from_ccda), "ConditionRecord")
    assert a is not None and b is not None
    assert isinstance(a, Condition) and isinstance(b, Condition)
    assert a.source_identity == b.source_identity == "org:meridian"
    assert a.source_record_id != b.source_record_id
