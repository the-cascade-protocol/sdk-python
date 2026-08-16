"""Tests for health v2.6 — interpretation value set and multi-valued codes.

Two things changed in health v2.6 and both are checked here:

  - ``health:interpretation`` is bound to the HL7 v3 ObservationInterpretation
    code system (49 selectable codes, version 3.0.0), plus the
    data-absent-reason code ``"unknown"`` and the ten retained v2.5 words.
    The five-member set this SDK previously documented was not that list: it
    named ``"elevated"``, which no Cascade shape has ever accepted, and omitted
    ``"high"``, which every one of them has.
  - ``health:labCategory``, ``health:testCode``, ``health:icd10Code`` and
    ``health:snomedCode`` lost ``sh:maxCount 1``. FHIR R4 Observation.category
    is 0..* and CodeableConcept.coding is 0..*, so a record that preserved what
    the source sent was rejected for preserving it.

Every value below is synthetic. Codes are real code-system members (they have
to be, to be meaningful) but no combination describes a person.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import tempfile
from typing import get_args

import pytest

from cascade_protocol import (
    Condition,
    LabResult,
    condition_uri,
    content_hashed_uri,
    parse,
    parse_one,
    serialize,
    serialize_from_dict,
    LabInterpretation,
    VitalInterpretation,
    ObservationInterpretation,
    OBSERVATION_INTERPRETATION_CODES,
    OBSERVATION_INTERPRETATION_VALUES,
)

# ---------------------------------------------------------------------------
# The interpretation value set
# ---------------------------------------------------------------------------
#
# This SDK cannot read the shapes at test time: CI checks out `conformance` as
# a sibling but not `spec`, so a test that compared against the shape file
# would have to skip when the checkout is absent, and a skipped pin is not a
# pin. The list is therefore pinned by checksum instead. The digest below is
# SHA-256 over the accepted codes in their canonical order, newline-joined,
# UTF-8 encoded, with no trailing newline — the same rule stated in the
# comment above the constant in models/common.py.
#
# Recomputing it from the shapes (health v2.6, clinical v1.14 — the two lists
# are identical):
#
#   python - <<'EOF'
#   import re, hashlib
#   txt = open("spec/ontologies/health/v1/health.shapes.ttl").read()
#   m = re.search(r'sh:path\s+health:interpretation\s*;.*?sh:in\s*\((.*?)\)\s*;', txt, re.S)
#   codes = re.findall(r'"([^"]*)"', m.group(1))
#   print(hashlib.sha256("\n".join(codes).encode()).hexdigest())
#   EOF
#
_INTERPRETATION_SHA256 = "1ae24bf8ceccfa2a71d870bae21dc91cc7f906d736496ec23ca78b4181ba05b0"

# All 15 codes of http://terminology.hl7.org/CodeSystem/data-absent-reason,
# in the order the shape lists them. health v2.6 accepted only "unknown";
# health v2.7 / clinical v1.15 accept all 15.
_DATA_ABSENT_REASON_CODES = (
    "unknown", "asked-unknown", "temp-unknown", "not-asked",
    "asked-declined", "masked", "not-applicable", "unsupported",
    "as-text", "error", "not-a-number", "negative-infinity",
    "positive-infinity", "not-performed", "not-permitted",
)

# The ten words retained from health v2.5 so data already written keeps
# validating. Not recommended for new writes.
_RETAINED_V25_WORDS = (
    "normal", "high", "low", "abnormal", "critical",
    "Normal", "High", "Low", "Abnormal", "Critical",
)


def test_interpretation_checksum_matches_the_ratified_list() -> None:
    """The accepted set is byte-identical to the health v2.6 shape's sh:in."""
    canonical = "\n".join(OBSERVATION_INTERPRETATION_CODES)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    assert digest == _INTERPRETATION_SHA256, (
        "The interpretation value set no longer matches health v2.7. If the "
        "vocabulary changed, re-derive the digest from the shape file and "
        "update both this test and the comment in models/common.py."
    )


def test_interpretation_set_has_74_distinct_values() -> None:
    """49 selectable HL7 codes + the 15 data-absent-reason codes + 10 words."""
    assert len(OBSERVATION_INTERPRETATION_CODES) == 74
    assert len(set(OBSERVATION_INTERPRETATION_CODES)) == 74
    assert OBSERVATION_INTERPRETATION_VALUES == frozenset(OBSERVATION_INTERPRETATION_CODES)


