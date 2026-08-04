"""Tests for health v2.5 — clinical record classes, daily entries, containers.

The five clinical record classes and the 35 properties they use were already
supported here; v2.5 defined what this SDK was already emitting. The gaps this
covers are the ones that were real:

  - the single-day entry classes (``health:DailyActivitySnapshot``,
    ``health:DailySleepSnapshot``, ``health:DailyVitalReading``) and the five
    daily-snapshot properties, none of which resolved to anything;
  - the four ``health:sleepQuality`` named individuals, which are emitted as
    IRIs and were being read and written as string literals;
  - the six wellness container classes, whose ordered history lists could not
    be read at all.

Every fixture below is synthetic and written from the ontology and shapes.
"""

from __future__ import annotations

import pytest

from cascade_protocol import (
    DailyActivitySnapshot,
    DailySleepSnapshot,
    DailyVitalReading,
    ActivityData,
    SleepData,
    HeartRateData,
    BloodPressureData,
    HRVData,
    BodyMeasurements,
    serialize,
    parse,
    parse_wellness_container,
    validate_dict,
    TYPE_MAPPING,
    TYPE_TO_MAPPING_KEY,
    WELLNESS_HISTORY_PROPERTIES,
)
from cascade_protocol.models.wellness import SLEEP_QUALITY_VALUES
from cascade_protocol.vocabularies.namespaces import PROPERTY_PREDICATES

# ---------------------------------------------------------------------------
# The 40 properties health v2.5 defines for these classes
# ---------------------------------------------------------------------------

# 35 were already supported before this sync; 5 were not. Listing all 40 means
# a regression on either group is caught here.
_SHARED = ["notes", "sourceRecordId", "status", "onsetDate", "conditionName"]
_LAB = [
    "testName", "resultValue", "resultUnit", "interpretation", "performedDate",
    "reportedDate", "testCode", "labCategory", "referenceRange", "specimenType",
    "orderingProvider", "performingLab",
]
_CONDITION = ["icd10Code", "conditionClass", "monitoredVitalSigns"]
_ALLERGY = ["allergen", "allergyCategory", "reaction", "allergySeverity"]
_IMMUNIZATION = [
    "vaccineName", "administrationDate", "vaccineCode", "manufacturer",
    "lotNumber", "doseQuantity", "route", "site", "administeringProvider",
    "administeringLocation",
]
_FAMILY = ["onsetAge"]
# The gap this sync closed.
_DAILY = ["steps", "activeEnergyKcal", "exerciseMinutes", "standHours", "durationHours"]

_HEALTH_25_PROPERTIES = (
    _SHARED + _LAB + _CONDITION + _ALLERGY + _IMMUNIZATION + _FAMILY + _DAILY
)


def test_health_25_defines_forty_properties() -> None:
    assert len(_HEALTH_25_PROPERTIES) == 40


def test_every_health_25_property_maps_to_a_predicate() -> None:
    """Absent the registration a field is silently dropped on serialize: the
    emitter looks the key up, finds nothing, and writes no triple at all."""
    registered = {
        shorthand.split(":", 1)[1]
        for shorthand in PROPERTY_PREDICATES.values()
        if shorthand.startswith("health:")
    }
    missing = [name for name in _HEALTH_25_PROPERTIES if name not in registered]
    assert not missing, f"health v2.5 properties not mapped: {missing}"


def test_the_five_record_classes_are_registered() -> None:
    rdf_types = {m["rdf_type"] for m in TYPE_MAPPING.values()}
    for name in [
        "LabResultRecord", "ConditionRecord", "AllergyRecord",
        "ImmunizationRecord", "FamilyHistoryRecord",
    ]:
        assert f"health:{name}" in rdf_types


def test_the_six_wellness_containers_are_registered() -> None:
    rdf_types = {m["rdf_type"] for m in TYPE_MAPPING.values()}
    for name in [
        "ActivityData", "SleepData", "HeartRateData", "BloodPressureData",
        "HRVData", "BodyMeasurements",
    ]:
        assert f"health:{name}" in rdf_types
        assert name in TYPE_TO_MAPPING_KEY
        assert name in WELLNESS_HISTORY_PROPERTIES


def test_daily_entry_classes_are_distinct_from_the_weekly_aggregates() -> None:
    """health:ActivitySnapshot is the 7-day aggregate and
    health:DailyActivitySnapshot is the single day. The vocabulary keeps them
    apart because their properties differ; collapsing them would make a
    7-day step total read as one day's."""
    aggregate = TYPE_MAPPING[TYPE_TO_MAPPING_KEY["ActivitySnapshot"]]["rdf_type"]
    daily = TYPE_MAPPING[TYPE_TO_MAPPING_KEY["DailyActivitySnapshot"]]["rdf_type"]
    assert aggregate == "health:ActivitySnapshot"
    assert daily == "health:DailyActivitySnapshot"
    assert aggregate != daily


