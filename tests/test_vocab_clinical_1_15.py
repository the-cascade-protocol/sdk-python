"""clinical v1.15 / health v2.7: the source code, the vital ratchet, the spelling.

Three rulings land here:

1. ``interpretationSourceCode`` (both spellings): the source's own
   interpretation code, verbatim, when it is a member of neither ratified
   value set. Unconstrained in VALUE by design, single-valued in cardinality.
2. ``clinical:VitalSignShape``'s interpretation binding at ``sh:Warning``. A
   vital carrying a value outside the 74-code set is REPORTED, not rejected.
   The lab shapes bind the same set at ``sh:Violation``.
3. ``clinical:ProcedureShape``'s name requirement as an ``sh:or`` over
   ``clinical:procedureName`` (canonical) and ``health:procedureName`` (the
   deprecated import spelling, accepted for the migration window).
"""

from __future__ import annotations

from cascade_protocol import serialize, validate_dict
from cascade_protocol.models.lab_result import LabResult
from cascade_protocol.models.procedure import Procedure
from cascade_protocol.models.vital_sign import VitalSign
from cascade_protocol.serializer.turtle_serializer import serialize_from_dict
from cascade_protocol.vocabularies.namespaces import (
    PROPERTY_PREDICATES,
    PROPERTY_PREDICATES_CAMEL,
    TYPE_MAPPING,
    TYPE_TO_MAPPING_KEY,
)


def _vital(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "id": "urn:uuid:c115v000-0000-4000-8000-000000000001",
        "type": "VitalSign",
        "vitalType": "bloodPressureSystolic",
        "value": 134,
        "unit": "mmHg",
        "dataProvenance": "ClinicalGenerated",
        "schemaVersion": "1.3",
    }
    data.update(overrides)
    return data


def _procedure(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "id": "urn:uuid:c115p000-0000-4000-8000-000000000001",
        "type": "Procedure",
        "dataProvenance": "EHRVerified",
        "schemaVersion": "1.3",
    }
    data.update(overrides)
    return data


# ---------------------------------------------------------------------------
# 1. interpretationSourceCode
# ---------------------------------------------------------------------------

def test_the_source_code_is_registered_in_both_spellings() -> None:
    assert (
        PROPERTY_PREDICATES["interpretation_source_code"]
        == "health:interpretationSourceCode"
    )
    assert (
        PROPERTY_PREDICATES_CAMEL["interpretationSourceCode"]
        == "health:interpretationSourceCode"
    )


def test_a_lab_writes_the_health_spelling() -> None:
    turtle = serialize(
        LabResult(
            id="urn:uuid:c115l000-0000-4000-8000-000000000001",
            test_name="Ferritin",
            data_provenance="EHRVerified",
            schema_version="1.3",
            interpretation="A",
            interpretation_source_code="HIGH-LOCAL",
        )
    )
    assert 'health:interpretationSourceCode "HIGH-LOCAL"' in turtle


def test_a_vital_writes_the_clinical_spelling() -> None:
    """The escape hatch follows the property it explains into clinical:.

    Writing the health: spelling on a vital would put the source code on a
    different predicate from the interpretation it explains, and a consumer
    reading one would not find the other.
    """
    turtle = serialize(
        VitalSign(
            id="urn:uuid:c115v000-0000-4000-8000-000000000002",
            vital_type="bloodPressureSystolic",
            value=134,
            unit="mmHg",
            data_provenance="ClinicalGenerated",
            schema_version="1.3",
            interpretation="H",
            interpretation_source_code="elevated",
        )
    )
    assert 'clinical:interpretationSourceCode "elevated"' in turtle
    assert "health:interpretationSourceCode" not in turtle


def test_the_value_is_not_constrained() -> None:
    """A value set or a pattern would recreate the loss the property prevents."""
    for code in ("ZQ7", "elevated", "HIGH-LOCAL", "??", "unknown"):
        assert validate_dict(_vital(interpretation="H", interpretationSourceCode=code)).is_valid


def test_two_source_codes_on_one_record_are_rejected() -> None:
    """interpretation is 0..1, so the code that explains it is 0..1 too."""
    result = validate_dict(
        _vital(interpretation="A", interpretationSourceCode=["ZQ7", "HIGH-LOCAL"])
    )
    assert not result.is_valid
    assert any("interpretationSourceCode" in e for e in result.errors)


