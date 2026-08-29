"""clinical v1.16: the fields a conformant export sends and an Encounter had
nowhere to keep.

Fifteen terms — fourteen properties and one class. Every one is a source element
a conformant R4 server sends and that this vocabulary gave an importer no way to
record, so an importer dropped it.

Four rulings are pinned here:

1. ENCOUNTER, nine terms. The ``Encounter.class`` Coding survives whole, not
   just its code; the reason is repeatable because ``Encounter.reasonCode`` is
   0..*; and the two ``Encounter.hospitalization`` fields are the only
   structured signal separating an admission from an office visit.
2. PARTICIPATION IS A STRUCTURE. A flat family of role-qualified predicates
   cannot represent two participants in the SAME role and cannot carry a local
   role code from an extensibly-bound source vocabulary at all.
3. TWO IDENTIFIER SPACES THAT DO NOT JOIN. ``sourceRecordId`` holds the
   server-assigned logical id and exactly one of them; ``businessIdentifier``
   holds the 0..* identifiers the source publishes, in FHIR token form.
4. A DOCUMENT HAS TWO STATUSES AND TWO ATTRIBUTIONS. ``entered-in-error`` is in
   both status value sets and means different things in each, which is why one
   predicate for both was ambiguous exactly where ambiguity costs most.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cascade_protocol import (
    Encounter,
    EncounterParticipant,
    Medication,
    serialize,
    validate,
    validate_dict,
)
from cascade_protocol.deserializer.turtle_parser import (
    parse,
    parse_encounter_participants,
)
from cascade_protocol.vocabularies.namespaces import (
    PROPERTY_PREDICATES,
    PROPERTY_PREDICATES_CAMEL,
    TYPE_MAPPING,
    TYPE_TO_MAPPING_KEY,
)

_FIXTURES = Path(__file__).resolve().parent.parent.parent / "conformance" / "fixtures"

_ENC_ID = "urn:uuid:e0c00116-0000-4000-8000-000000000001"
_P1 = "urn:uuid:e0c00116-0000-4000-8000-00000000000a"
_P2 = "urn:uuid:e0c00116-0000-4000-8000-00000000000b"


def _encounter(**overrides: object) -> Encounter:
    data: dict[str, object] = {
        "id": _ENC_ID,
        "encounter_type": "Inpatient Admission",
        "data_provenance": "EHRVerified",
        "schema_version": "1.4",
    }
    data.update(overrides)
    return Encounter(**data)  # type: ignore[arg-type]


def _encounter_dict(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "id": _ENC_ID,
        "type": "Encounter",
        "encounterType": "Inpatient Admission",
        "dataProvenance": "EHRVerified",
        "schemaVersion": "1.4",
    }
    data.update(overrides)
    return data


# ---------------------------------------------------------------------------
# 0. Registration
# ---------------------------------------------------------------------------

def test_all_fifteen_clinical_v1_16_terms_are_registered() -> None:
    assert (
        TYPE_MAPPING[TYPE_TO_MAPPING_KEY["EncounterParticipant"]]["rdf_type"]
        == "clinical:EncounterParticipant"
    )
    expected = {
        "encounter_class_display": "clinical:encounterClassDisplay",
        "encounter_class_system": "clinical:encounterClassSystem",
        "encounter_reason": "clinical:encounterReason",
        "admit_source": "clinical:admitSource",
        "discharge_disposition": "clinical:dischargeDisposition",
        "has_participant": "clinical:hasParticipant",
        "participant_name": "clinical:participantName",
        "participant_role": "clinical:participantRole",
        "participant_role_code": "clinical:participantRoleCode",
        "participant_specialty": "clinical:participantSpecialty",
        "business_identifier": "clinical:businessIdentifier",
        "document_reference_status": "clinical:documentReferenceStatus",
        "document_author_name": "clinical:documentAuthorName",
        "authenticator_name": "clinical:authenticatorName",
    }
    for snake, pred in expected.items():
        assert PROPERTY_PREDICATES[snake] == pred
    camel = {
        "encounterClassDisplay", "encounterClassSystem", "encounterReason",
        "admitSource", "dischargeDisposition", "hasParticipant",
        "participantName", "participantRole", "participantRoleCode",
        "participantSpecialty", "businessIdentifier",
        "documentReferenceStatus", "documentAuthorName", "authenticatorName",
    }
    for key in camel:
        assert PROPERTY_PREDICATES_CAMEL[key].startswith("clinical:")


# ---------------------------------------------------------------------------
# 1. Encounter.class survives as a whole Coding
# ---------------------------------------------------------------------------

def test_the_class_code_display_and_system_are_all_written() -> None:
    """Encounter.class is bound only EXTENSIBLY, so a server may send a local
    code. A local code with no display and no system is unreadable AND
    unmappable, and through v1.15 only the code survived."""
    turtle = serialize(
        _encounter(
            encounter_class="IMP",
            encounter_class_display="inpatient encounter",
            encounter_class_system="http://terminology.hl7.org/CodeSystem/v3-ActCode",
        )
    )
    assert 'clinical:encounterClass "IMP"' in turtle
    assert 'clinical:encounterClassDisplay "inpatient encounter"' in turtle
    assert "clinical:encounterClassSystem" in turtle


def test_the_class_system_is_written_as_a_typed_anyuri_literal() -> None:
    """rdfs:range is xsd:anyURI. It is a LITERAL, not an angle-bracket IRI: the
    property is a DatatypeProperty, so a resource reference would violate the
    shape's datatype constraint on both branches of its sh:or."""
    turtle = serialize(
        _encounter(encounter_class_system="urn:oid:2.16.840.1.113883.19.5.99991.7")
    )
    assert (
        'clinical:encounterClassSystem "urn:oid:2.16.840.1.113883.19.5.99991.7"^^xsd:anyURI'
        in turtle
    )
    assert "clinical:encounterClassSystem <" not in turtle