def test_interpretation_composition_is_hl7_then_absence_then_legacy() -> None:
    """Order is load-bearing: the first 49 are the code system's own order."""
    hl7_selectable = OBSERVATION_INTERPRETATION_CODES[:49]
    assert hl7_selectable[0] == "EX"
    assert hl7_selectable[-1] == "SYN-S"
    # The eight abstract (notSelectable) concepts are hierarchy nodes, not
    # values, and must not be accepted.
    for abstract in (
        "_GeneticObservationInterpretation",
        "_ObservationInterpretationChange",
        "_ObservationInterpretationExceptions",
        "_ObservationInterpretationNormality",
        "_ObservationInterpretationSusceptibility",
        "ObservationInterpretationDetection",
        "ObservationInterpretationExpectation",
        "ReactivityObservationInterpretation",
    ):
        assert abstract not in OBSERVATION_INTERPRETATION_VALUES

    assert tuple(OBSERVATION_INTERPRETATION_CODES[49:64]) == _DATA_ABSENT_REASON_CODES
    assert tuple(OBSERVATION_INTERPRETATION_CODES[64:]) == _RETAINED_V25_WORDS


def test_susceptibility_detection_reactivity_and_change_codes_are_accepted() -> None:
    """The four families of conformant result that v2.5 rejected."""
    for code in ("S", "I", "R"):            # susceptibility
        assert code in OBSERVATION_INTERPRETATION_VALUES
    for code in ("POS", "NEG", "DET", "ND", "IND"):  # detection
        assert code in OBSERVATION_INTERPRETATION_VALUES
    for code in ("RR", "WR", "NR"):         # reactivity
        assert code in OBSERVATION_INTERPRETATION_VALUES
    for code in ("B", "D", "U", "W"):       # change
        assert code in OBSERVATION_INTERPRETATION_VALUES


def test_deprecated_hl7_codes_are_still_accepted() -> None:
    """A deprecated code is still a defined code; historical results carry it."""
    for code in ("Carrier", "AC", "QCF", "TOX", "MS", "VS", "HM", "OBX", "H>", "L<"):
        assert code in OBSERVATION_INTERPRETATION_VALUES


def test_elevated_is_not_accepted_and_high_is() -> None:
    """The correction this sync makes.

    ``"elevated"`` was named by this SDK's own type aliases through v1.5.0 and
    by the docstrings on both models, and no Cascade shape has ever accepted
    it. ``"high"`` has always been accepted and was never named.
    """
    assert "elevated" not in OBSERVATION_INTERPRETATION_VALUES
    assert "high" in OBSERVATION_INTERPRETATION_VALUES


def test_type_aliases_expose_the_same_set() -> None:
    """LabInterpretation and VitalInterpretation are the one shared set.

    health:interpretation and clinical:interpretation carry identical sh:in
    lists, so two aliases that disagreed would mean one of them was wrong.
    """
    assert get_args(ObservationInterpretation) == tuple(OBSERVATION_INTERPRETATION_CODES)
    assert get_args(LabInterpretation) == tuple(OBSERVATION_INTERPRETATION_CODES)
    assert get_args(VitalInterpretation) == tuple(OBSERVATION_INTERPRETATION_CODES)


# ---------------------------------------------------------------------------
# The validator enforces the value set
# ---------------------------------------------------------------------------

def _lab_dict(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "id": "urn:uuid:1ab00000-0000-4000-8000-000000000020",
        "type": "LabResultRecord",
        "testName": "Glucose",
        "dataProvenance": "ClinicalGenerated",
        "schemaVersion": "1.3",
    }
    data.update(overrides)
    return data


def test_validator_rejects_an_out_of_vocabulary_interpretation() -> None:
    from cascade_protocol import validate_dict

    result = validate_dict(_lab_dict(interpretation="quite high"))
    assert not result.is_valid
    assert any("interpretation" in e for e in result.errors)


@pytest.mark.parametrize("code", ["I", "unknown", "H", "POS", "normal"])
def test_validator_accepts_every_ratified_value(code: str) -> None:
    from cascade_protocol import validate_dict

    assert validate_dict(_lab_dict(interpretation=code)).is_valid


def _vital_dict(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "id": "urn:uuid:0f000000-0000-4000-8000-000000000020",
        "type": "VitalSign",
        "vitalType": "bloodPressureSystolic",
        "value": 118,
        "unit": "mmHg",
        "dataProvenance": "ClinicalGenerated",
        "schemaVersion": "1.3",
    }
    data.update(overrides)
    return data


