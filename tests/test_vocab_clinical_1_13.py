"""Tests for clinical v1.10 through v1.13.

Four releases, not one:

  v1.10  clinical:hasEncounter, clinical:indicationReference,
         clinical:linkedCondition; clinical:linkedConditionIds deprecated.
  v1.11  clinical:indicationReference widened (restrictive rdfs:domain dropped),
         so it applies to procedures and administrations, not only medications.
  v1.12  clinical:parsedIndicationReference, a subproperty of
         clinical:indicationReference.
  v1.13  clinical:LabResult, clinical:Condition, clinical:Allergy and
         clinical:Immunization deprecated in favour of the health: forms.

The v1.13 deprecation is an asymmetry, and the asymmetry is the point:
READERS must keep accepting both spellings, because the pod export path is
still the sole emitter of the four clinical: classes and existing pods contain
them. WRITERS should emit only the health: forms. A reader that dropped the
deprecated types would return zero records for data that is right there in the
file, which is worse than an error: it looks like an empty pod.

Every fixture below is synthetic and written from the ontology.
"""

from __future__ import annotations

import pytest

from cascade_protocol import (
    Condition,
    Medication,
    Procedure,
    LabResult,
    MedicationAdministration,
    serialize,
    parse,
    DEPRECATED_TYPE_ALIASES,
)
from cascade_protocol.vocabularies.namespaces import (
    PROPERTY_PREDICATES,
    build_reverse_predicate_map,
)

CLINICAL = "https://ns.cascadeprotocol.org/clinical/v1#"

# ---------------------------------------------------------------------------
# v1.13 — deprecated class spellings must still READ
# ---------------------------------------------------------------------------

DEPRECATED_SPELLINGS_TTL = """
@prefix cascade: <https://ns.cascadeprotocol.org/core/v1#> .
@prefix clinical: <https://ns.cascadeprotocol.org/clinical/v1#> .
@prefix health: <https://ns.cascadeprotocol.org/health/v1#> .

<urn:uuid:cond-0001-aaaa-bbbb-ccccddddeeee> a clinical:Condition ;
    health:conditionName "Type 2 diabetes mellitus" ;
    health:status "active" ;
    cascade:dataProvenance cascade:ClinicalGenerated ;
    cascade:schemaVersion "1.3" .

<urn:uuid:labr-0001-aaaa-bbbb-ccccddddeeee> a clinical:LabResult ;
    health:testName "Hemoglobin A1c" ;
    health:resultValue "7.2" ;
    cascade:dataProvenance cascade:ClinicalGenerated ;
    cascade:schemaVersion "1.3" .

<urn:uuid:alrg-0001-aaaa-bbbb-ccccddddeeee> a clinical:Allergy ;
    health:allergen "Penicillin" ;
    cascade:dataProvenance cascade:ClinicalGenerated ;
    cascade:schemaVersion "1.3" .

<urn:uuid:immz-0001-aaaa-bbbb-ccccddddeeee> a clinical:Immunization ;
    health:vaccineName "Influenza, seasonal" ;
    cascade:dataProvenance cascade:ClinicalGenerated ;
    cascade:schemaVersion "1.3" .
"""


def test_the_four_deprecated_classes_are_declared_with_their_replacements() -> None:
    assert DEPRECATED_TYPE_ALIASES == {
        "clinical:LabResult": "health:LabResultRecord",
        "clinical:Condition": "health:ConditionRecord",
        "clinical:Allergy": "health:AllergyRecord",
        "clinical:Immunization": "health:ImmunizationRecord",
    }