# ---------------------------------------------------------------------------
# Daily activity snapshot
# ---------------------------------------------------------------------------

def test_daily_activity_serializes_with_the_cascade_date_spelling() -> None:
    """health:DailyActivitySnapshotShape asserts cascade:date, not the
    health:date the aggregate snapshots use. Writing the wrong one produces a
    snapshot the shape reports as missing its required timestamp."""
    turtle = serialize(DailyActivitySnapshot(
        id="urn:uuid:dact-0001-aaaa-bbbb-ccccddddeeee",
        date="2026-01-20T00:00:00Z",
        steps=8432,
        active_energy_kcal=412.5,
        exercise_minutes=37,
        stand_hours=11,
        data_provenance="DeviceGenerated",
        schema_version="1.3",
    ))
    assert "a health:DailyActivitySnapshot" in turtle
    assert 'cascade:date "2026-01-20T00:00:00Z"^^xsd:dateTime' in turtle
    assert "health:date" not in turtle
    assert "health:steps 8432" in turtle
    assert "health:exerciseMinutes 37" in turtle
    assert "health:standHours 11" in turtle


def test_whole_numbered_active_energy_keeps_its_decimal_datatype() -> None:
    """A bare Turtle numeric for a whole-numbered value is xsd:integer, and
    health:DailyActivitySnapshotShape asserts sh:datatype xsd:decimal. Without
    the explicit datatype, 412.0 kcal serializes to a shape violation while
    412.5 passes: a bug that only shows on round numbers."""
    turtle = serialize(DailyActivitySnapshot(
        id="urn:uuid:dact-0002-aaaa-bbbb-ccccddddeeee",
        date="2026-01-21T00:00:00Z",
        active_energy_kcal=412.0,
        data_provenance="DeviceGenerated",
        schema_version="1.3",
    ))
    assert 'health:activeEnergyKcal "412.0"^^xsd:decimal' in turtle


def test_daily_activity_round_trips() -> None:
    original = DailyActivitySnapshot(
        id="urn:uuid:dact-0003-aaaa-bbbb-ccccddddeeee",
        date="2026-01-22T00:00:00+00:00",
        steps=6128,
        active_energy_kcal=258.0,
        exercise_minutes=12,
        stand_hours=9,
        data_provenance="DeviceGenerated",
        schema_version="1.3",
    )
    parsed = parse(serialize(original), "DailyActivitySnapshot")
    assert len(parsed) == 1
    assert parsed[0] == original


@pytest.mark.parametrize(
    "field,value,valid",
    [
        ("exerciseMinutes", 1440, True),
        # 2220 is 37 minutes expressed in seconds. A unit error at an import
        # boundary is the realistic way this bound gets crossed, and 2220 is
        # not an absurd-looking integer on its own.
        ("exerciseMinutes", 2220, False),
        ("standHours", 24, True),
        ("standHours", 25, False),
        ("steps", 0, True),
        ("steps", -1, False),
    ],
)
def test_daily_activity_bounds_are_enforced(field: str, value: int, valid: bool) -> None:
    result = validate_dict({
        "id": "urn:uuid:dact-0004-aaaa-bbbb-ccccddddeeee",
        "type": "DailyActivitySnapshot",
        "date": "2026-01-21T00:00:00Z",
        field: value,
        "dataProvenance": "DeviceGenerated",
    })
    assert result.is_valid is valid, result.errors


# ---------------------------------------------------------------------------
# Daily sleep snapshot and the sleep-quality individuals
# ---------------------------------------------------------------------------

def test_sleep_quality_is_written_as_an_iri_not_a_literal() -> None:
    """Every known emitter writes health:sleepQuality health:Good. A string
    literal is data no Cascade deserializer reads back and fails the shape's
    sh:in over the four health: individuals."""
    turtle = serialize(DailySleepSnapshot(
        id="urn:uuid:dslp-0001-aaaa-bbbb-ccccddddeeee",
        date="2026-01-20T00:00:00Z",
        duration_hours=7.4,
        sleep_quality="Good",
        data_provenance="DeviceGenerated",
        schema_version="1.3",
    ))
    assert "health:sleepQuality health:Good" in turtle
    assert '"Good"' not in turtle
    assert 'health:durationHours "7.4"^^xsd:decimal' in turtle


