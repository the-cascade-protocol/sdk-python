"""Tests for clinical v1.14 — shared interpretation set, multi-valued snomedCode.

clinical v1.14 makes two changes this SDK has to carry:

  - ``clinical:interpretation`` is bound to the same HL7 v3
    ObservationInterpretation list as ``health:interpretation``. The two lists
    are identical, so this SDK holds one set, not two.
  - ``clinical:snomedCode`` lost ``sh:maxCount 1`` in four shapes (Medication,
    Allergy, Condition, Procedure) and the new Encounter shape is multi-valued
    from the start. FHIR R4 CodeableConcept.coding is 0..*.

``VitalSign`` is the model that writes both properties under the ``clinical:``
namespace rather than ``health:``, which is why it carries most of the cases
below. Every value is synthetic.

The rest of v1.14 needs no code change here and is deliberately not tested:
the widened ``clinical:cptCode`` pattern, the date properties that now accept
``xsd:date``, and the new Encounter shape are all constraints this SDK never
enforced in the first place, so there is nothing that was rejecting them.
"""

from __future__ import annotations

import pytest

from cascade_protocol import (
    Encounter,
    MedicationAdministration,
    Procedure,
    VitalSign,
    OBSERVATION_INTERPRETATION_VALUES,
    parse_one,
    serialize,
)


def _vital(**kwargs: object) -> VitalSign:
    base: dict[str, object] = dict(
        id="urn:uuid:0f000000-0000-4000-8000-000000000001",
        vital_type="bloodPressureSystolic",
        value=118.0,
        unit="mmHg",
        data_provenance="ClinicalGenerated",
        schema_version="1.3",
    )
    base.update(kwargs)
    return VitalSign(**base)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# clinical:snomedCode is multi-valued
# ---------------------------------------------------------------------------

def test_vital_sign_snomed_emits_one_clinical_triple_per_value() -> None:
    turtle = serialize(
        _vital(snomed_code=["http://snomed.info/sct/271649006", "http://snomed.info/sct/407554009"])
    )
    assert turtle.count("clinical:snomedCode") == 2
    assert "health:snomedCode" not in turtle
    assert "<http://snomed.info/sct/271649006>" in turtle
    assert "<http://snomed.info/sct/407554009>" in turtle


def test_vital_sign_snomed_round_trip() -> None:
    original = _vital(
        snomed_code=["http://snomed.info/sct/271649006", "http://snomed.info/sct/407554009"]
    )
    parsed = parse_one(serialize(original), "VitalSign")
    assert parsed is not None
    assert isinstance(parsed, VitalSign)
    assert len(parsed.snomed_code or []) == 2
    assert set(parsed.snomed_code or []) == set(original.snomed_code or [])


def test_procedure_snomed_round_trip() -> None:
    original = Procedure(
        id="urn:uuid:04000000-0000-4000-8000-000000000001",
        procedure_name="Appendectomy",
        data_provenance="ClinicalGenerated",
        schema_version="1.3",
        snomed_code=["http://snomed.info/sct/80146002", "http://snomed.info/sct/174041007"],
    )
    turtle = serialize(original)
    assert turtle.count("health:snomedCode") == 2

    parsed = parse_one(turtle, "ProcedureRecord")
    assert parsed is not None
    assert isinstance(parsed, Procedure)
    assert set(parsed.snomed_code or []) == set(original.snomed_code or [])


def test_encounter_snomed_serializes_multi_valued() -> None:
    """Serialize only: ``Encounter`` has no deserializer registration.

    That gap predates this change and is recorded in CLAUDE.md; asserting a
    round trip here would fail for a reason that has nothing to do with
    cardinality.
    """
    turtle = serialize(
        Encounter(
            id="urn:uuid:e0000000-0000-4000-8000-000000000001",
            encounter_type="Ambulatory visit",
            data_provenance="ClinicalGenerated",
            schema_version="1.3",
            snomed_code=[
                "http://snomed.info/sct/308335008",
                "http://snomed.info/sct/185349003",
            ],
        )
    )
    assert turtle.count("health:snomedCode") == 2


def test_medication_administration_snomed_serializes_multi_valued() -> None:
    """Serialize only, for the same reason as ``Encounter``."""
    turtle = serialize(
        MedicationAdministration(
            id="urn:uuid:ad000000-0000-4000-8000-000000000001",
            medication_name="Cefazolin",
            data_provenance="ClinicalGenerated",
            schema_version="1.3",
            snomed_code=[
                "http://snomed.info/sct/372800003",
                "http://snomed.info/sct/764146007",
            ],
        )
    )
    assert turtle.count("health:snomedCode") == 2


# ---------------------------------------------------------------------------
# clinical:interpretation
# ---------------------------------------------------------------------------

def test_clinical_interpretation_round_trips_an_hl7_code() -> None:
    original = _vital(interpretation="HH")
    turtle = serialize(original)
    assert "clinical:interpretation" in turtle
    assert '"HH"' in turtle

    parsed = parse_one(turtle, "VitalSign")
    assert parsed is not None
    assert isinstance(parsed, VitalSign)
    assert parsed.interpretation == "HH"


def test_clinical_interpretation_stays_single_valued() -> None:
    """v1.14 widened the value set, not the cardinality.

    ``sh:maxCount 1`` is still asserted on both ``clinical:interpretation`` and
    ``health:interpretation``, so this field must not become a list along with
    the code properties.
    """
    parsed = parse_one(serialize(_vital(interpretation="N")), "VitalSign")
    assert parsed is not None
    assert isinstance(parsed, VitalSign)
    assert parsed.interpretation == "N"
    assert not isinstance(parsed.interpretation, list)


def test_vital_interpretation_shares_the_health_value_set() -> None:
    """One set for both namespaces; the shapes' sh:in lists are identical."""
    for code in ("N", "A", "HH", "LL", "unknown", "normal", "Critical"):
        assert code in OBSERVATION_INTERPRETATION_VALUES