@pytest.mark.parametrize(
    "record_type,expected_id",
    [
        ("ConditionRecord", "urn:uuid:cond-0001-aaaa-bbbb-ccccddddeeee"),
        ("LabResultRecord", "urn:uuid:labr-0001-aaaa-bbbb-ccccddddeeee"),
        ("AllergyRecord", "urn:uuid:alrg-0001-aaaa-bbbb-ccccddddeeee"),
        ("ImmunizationRecord", "urn:uuid:immz-0001-aaaa-bbbb-ccccddddeeee"),
    ],
)
def test_deprecated_class_spellings_still_parse(record_type: str, expected_id: str) -> None:
    """Absent the alias, each of these returns an EMPTY list: the type URI
    resolves to nothing, the subject is skipped, and a pod full of records
    reads as a pod with none. Existing pods carry these spellings."""
    records = parse(DEPRECATED_SPELLINGS_TTL, record_type)
    assert len(records) == 1, f"{record_type} did not parse from its deprecated spelling"
    assert records[0].id == expected_id


def test_fields_survive_the_deprecated_spelling() -> None:
    """Resolving the type is not enough; the record has to come back
    populated, or the alias would only be trading an empty list for an empty
    record."""
    condition = parse(DEPRECATED_SPELLINGS_TTL, "ConditionRecord")[0]
    assert condition.condition_name == "Type 2 diabetes mellitus"
    assert condition.status == "active"
    assert condition.data_provenance == "ClinicalGenerated"

    lab = parse(DEPRECATED_SPELLINGS_TTL, "LabResultRecord")[0]
    assert lab.test_name == "Hemoglobin A1c"
    assert lab.result_value == "7.2"


def test_both_spellings_parse_from_one_document() -> None:
    """A pod mid-migration holds both. Neither may shadow the other."""
    turtle = DEPRECATED_SPELLINGS_TTL + """
<urn:uuid:cond-0002-aaaa-bbbb-ccccddddeeee> a health:ConditionRecord ;
    health:conditionName "Hypertension" ;
    health:status "active" ;
    cascade:dataProvenance cascade:ClinicalGenerated ;
    cascade:schemaVersion "1.3" .
"""
    names = sorted(c.condition_name for c in parse(turtle, "ConditionRecord"))
    assert names == ["Hypertension", "Type 2 diabetes mellitus"]


@pytest.mark.parametrize(
    "record,deprecated,preferred",
    [
        (
            Condition(
                id="urn:uuid:cond-0003-aaaa-bbbb-ccccddddeeee",
                condition_name="Hypertension", status="active",
                data_provenance="ClinicalGenerated", schema_version="1.3",
            ),
            "clinical:Condition", "health:ConditionRecord",
        ),
        (
            LabResult(
                id="urn:uuid:labr-0003-aaaa-bbbb-ccccddddeeee",
                test_name="Potassium",
                data_provenance="ClinicalGenerated", schema_version="1.3",
            ),
            "clinical:LabResult", "health:LabResultRecord",
        ),
    ],
)
def test_the_writer_emits_only_the_preferred_spelling(
    record, deprecated: str, preferred: str
) -> None:
    """The other half of the asymmetry. Reading both and writing both would
    keep the deprecated types alive in newly written data."""
    turtle = serialize(record)
    assert f"a {preferred}" in turtle
    assert deprecated not in turtle


# ---------------------------------------------------------------------------
# v1.10-v1.12 — traversable graph edges
# ---------------------------------------------------------------------------

def test_the_edge_predicates_are_registered() -> None:
    for field, predicate in [
        ("has_encounter", "clinical:hasEncounter"),
        ("indication_reference", "clinical:indicationReference"),
        ("parsed_indication_reference", "clinical:parsedIndicationReference"),
        ("linked_condition", "clinical:linkedCondition"),
        ("linked_condition_ids", "clinical:linkedConditionIds"),
    ]:
        assert PROPERTY_PREDICATES[field] == predicate

    reverse = build_reverse_predicate_map()
    for local, field in [
        ("hasEncounter", "has_encounter"),
        ("indicationReference", "indication_reference"),
        ("parsedIndicationReference", "parsed_indication_reference"),
        ("linkedCondition", "linked_condition"),
        ("linkedConditionIds", "linked_condition_ids"),
    ]:
        assert reverse[f"{CLINICAL}{local}"] == field


