"""coverage v1.5: a coverage record can finally say whether the plan is in force.

ONE new property, ``coverage:status``, for FHIR R4 ``Coverage.status``: a code,
1..1 at source, REQUIRED binding to fm-status — active | cancelled | draft |
entered-in-error.

Through coverage v1.4 ``coverage:InsurancePlan`` had no status property at all,
so an importer reading a conformant Coverage resource had to discard the one
element FHIR requires it to carry. ``coverage:claimStatus`` and
``coverage:adjudicationStatus`` were never substitutes: they belong to the
denial and appeal workflow and describe a CLAIM.

FHIR marks ``Coverage.status`` a MODIFIER element, which is why this is not a
nice-to-have: a cancelled plan read as an active one is a wrong answer to "am I
covered", not a missing one.

Two things about the sync itself are pinned here as well, because without them
the property would have been shipped green and unexercised:

- The bare field name ``status`` is bound to ``health:status`` (a Condition's
  clinical status), so the coverage spelling needs a type-specific override on
  the way out and an explicit reverse mapping on the way back.
- ``coverage:InsurancePlan`` resolved to no known rdf:type in this SDK, so a
  subject typed that way was SKIPPED by the reader and by the validator alike.
  A coverage fixture did not pass validation; it was never validated.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cascade_protocol import Coverage, serialize, validate, validate_dict
from cascade_protocol.deserializer.turtle_parser import parse
from cascade_protocol.serializer.turtle_serializer import serialize_from_dict
from cascade_protocol.vocabularies.namespaces import (
    NAMESPACES,
    PROPERTY_PREDICATES,
    READ_ONLY_TYPE_ALIASES,
    build_reverse_predicate_map,
    ADDITIONAL_PREDICATE_SPELLINGS,
)

_FIXTURES = Path(__file__).resolve().parent.parent.parent / "conformance" / "fixtures"

_PLAN_ID = "urn:uuid:c0000105-0000-4000-8000-000000000001"

_FM_STATUS = ("active", "cancelled", "draft", "entered-in-error")


def _plan(**overrides: object) -> Coverage:
    data: dict[str, object] = {
        "id": _PLAN_ID,
        "provider_name": "Kestrel Mutual Health",
        "plan_name": "Kestrel Select PPO",
        "data_provenance": "SelfReported",
        "schema_version": "1.4",
    }
    data.update(overrides)
    return Coverage(**data)  # type: ignore[arg-type]


def _plan_dict(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "id": _PLAN_ID,
        "type": "InsurancePlan",
        "providerName": "Kestrel Mutual Health",
        "dataProvenance": "SelfReported",
        "schemaVersion": "1.4",
    }
    data.update(overrides)
    return data


# ---------------------------------------------------------------------------
# 1. The predicate, and the collision it has to survive
# ---------------------------------------------------------------------------

def test_a_plan_writes_the_coverage_spelling_not_the_health_one() -> None:
    """"status" is health:status globally — a Condition's clinical status. On a
    coverage record the same field name carries a DIFFERENT FHIR element, so
    the predicate is overridden per record type."""
    turtle = serialize(_plan(status="active"))
    assert 'coverage:status "active"' in turtle
    assert "health:status" not in turtle


def test_the_condition_spelling_is_untouched() -> None:
    """The override must be narrow: a Condition still writes health:status."""
    assert PROPERTY_PREDICATES["status"] == "health:status"
    from cascade_protocol import Condition

    turtle = serialize(
        Condition(
            id="urn:uuid:c105cond-0000-4000-8000-000000000001",
            condition_name="Hypertension",
            status="active",
            data_provenance="EHRVerified",
            schema_version="1.4",
        )
    )
    assert 'health:status "active"' in turtle
    assert "coverage:status" not in turtle


@pytest.mark.parametrize("type_spelling", ["InsurancePlan", "CoverageRecord"])
def test_both_accepted_type_spellings_write_the_override(type_spelling: str) -> None:
    """The Coverage dataclass serves both, and a caller may set either."""
    turtle = serialize_from_dict(
        {
            "id": _PLAN_ID,
            "type": type_spelling,
            "providerName": "Kestrel Mutual Health",
            "status": "cancelled",
            "dataProvenance": "SelfReported",
            "schemaVersion": "1.4",
        }
    )
    assert 'coverage:status "cancelled"' in turtle
    assert "health:status" not in turtle


def test_the_coverage_status_is_read_back() -> None:
    """Registered on the way out and dropped on the way in is the same silent
    loss the property exists to end, just moved to the reader."""
    turtle = serialize(_plan(status="cancelled"))
    back = parse(turtle, "CoverageRecord")
    assert len(back) == 1
    assert back[0].status == "cancelled"


def test_the_reverse_map_resolves_the_coverage_spelling() -> None:
    reverse = build_reverse_predicate_map(ADDITIONAL_PREDICATE_SPELLINGS)
    assert reverse[f"{NAMESPACES['coverage']}status"] == "status"


# ---------------------------------------------------------------------------
# 2. The value set — an error, not a warning
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("code", _FM_STATUS)
def test_every_fm_status_code_is_accepted(code: str) -> None:
    assert validate_dict(_plan_dict(status=code)).is_valid


@pytest.mark.parametrize("code", ["terminated", "inactive", "expired", "ACTIVE", ""])
def test_a_code_outside_fm_status_is_rejected(code: str) -> None:
    """FHIR binds Coverage.status REQUIRED, where a payer may NOT conformantly
    send an outside code — unlike Coverage.type, bound EXTENSIBLY, whose value
    this SDK deliberately does not constrain. The severity follows the binding
    strength of the source element."""
    result = validate_dict(_plan_dict(status=code))
    if code == "":
        # An empty string is absence, not a wrong code; presence is not required.
        assert result.is_valid
        return
    assert not result.is_valid
    assert any("status" in e for e in result.errors)


def test_presence_is_deliberately_not_required() -> None:
    """No producer has yet had the chance to write it, and a minCount would
    turn every existing plan record red for something nobody could supply."""
    assert validate_dict(_plan_dict()).is_valid
    assert validate(serialize(_plan())).is_valid


def test_the_condition_status_vocabulary_is_not_applied_to_a_plan() -> None:
    """"resolved" is a Condition status and is not an fm-status code. If the
    check were keyed on the field name rather than the record type, this would
    pass."""
    assert not validate_dict(_plan_dict(status="resolved")).is_valid


# ---------------------------------------------------------------------------
# 3. The type alias, without which none of the above is exercised on real data
# ---------------------------------------------------------------------------

def test_the_insurance_plan_type_spelling_is_registered_for_reading() -> None:
    """coverage:InsurancePlan is CURRENT, not deprecated: it is the coverage
    vocabulary's own class name and is what the fixtures and the other SDKs
    write. Until it resolved, such a subject was skipped in silence."""
    assert READ_ONLY_TYPE_ALIASES["coverage:InsurancePlan"] == "clinical:CoverageRecord"


def test_a_coverage_vocabulary_document_is_actually_read() -> None:
    """Written entirely in the coverage: spellings, as another SDK would emit
    it. Before the alias this parsed to zero records."""
    turtle = f"""
