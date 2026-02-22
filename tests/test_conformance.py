"""
Conformance test suite for the Cascade Protocol Python SDK.

Runs all conformance fixtures from the protocol's conformance test suite:
  - Positive fixtures (shouldAccept: true): serialize the input and validate structurally
  - Negative fixtures (shouldAccept: false): verify that structural validation rejects the input

The conformance fixtures are located relative to this file at:
  ../../../../conformance/fixtures/*.json

This path assumes the standard cascadeprotocol.org repo layout:
  cascadeprotocol.org/
    conformance/fixtures/
    sdk-python/tests/

Tests use structural validation only (no SHACL dependency required).
For SHACL validation, install: pip install "cascade-protocol[validation]"
"""

from __future__ import annotations

import json
import glob
from pathlib import Path
from typing import Any

import pytest
from cascade_protocol.serializer.turtle_serializer import serialize_from_dict
from cascade_protocol.validator.validator import validate_dict

# ---------------------------------------------------------------------------
# Locate conformance fixtures
# ---------------------------------------------------------------------------

# Absolute path to the conformance fixtures directory.
# sdk-python/tests/ -> sdk-python/ -> cascadeprotocol.org/ -> conformance/fixtures/
_THIS_FILE = Path(__file__).resolve()
_SDK_PYTHON_DIR = _THIS_FILE.parent.parent
_REPO_ROOT = _SDK_PYTHON_DIR.parent
_FIXTURES_DIR = _REPO_ROOT / "conformance" / "fixtures"

# Pod structure fixtures test pod-level structure, not individual records.
# These require special handling and are skipped in this test run.
_SKIP_DATA_TYPES = frozenset({"PodStructure"})

# ---------------------------------------------------------------------------
# Load fixtures
# ---------------------------------------------------------------------------

def _load_fixtures() -> list[dict[str, Any]]:
    """Load all conformance fixture JSON files."""
    if not _FIXTURES_DIR.exists():
        return []
    fixtures = []
    for path in sorted(_FIXTURES_DIR.glob("*.json")):
        with open(path, encoding="utf-8") as f:
            fixture = json.load(f)
        fixture["_path"] = str(path)
        fixtures.append(fixture)
    return fixtures

_ALL_FIXTURES = _load_fixtures()
_POSITIVE_FIXTURES = [f for f in _ALL_FIXTURES if f.get("shouldAccept") is True and f.get("dataType") not in _SKIP_DATA_TYPES]
_NEGATIVE_FIXTURES = [f for f in _ALL_FIXTURES if f.get("shouldAccept") is False and f.get("dataType") not in _SKIP_DATA_TYPES]


def _fixture_id(fixture: dict[str, Any]) -> str:
    return fixture.get("id", "unknown")


# ---------------------------------------------------------------------------
# Positive conformance tests
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not _FIXTURES_DIR.exists(),
    reason=f"Conformance fixtures not found at {_FIXTURES_DIR}",
)
@pytest.mark.parametrize("fixture", _POSITIVE_FIXTURES, ids=_fixture_id)
def test_positive_fixture_serializes(fixture: dict[str, Any]) -> None:
    """
    Positive fixture: the input should serialize without error.

    Strategy:
    1. Call serialize_from_dict() on the input (camelCase JSON dict).
    2. Verify the output is a non-empty Turtle string.
    3. Verify structural validation passes.
    """
    fixture_id = fixture["id"]
    input_data = fixture["input"]
    description = fixture.get("description", "")

    # Step 1: Serialize
    try:
        turtle = serialize_from_dict(input_data)
    except ValueError as exc:
        pytest.fail(
            f"Fixture {fixture_id} ({description}): "
            f"serialize_from_dict() raised ValueError: {exc}"
        )
    except Exception as exc:
        pytest.fail(
            f"Fixture {fixture_id} ({description}): "
            f"Unexpected error during serialization: {type(exc).__name__}: {exc}"
        )

    # Step 2: Non-empty output
    assert turtle.strip(), (
        f"Fixture {fixture_id}: serialize_from_dict() returned empty output"
    )

    # Step 3: Contains expected Turtle patterns
    assert "@prefix" in turtle, (
        f"Fixture {fixture_id}: output missing @prefix declarations"
    )
    assert "cascade:" in turtle, (
        f"Fixture {fixture_id}: output missing cascade: namespace"
    )

    # Step 4: Structural validation
    result = validate_dict(input_data)
    assert result.is_valid, (
        f"Fixture {fixture_id} ({description}): "
        f"structural validation failed: {result.errors}"
    )