def test_validator_checks_clinical_interpretation_too() -> None:
    """The two properties carry identical sh:in lists, so one check serves both.

    MEMBERSHIP is keyed on the property rather than the record type: a check
    that fired only on lab results would let the same garbage through on a
    vital sign.
    """
    from cascade_protocol import validate_dict

    result = validate_dict(_vital_dict(interpretation="quite high"))
    assert result.warnings, "an out-of-set vital interpretation must be reported"


def test_an_out_of_set_vital_interpretation_warns_and_stays_valid() -> None:
    """clinical v1.15 binds the vital value set at sh:Warning, not sh:Violation.

    A warning is REPORTED without withholding conformance, so the record is
    still valid. This is the ratchet: the severity is raised in a later
    clinical version, once the warning is observably absent from conforming
    output. Rejecting here would be stricter than the shape and would fail
    records the ecosystem's own validator accepts.
    """
    from cascade_protocol import validate_dict

    result = validate_dict(_vital_dict(interpretation="elevated"))
    assert result.is_valid
    assert not result.errors
    assert len(result.warnings) == 1
    assert "elevated" in result.warnings[0]


def test_an_out_of_set_lab_interpretation_is_an_error_not_a_warning() -> None:
    """The lab shapes bind the same value set at sh:Violation.

    The severity split is the whole point: the same value is a warning on a
    vital and an error on a lab, because that is what the two shapes say.
    """
    from cascade_protocol import validate_dict

    result = validate_dict(_lab_dict(interpretation="elevated"))
    assert not result.is_valid
    assert result.errors
    assert not result.warnings


def test_a_ratified_vital_interpretation_warns_about_nothing() -> None:
    """The warning must fire on the value, not on every vital sign."""
    from cascade_protocol import validate_dict

    result = validate_dict(_vital_dict(interpretation="H"))
    assert result.is_valid
    assert not result.warnings


def test_a_record_with_no_interpretation_is_unaffected() -> None:
    from cascade_protocol import validate_dict

    assert validate_dict(_lab_dict()).is_valid


# ---------------------------------------------------------------------------
# Multi-valued lab codes: serializer
# ---------------------------------------------------------------------------

def _lab(**kwargs: object) -> LabResult:
    base: dict[str, object] = dict(
        id="urn:uuid:1ab00000-0000-4000-8000-000000000001",
        test_name="Glucose",
        data_provenance="ClinicalGenerated",
        schema_version="1.3",
    )
    base.update(kwargs)
    return LabResult(**base)  # type: ignore[arg-type]


def test_lab_category_emits_one_triple_per_value() -> None:
    turtle = serialize(_lab(lab_category=["Chemistry", "Routine Chemistry"]))
    assert turtle.count("health:labCategory") == 2
    assert '"Chemistry"' in turtle
    assert '"Routine Chemistry"' in turtle
    # Repeated predicates, NOT an rdf:List: the shape asserts
    # sh:datatype xsd:string on each value, which a collection node fails.
    assert "( " not in turtle


def test_test_code_emits_one_iri_triple_per_value() -> None:
    turtle = serialize(
        _lab(test_code=["http://loinc.org/rdf#2345-7", "http://loinc.org/rdf#2339-0"])
    )
    assert turtle.count("health:testCode") == 2
    assert "<http://loinc.org/rdf#2345-7>" in turtle
    assert "<http://loinc.org/rdf#2339-0>" in turtle


def test_bare_codes_in_a_list_are_expanded_against_their_code_system() -> None:
    """Same rule the scalar path already applied, applied per element."""
    turtle = serialize(_lab(test_code=["2345-7", "2339-0"]))
    assert "<http://loinc.org/rdf#2345-7>" in turtle
    assert "<http://loinc.org/rdf#2339-0>" in turtle
    assert "@prefix loinc:" in turtle


def test_single_element_list_emits_exactly_one_triple() -> None:
    turtle = serialize(_lab(lab_category=["Chemistry"]))
    assert turtle.count("health:labCategory") == 1


def test_empty_list_emits_no_triple() -> None:
    turtle = serialize(_lab(lab_category=[], test_code=[]))
    assert "health:labCategory" not in turtle
    assert "health:testCode" not in turtle


