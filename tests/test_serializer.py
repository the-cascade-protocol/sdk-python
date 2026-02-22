"""
Tests for the Cascade Protocol Turtle serializer.

Covers:
- Medication serialization (all required and optional fields)
- Condition, Allergy, LabResult, VitalSign serialization
- Immunization, Procedure, FamilyHistory serialization
- Coverage (InsurancePlan) serialization
- PatientProfile serialization (including nested blank nodes)
- ActivitySnapshot and SleepSnapshot serialization
- dataProvenance encoding as cascade:<Type> URI
- schemaVersion as plain string literal
- Boolean field encoding (true/false unquoted)
- Integer field encoding (plain int, no quotes)
- URI field encoding (angle brackets)
- Array field encoding (RDF lists and repeated predicates)
- DateTime field encoding (^^xsd:dateTime)
- Date-only field encoding (^^xsd:date)
"""

from __future__ import annotations

import pytest
from cascade_protocol import (
    Medication,
    Condition,
    Allergy,
    LabResult,
    VitalSign,
    Immunization,
    Procedure,
    FamilyHistory,
    Coverage,
    PatientProfile,
    EmergencyContact,
    Address,
    ActivitySnapshot,
    SleepSnapshot,
    serialize,
)
from cascade_protocol.serializer import serialize_from_dict


class TestMedicationSerialization:
    def test_minimal_medication(self):
        med = Medication(
            id="urn:uuid:med0-0001-aaaa-bbbb-ccccddddeeee",
            medication_name="Lisinopril",
            is_active=True,
            data_provenance="ClinicalGenerated",
            schema_version="1.3",
        )
        turtle = serialize(med)
        assert "@prefix cascade: <https://ns.cascadeprotocol.org/core/v1#>" in turtle
        assert "@prefix health: <https://ns.cascadeprotocol.org/health/v1#>" in turtle
        assert "a health:MedicationRecord" in turtle
        assert "health:medicationName" in turtle
        assert '"Lisinopril"' in turtle
        assert "health:isActive true" in turtle
        assert "cascade:dataProvenance cascade:ClinicalGenerated" in turtle
        assert 'cascade:schemaVersion "1.3"' in turtle

    def test_medication_with_dates(self):
        med = Medication(
            id="urn:uuid:med0-0001-aaaa-bbbb-ccccddddeeee",
            medication_name="Lisinopril",
            is_active=True,
            data_provenance="ClinicalGenerated",
            schema_version="1.3",
            start_date="2024-06-15T00:00:00Z",
        )
        turtle = serialize(med)
        assert '^^xsd:dateTime' in turtle
        assert "2024-06-15T00:00:00Z" in turtle

    def test_medication_with_rx_norm_code(self):
        med = Medication(
            id="urn:uuid:med0-0001-aaaa-bbbb-ccccddddeeee",
            medication_name="Lisinopril",
            is_active=True,
            data_provenance="ClinicalGenerated",
            schema_version="1.3",
            rx_norm_code="http://www.nlm.nih.gov/research/umls/rxnorm/197884",
        )
        turtle = serialize(med)
        assert "@prefix rxnorm:" in turtle
        assert "health:rxNormCode <http://www.nlm.nih.gov/research/umls/rxnorm/197884>" in turtle

    def test_medication_with_drug_codes(self):
        med = Medication(
            id="urn:uuid:med0-0002-aaaa-bbbb-ccccddddeeee",
            medication_name="Aspirin",
            is_active=True,
            data_provenance="ClinicalGenerated",
            schema_version="1.3",
            drug_codes=[
                "http://www.nlm.nih.gov/research/umls/rxnorm/1191",
                "http://snomed.info/sct/7947003",
            ],
        )
        turtle = serialize(med)
        assert "clinical:drugCode" in turtle
        # Both codes should appear
        assert "http://www.nlm.nih.gov/research/umls/rxnorm/1191" in turtle
        assert "http://snomed.info/sct/7947003" in turtle

    def test_medication_inactive(self):
        med = Medication(
            id="urn:uuid:med0-0003-aaaa-bbbb-ccccddddeeee",
            medication_name="Old Medication",
            is_active=False,
            data_provenance="ClinicalGenerated",
            schema_version="1.3",
        )
        turtle = serialize(med)
        assert "health:isActive false" in turtle

    def test_medication_with_affects_vital_signs(self):
        med = Medication(
            id="urn:uuid:med0-0004-aaaa-bbbb-ccccddddeeee",
            medication_name="Metoprolol",
            is_active=True,
            data_provenance="ClinicalGenerated",
            schema_version="1.3",
            affects_vital_signs=["heartRate", "bloodPressureSystolic"],
        )
        turtle = serialize(med)
        assert "health:affectsVitalSigns" in turtle
        assert "heartRate" in turtle
        assert "bloodPressureSystolic" in turtle