@pytest.mark.skipif(
    not _FIXTURES_DIR.exists(),
    reason=f"Conformance fixtures not found at {_FIXTURES_DIR}",
)
@pytest.mark.parametrize("fixture", _POSITIVE_FIXTURES, ids=_fixture_id)
def test_positive_fixture_rdf_type(fixture: dict[str, Any]) -> None:
    """Verify the serialized output contains the correct rdf:type declaration."""
    from cascade_protocol.vocabularies.namespaces import TYPE_TO_MAPPING_KEY, TYPE_MAPPING

    input_data = fixture["input"]
    record_type = input_data.get("type", "")
    mapping_key = TYPE_TO_MAPPING_KEY.get(record_type)

    if not mapping_key:
        pytest.skip(f"No mapping for type {record_type!r}")

    rdf_type = TYPE_MAPPING[mapping_key]["rdf_type"]
    local_name = rdf_type.split(":")[1]

    turtle = serialize_from_dict(input_data)
    assert local_name in turtle, (
        f"Fixture {fixture['id']}: expected rdf:type {rdf_type!r} in output"
    )


# ---------------------------------------------------------------------------
# Negative conformance tests
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not _FIXTURES_DIR.exists(),
    reason=f"Conformance fixtures not found at {_FIXTURES_DIR}",
)
@pytest.mark.parametrize("fixture", _NEGATIVE_FIXTURES, ids=_fixture_id)
def test_negative_fixture_fails_validation(fixture: dict[str, Any]) -> None:
    """
    Negative fixture: the input should fail structural validation.

    Strategy:
    1. Call validate_dict() on the input.
    2. Verify validation returns is_valid=False.

    Note: Some negative fixtures may still serialize (producing invalid Turtle),
    but structural validation must catch the violation.
    """
    fixture_id = fixture["id"]
    input_data = fixture["input"]
    description = fixture.get("description", "")
    shacl_violated = fixture.get("shaclConstraintViolated", "")

    result = validate_dict(input_data)
    assert not result.is_valid, (
        f"Fixture {fixture_id} ({description}): "
        f"Expected validation to fail (constraint: {shacl_violated!r}) "
        f"but validate_dict() returned is_valid=True"
    )


# ---------------------------------------------------------------------------
# Coverage summary
# ---------------------------------------------------------------------------

def test_fixture_coverage_summary() -> None:
    """Print a summary of conformance fixture coverage (always passes)."""
    if not _FIXTURES_DIR.exists():
        pytest.skip("Conformance fixtures not found")

    total = len(_ALL_FIXTURES)
    positive = len(_POSITIVE_FIXTURES)
    negative = len(_NEGATIVE_FIXTURES)
    skipped = len([f for f in _ALL_FIXTURES if f.get("dataType") in _SKIP_DATA_TYPES])

    # Just assert reasonable counts — this is a smoke check
    assert total > 0, "No fixtures found"
    assert positive > 0, "No positive fixtures found"
    assert negative > 0, "No negative fixtures found"


def test_fixtures_directory_exists() -> None:
    """Verify the conformance fixtures directory is accessible."""
    assert _FIXTURES_DIR.exists(), (
        f"Conformance fixtures directory not found: {_FIXTURES_DIR}\n"
        f"This test expects the cascadeprotocol.org repo layout:\n"
        f"  {_REPO_ROOT}/conformance/fixtures/*.json"
    )