def test_encounter_and_linked_condition_edges_are_iris_not_literals() -> None:
    """clinical:linkedCondition exists precisely because its predecessor
    packed UUIDs into a literal that no graph query can traverse. Writing
    these as strings would reproduce the defect the property replaced."""
    turtle = serialize(Condition(
        id="urn:uuid:cond-0004-aaaa-bbbb-ccccddddeeee",
        condition_name="Diabetic nephropathy", status="active",
        data_provenance="ClinicalGenerated", schema_version="1.3",
        has_encounter="urn:uuid:enco-0001-aaaa-bbbb-ccccddddeeee",
        linked_condition=[
            "urn:uuid:cond-0001-aaaa-bbbb-ccccddddeeee",
            "urn:uuid:cond-0002-aaaa-bbbb-ccccddddeeee",
        ],
    ))
    assert "clinical:hasEncounter <urn:uuid:enco-0001-aaaa-bbbb-ccccddddeeee>" in turtle
    assert "clinical:linkedCondition <urn:uuid:cond-0001-aaaa-bbbb-ccccddddeeee>" in turtle
    assert "clinical:linkedCondition <urn:uuid:cond-0002-aaaa-bbbb-ccccddddeeee>" in turtle
    assert '"urn:uuid:cond-0001-aaaa-bbbb-ccccddddeeee"' not in turtle


def test_condition_edges_round_trip() -> None:
    original = Condition(
        id="urn:uuid:cond-0005-aaaa-bbbb-ccccddddeeee",
        condition_name="Diabetic nephropathy", status="active",
        data_provenance="ClinicalGenerated", schema_version="1.3",
        has_encounter="urn:uuid:enco-0001-aaaa-bbbb-ccccddddeeee",
        linked_condition=["urn:uuid:cond-0001-aaaa-bbbb-ccccddddeeee"],
    )
    parsed = parse(serialize(original), "ConditionRecord")[0]
    assert parsed.has_encounter == original.has_encounter
    assert parsed.linked_condition == original.linked_condition


def test_stated_and_parsed_indications_stay_distinguishable() -> None:
    """v1.12 models the parsed form as a SUBPROPERTY so one traversal returns
    both, while the predicate itself stays the machine-readable basis:
    indicationReference restates a reference the source carried,
    parsedIndicationReference records a match an importer computed. Collapsing
    them into one field would present a computed guess as something the record
    said."""
    original = Medication(
        id="urn:uuid:medi-0001-aaaa-bbbb-ccccddddeeee",
        medication_name="Lisinopril", is_active=True,
        data_provenance="ClinicalGenerated", schema_version="1.3",
        indication_reference=["urn:uuid:cond-0002-aaaa-bbbb-ccccddddeeee"],
        parsed_indication_reference=["urn:uuid:cond-0001-aaaa-bbbb-ccccddddeeee"],
    )
    turtle = serialize(original)
    assert "clinical:indicationReference <urn:uuid:cond-0002-aaaa-bbbb-ccccddddeeee>" in turtle
    assert "clinical:parsedIndicationReference <urn:uuid:cond-0001-aaaa-bbbb-ccccddddeeee>" in turtle

    parsed = parse(turtle, "MedicationRecord")[0]
    assert parsed.indication_reference == ["urn:uuid:cond-0002-aaaa-bbbb-ccccddddeeee"]
    assert parsed.parsed_indication_reference == ["urn:uuid:cond-0001-aaaa-bbbb-ccccddddeeee"]
    assert parsed.indication_reference != parsed.parsed_indication_reference


def test_indication_reference_round_trips_on_a_procedure() -> None:
    """v1.11 dropped the restrictive rdfs:domain because FHIR carries
    reasonReference on Procedure, MedicationAdministration and other event
    resources, not only medications. Procedure indications are the common
    case in real exports, so supporting the edge on medications alone would
    silently drop most of them."""
    record = Procedure(
        id="urn:uuid:proc-0001-aaaa-bbbb-ccccddddeeee",
        procedure_name="Coronary angioplasty",
        data_provenance="ClinicalGenerated", schema_version="1.3",
        indication_reference=["urn:uuid:cond-0001-aaaa-bbbb-ccccddddeeee"],
    )
    parsed = parse(serialize(record), "ProcedureRecord")[0]
    assert parsed.indication_reference == ["urn:uuid:cond-0001-aaaa-bbbb-ccccddddeeee"]


