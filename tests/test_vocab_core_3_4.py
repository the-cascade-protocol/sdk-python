"""Tests for core v3.4 — the pod export manifest vocabulary.

Thirty-two ``cascade:`` terms appear in a conforming pod export and none of
them had a definition before core v3.4, nor any support in this SDK. Reading a
pod's ``manifest.ttl`` returned nothing at all: the manifest is the only place
that says, up front, how many records of each kind an export holds and which
provenance layers are represented.

Every fixture below is synthetic and written from the ontology.
"""

from __future__ import annotations

import pytest

from cascade_protocol import (
    ExportManifest,
    RecordSummary,
    InteractionScenario,
    DeviceSource,
    serialize_export_manifest,
    parse_export_manifest,
    validate_dict,
    NAMESPACES,
    TYPE_MAPPING,
    RECORD_SUMMARY_COUNT_CLASSES,
    RECORD_SUMMARY_ENTITY_COUNTS,
    RECORD_SUMMARY_DAY_COUNTS,
)
from cascade_protocol.serializer.turtle_serializer import _TYPE_PREDICATE_OVERRIDES
from cascade_protocol.vocabularies.namespaces import (
    PROPERTY_PREDICATES,
    build_reverse_predicate_map,
)

CASCADE = NAMESPACES["cascade"]

# ---------------------------------------------------------------------------
# Synthetic manifest, written from ontologies/core/v1/core.ttl and
# core.shapes.ttl. Not derived from any real export.
# ---------------------------------------------------------------------------

SYNTHETIC_MANIFEST_TTL = """
@prefix cascade: <https://ns.cascadeprotocol.org/core/v1#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<> a cascade:ExportManifest ;
    dcterms:title "Synthetic Test Pod" ;
    dcterms:description "Written from the core v3.4 ontology for SDK tests." ;
    dcterms:created "2026-08-03T00:00:00+00:00"^^xsd:dateTime ;
    dcterms:creator "Cascade Protocol Test Suite" ;
    cascade:schemaVersion "1.3" ;
    cascade:patientProfileVersion "2.0" ;
    cascade:provenanceLayers (
        cascade:ClinicalGenerated
        cascade:DeviceGenerated
        cascade:SelfReported
    ) ;
    cascade:clinicalSummary [
        a cascade:RecordSummary ;
        cascade:domain "clinical" ;
        cascade:conditionCount "4"^^xsd:integer ;
        cascade:medicationCount "6"^^xsd:integer ;
        cascade:allergyCount "2"^^xsd:integer ;
        cascade:labResultCount "9"^^xsd:integer ;
        cascade:immunizationCount "3"^^xsd:integer ;
        cascade:coverageCount "1"^^xsd:integer ;
        cascade:vitalSignDays "14"^^xsd:integer ;
        cascade:dataProvenance cascade:ClinicalGenerated ;
        cascade:notes "Synthetic clinical partition."
    ] ;
    cascade:wellnessSummary [
        a cascade:RecordSummary ;
        cascade:domain "wellness" ;
        cascade:supplementCount "2"^^xsd:integer ;
        cascade:heartRateDays "14"^^xsd:integer ;
        cascade:bloodPressureDays "14"^^xsd:integer ;
        cascade:activityDays "14"^^xsd:integer ;
        cascade:sleepDays "14"^^xsd:integer ;
        cascade:dataProvenance cascade:DeviceGenerated ;
        cascade:notes "Synthetic wellness partition."
    ] ;
    cascade:deviceSources (
        [ a prov:Agent ; prov:label "Test Wearable" ;
          cascade:sourceType "healthKit" ;
          cascade:dataTypes "heartRate, activity, sleep" ]
        [ a prov:Agent ; prov:label "Test BP Cuff" ;
          cascade:sourceType "bluetoothDevice" ;
          cascade:dataTypes "bloodPressure" ]
    ) ;
    cascade:interactionScenarios (
        [
            a cascade:InteractionScenario ;
            dcterms:title "Synthetic cross-provenance interaction" ;
            dcterms:description "An EHR-prescribed drug against a self-reported supplement against a lab value." ;
            cascade:involvedResources (
                <clinical/medications.ttl>
                <wellness/supplements.ttl>
                <clinical/lab-results.ttl>
            ) ;
            cascade:severity "high" ;
            cascade:requiresCrossProvenance true
        ]
    ) .
"""


