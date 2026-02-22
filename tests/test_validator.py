"""
Tests for the Cascade Protocol structural validator.
"""

from __future__ import annotations

import pytest
from cascade_protocol import Medication, serialize, validate, validate_dict
from cascade_protocol.validator import ValidationResult, ValidationError


class TestStructuralValidation:
    def test_valid_medication_turtle(self):
        med = Medication(
            id="urn:uuid:med0-0001-aaaa-bbbb-ccccddddeeee",
            medication_name="Lisinopril",
            is_active=True,
            data_provenance="ClinicalGenerated",
            schema_version="1.3",
        )
        turtle = serialize(med)
        result = validate(turtle)
        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert result.errors == []

    def test_valid_medication_dataclass(self):
        med = Medication(
            id="urn:uuid:med0-0001-aaaa-bbbb-ccccddddeeee",
            medication_name="Lisinopril",
            is_active=True,
            data_provenance="ClinicalGenerated",
            schema_version="1.3",
        )
        result = validate(med)
        assert result.is_valid is True

    def test_invalid_schema_version_pattern(self):
        result = validate_dict({
            "id": "urn:uuid:neg0-0001-aaaa-bbbb-ccccddddeeee",
            "type": "MedicationRecord",
            "medicationName": "Lisinopril",
            "isActive": True,
            "dataProvenance": "ClinicalGenerated",
            "schemaVersion": "1",  # Invalid: must be X.Y format
        })
        assert result.is_valid is False
        assert any("schemaVersion" in e or "schema" in e.lower() for e in result.errors)

    def test_missing_required_field_medication_name(self):
        result = validate_dict({
            "id": "urn:uuid:neg0-0001-aaaa-bbbb-ccccddddeeee",
            "type": "MedicationRecord",
            # medicationName is missing
            "isActive": True,
            "dataProvenance": "ClinicalGenerated",
            "schemaVersion": "1.3",
        })
        assert result.is_valid is False

    def test_unknown_record_type(self):
        result = validate_dict({
            "id": "urn:uuid:test",
            "type": "UnknownRecord",
            "dataProvenance": "ClinicalGenerated",
            "schemaVersion": "1.3",
        })
        assert result.is_valid is False
        assert any("Unknown record type" in e for e in result.errors)

    def test_vital_sign_missing_value(self):
        result = validate_dict({
            "id": "urn:uuid:vs01-neg0-0001-aaaa-bbbb",
            "type": "VitalSign",
            "vitalType": "heartRate",
            # value and unit are missing
            "dataProvenance": "DeviceGenerated",
            "schemaVersion": "1.3",
        })
        assert result.is_valid is False

    def test_valid_vital_sign_dict(self):
        result = validate_dict({
            "id": "urn:uuid:vs01-0001-aaaa-bbbb-ccccddddeeee",
            "type": "VitalSign",
            "vitalType": "heartRate",
            "value": 72,
            "unit": "bpm",
            "dataProvenance": "DeviceGenerated",
            "schemaVersion": "1.3",
        })
        assert result.is_valid is True

    def test_valid_patient_profile_dict(self):
        result = validate_dict({
            "id": "urn:uuid:a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "type": "PatientProfile",
            "dateOfBirth": "1973-08-15",
            "biologicalSex": "male",
            "dataProvenance": "ClinicalGenerated",
            "schemaVersion": "1.3",
        })
        assert result.is_valid is True