def test_a_local_class_code_survives_with_its_display_and_system() -> None:
    """The case the release names: a class code of "5" is meaningless alone."""
    turtle = serialize(
        _encounter(
            encounter_class="5",
            encounter_class_display="Hospital Encounter",
            encounter_class_system="urn:oid:1.2.840.114350.1.72.1.7",
        )
    )
    back = parse(turtle, "Encounter")[0]
    assert back.encounter_class == "5"
    assert back.encounter_class_display == "Hospital Encounter"
    assert back.encounter_class_system == "urn:oid:1.2.840.114350.1.72.1.7"


# ---------------------------------------------------------------------------
# 2. Reason (repeatable) and the two hospitalization fields
# ---------------------------------------------------------------------------

def test_every_encounter_reason_survives() -> None:
    """Encounter.reasonCode is 0..*; a single-valued predicate was discarding
    every reason after the first."""
    turtle = serialize(
        _encounter(
            encounter_reason=[
                "Peripheral oedema, three-day history",
                "Shortness of breath on exertion",
            ]
        )
    )
    assert turtle.count("clinical:encounterReason") == 2
    back = parse(turtle, "Encounter")[0]
    assert back.encounter_reason == [
        "Peripheral oedema, three-day history",
        "Shortness of breath on exertion",
    ]


def test_no_value_set_is_bound_to_the_source_text_properties() -> None:
    """FHIR binds reasonCode and admitSource PREFERRED and
    dischargeDisposition EXAMPLE. An enum over an example-strength binding
    rejects conformant data by construction."""
    assert validate_dict(
        _encounter_dict(
            encounterReason=["a local free-text reason", "302866003"],
            admitSource="Walked in off the street",
            dischargeDisposition="Left against medical advice",
        )
    ).is_valid


def test_the_hospitalization_fields_are_single_valued() -> None:
    """Encounter.hospitalization.admitSource is 0..1: a patient came from ONE
    place. Two is a merge artefact a reader cannot choose between."""
    result = validate_dict(
        _encounter_dict(admitSource=["Transfer from another hospital", "Home"])
    )
    assert not result.is_valid
    assert any("admitSource" in e for e in result.errors)


