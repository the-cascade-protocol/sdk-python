"""
cascade-protocol — Python SDK for the Cascade Protocol.

A privacy-first, local-first standard for serializing personal health data
as RDF/Turtle. Zero network calls. All processing is local.

Quick start:
    >>> from cascade_protocol import Medication, serialize, validate, Pod
    >>>
    >>> med = Medication(
    ...     id="urn:uuid:med0-0001-aaaa-bbbb-ccccddddeeee",
    ...     medication_name="Metoprolol Succinate",
    ...     is_active=True,
    ...     dose="25mg",
    ...     data_provenance="ClinicalGenerated",
    ...     schema_version="1.3",
    ... )
    >>> turtle = serialize(med)
    >>> result = validate(turtle)
    >>> pod = Pod.open("./my-pod")
    >>> meds = pod.query("medications")
    >>> df = meds.to_dataframe()

See: https://cascadeprotocol.org/docs
"""

from cascade_protocol.models import (
    # Base
    CascadeRecord,
    # Record types
    Medication,
    Condition,
    Allergy,
    LabResult,
    VitalSign,
    Immunization,
    Procedure,
    FamilyHistory,
    Coverage,
    Encounter,
    MedicationAdministration,
    ImplantedDevice,
    ImagingStudy,
    ClaimRecord,
    BenefitStatement,
    DenialNotice,
    AppealRecord,
    PatientProfile,
    EmergencyContact,
    Address,
    PharmacyInfo,
    ActivitySnapshot,
    SleepSnapshot,
    HealthProfile,
    # Type aliases
    ProvenanceType,
    ProvenanceClass,
    ConditionStatus,
    AllergySeverity,
    AllergyCategory,
    LabInterpretation,
    MedicationClinicalIntent,
    CourseOfTherapyType,
    PrescriptionCategory,
    SourceFhirResourceType,
    VitalType,
    VitalInterpretation,
    ImmunizationStatus,
    PlanType,
    CoverageType,
    SubscriberRelationship,
    BiologicalSex,
    AgeGroup,
    BloodType,
    ProcedureStatus,
)
from cascade_protocol.serializer.turtle_serializer import (
    serialize,
    serialize_from_dict,
    serialize_medication,
    serialize_condition,
    serialize_allergy,
    serialize_lab_result,
    serialize_vital_sign,
    serialize_immunization,
    serialize_procedure,
    serialize_family_history,
    serialize_coverage,
    serialize_patient_profile,
    serialize_activity_snapshot,
    serialize_sleep_snapshot,
)
from cascade_protocol.deserializer.turtle_parser import parse, parse_one
from cascade_protocol.validator.validator import (
    validate,
    validate_dict,
    ValidationResult,
    ValidationError,
)
from cascade_protocol.pod.pod import Pod, RecordSet
from cascade_protocol.utils.deterministic_uri import (
    content_hashed_uri,
    deterministic_uuid,
    patient_uri,
    immunization_uri,
    observation_uri,
    condition_uri,
    allergy_uri,
    medication_uri,
)
from cascade_protocol.vocabularies.namespaces import (
    NAMESPACES,
    TYPE_MAPPING,
    TYPE_TO_MAPPING_KEY,
    PROPERTY_PREDICATES,
    CURRENT_SCHEMA_VERSION,
)

__version__ = "1.0.0"
__author__ = "Cascade Agentic Labs"
__license__ = "Apache-2.0"

__all__ = [
    # Version
    "__version__",
    # Models
    "CascadeRecord",
    "Medication",
    "Condition",
    "Allergy",
    "LabResult",
    "VitalSign",
    "Immunization",
    "Procedure",
    "FamilyHistory",
    "Coverage",
    "Encounter",
    "MedicationAdministration",
    "ImplantedDevice",
    "ImagingStudy",
    "ClaimRecord",
    "BenefitStatement",
    "DenialNotice",
    "AppealRecord",
    "PatientProfile",
    "EmergencyContact",
    "Address",
    "PharmacyInfo",
    "ActivitySnapshot",
    "SleepSnapshot",
    "HealthProfile",
    # Type aliases
    "ProvenanceType",
    "ProvenanceClass",
    "ConditionStatus",
    "AllergySeverity",
    "AllergyCategory",
    "LabInterpretation",
    "MedicationClinicalIntent",
    "CourseOfTherapyType",
    "PrescriptionCategory",
    "SourceFhirResourceType",
    "VitalType",
    "VitalInterpretation",
    "ImmunizationStatus",
    "PlanType",
    "CoverageType",
    "SubscriberRelationship",
    "BiologicalSex",
    "AgeGroup",
    "BloodType",
    "ProcedureStatus",
    # Serialization
    "serialize",
    "serialize_from_dict",
    "serialize_medication",
    "serialize_condition",
    "serialize_allergy",
    "serialize_lab_result",
    "serialize_vital_sign",
    "serialize_immunization",
    "serialize_procedure",
    "serialize_family_history",
    "serialize_coverage",
    "serialize_patient_profile",
    "serialize_activity_snapshot",
    "serialize_sleep_snapshot",
    # Deserialization
    "parse",
    "parse_one",
    # Validation
    "validate",
    "validate_dict",
    "ValidationResult",
    "ValidationError",
    # Pod
    "Pod",
    "RecordSet",
    # Deterministic URI utilities
    "content_hashed_uri",
    "deterministic_uuid",
    "patient_uri",
    "immunization_uri",
    "observation_uri",
    "condition_uri",
    "allergy_uri",
    "medication_uri",
    # Vocabulary
    "NAMESPACES",
    "TYPE_MAPPING",
    "TYPE_TO_MAPPING_KEY",
    "PROPERTY_PREDICATES",
    "CURRENT_SCHEMA_VERSION",
]