def test_scalar_values_still_serialize() -> None:
    """Conformance fixtures carry scalars and must keep working.

    The camelCase fixture path feeds external JSON straight into the
    serializer. Widening the model must not make that input unserializable.
    """
    turtle = serialize_from_dict(
        {
            "id": "urn:uuid:1ab00000-0000-4000-8000-000000000002",
            "type": "LabResultRecord",
            "testName": "Glucose",
            "labCategory": "Chemistry",
            "testCode": "http://loinc.org/rdf#2345-7",
            "dataProvenance": "ClinicalGenerated",
            "schemaVersion": "1.3",
        }
    )
    assert turtle.count("health:labCategory") == 1
    assert '"Chemistry"' in turtle
    assert "<http://loinc.org/rdf#2345-7>" in turtle


def test_snake_case_scalars_still_serialize() -> None:
    """Callers who upgrade the package without editing their code.

    ``cascade-protocol`` is published, so code written against 1.x passes a
    bare string to these fields. The value is still emitted rather than
    silently dropped, which is what a list-only branch would do.
    """
    lab = LabResult(
        id="urn:uuid:1ab00000-0000-4000-8000-000000000005",
        test_name="Glucose",
        data_provenance="ClinicalGenerated",
        schema_version="1.3",
    )
    lab.lab_category = "Chemistry"  # type: ignore[assignment]
    lab.test_code = "http://loinc.org/rdf#2345-7"  # type: ignore[assignment]
    turtle = serialize(lab)
    assert turtle.count("health:labCategory") == 1
    assert '"Chemistry"' in turtle
    assert "<http://loinc.org/rdf#2345-7>" in turtle


def test_camel_case_lists_serialize_too() -> None:
    turtle = serialize_from_dict(
        {
            "id": "urn:uuid:1ab00000-0000-4000-8000-000000000003",
            "type": "LabResultRecord",
            "testName": "Glucose",
            "labCategory": ["Chemistry", "Point of Care"],
            "testCode": ["2345-7", "2339-0"],
            "dataProvenance": "ClinicalGenerated",
            "schemaVersion": "1.3",
        }
    )
    assert turtle.count("health:labCategory") == 2
    assert turtle.count("health:testCode") == 2


# ---------------------------------------------------------------------------
# Multi-valued codes: round trip
# ---------------------------------------------------------------------------

def test_lab_multi_value_round_trip() -> None:
    original = _lab(
        lab_category=["Chemistry", "Point of Care"],
        test_code=["http://loinc.org/rdf#2345-7", "http://loinc.org/rdf#2339-0"],
        interpretation="H",
    )
    parsed = parse_one(serialize(original), "LabResultRecord")
    assert parsed is not None
    assert isinstance(parsed, LabResult)
    assert sorted(parsed.lab_category or []) == ["Chemistry", "Point of Care"]
    assert sorted(parsed.test_code or []) == [
        "http://loinc.org/rdf#2339-0",
        "http://loinc.org/rdf#2345-7",
    ]
    assert parsed.interpretation == "H"


def test_condition_multi_value_round_trip() -> None:
    original = Condition(
        id="urn:uuid:c0000000-0000-4000-8000-000000000001",
        condition_name="Type 2 diabetes mellitus",
        status="active",
        data_provenance="ClinicalGenerated",
        schema_version="1.3",
        icd10_code=[
            "http://hl7.org/fhir/sid/icd-10-cm/E11.9",
            "http://hl7.org/fhir/sid/icd-10-cm/E11.65",
        ],
        snomed_code=[
            "http://snomed.info/sct/44054006",
            "http://snomed.info/sct/73211009",
        ],
    )
    turtle = serialize(original)
    assert turtle.count("health:icd10Code") == 2
    assert turtle.count("health:snomedCode") == 2

    parsed = parse_one(turtle, "ConditionRecord")
    assert parsed is not None
    assert isinstance(parsed, Condition)
    assert len(parsed.icd10_code or []) == 2
    assert len(parsed.snomed_code or []) == 2
    assert set(parsed.icd10_code or []) == set(original.icd10_code or [])
    assert set(parsed.snomed_code or []) == set(original.snomed_code or [])


def test_parsed_multi_values_are_sorted() -> None:
    """Parse order is deterministic.

    Repeated predicates come out of the triple store in an order that is
    neither document order nor insertion order, and it varies between
    processes. FHIR coding is a set, so nothing is lost by sorting, and a
    caller comparing two parses gets the same answer every time.
    """
    turtle = serialize(_lab(lab_category=["Zoology", "Anatomy", "Microbiology"]))
    parsed = parse_one(turtle, "LabResultRecord")
    assert parsed is not None
    assert isinstance(parsed, LabResult)
    assert parsed.lab_category == ["Anatomy", "Microbiology", "Zoology"]


