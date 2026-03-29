"""
Cascade Protocol data models.

All record types available as top-level imports from this package.
"""

from cascade_protocol.models.common import (
    CascadeRecord,
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
from cascade_protocol.models.medication import Medication
from cascade_protocol.models.condition import Condition
from cascade_protocol.models.allergy import Allergy
from cascade_protocol.models.lab_result import LabResult
from cascade_protocol.models.vital_sign import VitalSign
from cascade_protocol.models.immunization import Immunization
from cascade_protocol.models.procedure import Procedure
from cascade_protocol.models.family_history import FamilyHistory
from cascade_protocol.models.coverage import Coverage
from cascade_protocol.models.encounter import Encounter
from cascade_protocol.models.medication_administration import MedicationAdministration
from cascade_protocol.models.implanted_device import ImplantedDevice
from cascade_protocol.models.imaging_study import ImagingStudy
from cascade_protocol.models.claim_record import ClaimRecord, BenefitStatement, DenialNotice, AppealRecord
from cascade_protocol.models.patient_profile import PatientProfile, EmergencyContact, Address, PharmacyInfo
from cascade_protocol.models.wellness import ActivitySnapshot, SleepSnapshot
from cascade_protocol.models.health_profile import HealthProfile
from cascade_protocol.models.social_history_clinical import ClinicalSocialHistoryRecord
from cascade_protocol.models.ai_extraction import AIExtractionActivity, AIDiscardedExtraction, SocialHistoryConsent

__all__ = [
    # Base
    "CascadeRecord",
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
    # Record types
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
    # Clinical social history (EHR-extracted, clinical v1.8)
    "ClinicalSocialHistoryRecord",
    # AI extraction provenance (core v3.0)
    "AIExtractionActivity",
    "AIDiscardedExtraction",
    "SocialHistoryConsent",
]