def _make_manifest() -> ExportManifest:
    """Build the dataclass equivalent of SYNTHETIC_MANIFEST_TTL."""
    return ExportManifest(
        title="Synthetic Test Pod",
        description="Written from the core v3.4 ontology for SDK tests.",
        created="2026-08-03T00:00:00+00:00",
        creator="Cascade Protocol Test Suite",
        schema_version="1.3",
        patient_profile_version="2.0",
        provenance_layers=["ClinicalGenerated", "DeviceGenerated", "SelfReported"],
        clinical_summary=RecordSummary(
            domain="clinical",
            condition_count=4,
            medication_count=6,
            allergy_count=2,
            lab_result_count=9,
            immunization_count=3,
            coverage_count=1,
            vital_sign_days=14,
            data_provenance="ClinicalGenerated",
            notes="Synthetic clinical partition.",
        ),
        wellness_summary=RecordSummary(
            domain="wellness",
            supplement_count=2,
            heart_rate_days=14,
            blood_pressure_days=14,
            activity_days=14,
            sleep_days=14,
            data_provenance="DeviceGenerated",
            notes="Synthetic wellness partition.",
        ),
        device_sources=[
            DeviceSource(
                label="Test Wearable",
                source_type="healthKit",
                data_types="heartRate, activity, sleep",
            ),
            DeviceSource(
                label="Test BP Cuff",
                source_type="bluetoothDevice",
                data_types="bloodPressure",
            ),
        ],
        interaction_scenarios=[
            InteractionScenario(
                title="Synthetic cross-provenance interaction",
                description=(
                    "An EHR-prescribed drug against a self-reported supplement "
                    "against a lab value."
                ),
                involved_resources=[
                    "clinical/medications.ttl",
                    "wellness/supplements.ttl",
                    "clinical/lab-results.ttl",
                ],
                severity="high",
                requires_cross_provenance=True,
            )
        ],
    )


# ---------------------------------------------------------------------------
# Term registration
# ---------------------------------------------------------------------------

# The 32 terms core v3.4 defines. Enumerated by hand from the ontology so that
# dropping a registration fails here rather than showing up as a silently
# missing field on a parsed manifest.
_CORE_34_CLASSES = ["ExportManifest", "RecordSummary", "InteractionScenario"]

_CORE_34_PROPERTIES = [
    # manifest structure
    "patientProfileVersion", "provenanceLayers", "clinicalSummary",
    "wellnessSummary", "deviceSources", "interactionScenarios",
    # record summary
    "domain", "notes",
    "conditionCount", "medicationCount", "allergyCount", "labResultCount",
    "immunizationCount", "coverageCount", "supplementCount",
    "vitalSignDays", "heartRateDays", "bloodPressureDays", "activityDays",
    "sleepDays",
    # interaction scenario
    "involvedResources", "severity", "requiresCrossProvenance",
    # device sources
    "sourceType", "dataTypes", "version",
    # reading-level
    "date", "sampleCount", "loincCode",
]


def _registered_cascade_locals() -> set[str]:
    """Every cascade: local name this SDK can write or read."""
    names: set[str] = set()
    for shorthand in PROPERTY_PREDICATES.values():
        if shorthand.startswith("cascade:"):
            names.add(shorthand.split(":", 1)[1])
    # Type-scoped spellings (cascade:date, cascade:notes, cascade:loincCode)
    # live in the serializer overrides, not the global table.
    for overrides in _TYPE_PREDICATE_OVERRIDES.values():
        for shorthand in overrides.values():
            if shorthand.startswith("cascade:"):
                names.add(shorthand.split(":", 1)[1])
    return names