def test_sleep_quality_round_trips_through_the_iri_form() -> None:
    """Parsing must strip the namespace back to the bare local name, or the
    value read out never compares equal to the value put in."""
    original = DailySleepSnapshot(
        id="urn:uuid:dslp-0002-aaaa-bbbb-ccccddddeeee",
        date="2026-01-21T00:00:00+00:00",
        duration_hours=6.8,
        sleep_quality="Fair",
        data_provenance="DeviceGenerated",
        schema_version="1.3",
    )
    parsed = parse(serialize(original), "DailySleepSnapshot")
    assert len(parsed) == 1
    assert parsed[0].sleep_quality == "Fair"
    assert parsed[0] == original


def test_the_four_sleep_quality_individuals_are_the_permitted_set() -> None:
    assert SLEEP_QUALITY_VALUES == {"Excellent", "Good", "Fair", "Poor"}


def test_out_of_vocabulary_sleep_quality_is_rejected() -> None:
    """A vendor-specific label leaking through an importer is the realistic
    source of this. Without the check it is stored and later compared against
    the four defined ratings as if it were one of them."""
    result = validate_dict({
        "id": "urn:uuid:dslp-0003-aaaa-bbbb-ccccddddeeee",
        "type": "DailySleepSnapshot",
        "date": "2026-01-21T00:00:00Z",
        "durationHours": 5.1,
        "sleepQuality": "Restless",
        "dataProvenance": "DeviceGenerated",
    })
    assert result.is_valid is False
    assert any("sleepQuality" in e for e in result.errors)


def test_sleep_duration_is_bounded_to_a_day() -> None:
    assert validate_dict({
        "id": "urn:uuid:dslp-0004-aaaa-bbbb-ccccddddeeee",
        "type": "DailySleepSnapshot", "date": "2026-01-21T00:00:00Z",
        "durationHours": 24,
    }).is_valid is True
    result = validate_dict({
        "id": "urn:uuid:dslp-0005-aaaa-bbbb-ccccddddeeee",
        "type": "DailySleepSnapshot", "date": "2026-01-21T00:00:00Z",
        "durationHours": 25,
    })
    assert result.is_valid is False


# ---------------------------------------------------------------------------
# Daily vital reading
# ---------------------------------------------------------------------------

def test_daily_vital_reading_uses_the_health_value_spelling() -> None:
    """health:value / health:unit, not the clinical: spellings a
    clinical:VitalSign uses. Same Python field, different predicate per class:
    writing the clinical: form here produces triples the DailyVitalReading
    shape does not see."""
    turtle = serialize(DailyVitalReading(
        id="urn:uuid:dvr0-0001-aaaa-bbbb-ccccddddeeee",
        date="2026-01-20T00:00:00Z",
        value=68,
        unit="bpm",
        sample_count=1440,
        loinc_code="8867-4",
        data_provenance="DeviceGenerated",
        schema_version="1.3",
    ))
    assert "a health:DailyVitalReading" in turtle
    assert "health:value 68" in turtle
    assert 'health:unit "bpm"' in turtle
    assert "clinical:value" not in turtle
    assert "cascade:sampleCount 1440" in turtle


def test_bare_loinc_codes_are_expanded_to_absolute_iris() -> None:
    """<8867-4> is a relative IRI: it resolves against the document base, so
    the same reading denotes a different resource on every host that reads
    it. Expanding against LOINC is the only stable reading."""
    turtle = serialize(DailyVitalReading(
        id="urn:uuid:dvr0-0002-aaaa-bbbb-ccccddddeeee",
        date="2026-01-20T00:00:00Z",
        loinc_code="8867-4",
        data_provenance="DeviceGenerated",
        schema_version="1.3",
    ))
    assert "cascade:loincCode <http://loinc.org/rdf#8867-4>" in turtle
    assert "<8867-4>" not in turtle


def test_an_already_absolute_code_iri_is_left_alone() -> None:
    turtle = serialize(DailyVitalReading(
        id="urn:uuid:dvr0-0003-aaaa-bbbb-ccccddddeeee",
        date="2026-01-20T00:00:00Z",
        loinc_code="http://loinc.org/rdf#40443-4",
        data_provenance="DeviceGenerated",
        schema_version="1.3",
    ))
    assert "cascade:loincCode <http://loinc.org/rdf#40443-4>" in turtle