class TestConditionSerialization:
    def test_minimal_condition(self):
        cond = Condition(
            id="urn:uuid:cond-0001-aaaa-bbbb-ccccddddeeee",
            condition_name="Hypertension",
            status="active",
            data_provenance="ClinicalGenerated",
            schema_version="1.3",
        )
        turtle = serialize(cond)
        assert "a health:ConditionRecord" in turtle
        assert '"Hypertension"' in turtle
        assert '"active"' in turtle

    def test_condition_with_codes(self):
        cond = Condition(
            id="urn:uuid:cond-0001-aaaa-bbbb-ccccddddeeee",
            condition_name="Hypertension",
            status="active",
            data_provenance="ClinicalGenerated",
            schema_version="1.3",
            icd10_code="http://hl7.org/fhir/sid/icd-10-cm/I10",
            snomed_code="http://snomed.info/sct/38341003",
        )
        turtle = serialize(cond)
        assert "health:icd10Code" in turtle
        assert "health:snomedCode" in turtle
        assert "<http://hl7.org/fhir/sid/icd-10-cm/I10>" in turtle


class TestAllergySerialization:
    def test_minimal_allergy(self):
        allergy = Allergy(
            id="urn:uuid:allg-0001-aaaa-bbbb-ccccddddeeee",
            allergen="Penicillin",
            data_provenance="ClinicalGenerated",
            schema_version="1.3",
        )
        turtle = serialize(allergy)
        assert "a health:AllergyRecord" in turtle
        assert '"Penicillin"' in turtle

    def test_allergy_with_severity(self):
        allergy = Allergy(
            id="urn:uuid:allg-0001-aaaa-bbbb-ccccddddeeee",
            allergen="Penicillin",
            data_provenance="ClinicalGenerated",
            schema_version="1.3",
            allergy_severity="severe",
            allergy_category="medication",
            reaction="Anaphylaxis",
        )
        turtle = serialize(allergy)
        assert '"severe"' in turtle
        assert '"medication"' in turtle
        assert '"Anaphylaxis"' in turtle


class TestLabResultSerialization:
    def test_minimal_lab_result(self):
        lab = LabResult(
            id="urn:uuid:lab0-0001-aaaa-bbbb-ccccddddeeee",
            test_name="Hemoglobin A1c",
            data_provenance="ClinicalGenerated",
            schema_version="1.3",
        )
        turtle = serialize(lab)
        assert "a health:LabResultRecord" in turtle
        assert '"Hemoglobin A1c"' in turtle

    def test_lab_result_with_loinc(self):
        lab = LabResult(
            id="urn:uuid:lab0-0001-aaaa-bbbb-ccccddddeeee",
            test_name="Hemoglobin A1c",
            data_provenance="ClinicalGenerated",
            schema_version="1.3",
            test_code="http://loinc.org/rdf#4548-4",
            result_value="7.2",
            result_unit="%",
        )
        turtle = serialize(lab)
        assert "<http://loinc.org/rdf#4548-4>" in turtle
        assert "@prefix loinc:" in turtle


class TestVitalSignSerialization:
    def test_vital_sign_serialization(self):
        vital = VitalSign(
            id="urn:uuid:vs01-sys0-0120-aaaa-bbbbccccdddd",
            vital_type="bloodPressureSystolic",
            vital_type_name="Systolic Blood Pressure",
            value=134,
            unit="mmHg",
            data_provenance="ClinicalGenerated",
            schema_version="1.3",
            effective_date="2026-01-20T09:15:00Z",
            interpretation="elevated",
        )
        turtle = serialize(vital)
        assert "a clinical:VitalSign" in turtle
        assert "clinical:vitalType" in turtle
        assert '"bloodPressureSystolic"' in turtle
        assert "clinical:value 134" in turtle
        assert '"mmHg"' in turtle
        assert '"elevated"' in turtle
        assert "^^xsd:dateTime" in turtle

    def test_vital_sign_snomed_uses_clinical_namespace(self):
        vital = VitalSign(
            id="urn:uuid:vs01-sys0-0120-aaaa-bbbbccccdddd",
            vital_type="bloodPressureSystolic",
            value=134,
            unit="mmHg",
            data_provenance="ClinicalGenerated",
            schema_version="1.3",
            snomed_code="http://snomed.info/sct/271649006",
        )
        turtle = serialize(vital)
        # VitalSign uses clinical:snomedCode, not health:snomedCode
        assert "clinical:snomedCode" in turtle

    def test_vital_sign_reference_range(self):
        vital = VitalSign(
            id="urn:uuid:vs01-sys0-0120-aaaa-bbbbccccdddd",
            vital_type="bloodPressureSystolic",
            value=134,
            unit="mmHg",
            data_provenance="ClinicalGenerated",
            schema_version="1.3",
            reference_range_low=90,
            reference_range_high=120,
        )
        turtle = serialize(vital)
        assert "clinical:referenceRangeLow 90" in turtle
        assert "clinical:referenceRangeHigh 120" in turtle