def test_core_34_defines_thirty_two_terms() -> None:
    assert len(_CORE_34_CLASSES) + len(_CORE_34_PROPERTIES) == 32


def test_core_34_classes_are_registered() -> None:
    """Absent the registration, TYPE_MAPPING has no entry and neither the
    serializer nor the deserializer can resolve the class at all."""
    rdf_types = {m["rdf_type"] for m in TYPE_MAPPING.values()}
    for name in _CORE_34_CLASSES:
        assert f"cascade:{name}" in rdf_types, f"cascade:{name} not in TYPE_MAPPING"


def test_core_34_properties_are_registered() -> None:
    registered = _registered_cascade_locals()
    missing = [n for n in _CORE_34_PROPERTIES if n not in registered]
    assert not missing, f"core v3.4 properties not registered: {missing}"


def test_core_34_properties_resolve_in_the_reverse_map() -> None:
    """A predicate whose prefix does not resolve is silently dropped from the
    reverse map, so it would parse to nothing rather than raising."""
    reverse = build_reverse_predicate_map()
    for name in ["patientProfileVersion", "domain", "conditionCount", "severity",
                 "requiresCrossProvenance", "sourceType", "sampleCount"]:
        assert f"{CASCADE}{name}" in reverse, f"cascade:{name} missing from reverse map"


# ---------------------------------------------------------------------------
# VoID modelling (core v3.4)
# ---------------------------------------------------------------------------

def test_entity_counts_are_paired_with_the_void_class_they_count() -> None:
    """cascade:RecordSummary is a void:Dataset and each entity count is a
    subproperty of void:entities naming the void:class it counts. Absent the
    pairing a VoID-aware consumer cannot tell what a count is counting."""
    assert RECORD_SUMMARY_COUNT_CLASSES["cascade:conditionCount"] == (
        "https://ns.cascadeprotocol.org/health/v1#ConditionRecord"
    )
    assert RECORD_SUMMARY_COUNT_CLASSES["cascade:medicationCount"] == (
        "https://ns.cascadeprotocol.org/clinical/v1#Medication"
    )
    assert RECORD_SUMMARY_COUNT_CLASSES["cascade:supplementCount"] == (
        "https://ns.cascadeprotocol.org/clinical/v1#Supplement"
    )
    # Lab results, allergies and immunizations count the health: classes, not
    # the deprecated clinical: spellings.
    for prop, cls in [
        ("cascade:labResultCount", "LabResultRecord"),
        ("cascade:allergyCount", "AllergyRecord"),
        ("cascade:immunizationCount", "ImmunizationRecord"),
    ]:
        assert RECORD_SUMMARY_COUNT_CLASSES[prop] == (
            f"https://ns.cascadeprotocol.org/health/v1#{cls}"
        )


def test_coverage_count_is_an_entity_count_with_no_paired_class() -> None:
    """It is rdfs:subPropertyOf void:entities but the ontology names no
    void:class for it. Asserting a class here would be inventing one."""
    assert "cascade:coverageCount" in RECORD_SUMMARY_ENTITY_COUNTS
    assert "cascade:coverageCount" not in RECORD_SUMMARY_COUNT_CLASSES


def test_day_counts_are_not_entity_counts() -> None:
    """Day counts count DAYS COVERED, not entities: a 30-day heart rate
    history holds far more than 30 readings. Conflating the two makes the VoID
    reading of a pod wrong, so they must not overlap."""
    assert RECORD_SUMMARY_DAY_COUNTS.isdisjoint(RECORD_SUMMARY_ENTITY_COUNTS)
    assert "cascade:sleepDays" in RECORD_SUMMARY_DAY_COUNTS
    assert len(RECORD_SUMMARY_DAY_COUNTS) == 5


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def test_parses_a_manifest_into_typed_fields() -> None:
    """Absent parse_export_manifest, a pod's manifest.ttl is unreadable: the
    entire manifest vocabulary was unregistered, so every field below came
    back as nothing."""
    manifest = parse_export_manifest(SYNTHETIC_MANIFEST_TTL)
    assert manifest is not None
    assert manifest.title == "Synthetic Test Pod"
    assert manifest.schema_version == "1.3"
    assert manifest.patient_profile_version == "2.0"
    assert manifest.creator == "Cascade Protocol Test Suite"
    # <> is the empty relative IRI meaning "this document".
    assert manifest.id == ""


