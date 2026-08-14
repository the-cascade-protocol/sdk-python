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
from typing import Literal, get_args

# ---------------------------------------------------------------------------
# Provenance Types
# ---------------------------------------------------------------------------

ProvenanceType = Literal[
    "ClinicalGenerated",
    "DeviceGenerated",
    "SelfReported",
    "AIExtracted",
    "AIAsserted",
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
# Observation Interpretation (health v2.6 / clinical v1.14)
# ---------------------------------------------------------------------------
#
# health:interpretation and clinical:interpretation are bound to the HL7 v3
# ObservationInterpretation code system,
# http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation (version
# 3.0.0), which is what FHIR R4 binds Observation.interpretation to. The two
# Cascade properties carry identical sh:in lists, so this SDK holds ONE set.
#
# The 60 accepted values are, in order:
#
#   1. The 49 SELECTABLE codes of that code system, verbatim and in the code
#      system's own order. The eight abstract concepts it marks notSelectable
#      (_GeneticObservationInterpretation, _ObservationInterpretationChange,
#      _ObservationInterpretationExceptions, _ObservationInterpretationNormality,
#      _ObservationInterpretationSusceptibility,
#      ObservationInterpretationDetection, ObservationInterpretationExpectation,
#      ReactivityObservationInterpretation) are hierarchy nodes, not values, and
#      are deliberately absent. Codes the code system marks deprecated
#      (Carrier, AC, QCF, TOX, MS, VS, HM, OBX, H>, L<) ARE accepted: a
#      deprecated code is still a defined code and historical results carry it.
#   2. "unknown", from
#      http://terminology.hl7.org/CodeSystem/data-absent-reason, written by
#      importers when the source Observation carried no interpretation at all.
#   3. The ten lower- and title-case English words this SDK accepted through
#      v1.5.0, retained so data already written keeps validating. NOT
#      recommended for new writes.
#
# What this corrects: through v1.5.0 the aliases below named "elevated", which
# no Cascade shape has ever accepted, and omitted "high", which every one of
# them has. Laboratories also report susceptibility (S/I/R), detection
# (POS/NEG/DET/ND/IND), reactivity (RR/WR/NR) and change (B/D/U/W) results,
# all conformant FHIR, and none of them had any representation here.
#
# Pinned by checksum rather than by reading the shapes. This package's CI
# checks out `conformance` as a sibling but not `spec`, so a test that
# compared against the shape file would have to skip when the checkout is
# absent, and a check that can skip is not a check. The digest is SHA-256 over
# OBSERVATION_INTERPRETATION_CODES in the order below, newline-joined, UTF-8
# encoded, with no trailing newline:
#
#   health v2.6 / clinical v1.14
#   sha256 = 2da0a308329c92456edf7f46d1529c1a2971b79294d0776025328d04773695f2
#
# tests/test_vocab_health_2_6.py recomputes it from the constant. If the
# vocabulary changes, re-derive the digest from the shape file and update both
# places; do not edit one to match the other.

ObservationInterpretation = Literal[
    # -- HL7 v3 ObservationInterpretation, 49 selectable codes, code system order
    "EX", "HM", "OBX", "CAR", "Carrier", "B", "D", "U", "W",
    "<", ">", "AC", "IE", "QCF", "TOX",
    "A", "N", "I", "MS", "NCL", "NS", "R", "S", "VS",
    "AA", "H", "L", "HH", "LL", "HX", "LX", "H>", "HU", "E", "L<", "LU",
    "ND", "IND", "NEG", "POS", "EXP", "UNE", "DET",
    "SYN-R", "NR", "RR", "WR", "SDD", "SYN-S",
    # -- data-absent-reason
    "unknown",
    # -- retained from health v2.5 / clinical v1.13; not for new writes
    "normal", "high", "low", "abnormal", "critical",
    "Normal", "High", "Low", "Abnormal", "Critical",
]

OBSERVATION_INTERPRETATION_CODES: tuple[str, ...] = get_args(ObservationInterpretation)
"""The accepted ``interpretation`` values, in canonical order.

Derived from the type alias so the two can never disagree. Order is part of
the definition: it is the code system's own order, and the checksum that pins
this list to health v2.6 is computed over it.
"""

OBSERVATION_INTERPRETATION_VALUES: frozenset[str] = frozenset(OBSERVATION_INTERPRETATION_CODES)
"""Membership view of :data:`OBSERVATION_INTERPRETATION_CODES`."""

# ---------------------------------------------------------------------------
# Lab Result Types
# ---------------------------------------------------------------------------

# health:interpretation and clinical:interpretation carry identical value sets,
# so LabInterpretation and VitalInterpretation are two names for one set rather
# than two sets that would have to be kept in step by hand. Both names are
# retained: they are public API and callers annotate with them.
LabInterpretation = ObservationInterpretation

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

VitalInterpretation = ObservationInterpretation

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
    - ``type`` maps to ``rdf:type`` (e.g., ``clinical:Medication``)
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

    source_identity: str | None = None
    """
    ORIGIN: the canonical, transport-independent identity of the organization
    this record came from (core v3.5). Two records that a FHIR export and a
    C-CDA document of the SAME health system produced carry the same value
    here, which is what makes it usable as a reconciliation key.

    A scheme-prefixed token, so a consumer can always tell how much the
    producer actually knew:

    - ``org:{slug}``: an organization was derivable (``"org:meridian"``).
    - ``ns:{namespace}``: no organization was derivable, but the identifiers
      have an assigning authority: the FHIR server base URL, or the C-CDA
      ``<id>`` root OID. Records agree on origin only if the namespaces agree.
    - ``transport:{label}``: LAST RESORT. Nothing named or located an
      organization, so the value restates the ingestion batch, honestly
      prefixed. Not an origin claim: two ``transport:`` values mean "origin
      unknown", not "same source".

    Carried, not derived and not validated. The slug normalization is defined
    in core.ttl and belongs to the producers that mint the value; this SDK
    would otherwise be arbitrating a rule it does not implement, and would
    drop data a conforming producer had already written. The value is a plain
    ``xsd:string``: the colon is part of the token, not a CURIE separator.

    Distinct from two neighbours it is easy to collapse into, and the
    collapse is the defect core v3.5 exists to end: ``cascade:sourceSystem``
    is the INGESTION batch (one batch routinely carries several
    organizations), and ``clinical:sourceEHR`` is a display LABEL (two
    spellings of one organization are two labels).

    Maps to ``cascade:sourceIdentity`` in Turtle serialization.
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