@prefix cascade: <{NAMESPACES['cascade']}> .
@prefix coverage: <{NAMESPACES['coverage']}> .

<{_PLAN_ID}> a coverage:InsurancePlan ;
    coverage:providerName "Kestrel Mutual Health" ;
    coverage:planName "Kestrel Select PPO" ;
    coverage:memberId "KM-40118823" ;
    coverage:status "active" ;
    cascade:dataProvenance cascade:SelfReported ;
    cascade:schemaVersion "1.4" .
"""
    records = parse(turtle, "CoverageRecord")
    assert len(records) == 1
    plan = records[0]
    assert plan.status == "active"
    assert plan.provider_name == "Kestrel Mutual Health"
    assert plan.plan_name == "Kestrel Select PPO"
    assert plan.member_id == "KM-40118823"


def test_a_bad_status_in_a_coverage_vocabulary_document_is_caught() -> None:
    """The tripwire for the vacuous-green failure: before the alias, this
    document validated clean because the subject was never validated at all."""
    turtle = f"""
@prefix cascade: <{NAMESPACES['cascade']}> .
@prefix coverage: <{NAMESPACES['coverage']}> .

<{_PLAN_ID}> a coverage:InsurancePlan ;
    coverage:providerName "Kestrel Mutual Health" ;
    coverage:status "terminated" ;
    cascade:dataProvenance cascade:SelfReported ;
    cascade:schemaVersion "1.4" .