def test_admission_signals_round_trip() -> None:
    turtle = serialize(
        _encounter(
            admit_source="Transfer from another hospital",
            discharge_disposition="Discharged to home under care of a home health service",
        )
    )
    back = parse(turtle, "Encounter")[0]
    assert back.admit_source == "Transfer from another hospital"
    assert (
        back.discharge_disposition
        == "Discharged to home under care of a home health service"
    )


# ---------------------------------------------------------------------------
# 3. Participation is a structure
# ---------------------------------------------------------------------------

def test_two_participants_in_the_same_role_are_representable() -> None:
    """The axis a flat family of role-qualified predicates fails on: a visit
    routinely carries several participants in the SAME role, and
    one-predicate-per-role cannot hold them without reintroducing the
    single-value loss it was meant to fix."""
    turtle = serialize(_encounter(has_participant=[_P1, _P2]))
    assert turtle.count("clinical:hasParticipant") == 2
    assert f"clinical:hasParticipant <{_P1}>" in turtle
    assert f"clinical:hasParticipant <{_P2}>" in turtle

    both = [
        EncounterParticipant(
            id=_P1, participant_name="Alina Rooke, MD", participant_role="attending",
            participant_role_code=["ATND"],
        ),
        EncounterParticipant(
            id=_P2, participant_name="Owen Castellan, MD", participant_role="attending",
            participant_role_code=["ATND"],
        ),
    ]
    doc = "\n".join(serialize(p) for p in both)
    read = sorted(parse_encounter_participants(doc), key=lambda p: p.id)
    assert [p.participant_name for p in read] == ["Alina Rooke, MD", "Owen Castellan, MD"]
    assert [p.participant_role for p in read] == ["attending", "attending"]


def test_a_local_role_code_is_kept() -> None:
    """Encounter.participant.type is bound EXTENSIBLY, so a server may send a
    local role code and stay conformant. Rejecting one would discard the
    participant along with it."""
    p = EncounterParticipant(
        id=_P1,
        participant_name="Priya Nandakumar, NP",
        participant_role="primary performer",
        participant_role_code=["MRD-ROLE-NP", "PPRF"],
        participant_specialty="Nurse Practitioner, Acute Care",
    )
    turtle = serialize(p)
    assert turtle.count("clinical:participantRoleCode") == 2
    back = parse_encounter_participants(turtle)[0]
    assert back.participant_role_code == ["MRD-ROLE-NP", "PPRF"]
    assert validate(turtle).is_valid


def test_a_participation_requires_no_field() -> None:
    """FHIR makes every sub-element of Encounter.participant optional, and a
    participation stating only a role is still a fact the source asserted."""
    assert validate_dict(
        {"id": _P1, "type": "EncounterParticipant", "participantRole": "referrer"}
    ).is_valid


def test_a_participation_names_at_most_one_individual() -> None:
    """Encounter.participant.individual is 0..1. Two names on one participation
    is two participations."""
    result = validate_dict(
        {
            "id": _P1,
            "type": "EncounterParticipant",
            "participantName": ["Alina Rooke, MD", "Owen Castellan, MD"],
        }
    )
    assert not result.is_valid
    assert any("participantName" in e for e in result.errors)


def test_specialty_is_carried_on_the_participation_not_the_person() -> None:
    """In FHIR specialty is a property of the ROLE
    (PractitionerRole.specialty): the same clinician has different specialties
    in different roles, and it is the one they acted in on this visit that
    describes the visit."""
    assert "participant_specialty" in EncounterParticipant.__dataclass_fields__
    turtle = serialize(
        EncounterParticipant(id=_P1, participant_specialty="Cardiology")
    )
    assert 'clinical:participantSpecialty "Cardiology"' in turtle


def test_a_participation_is_not_a_health_record() -> None:
    """It carries no provenance and no schema version, and its shape requires
    neither. Subclassing CascadeRecord would invent two required fields."""
    from cascade_protocol.models.common import CascadeRecord

    assert not issubclass(EncounterParticipant, CascadeRecord)
    fields = set(EncounterParticipant.__dataclass_fields__)
    assert fields.isdisjoint({"data_provenance", "schema_version"})


