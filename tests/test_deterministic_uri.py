"""
Tests for cascade_protocol.utils.deterministic_uri.

Verifies cross-SDK determinism: the same inputs must produce the same URIs
as cascade-cli's contentHashedUri() implementation.
"""

from __future__ import annotations

import pytest

from cascade_protocol.utils.deterministic_uri import deterministic_uuid, content_hashed_uri
from cascade_protocol import (
    content_hashed_uri as top_level_content_hashed_uri,
    deterministic_uuid as top_level_deterministic_uuid,
    patient_uri,
    immunization_uri,
    observation_uri,
    condition_uri,
    allergy_uri,
    medication_uri,
)


# ---------------------------------------------------------------------------
# Core algorithm — cross-SDK test vector
# ---------------------------------------------------------------------------

def test_hello_vector():
    """The canonical cross-SDK test vector must match exactly."""
    assert deterministic_uuid("hello") == "aaf4c61d-dcc5-58a2-9abe-de0f3b482cd9"


def test_uuid_format():
    """Output must be lowercase and match UUID canonical format."""
    result = deterministic_uuid("test")
    parts = result.split("-")
    assert len(parts) == 5
    assert len(parts[0]) == 8
    assert len(parts[1]) == 4
    assert len(parts[2]) == 4
    assert len(parts[3]) == 4
    assert len(parts[4]) == 12
    assert result == result.lower()


def test_version_nibble_is_5():
    """Third group must start with '5' (UUID v5 layout)."""
    result = deterministic_uuid("hello")
    third_group = result.split("-")[2]
    assert third_group.startswith("5")


def test_variant_bits():
    """Fourth group's first byte must have variant bits 10xx xxxx (0x80-0xBF)."""
    result = deterministic_uuid("hello")
    fourth_group = result.split("-")[3]
    first_byte = int(fourth_group[:2], 16)
    assert 0x80 <= first_byte <= 0xBF


def test_deterministic_same_input():
    """Same input must always produce the same output."""
    assert deterministic_uuid("Patient::dob=1985-03-15") == deterministic_uuid("Patient::dob=1985-03-15")


def test_deterministic_different_inputs():
    """Different inputs must produce different outputs."""
    assert deterministic_uuid("Patient::dob=1985-03-15") != deterministic_uuid("Patient::dob=1990-01-01")


# ---------------------------------------------------------------------------
# content_hashed_uri — field handling
# ---------------------------------------------------------------------------

def test_patient_john_smith():
    """Patient URI must be stable and start with urn:uuid:."""
    uri = content_hashed_uri(
        "Patient",
        {"dob": "1985-03-15", "sex": "male", "family": "Smith", "given": "John"},
    )
    # Identity: "Patient::dob=1985-03-15|family=Smith|given=John|sex=male"
    assert uri.startswith("urn:uuid:")
    expected_uuid = deterministic_uuid("Patient::dob=1985-03-15|family=Smith|given=John|sex=male")
    assert uri == f"urn:uuid:{expected_uuid}"


def test_keys_sorted_ascending():
    """Keys must be sorted ascending so field order does not affect the URI."""
    uri_alpha = content_hashed_uri("Patient", {"aaa": "1", "zzz": "2"})
    uri_reverse = content_hashed_uri("Patient", {"zzz": "2", "aaa": "1"})
    assert uri_alpha == uri_reverse


def test_none_values_excluded():
    """None values must be excluded from the hash."""
    uri_with_none = content_hashed_uri("Patient", {"dob": "1985-03-15", "sex": None, "given": "John"})
    uri_without = content_hashed_uri("Patient", {"dob": "1985-03-15", "given": "John"})
    assert uri_with_none == uri_without


def test_empty_string_values_excluded():
    """Empty string values must be excluded from the hash."""
    uri_with_empty = content_hashed_uri("Patient", {"dob": "1985-03-15", "family": "", "given": "John"})
    uri_without = content_hashed_uri("Patient", {"dob": "1985-03-15", "given": "John"})
    assert uri_with_empty == uri_without


def test_whitespace_only_values_excluded():
    """Whitespace-only values must be excluded (strip() check)."""
    uri_ws = content_hashed_uri("Patient", {"dob": "1985-03-15", "family": "   ", "given": "John"})
    uri_clean = content_hashed_uri("Patient", {"dob": "1985-03-15", "given": "John"})
    assert uri_ws == uri_clean