def test_single_value_round_trips_as_a_one_element_list() -> None:
    parsed = parse_one(serialize(_lab(lab_category=["Chemistry"])), "LabResultRecord")
    assert parsed is not None
    assert isinstance(parsed, LabResult)
    assert parsed.lab_category == ["Chemistry"]


def test_n_triples_in_yields_n_values_out() -> None:
    """Written directly as Turtle, so the parser is tested without the writer."""
    turtle = """
@prefix cascade: <https://ns.cascadeprotocol.org/core/v1#> .
@prefix health: <https://ns.cascadeprotocol.org/health/v1#> .

<urn:uuid:1ab00000-0000-4000-8000-000000000004> a health:LabResultRecord ;
    health:testName "Basic metabolic panel" ;
    health:labCategory "Chemistry" ;
    health:labCategory "Point of Care" ;
    health:labCategory "Send Out" ;
    health:testCode <http://loinc.org/rdf#24323-8> ;
    health:testCode <http://loinc.org/rdf#51990-0> ;
    cascade:dataProvenance cascade:ClinicalGenerated ;
    cascade:schemaVersion "1.3" .
"""
    parsed = parse_one(turtle, "LabResultRecord")
    assert parsed is not None
    assert isinstance(parsed, LabResult)
    assert len(parsed.lab_category or []) == 3
    assert len(parsed.test_code or []) == 2


# ---------------------------------------------------------------------------
# Deterministic URIs over multi-valued codes
# ---------------------------------------------------------------------------

def test_condition_uri_accepts_a_list_of_codes() -> None:
    uri = condition_uri(snomed_code=["44054006", "73211009"], icd10_code=["E11.9"])
    assert uri.startswith("urn:uuid:")


def test_condition_uri_is_order_independent() -> None:
    """Codes are a set; two orderings are the same condition."""
    a = condition_uri(snomed_code=["44054006", "73211009"], icd10_code=["E11.9"])
    b = condition_uri(snomed_code=["73211009", "44054006"], icd10_code=["E11.9"])
    assert a == b


def test_condition_uri_deduplicates() -> None:
    a = condition_uri(snomed_code=["44054006", "44054006"])
    b = condition_uri(snomed_code=["44054006"])
    assert a == b


def test_single_element_list_hashes_identically_to_the_scalar() -> None:
    """Identities already written must not move.

    A record that carried one code before this release and holds it in a
    one-element list after must keep the same URI, or every stored reference
    to it breaks.
    """
    assert condition_uri(snomed_code=["44054006"]) == condition_uri(snomed_code="44054006")
    assert content_hashed_uri("Condition", {"snomedCode": ["44054006"]}) == content_hashed_uri(
        "Condition", {"snomedCode": "44054006"}
    )


def test_condition_uri_scalar_form_is_unchanged() -> None:
    """The pre-existing vector, recomputed."""
    assert condition_uri(
        snomed_code="44054006",
        icd10_code="E11",
        onset_date="2020-01-01",
        patient="urn:uuid:abc",
    ) == content_hashed_uri(
        "Condition",
        {
            "snomedCode": "44054006",
            "icd10Code": "E11",
            "onsetDate": "2020-01-01",
            "patient": "urn:uuid:abc",
        },
    )


_CROSS_PROCESS_SNIPPET = (
    "from cascade_protocol import condition_uri;"
    "print(condition_uri("
    "snomed_code=['73211009', '44054006', '44054006'],"
    "icd10_code=['E11.65', 'E11.9']))"
)


def _run_in_subprocess(cwd: str, hash_seed: str) -> str:
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = hash_seed
    proc = subprocess.run(
        [sys.executable, "-c", _CROSS_PROCESS_SNIPPET],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.strip()


def test_multi_code_uri_is_identical_across_processes_and_directories() -> None:
    """A set iteration order must never reach an identifier.

    Same call, two interpreter processes, two hash seeds, two working
    directories. PYTHONHASHSEED is pinned to different values because that is
    exactly what makes an accidental set ordering differ between runs, and a
    single-process assertion would never see it.
    """
    with tempfile.TemporaryDirectory() as dir_a, tempfile.TemporaryDirectory() as dir_b:
        first = _run_in_subprocess(dir_a, "0")
        second = _run_in_subprocess(dir_b, "524287")
    assert first == second
    assert first.startswith("urn:uuid:")
