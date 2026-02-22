"""
Common types shared across all Cascade Protocol data models.

These types map directly to the Cascade Protocol vocabularies:
- cascade: https://ns.cascadeprotocol.org/core/v1#
- health:  https://ns.cascadeprotocol.org/health/v1#
- clinical: https://ns.cascadeprotocol.org/clinical/v1#

See: https://cascadeprotocol.org/docs/cascade-protocol-schemas
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field, fields
from typing import Literal

# ---------------------------------------------------------------------------
# Provenance Types
# ---------------------------------------------------------------------------

ProvenanceType = Literal[
    "ClinicalGenerated",
    "DeviceGenerated",
    "SelfReported",
    "AIExtracted",
    "AIGenerated",
    "EHRVerified",
]

ProvenanceClass = Literal[
    "healthKitFHIR",
    "userTracked",
    "manualEntry",
    "deviceSync",
]

# ---------------------------------------------------------------------------
# Condition Types
# ---------------------------------------------------------------------------

ConditionStatus = Literal["active", "resolved", "remission", "inactive"]

# ---------------------------------------------------------------------------
# Allergy Types
# ---------------------------------------------------------------------------

AllergySeverity = Literal["mild", "moderate", "severe", "life-threatening"]

AllergyCategory = Literal["medication", "food", "environmental", "biologic"]

# ---------------------------------------------------------------------------
# Lab Result Types
# ---------------------------------------------------------------------------

LabInterpretation = Literal["normal", "abnormal", "critical", "elevated", "low"]

# ---------------------------------------------------------------------------
# Medication Types
# ---------------------------------------------------------------------------

MedicationClinicalIntent = Literal[
    "prescribed", "otc", "supplement", "prn", "reportedUse"
]

CourseOfTherapyType = Literal["continuous", "acute", "seasonal"]

PrescriptionCategory = Literal["community", "inpatient", "discharge"]

SourceFhirResourceType = Literal[
    "MedicationRequest", "MedicationStatement", "MedicationDispense"
]

# ---------------------------------------------------------------------------
# Vital Sign Types
# ---------------------------------------------------------------------------

VitalType = Literal[
    "heartRate",
    "bloodPressureSystolic",
    "bloodPressureDiastolic",
    "respiratoryRate",
    "temperature",
    "oxygenSaturation",
    "weight",
    "height",
    "bmi",
]

VitalInterpretation = Literal["normal", "elevated", "low", "critical"]

# ---------------------------------------------------------------------------
# Immunization Types
# ---------------------------------------------------------------------------

ImmunizationStatus = Literal["completed", "entered-in-error", "not-done"]

# ---------------------------------------------------------------------------
# Coverage Types
# ---------------------------------------------------------------------------

PlanType = Literal["ppo", "hmo", "pos", "epo", "hdhp", "medicare", "medicaid"]

CoverageType = Literal["primary", "secondary", "supplemental"]

SubscriberRelationship = Literal["self", "spouse", "child", "other"]

# ---------------------------------------------------------------------------
# Patient Profile Types
# ---------------------------------------------------------------------------

BiologicalSex = Literal["male", "female", "intersex"]

AgeGroup = Literal[
    "infant", "child", "adolescent", "young_adult", "adult", "senior"
]

BloodType = Literal[
    "aPositive", "aNegative",
    "bPositive", "bNegative",
    "abPositive", "abNegative",
    "oPositive", "oNegative",
]

# ---------------------------------------------------------------------------
# Procedure Types
# ---------------------------------------------------------------------------

ProcedureStatus = Literal[
    "completed", "in-progress", "not-done", "preparation", "stopped"
]

# ---------------------------------------------------------------------------
# Base Record Dataclass
# ---------------------------------------------------------------------------
#
# Design note: Python dataclass inheritance requires that fields with defaults
# come AFTER fields without defaults. Since subclasses add domain-specific
# fields (all with defaults of "" or None), and the base class has required
# fields (id, type, data_provenance, schema_version), we declare all fields
# with defaults to allow flexible keyword-argument construction.
#
# Callers must always provide id, type, data_provenance, schema_version.
# The empty string defaults are validation targets (validator rejects empty
# required fields).


@dataclass
class CascadeRecord:
    """
    Base class for all Cascade Protocol health records.

    Every record must include an ``id``, ``type``, ``data_provenance``,
    and ``schema_version``. Additional optional metadata fields are
    available for traceability.

    - ``id`` maps to the RDF subject URI (e.g., ``urn:uuid:...``)
    - ``type`` maps to ``rdf:type`` (e.g., ``health:MedicationRecord``)
    - ``data_provenance`` maps to ``cascade:dataProvenance``
    - ``schema_version`` maps to ``cascade:schemaVersion``

    All fields are keyword-only to prevent positional argument confusion
    and to allow subclasses to extend without ordering constraints.
    """

    id: str = ""
    """Unique identifier for this record (URN UUID format: ``urn:uuid:...``)."""

    type: str = ""
    """RDF type of this record (e.g., ``MedicationRecord``, ``ConditionRecord``)."""

    data_provenance: str = ""
    """
    Data provenance classification indicating the source of this record.
    Maps to ``cascade:dataProvenance`` in Turtle serialization.
    """

    schema_version: str = ""
    """
    Schema version in major.minor format (e.g., ``"1.3"``).
    Maps to ``cascade:schemaVersion`` in Turtle serialization.
    """

    source_record_id: str | None = None
    """
    Identifier linking back to the source record in the originating system.
    Maps to ``health:sourceRecordId`` in Turtle serialization.
    """

    notes: str | None = None
    """
    Free-text notes associated with this record.
    Maps to ``health:notes`` in Turtle serialization.
    """

    def to_dict(self) -> dict:
        """Convert this record to a dict, excluding None values."""
        result = {}
        for f in fields(self):
            val = getattr(self, f.name)
            if val is not None:
                result[f.name] = val
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "CascadeRecord":
        """Construct a record from a dict (snake_case keys)."""
        valid = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in valid})