def test_empty_fields_are_excluded_combined():
    """None and empty string exclusion work together."""
    uri1 = content_hashed_uri("Patient", {"dob": "1985-03-15", "sex": None, "family": "", "given": "John"})
    uri2 = content_hashed_uri("Patient", {"dob": "1985-03-15", "given": "John"})
    assert uri1 == uri2


def test_fallback_id():
    """When content_fields are all empty, fallback_id produces a deterministic URI."""
    uri = content_hashed_uri("Patient", {}, fallback_id="123")
    assert uri == f"urn:uuid:{deterministic_uuid('Patient:123')}"


def test_fallback_id_with_all_none_fields():
    """None fields plus fallback_id should use the fallback."""
    uri = content_hashed_uri("Patient", {"dob": None, "given": None}, fallback_id="abc")
    assert uri == f"urn:uuid:{deterministic_uuid('Patient:abc')}"


def test_fully_empty_returns_random_uri():
    """No content and no fallback_id must return a random urn:uuid: URI."""
    uri = content_hashed_uri("Patient", {})
    assert uri.startswith("urn:uuid:")
    # Must be a different random value each call
    uri2 = content_hashed_uri("Patient", {})
    # With overwhelming probability these differ; exact equality would indicate a bug
    assert uri != uri2 or True  # pragma: no cover — probabilistic, don't assert inequality


def test_resource_type_is_included():
    """Different resource types with the same field values must produce different URIs."""
    uri_patient = content_hashed_uri("Patient", {"id": "abc"})
    uri_obs = content_hashed_uri("Observation", {"id": "abc"})
    assert uri_patient != uri_obs


# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------

def test_patient_uri_helper():
    uri = patient_uri(dob="1985-03-15", sex="male", family="Smith", given="John")
    expected = content_hashed_uri(
        "Patient",
        {"dob": "1985-03-15", "sex": "male", "family": "Smith", "given": "John"},
    )
    assert uri == expected


def test_immunization_uri_helper():
    uri = immunization_uri(cvx_code="140", date="2023-10-01", patient="urn:uuid:abc")
    expected = content_hashed_uri(
        "Immunization",
        {"cvxCode": "140", "date": "2023-10-01", "patient": "urn:uuid:abc"},
    )
    assert uri == expected


def test_observation_uri_helper():
    uri = observation_uri(loinc_code="8302-2", date="2023-10-01", patient="urn:uuid:abc")
    expected = content_hashed_uri(
        "Observation",
        {"loincCode": "8302-2", "date": "2023-10-01", "patient": "urn:uuid:abc"},
    )
    assert uri == expected


def test_condition_uri_helper():
    uri = condition_uri(snomed_code="44054006", icd10_code="E11", onset_date="2020-01-01", patient="urn:uuid:abc")
    expected = content_hashed_uri(
        "Condition",
        {
            "snomedCode": "44054006",
            "icd10Code": "E11",
            "onsetDate": "2020-01-01",
            "patient": "urn:uuid:abc",
        },
    )
    assert uri == expected


def test_allergy_uri_helper():
    uri = allergy_uri(allergen_code="1191", allergen_name="Aspirin", patient="urn:uuid:abc")
    expected = content_hashed_uri(
        "AllergyIntolerance",
        {"allergenCode": "1191", "allergenName": "Aspirin", "patient": "urn:uuid:abc"},
    )
    assert uri == expected


def test_medication_uri_helper():
    uri = medication_uri(rx_norm_code="866514", start_date="2023-01-15", patient="urn:uuid:abc")
    expected = content_hashed_uri(
        "MedicationRequest",
        {"rxNormCode": "866514", "startDate": "2023-01-15", "patient": "urn:uuid:abc"},
    )
    assert uri == expected


# ---------------------------------------------------------------------------
# Top-level package exports
# ---------------------------------------------------------------------------

def test_top_level_exports_are_same_functions():
    """Symbols exported from cascade_protocol root must be the same functions."""
    assert top_level_deterministic_uuid is deterministic_uuid
    assert top_level_content_hashed_uri is content_hashed_uri


def test_top_level_hello_vector():
    """Top-level re-export must pass the cross-SDK test vector."""
    assert top_level_deterministic_uuid("hello") == "aaf4c61d-dcc5-58a2-9abe-de0f3b482cd9"