@pytest.mark.parametrize("spelling", ["cascade:date", "health:date"])
def test_both_timestamp_spellings_are_read(spelling: str) -> None:
    """health:DailyVitalReadingShape requires a timestamp through an sh:or
    over cascade:date and health:date, because two live emitters spell it
    differently. Reading only one spelling drops every reading written by the
    other emitter out of the time series it belongs to."""
    turtle = f"""
    @prefix cascade: <https://ns.cascadeprotocol.org/core/v1#> .
    @prefix health: <https://ns.cascadeprotocol.org/health/v1#> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    <urn:uuid:dvr0-0004-aaaa-bbbb-ccccddddeeee> a health:DailyVitalReading ;
        {spelling} "2026-01-20T07:00:00Z"^^xsd:dateTime ;
        health:value 68 ;
        health:unit "bpm" ;
        cascade:sampleCount 142 ;
        cascade:dataProvenance cascade:DeviceGenerated .
    """
    readings = parse(turtle, "DailyVitalReading")
    assert len(readings) == 1
    assert readings[0].date == "2026-01-20T07:00:00+00:00"
    assert readings[0].sample_count == 142


def test_a_reading_with_neither_timestamp_spelling_is_rejected() -> None:
    """Omitting both is the only way to violate the sh:or, and it is exactly
    the failure that drops a reading out of its time series."""
    result = validate_dict({
        "id": "urn:uuid:dvr0-0005-aaaa-bbbb-ccccddddeeee",
        "type": "DailyVitalReading",
        "value": 68,
        "unit": "bpm",
        "sampleCount": 1440,
        "dataProvenance": "DeviceGenerated",
    })
    assert result.is_valid is False
    assert any("date" in e for e in result.errors)


# ---------------------------------------------------------------------------
# Wellness containers and history order
# ---------------------------------------------------------------------------

CONTAINER_TTL = """
@prefix cascade: <https://ns.cascadeprotocol.org/core/v1#> .
@prefix health: <https://ns.cascadeprotocol.org/health/v1#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<#activity> a health:ActivityData ;
    health:dailyActivityHistory (
        [ a health:DailyActivitySnapshot ; cascade:date "2026-01-22T00:00:00Z"^^xsd:dateTime ; health:steps 9234 ]
        [ a health:DailyActivitySnapshot ; cascade:date "2026-01-20T00:00:00Z"^^xsd:dateTime ; health:steps 6128 ]
        [ a health:DailyActivitySnapshot ; cascade:date "2026-01-21T00:00:00Z"^^xsd:dateTime ; health:steps 7842 ]
    ) .
"""


def test_reads_a_wellness_container_and_its_history() -> None:
    """Absent the container support this returns nothing: health:ActivityData
    resolved to no class, so a wellness file read as empty even though it held
    a full history."""
    containers = parse_wellness_container(CONTAINER_TTL, "ActivityData")
    assert len(containers) == 1
    assert isinstance(containers[0], ActivityData)
    assert len(containers[0]) == 3
    assert containers[0].id.endswith("#activity")


def test_history_preserves_document_order_not_sort_order() -> None:
    """The history properties are rdf:Lists and these are time series, so
    entry order is part of the data. The fixture is deliberately written out
    of chronological order: a reader that returned entries sorted, or in
    triple-store order, would pass a test written against a sorted fixture and
    still be wrong."""
    history = parse_wellness_container(CONTAINER_TTL, "ActivityData")[0].history
    steps = [entry.steps for entry in history]
    dates = [entry.date for entry in history]
    assert steps == [9234, 6128, 7842]
    # Neither field is in sorted order in the file, so a reader that sorted by
    # either one, or returned triple-store order, produces a different list.
    assert steps != sorted(steps)
    assert dates != sorted(dates)


def test_container_entries_parse_as_typed_records() -> None:
    history = parse_wellness_container(CONTAINER_TTL, "ActivityData")[0].history
    assert all(isinstance(e, DailyActivitySnapshot) for e in history)
    assert history[1].date == "2026-01-20T00:00:00+00:00"


@pytest.mark.parametrize(
    "container_type,cls",
    [
        ("ActivityData", ActivityData),
        ("SleepData", SleepData),
        ("HeartRateData", HeartRateData),
        ("BloodPressureData", BloodPressureData),
        ("HRVData", HRVData),
        ("BodyMeasurements", BodyMeasurements),
    ],
)
def test_every_container_type_is_readable(container_type: str, cls: type) -> None:
    turtle = f"""
    @prefix health: <https://ns.cascadeprotocol.org/health/v1#> .
    <#c> a health:{container_type} .
    """
    containers = parse_wellness_container(turtle, container_type)
    assert len(containers) == 1
    assert isinstance(containers[0], cls)


def test_unknown_container_type_raises_rather_than_returning_empty() -> None:
    """Returning an empty list for a typo would be indistinguishable from a
    pod that genuinely holds no such container."""
    with pytest.raises(ValueError, match="Unknown wellness container type"):
        parse_wellness_container(CONTAINER_TTL, "StepData")
