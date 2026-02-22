"""
Tests for the Cascade Protocol Turtle deserializer.

Covers round-trip serialization: model -> Turtle -> model.
"""

from __future__ import annotations

import pytest
from cascade_protocol import (
    Medication,
    Condition,
    Allergy,
    LabResult,
    VitalSign,
    serialize,
    parse,
    parse_one,
)


class TestMedicationRoundTrip:
    def test_basic_round_trip(self):
        original = Medication(
            id="urn:uuid:med0-0001-aaaa-bbbb-ccccddddeeee",
            medication_name="Lisinopril",
            is_active=True,
            data_provenance="ClinicalGenerated",
            schema_version="1.3",
            dose="20 mg",
            frequency="once daily",
            route="oral",
        )
        turtle = serialize(original)
        parsed = parse(turtle, "MedicationRecord")

        assert len(parsed) == 1
        med = parsed[0]
        assert med.id == original.id
        assert isinstance(med, Medication)
        assert med.medication_name == "Lisinopril"
        assert med.is_active is True
        assert med.data_provenance == "ClinicalGenerated"
        assert med.schema_version == "1.3"
        assert med.dose == "20 mg"

    def test_parse_one(self):
        original = Medication(
            id="urn:uuid:med0-0001-aaaa-bbbb-ccccddddeeee",
            medication_name="Aspirin",
            is_active=True,
            data_provenance="SelfReported",
            schema_version="1.3",
        )
        turtle = serialize(original)
        med = parse_one(turtle, "MedicationRecord")
        assert med is not None
        assert isinstance(med, Medication)
        assert med.medication_name == "Aspirin"

    def test_empty_parse_returns_empty_list(self):
        turtle = """
@prefix cascade: <https://ns.cascadeprotocol.org/core/v1#> .
@prefix health: <https://ns.cascadeprotocol.org/health/v1#> .
"""
        result = parse(turtle, "MedicationRecord")
        assert result == []

    def test_parse_one_empty_returns_none(self):
        turtle = """
@prefix cascade: <https://ns.cascadeprotocol.org/core/v1#> .
"""
        result = parse_one(turtle, "MedicationRecord")
        assert result is None


class TestConditionRoundTrip:
    def test_condition_round_trip(self):
        original = Condition(
            id="urn:uuid:cond-0001-aaaa-bbbb-ccccddddeeee",
            condition_name="Hypertension",
            status="active",
            data_provenance="ClinicalGenerated",
            schema_version="1.3",
        )
        turtle = serialize(original)
        parsed = parse(turtle, "ConditionRecord")
        assert len(parsed) == 1
        cond = parsed[0]
        assert isinstance(cond, Condition)
        assert cond.condition_name == "Hypertension"
        assert cond.status == "active"


class TestVitalSignRoundTrip:
    def test_vital_sign_round_trip(self):
        original = VitalSign(
            id="urn:uuid:vs01-sys0-0120-aaaa-bbbbccccdddd",
            vital_type="bloodPressureSystolic",
            value=134,
            unit="mmHg",
            data_provenance="ClinicalGenerated",
            schema_version="1.3",
            reference_range_low=90,
            reference_range_high=120,
        )
        turtle = serialize(original)
        parsed = parse(turtle, "VitalSign")
        assert len(parsed) == 1
        vital = parsed[0]
        assert isinstance(vital, VitalSign)
        assert vital.vital_type == "bloodPressureSystolic"
        assert vital.value == 134.0
        assert vital.unit == "mmHg"


class TestUnknownTypeRaises:
    def test_parse_unknown_type_raises(self):
        turtle = "@prefix cascade: <https://ns.cascadeprotocol.org/core/v1#> .\n"
        with pytest.raises(ValueError, match="Unknown record type"):
            parse(turtle, "NonExistentRecord")