# ---------------------------------------------------------------------------
# 4. The two identifier spaces
# ---------------------------------------------------------------------------

def test_business_identifier_is_repeatable_and_source_record_id_is_not() -> None:
    """Two different id spaces. Through v1.15 both were written to
    sourceRecordId, which is why a second identifier had nowhere to go."""
    turtle = serialize(
        _encounter(
            source_record_id="enc-7712",
            business_identifier=[
                "https://fhir.meridianhealth.example/visit-number|MRD-2031-0455",
                "urn:oid:2.16.840.1.113883.19.5.99991.1|VN-4471180",
            ],
        )
    )
    assert turtle.count("clinical:businessIdentifier") == 2
    assert turtle.count("health:sourceRecordId") == 1

    back = parse(turtle, "Encounter")[0]
    assert back.source_record_id == "enc-7712"
    assert back.business_identifier == [
        "https://fhir.meridianhealth.example/visit-number|MRD-2031-0455",
        "urn:oid:2.16.840.1.113883.19.5.99991.1|VN-4471180",
    ]


def test_the_token_form_survives_verbatim() -> None:
    """"{system}|{value}" is the ratified way to write a system-qualified
    identifier as one string, and is what makes two identifiers comparable
    across transports without a side table. The pipe must not be mangled."""
    ident = "urn:oid:2.16.840.1.113883.19.5.99991.1|VN-4471180"
    back = parse(serialize(_encounter(business_identifier=[ident])), "Encounter")[0]
    assert back.business_identifier == [ident]


def test_business_identifier_is_domain_free() -> None:
    """FHIR's .identifier is 0..* on EVERY resource, so restricting it to
    encounters would be false in the same way the domains v1.16 corrected
    were false."""
    turtle = serialize(
        Medication(
            id="urn:uuid:c116m000-0000-4000-8000-000000000001",
            medication_name="Lisinopril",
            is_active=True,
            data_provenance="EHRVerified",
            schema_version="1.4",
            business_identifier=["urn:oid:1.2.3|RX-99"],
        )
    )
    assert 'clinical:businessIdentifier "urn:oid:1.2.3|RX-99"' in turtle


# ---------------------------------------------------------------------------
# 5. Documents: two statuses, two attributions
# ---------------------------------------------------------------------------

def test_document_reference_status_is_a_different_predicate_from_status() -> None:
    """"entered-in-error" is in BOTH value sets and means different things in
    each — the reference was filed in error, versus the clinical content is
    repudiated. Sharing one predicate was ambiguous exactly where ambiguity
    costs most."""
    assert PROPERTY_PREDICATES["document_reference_status"] == (
        "clinical:documentReferenceStatus"
    )
    assert PROPERTY_PREDICATES["status"] != "clinical:documentReferenceStatus"


def test_an_out_of_set_document_reference_status_warns() -> None:
    """sh:Warning on the shape, so a warning here: reported, not rejected."""
    result = validate_dict(
        {
            "id": "urn:uuid:d0c00116-0000-4000-8000-000000000001",
            "type": "Encounter",
            "encounterType": "visit",
            "dataProvenance": "EHRVerified",
            "schemaVersion": "1.4",
            "documentReferenceStatus": "retired",
        }
    )
    assert result.is_valid
    assert any("documentReferenceStatus" in w for w in result.warnings)


@pytest.mark.parametrize("code", ["current", "superseded", "entered-in-error"])
def test_the_three_ratified_reference_statuses_are_clean(code: str) -> None:
    result = validate_dict(
        {
            "id": "urn:uuid:d0c00116-0000-4000-8000-000000000001",
            "type": "Encounter",
            "encounterType": "visit",
            "dataProvenance": "EHRVerified",
            "schemaVersion": "1.4",
            "documentReferenceStatus": code,
        }
    )
    assert result.is_valid
    assert not [w for w in result.warnings if "documentReferenceStatus" in w]