def test_parses_provenance_layers_as_ordered_local_names() -> None:
    """The layers are an rdf:List of cascade: IRIs. Order is asserted because
    the property is documented as an ordered list, and the local names are
    stripped so a caller can compare them to a dataProvenance value."""
    manifest = parse_export_manifest(SYNTHETIC_MANIFEST_TTL)
    assert manifest is not None
    assert manifest.provenance_layers == [
        "ClinicalGenerated",
        "DeviceGenerated",
        "SelfReported",
    ]


def test_parses_record_summaries_including_the_cascade_notes_spelling() -> None:
    """cascade:notes is a different predicate from health:notes; reading the
    manifest with the record-level spelling drops the commentary entirely."""
    manifest = parse_export_manifest(SYNTHETIC_MANIFEST_TTL)
    assert manifest is not None
    clinical = manifest.clinical_summary
    assert clinical is not None
    assert clinical.domain == "clinical"
    assert clinical.condition_count == 4
    assert clinical.medication_count == 6
    assert clinical.allergy_count == 2
    assert clinical.lab_result_count == 9
    assert clinical.immunization_count == 3
    assert clinical.coverage_count == 1
    assert clinical.vital_sign_days == 14
    assert clinical.data_provenance == "ClinicalGenerated"
    assert clinical.notes == "Synthetic clinical partition."

    wellness = manifest.wellness_summary
    assert wellness is not None
    assert wellness.supplement_count == 2
    assert wellness.sleep_days == 14
    assert wellness.activity_days == 14


def test_summary_for_selects_by_domain() -> None:
    manifest = parse_export_manifest(SYNTHETIC_MANIFEST_TTL)
    assert manifest is not None
    assert manifest.summary_for("wellness") is manifest.wellness_summary
    assert manifest.summary_for("clinical") is manifest.clinical_summary
    assert manifest.summary_for("genomics") is None


def test_parses_device_sources_in_order() -> None:
    manifest = parse_export_manifest(SYNTHETIC_MANIFEST_TTL)
    assert manifest is not None
    assert [d.label for d in manifest.device_sources] == [
        "Test Wearable",
        "Test BP Cuff",
    ]
    assert manifest.device_sources[0].source_type == "healthKit"
    assert manifest.device_sources[1].data_types == "bloodPressure"


def test_parses_interaction_scenario_with_relative_resource_paths() -> None:
    """involvedResources are pod-relative IRIs. They are resolved against a
    fixed sentinel base and stripped back, so they read as the paths the file
    carries rather than as whatever the parsing host's cwd happened to be."""
    manifest = parse_export_manifest(SYNTHETIC_MANIFEST_TTL)
    assert manifest is not None
    assert len(manifest.interaction_scenarios) == 1
    scenario = manifest.interaction_scenarios[0]
    assert scenario.title == "Synthetic cross-provenance interaction"
    assert scenario.severity == "high"
    assert scenario.requires_cross_provenance is True
    assert scenario.involved_resources == [
        "clinical/medications.ttl",
        "wellness/supplements.ttl",
        "clinical/lab-results.ttl",
    ]


def test_parse_returns_none_when_the_document_declares_no_manifest() -> None:
    turtle = """
    @prefix cascade: <https://ns.cascadeprotocol.org/core/v1#> .
    <urn:uuid:x> cascade:schemaVersion "1.3" .
    """
    assert parse_export_manifest(turtle) is None


# ---------------------------------------------------------------------------
# Serialization and round trip
# ---------------------------------------------------------------------------

def test_serializes_the_empty_relative_subject() -> None:
    """A manifest describes the document it lives in, so its subject is <>."""
    turtle = serialize_export_manifest(_make_manifest())
    assert "<> " in turtle
    assert "a cascade:ExportManifest" in turtle