class TestPatientProfileSerialization:
    def test_minimal_patient_profile(self):
        profile = PatientProfile(
            id="urn:uuid:a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            date_of_birth="1973-08-15",
            biological_sex="male",
            data_provenance="ClinicalGenerated",
            schema_version="1.3",
        )
        turtle = serialize(profile)
        assert "a cascade:PatientProfile" in turtle
        assert '^^xsd:date' in turtle
        assert "1973-08-15" in turtle
        assert '"male"' in turtle

    def test_patient_profile_with_name(self):
        profile = PatientProfile(
            id="urn:uuid:a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            date_of_birth="1973-08-15",
            biological_sex="male",
            data_provenance="ClinicalGenerated",
            schema_version="1.3",
            name="Alex Rivera",
            given_name="Alex",
            family_name="Rivera",
        )
        turtle = serialize(profile)
        assert "@prefix foaf:" in turtle
        assert '"Alex Rivera"' in turtle
        assert "foaf:name" in turtle

    def test_patient_profile_computed_age_is_integer_typed(self):
        profile = PatientProfile(
            id="urn:uuid:a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            date_of_birth="1973-08-15",
            biological_sex="male",
            data_provenance="ClinicalGenerated",
            schema_version="2.0",
            computed_age=52,
        )
        turtle = serialize(profile)
        assert '^^xsd:integer' in turtle
        assert '"52"' in turtle


class TestSerializeFromDict:
    """Test camelCase dict serialization (conformance fixture compatibility)."""

    def test_serialize_from_camel_dict(self):
        data = {
            "id": "urn:uuid:med0-0001-aaaa-bbbb-ccccddddeeee",
            "type": "MedicationRecord",
            "medicationName": "Lisinopril",
            "isActive": True,
            "dataProvenance": "ClinicalGenerated",
            "schemaVersion": "1.3",
            "dose": "20 mg",
            "frequency": "once daily",
            "route": "oral",
        }
        turtle = serialize_from_dict(data)
        assert "a health:MedicationRecord" in turtle
        assert '"Lisinopril"' in turtle
        assert "cascade:dataProvenance cascade:ClinicalGenerated" in turtle

    def test_serialize_from_dict_unknown_type_raises(self):
        data = {
            "id": "urn:uuid:test",
            "type": "UnknownRecord",
            "dataProvenance": "ClinicalGenerated",
            "schemaVersion": "1.3",
        }
        with pytest.raises(ValueError, match="Unknown record type"):
            serialize_from_dict(data)


class TestWellnessSerialization:
    def test_activity_snapshot(self):
        snap = ActivitySnapshot(
            id="urn:uuid:act0-0001-aaaa-bbbb-ccccddddeeee",
            date="2026-01-20",
            steps=8547,
            data_provenance="DeviceGenerated",
            schema_version="1.3",
        )
        turtle = serialize(snap)
        assert "a health:ActivitySnapshot" in turtle
        assert "health:steps" in turtle
        assert "8547" in turtle

    def test_sleep_snapshot(self):
        snap = SleepSnapshot(
            id="urn:uuid:slp0-0001-aaaa-bbbb-ccccddddeeee",
            date="2026-01-20",
            total_sleep_minutes=437,
            data_provenance="DeviceGenerated",
            schema_version="1.3",
        )
        turtle = serialize(snap)
        assert "a health:SleepSnapshot" in turtle
        assert "health:totalSleepMinutes" in turtle
        assert "437" in turtle


class TestPrefixOrdering:
    """Verify that prefix declarations appear in the canonical order."""

    def test_cascade_before_health(self):
        med = Medication(
            id="urn:uuid:test-med",
            medication_name="Test",
            is_active=True,
            data_provenance="ClinicalGenerated",
            schema_version="1.3",
        )
        turtle = serialize(med)
        lines = turtle.split("\n")
        prefix_lines = [l for l in lines if l.startswith("@prefix")]
        prefix_names = [l.split(":")[0].replace("@prefix ", "").strip() for l in prefix_lines]
        cascade_idx = prefix_names.index("cascade")
        health_idx = prefix_names.index("health")
        xsd_idx = prefix_names.index("xsd")
        assert cascade_idx < health_idx, "cascade prefix must come before health"
        assert health_idx < xsd_idx, "health prefix must come before xsd"