def test_document_author_name_is_repeatable_unlike_provider_name() -> None:
    """clinical:providerName is sh:maxCount 1 on the document shapes, so every
    author past the first was discarded on import with nothing recording it."""
    from cascade_protocol.serializer.turtle_serializer import serialize_from_dict

    turtle = serialize_from_dict(
        {
            "id": "urn:uuid:d0c00116-0000-4000-8000-000000000001",
            "type": "Encounter",
            "encounterType": "Consultation",
            "dataProvenance": "EHRVerified",
            "schemaVersion": "1.4",
            "providerName": "Alina Rooke, MD",
            "documentAuthorName": ["Owen Castellan, MD", "Priya Nandakumar, NP"],
            "authenticatorName": "Marcus Ilbery, MD",
        }
    )
    assert turtle.count("clinical:documentAuthorName") == 2
    assert turtle.count("clinical:providerName") == 1
    assert 'clinical:authenticatorName "Marcus Ilbery, MD"' in turtle


# ---------------------------------------------------------------------------
# 6. Encounter now reads back at all
# ---------------------------------------------------------------------------

def test_encounter_parses_rather_than_reading_as_empty() -> None:
    """Encounter serialized correctly but was not registered for reading, so
    parse() returned an empty list — not an error — for data sitting in the
    file. Every v1.16 encounter field would otherwise be write-only, and a
    round-trip test would pass vacuously against zero records."""
    records = parse(serialize(_encounter()), "Encounter")
    assert len(records) == 1
    assert isinstance(records[0], Encounter)


# ---------------------------------------------------------------------------
# 7. Against the shared conformance fixtures
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _FIXTURES.exists(), reason="conformance checkout not a sibling")
@pytest.mark.parametrize(
    "name,expected_valid",
    [
        ("encounter-inpatient-full.VALID.ttl", True),
        ("encounter-participant-standalone.VALID.ttl", True),
        ("encounter-participant-two-names.INVALID.ttl", False),
        ("encounter-two-admit-sources.INVALID.ttl", False),
    ],
)
def test_clinical_v1_16_conformance_fixtures(name: str, expected_valid: bool) -> None:
    turtle = (_FIXTURES / "clinical" / name).read_text(encoding="utf-8")
    assert validate(turtle).is_valid is expected_valid


@pytest.mark.skipif(not _FIXTURES.exists(), reason="conformance checkout not a sibling")
def test_the_canonical_encounter_fixture_reads_back_whole() -> None:
    """Read the SHARED fixture, not our own output. A round trip through one
    serializer only proves its two halves agree with each other."""
    turtle = (_FIXTURES / "clinical" / "encounter-inpatient-full.VALID.ttl").read_text(
        encoding="utf-8"
    )
    enc = parse(turtle, "Encounter")[0]

    assert enc.encounter_class == "IMP"
    assert enc.encounter_class_display == "inpatient encounter"
    assert enc.encounter_class_system == (
        "http://terminology.hl7.org/CodeSystem/v3-ActCode"
    )
    assert enc.encounter_reason == [
        "Peripheral oedema, three-day history",
        "Shortness of breath on exertion",
    ]
    assert enc.admit_source == "Transfer from another hospital"
    assert enc.discharge_disposition == (
        "Discharged to home under care of a home health service"
    )
    assert enc.has_participant == [
        "urn:uuid:e0c00116-0000-4000-8000-00000000000a",
        "urn:uuid:e0c00116-0000-4000-8000-00000000000b",
    ]
    # The two id spaces, kept apart.
    assert enc.source_record_id == "enc-7712"
    assert enc.business_identifier == [
        "https://fhir.meridianhealth.example/visit-number|MRD-2031-0455",
        "urn:oid:2.16.840.1.113883.19.5.99991.1|VN-4471180",
    ]

    participants = sorted(parse_encounter_participants(turtle), key=lambda p: p.id)
    assert len(participants) == 2
    assert [p.participant_name for p in participants] == [
        "Alina Rooke, MD",
        "Owen Castellan, MD",
    ]
    assert [p.participant_role for p in participants] == [
        "attending",
        "consulting physician",
    ]
    assert [p.participant_role_code for p in participants] == [["ATND"], ["CON"]]
    assert [p.participant_specialty for p in participants] == [
        "Internal Medicine",
        "Cardiology",
    ]