def test_indication_reference_is_emitted_on_a_medication_administration() -> None:
    """Write path only, deliberately: clinical:MedicationAdministration has no
    deserializer registration in this SDK, which predates this sync and is
    tracked separately. Asserting a round trip here would fail for a reason
    that has nothing to do with the indication edge, and asserting nothing
    would leave the edge untested on this class."""
    turtle = serialize(MedicationAdministration(
        id="urn:uuid:mdad-0001-aaaa-bbbb-ccccddddeeee",
        medication_name="Furosemide",
        data_provenance="ClinicalGenerated", schema_version="1.3",
        indication_reference=["urn:uuid:cond-0001-aaaa-bbbb-ccccddddeeee"],
    ))
    assert "a clinical:MedicationAdministration" in turtle
    assert "clinical:indicationReference <urn:uuid:cond-0001-aaaa-bbbb-ccccddddeeee>" in turtle


def test_the_deprecated_id_literal_is_still_read() -> None:
    """clinical:linkedConditionIds is deprecated, not removed, and existing
    data carries it. Not registering the property drops the links entirely on
    parse, with nothing to say they were there."""
    turtle = """
    @prefix cascade: <https://ns.cascadeprotocol.org/core/v1#> .
    @prefix clinical: <https://ns.cascadeprotocol.org/clinical/v1#> .
    @prefix health: <https://ns.cascadeprotocol.org/health/v1#> .
    <urn:uuid:cond-0006-aaaa-bbbb-ccccddddeeee> a health:ConditionRecord ;
        health:conditionName "Chronic kidney disease" ;
        health:status "active" ;
        clinical:linkedConditionIds "cond-0001 cond-0002" ;
        cascade:dataProvenance cascade:ClinicalGenerated ;
        cascade:schemaVersion "1.3" .
    """
    condition = parse(turtle, "ConditionRecord")[0]
    assert condition.linked_condition_ids == "cond-0001 cond-0002"


def test_the_deprecated_id_literal_is_never_written_by_default() -> None:
    """Read support must not become write support: a record built without it
    stays without it."""
    turtle = serialize(Condition(
        id="urn:uuid:cond-0007-aaaa-bbbb-ccccddddeeee",
        condition_name="Chronic kidney disease", status="active",
        data_provenance="ClinicalGenerated", schema_version="1.3",
        linked_condition=["urn:uuid:cond-0001-aaaa-bbbb-ccccddddeeee"],
    ))
    assert "clinical:linkedConditionIds" not in turtle
    assert "clinical:linkedCondition " in turtle


# ---------------------------------------------------------------------------
# clinical v1.8 value set, claimed as supported since v1.9
# ---------------------------------------------------------------------------

def test_social_history_category_value_set_is_enforced() -> None:
    """clinical:SocialHistoryRecordShape constrains the category with an
    sh:in. Without the check a record categorised "tobacco" instead of
    "smokingStatus" validates clean and then matches no query keyed on the
    defined set."""
    from cascade_protocol import validate_dict

    assert validate_dict({
        "id": "urn:uuid:soch-0001-aaaa-bbbb-ccccddddeeee",
        "type": "SocialHistoryRecord",
        "socialHistoryCategory": "smokingStatus",
        "dataProvenance": "AIExtracted",
        "schemaVersion": "1.3",
    }).is_valid is True

    result = validate_dict({
        "id": "urn:uuid:soch-0002-aaaa-bbbb-ccccddddeeee",
        "type": "SocialHistoryRecord",
        "socialHistoryCategory": "tobacco",
        "dataProvenance": "AIExtracted",
        "schemaVersion": "1.3",
    })
    assert result.is_valid is False
    assert any("socialHistoryCategory" in e for e in result.errors)