def test_serializes_provenance_layers_as_iris_not_literals() -> None:
    """cascade:provenanceLayers ranges over cascade:DataProvenance
    individuals. Writing them as string literals would produce data no
    provenance-aware consumer can match against a dataProvenance value."""
    turtle = serialize_export_manifest(_make_manifest())
    assert "cascade:provenanceLayers ( cascade:ClinicalGenerated" in turtle
    assert '"ClinicalGenerated"' not in turtle


def test_serializes_summary_notes_with_the_cascade_spelling() -> None:
    turtle = serialize_export_manifest(_make_manifest())
    assert "cascade:notes " in turtle
    assert "health:notes" not in turtle


def test_round_trips_a_manifest() -> None:
    """Serialize then parse must return the same manifest. Absent either
    direction this is the test that fails; it is the only check that the
    predicate a field is written under is the predicate it is read from."""
    original = _make_manifest()
    parsed = parse_export_manifest(serialize_export_manifest(original))
    assert parsed == original


def test_round_trips_a_manifest_read_from_turtle() -> None:
    """The hand-written Turtle and the dataclass describe the same manifest,
    so parsing the Turtle must produce exactly the dataclass. This catches a
    parser that agrees with its own serializer but not with the ontology."""
    assert parse_export_manifest(SYNTHETIC_MANIFEST_TTL) == _make_manifest()


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def test_manifest_without_schema_version_is_rejected() -> None:
    """cascade:ExportManifestShape requires it: without a schema version a
    consumer cannot decide whether it can read the export at all."""
    result = validate_dict({
        "id": "",
        "type": "ExportManifest",
        "title": "Incomplete Manifest",
        "created": "2026-08-03T00:00:00Z",
    })
    assert result.is_valid is False
    assert any("schemaVersion" in e for e in result.errors)


def test_manifest_with_the_empty_relative_subject_is_accepted() -> None:
    """<> is the correct subject for a manifest, so an empty id must not be
    treated as a missing required field."""
    result = validate_dict({
        "id": "",
        "type": "ExportManifest",
        "title": "Complete Manifest",
        "created": "2026-08-03T00:00:00Z",
        "schemaVersion": "1.3",
    })
    assert result.is_valid is True, result.errors


@pytest.mark.parametrize("count,expected_valid", [(0, True), (5, True), (-1, False)])
def test_record_summary_counts_must_be_non_negative(count: int, expected_valid: bool) -> None:
    """A negative count silently corrupts any completeness check built on it."""
    result = validate_dict({
        "type": "RecordSummary",
        "domain": "clinical",
        "conditionCount": count,
    })
    assert result.is_valid is expected_valid


def test_day_counts_are_bounded_above() -> None:
    """A "days covered" figure larger than a decade of daily readings is a
    unit error, not a long history."""
    assert validate_dict({
        "type": "RecordSummary", "domain": "wellness", "sleepDays": 36500,
    }).is_valid is True
    result = validate_dict({
        "type": "RecordSummary", "domain": "wellness", "sleepDays": 36501,
    })
    assert result.is_valid is False
    assert any("sleepDays" in e for e in result.errors)


def test_interaction_scenario_severity_is_constrained() -> None:
    assert validate_dict({
        "type": "InteractionScenario",
        "title": "T",
        "involvedResources": ["clinical/medications.ttl"],
        "severity": "critical",
    }).is_valid is True
    result = validate_dict({
        "type": "InteractionScenario",
        "title": "T",
        "involvedResources": ["clinical/medications.ttl"],
        "severity": "catastrophic",
    })
    assert result.is_valid is False
    assert any("severity" in e for e in result.errors)


def test_interaction_scenario_without_resources_is_rejected() -> None:
    """A scenario naming no resources states that a risk exists and gives a
    consumer nothing to check it against."""
    result = validate_dict({"type": "InteractionScenario", "title": "T"})
    assert result.is_valid is False
    assert any("involvedResources" in e for e in result.errors)