# ---------------------------------------------------------------------------
# 2. The vital ratchet: sh:Warning, not sh:Violation
# ---------------------------------------------------------------------------

def test_an_out_of_set_vital_interpretation_is_reported_not_rejected() -> None:
    result = validate_dict(_vital(interpretation="elevated"))
    assert result.is_valid, "clinical v1.15 binds the vital value set at sh:Warning"
    assert not result.errors
    assert len(result.warnings) == 1


def test_the_same_value_on_a_lab_is_an_error() -> None:
    """The severity split is the ruling, and it is keyed on the record type."""
    result = validate_dict(
        {
            "id": "urn:uuid:c115l000-0000-4000-8000-000000000002",
            "type": "LabResultRecord",
            "testName": "Ferritin",
            "interpretation": "elevated",
            "dataProvenance": "EHRVerified",
            "schemaVersion": "1.3",
        }
    )
    assert not result.is_valid
    assert result.errors
    assert not result.warnings


def test_the_migration_pair_validates_clean() -> None:
    """What a producer is supposed to write instead of the bare legacy word."""
    result = validate_dict(
        _vital(interpretation="H", interpretationSourceCode="elevated")
    )
    assert result.is_valid
    assert not result.warnings


def test_the_fourteen_new_absence_codes_are_legal_interpretations() -> None:
    """health v2.6 admitted only "unknown", so three facts became one."""
    for code in ("not-asked", "asked-unknown", "temp-unknown", "masked"):
        result = validate_dict(_vital(interpretation=code))
        assert result.is_valid
        assert not result.warnings


# ---------------------------------------------------------------------------
# 3. The procedure-name migration window
# ---------------------------------------------------------------------------

def test_the_procedure_class_is_the_shaped_one() -> None:
    """health: defines neither a procedure class nor health:procedureName."""
    assert TYPE_MAPPING[TYPE_TO_MAPPING_KEY["Procedure"]]["rdf_type"] == "clinical:Procedure"
    assert TYPE_MAPPING["procedures"]["name_pred"] == "clinical:procedureName"


def test_both_record_type_spellings_resolve() -> None:
    assert TYPE_TO_MAPPING_KEY["Procedure"] == TYPE_TO_MAPPING_KEY["ProcedureRecord"]


def test_the_canonical_spelling_is_written_and_validates() -> None:
    result = validate_dict(_procedure(procedureName="Screening Colonoscopy"))
    assert result.is_valid
    assert not result.warnings
    turtle = serialize_from_dict(_procedure(procedureName="Screening Colonoscopy"))
    assert "a clinical:Procedure" in turtle
    assert 'clinical:procedureName "Screening Colonoscopy"' in turtle


def test_the_deprecated_spelling_validates_and_warns() -> None:
    """Exactly what a C-CDA import path emits today.

    Under clinical v1.14 this FAILED the name requirement while carrying a
    name, on a predicate no shape targeted. v1.15 accepts it through an sh:or
    and warns, so the record validates without being rewritten.
    """
    result = validate_dict(_procedure(healthProcedureName="Screening Colonoscopy"))
    assert result.is_valid
    assert len(result.warnings) == 1
    assert "health:procedureName" in result.warnings[0]
    turtle = serialize_from_dict(_procedure(healthProcedureName="Screening Colonoscopy"))
    assert "a clinical:Procedure" in turtle
    assert 'health:procedureName "Screening Colonoscopy"' in turtle


def test_a_procedure_with_no_name_in_either_spelling_is_rejected() -> None:
    """The regression guard on the sh:or.

    A mis-authored sh:or makes the name OPTIONAL rather than either-spelling,
    and this is the fixture that catches it.
    """
    result = validate_dict(_procedure())
    assert not result.is_valid
    assert any("procedure name" in e.lower() for e in result.errors)


def test_the_typed_model_still_round_trips_under_the_retarget() -> None:
    from cascade_protocol import parse

    record = Procedure(
        id="urn:uuid:c115p000-0000-4000-8000-000000000002",
        procedure_name="Appendectomy",
        data_provenance="ClinicalGenerated",
        schema_version="1.3",
    )
    turtle = serialize(record)
    assert "a clinical:Procedure" in turtle
    parsed = parse(turtle, "ProcedureRecord")
    assert len(parsed) == 1
    assert parsed[0].procedure_name == "Appendectomy"
