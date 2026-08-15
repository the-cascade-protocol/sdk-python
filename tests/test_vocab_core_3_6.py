"""core v3.6: ``cascade:dataAbsentReason``.

Why a record's primary VALUE is absent. Semantics are exactly FHIR R4
``Observation.dataAbsentReason``, bound to the 15 codes of
http://terminology.hl7.org/CodeSystem/data-absent-reason.

The property is what keeps four distinctions a real document draws (UNK, NAV,
NASK, ASKU) from collapsing into one indistinguishable blank on import.
"""

from __future__ import annotations

import pytest

from cascade_protocol import serialize, validate_dict
from cascade_protocol.models.lab_result import LabResult
from cascade_protocol.vocabularies.namespaces import (
    PROPERTY_PREDICATES,
    PROPERTY_PREDICATES_CAMEL,
)

# The value set, verbatim from cascade:DataAbsentReasonShape's sh:in.
_DATA_ABSENT_REASON_CODES = (
    "unknown",
    "asked-unknown",
    "temp-unknown",
    "not-asked",
    "asked-declined",
    "masked",
    "not-applicable",
    "unsupported",
    "as-text",
    "error",
    "not-a-number",
    "negative-infinity",
    "positive-infinity",
    "not-performed",
    "not-permitted",
)


def _absent_lab(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "id": "urn:uuid:dab00000-0000-4000-8000-000000000001",
        "type": "LabResultRecord",
        "testName": "Serum Potassium",
        "dataProvenance": "EHRVerified",
        "schemaVersion": "1.3",
    }
    data.update(overrides)
    return data


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def test_the_predicate_is_registered_in_both_spellings() -> None:
    assert PROPERTY_PREDICATES["data_absent_reason"] == "cascade:dataAbsentReason"
    assert PROPERTY_PREDICATES_CAMEL["dataAbsentReason"] == "cascade:dataAbsentReason"


def test_source_system_is_registered_too() -> None:
    """The INGESTION axis, published in the JSON-LD context and never registered.

    Its absence meant the ORIGIN axis (``cascade:sourceIdentity``) could round
    trip while the ingestion axis could not, so a reader of a pod carrying both
    silently kept one and dropped the other.
    """
    assert PROPERTY_PREDICATES["source_system"] == "cascade:sourceSystem"
    assert PROPERTY_PREDICATES_CAMEL["sourceSystem"] == "cascade:sourceSystem"


def test_the_field_serializes_onto_the_core_predicate() -> None:
    turtle = serialize(
        LabResult(
            id="urn:uuid:dab00000-0000-4000-8000-000000000002",
            test_name="Serum Potassium",
            data_provenance="EHRVerified",
            schema_version="1.3",
            data_absent_reason="not-asked",
        )
    )
    assert 'cascade:dataAbsentReason "not-asked"' in turtle


# ---------------------------------------------------------------------------
# Value set
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("code", _DATA_ABSENT_REASON_CODES)
def test_every_ratified_code_is_accepted(code: str) -> None:
    assert validate_dict(_absent_lab(dataAbsentReason=code)).is_valid


@pytest.mark.parametrize("null_flavor", ["UNK", "ASKU", "NASK", "NAV", "NAVU", "MSK", "NA", "OTH", "NI"])
def test_a_raw_null_flavor_code_is_rejected(null_flavor: str) -> None:
    """A NullFlavor code is real, and belongs to a different code system.

    An importer maps nullFlavor on the way in, using the table stated on the
    property. Accepting both spellings would give every absence two encodings
    and put the burden of knowing both on every reader.
    """
    result = validate_dict(_absent_lab(dataAbsentReason=null_flavor))
    assert not result.is_valid
    assert any("dataAbsentReason" in e for e in result.errors)


def test_a_value_outside_both_code_systems_is_rejected() -> None:
    assert not validate_dict(_absent_lab(dataAbsentReason="no idea")).is_valid


def test_two_absence_reasons_are_rejected() -> None:
    """A value is absent for ONE reason; a reader cannot choose between two."""
    result = validate_dict(
        _absent_lab(dataAbsentReason=["not-asked", "asked-unknown"])
    )
    assert not result.is_valid
    assert any("one reason" in e for e in result.errors)


def test_one_reason_in_a_list_is_still_accepted() -> None:
    """The cardinality rule is about MORE than one, not about the container."""
    assert validate_dict(_absent_lab(dataAbsentReason=["not-asked"])).is_valid


def test_absence_of_the_property_is_not_a_finding() -> None:
    """Open-world: the shape targets subjects of the predicate.

    Every pod written before core v3.6 validates exactly as it did.
    """
    result = validate_dict(_absent_lab())
    assert result.is_valid
    assert not result.warnings