"""
    result = validate(turtle)
    assert not result.is_valid
    assert any("terminated" in e for e in result.errors)


# ---------------------------------------------------------------------------
# 4. Against the shared conformance fixture
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _FIXTURES.exists(), reason="conformance checkout not a sibling")
def test_the_negative_coverage_fixture_is_rejected() -> None:
    turtle = (_FIXTURES / "coverage" / "coverage-status-terminated.INVALID.ttl").read_text(
        encoding="utf-8"
    )
    result = validate(turtle)
    assert not result.is_valid
    assert any("terminated" in e for e in result.errors)


@pytest.mark.skipif(not _FIXTURES.exists(), reason="conformance checkout not a sibling")
def test_the_positive_coverage_fixture_validates_and_reads_back() -> None:
    """The fixture named VALID is finally treated as valid.

    It was not, and the reason had nothing to do with coverage v1.5: the
    fixture declares cascade:PatientReported, which seventeen sh:in lists
    across the shapes accepted but core.ttl defined nowhere. This SDK derives
    its provenance set from the ontology, so it rejected a value every shape
    permits. core v3.8 defines the individual and the disagreement is gone.

    Both halves are asserted here deliberately. Reading the status proves the
    v1.5 property works; validating proves the record is not being rejected for
    a reason unrelated to it, which is the state this fixture was stuck in.
    """
    turtle = (_FIXTURES / "coverage" / "coverage-status-active.VALID.ttl").read_text(
        encoding="utf-8"
    )
    result = validate(turtle)
    assert result.is_valid, result.errors

    plan = parse(turtle, "CoverageRecord")[0]
    assert plan.status == "active"
    assert plan.provider_name == "Kestrel Mutual Health"
    assert plan.data_provenance == "PatientReported"


def test_patient_reported_is_accepted_as_a_provenance(  ) -> None:
    """core v3.8 defines cascade:PatientReported; this SDK now admits it.

    Keyed on a plain record rather than the fixture so the check survives a
    fixture being renamed, and asserted on BOTH the runtime enum and a
    round-tripped document — a validator that accepts the value while the
    reader drops it would still lose the provenance.
    """
    from cascade_protocol.validator.validator import _VALID_PROVENANCE_TYPES

    assert "PatientReported" in _VALID_PROVENANCE_TYPES

    plan = _plan(status="active", data_provenance="PatientReported")
    turtle = serialize(plan)
    assert "cascade:dataProvenance cascade:PatientReported" in turtle

    result = validate(turtle)
    assert result.is_valid, result.errors
    assert parse(turtle, "CoverageRecord")[0].data_provenance == "PatientReported"


def test_patient_reported_is_distinct_from_self_reported() -> None:
    """Not an alias. In SelfReported the patient enters the data directly; in
    PatientReported their account is recorded by another party or system. Both
    are defined, and admitting one must not have collapsed the other."""
    from cascade_protocol.models.common import ProvenanceType
    from typing import get_args

    members = set(get_args(ProvenanceType))
    assert {"PatientReported", "SelfReported"} <= members


def test_an_undefined_provenance_is_still_rejected() -> None:
    """Widening the set by one term must not have widened it to anything."""
    assert not validate_dict(
        _plan_dict(status="active", dataProvenance="ClinicianReported")
    ).is_valid
