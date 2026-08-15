"""
Structural validator for Cascade Protocol records.

Implements two validation modes:

1. **Structural validation** (always available, no extra dependencies):
   Checks that required fields are present and schema version is valid.
   This is sufficient for most use cases.

2. **SHACL validation** (optional, requires ``pyshacl``):
   Full RDF shape validation against the Cascade Protocol SHACL shapes files.
   Enable with: ``pip install "cascade-protocol[validation]"``

Example:
    >>> from cascade_protocol import validate
    >>> result = validate(turtle_string)
    >>> if result.is_valid:
    ...     print("Valid!")
    ... else:
    ...     print(result.errors)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from cascade_protocol.models.common import OBSERVATION_INTERPRETATION_VALUES

# ---------------------------------------------------------------------------
# Required fields per record type
# ---------------------------------------------------------------------------

_REQUIRED_FIELDS_CAMEL: dict[str, list[str]] = {
    "MedicationRecord": ["id", "type", "medicationName", "isActive", "dataProvenance", "schemaVersion"],
    "ConditionRecord": ["id", "type", "conditionName", "status", "dataProvenance", "schemaVersion"],
    "AllergyRecord": ["id", "type", "allergen", "dataProvenance", "schemaVersion"],
    "LabResultRecord": ["id", "type", "testName", "dataProvenance", "schemaVersion"],
    "VitalSign": ["id", "type", "vitalType", "value", "unit", "dataProvenance", "schemaVersion"],
    "ImmunizationRecord": ["id", "type", "vaccineName", "dataProvenance", "schemaVersion"],
    "ProcedureRecord": ["id", "type", "procedureName", "dataProvenance", "schemaVersion"],
    # clinical v1.15: clinical:ProcedureShape requires a name through a
    # node-level sh:or over clinical:procedureName and health:procedureName,
    # not a plain minCount, so the name is enforced separately below rather
    # than listed here. Listing either spelling would reject a record that
    # carries the other one, which is the defect v1.15 corrects.
    "Procedure": ["id", "type", "dataProvenance", "schemaVersion"],
    "FamilyHistoryRecord": ["id", "type", "relationship", "conditionName", "dataProvenance", "schemaVersion"],
    "CoverageRecord": ["id", "type", "providerName", "dataProvenance", "schemaVersion"],
    "InsurancePlan": ["id", "type", "providerName", "dataProvenance", "schemaVersion"],
    "PatientProfile": ["id", "type", "dateOfBirth", "biologicalSex", "dataProvenance", "schemaVersion"],
    "ActivitySnapshot": ["id", "type", "date", "dataProvenance", "schemaVersion"],
    "SleepSnapshot": ["id", "type", "date", "dataProvenance", "schemaVersion"],
    "Encounter": ["id", "type", "encounterType", "dataProvenance", "schemaVersion"],
    "MedicationAdministration": ["id", "type", "medicationName", "dataProvenance", "schemaVersion"],
    "ImplantedDevice": ["id", "type", "deviceType", "dataProvenance", "schemaVersion"],
    "ImagingStudy": ["id", "type", "studyDescription", "dataProvenance", "schemaVersion"],
    "ClaimRecord": ["id", "type", "claimType", "dataProvenance", "schemaVersion"],
    "BenefitStatement": ["id", "type", "adjudicationStatus", "dataProvenance", "schemaVersion"],
    "DenialNotice": ["id", "type", "deniedProcedureCode", "dataProvenance", "schemaVersion"],
    "AppealRecord": ["id", "type", "appealLevel", "dataProvenance", "schemaVersion"],
    # -- health v2.4 --
    "SocialHistoryRecord": ["id", "type", "dataProvenance", "schemaVersion"],
    # -- core v3.1-3.3 (prov:Activity / prov:Agent classes — NOT cascade:HealthRecord
    #    subclasses, so no dataProvenance/schemaVersion; required fields follow each
    #    SHACL shape) --
    "AdvisoryApplicationActivity": ["id", "type"],
    "AIGenerationActivity": ["id", "type", "extractionModel", "trigger"],
    "ProxyAgent": ["id", "type", "actsForPatient", "proxyRelationship", "proxyGrantedAt"],
    # -- health v2.5 -- single-day history entries.
    #    DailyVitalReading's timestamp requirement is an sh:or over two
    #    spellings, not a plain minCount, so it is enforced separately below
    #    rather than listed here.
    "DailyActivitySnapshot": ["id", "type", "date"],
    "DailySleepSnapshot": ["id", "type", "date"],
    "DailyVitalReading": ["id", "type"],
    # -- core v3.4 -- pod export manifest.
    #    ExportManifestShape requires title, created and schemaVersion:
    #    without a schema version a consumer cannot decide whether it can read
    #    the export at all.
    #    'id' is deliberately NOT required for these three: a manifest's
    #    subject is the empty relative IRI <> ("this document"), and record
    #    summaries, scenarios and device sources are blank nodes. Requiring a
    #    non-empty id would reject every conforming manifest ever written.
    "ExportManifest": ["type", "title", "created", "schemaVersion"],
    "RecordSummary": ["type", "domain"],
    "InteractionScenario": ["type", "title", "involvedResources"],
}

_REQUIRED_FIELDS_SNAKE: dict[str, list[str]] = {
    "MedicationRecord": ["id", "type", "medication_name", "is_active", "data_provenance", "schema_version"],
    "ConditionRecord": ["id", "type", "condition_name", "status", "data_provenance", "schema_version"],
    "AllergyRecord": ["id", "type", "allergen", "data_provenance", "schema_version"],
    "LabResultRecord": ["id", "type", "test_name", "data_provenance", "schema_version"],
    "VitalSign": ["id", "type", "vital_type", "value", "unit", "data_provenance", "schema_version"],
    "ImmunizationRecord": ["id", "type", "vaccine_name", "data_provenance", "schema_version"],
    "ProcedureRecord": ["id", "type", "procedure_name", "data_provenance", "schema_version"],
    # See the camelCase table for why the name is not listed here.
    "Procedure": ["id", "type", "data_provenance", "schema_version"],
    "FamilyHistoryRecord": ["id", "type", "relationship", "condition_name", "data_provenance", "schema_version"],
    "CoverageRecord": ["id", "type", "provider_name", "data_provenance", "schema_version"],
    "InsurancePlan": ["id", "type", "provider_name", "data_provenance", "schema_version"],
    "PatientProfile": ["id", "type", "date_of_birth", "biological_sex", "data_provenance", "schema_version"],
    "ActivitySnapshot": ["id", "type", "date", "data_provenance", "schema_version"],
    "SleepSnapshot": ["id", "type", "date", "data_provenance", "schema_version"],
    "Encounter": ["id", "type", "encounter_type", "data_provenance", "schema_version"],
    "MedicationAdministration": ["id", "type", "medication_name", "data_provenance", "schema_version"],
    "ImplantedDevice": ["id", "type", "device_type", "data_provenance", "schema_version"],
    "ImagingStudy": ["id", "type", "study_description", "data_provenance", "schema_version"],
    "ClaimRecord": ["id", "type", "claim_type", "data_provenance", "schema_version"],
    "BenefitStatement": ["id", "type", "adjudication_status", "data_provenance", "schema_version"],
    "DenialNotice": ["id", "type", "denied_procedure_code", "data_provenance", "schema_version"],
    "AppealRecord": ["id", "type", "appeal_level", "data_provenance", "schema_version"],
    # -- health v2.4 --
    "SocialHistoryRecord": ["id", "type", "data_provenance", "schema_version"],
    # -- core v3.1-3.3 (prov:Activity / prov:Agent classes — NOT cascade:HealthRecord
    #    subclasses, so no dataProvenance/schemaVersion; required fields follow each
    #    SHACL shape) --
    "AdvisoryApplicationActivity": ["id", "type"],
    "AIGenerationActivity": ["id", "type", "extraction_model", "trigger"],
    "ProxyAgent": ["id", "type", "acts_for_patient", "proxy_relationship", "proxy_granted_at"],
    # -- health v2.5 --
    "DailyActivitySnapshot": ["id", "type", "date"],
    "DailySleepSnapshot": ["id", "type", "date"],
    "DailyVitalReading": ["id", "type"],
    # -- core v3.4 -- see the camelCase table for why 'id' is absent here.
    "ExportManifest": ["type", "title", "created", "schema_version"],
    "RecordSummary": ["type", "domain"],
    "InteractionScenario": ["type", "title", "involved_resources"],
}

_VALID_PROVENANCE_TYPES = frozenset({
    "ClinicalGenerated",
    "DeviceGenerated",
    "SelfReported",
    "AIExtracted",
    "AIAsserted",
    "AIGenerated",
    "EHRVerified",
})

# Enumerated vital types allowed by the Cascade Protocol VitalSignShape.
_VALID_VITAL_TYPES = frozenset({
    "heartRate",
    "bloodPressureSystolic",
    "bloodPressureDiastolic",
    "respiratoryRate",
    "temperature",
    "oxygenSaturation",
    "weight",
    "height",
    "bmi",
})

_SCHEMA_VERSION_PATTERN = r"^\d+\.\d+$"

# Categories permitted on clinical:SocialHistoryRecord by
# clinical:SocialHistoryRecordShape (clinical v1.8). Enforced here because the
# structural validator is the only check most consumers run: without it a
# record categorised "tobacco" instead of "smokingStatus" validated clean and
# then failed to match any query keyed on the defined set.
_VALID_SOCIAL_HISTORY_CATEGORIES = frozenset({
    "smokingStatus",
    "alcoholUse",
    "substanceUse",
    "occupation",
    "exercise",
    "diet",
    "sexualHistory",
    "other",
})

# health:sleepQuality ranges over four named individuals (health v2.5). A
# vendor-specific label leaking through an importer is the realistic way an
# out-of-vocabulary value gets here, and without the check it would be stored
# and later compared against the four defined ratings as if it were one.
_VALID_SLEEP_QUALITY = frozenset({"Excellent", "Good", "Fair", "Poor"})

# cascade:InteractionScenarioShape sh:in.
_VALID_INTERACTION_SEVERITY = frozenset({"low", "moderate", "high", "critical"})

# health:interpretation and clinical:interpretation (health v2.7 / clinical
# v1.15). The two properties carry identical sh:in lists, so MEMBERSHIP is
# keyed on the PROPERTY and serves lab results and vital signs alike; a check
# that fired only on one record type would let the same out-of-vocabulary value
# through on the other.
#
# SEVERITY, however, is keyed on the record type, because the shapes differ:
# the lab shapes bind the set at sh:Violation, and clinical:VitalSignShape
# binds the same set at sh:Warning (clinical v1.15). A vital carrying a value
# outside the set is REPORTED, not rejected, and is raised to a violation in a
# later clinical version only after a release in which the warning is
# observably absent from conforming output.
_VALID_INTERPRETATIONS = OBSERVATION_INTERPRETATION_VALUES

# The 15 codes of http://terminology.hl7.org/CodeSystem/data-absent-reason,
# which cascade:dataAbsentReason is bound to (core v3.6). A raw HL7 v3
# NullFlavor code (UNK, NAV, NASK, ASKU, ...) is NOT accepted: an importer maps
# nullFlavor on the way in, using the table stated on the property in core.ttl.
# Accepting both spellings would give every absence two encodings and put the
# burden of knowing both on every reader.
_VALID_DATA_ABSENT_REASONS = frozenset({
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
})

# Record types whose interpretation binding is sh:Warning rather than
# sh:Violation. Only vital signs: clinical:VitalSignShape carries the ratchet.
_WARNING_ONLY_INTERPRETATION_TYPES = frozenset({"VitalSign"})

# Numeric bounds asserted by the health v2.5 daily-snapshot shapes and the
# core v3.4 record-summary shape. (field, record types, lower, upper).
# A day count larger than a decade of daily readings is a unit error, not a
# long history; exercise minutes above 1440 is a seconds-for-minutes mix-up at
# an import boundary, which is silently plausible without the bound.
_NUMERIC_BOUNDS: list[tuple[str, str, frozenset[str], float, float | None]] = [
    ("steps", "steps", frozenset({"DailyActivitySnapshot"}), 0, None),
    ("activeEnergyKcal", "active_energy_kcal", frozenset({"DailyActivitySnapshot"}), 0, None),
    ("exerciseMinutes", "exercise_minutes", frozenset({"DailyActivitySnapshot"}), 0, 1440),
    ("standHours", "stand_hours", frozenset({"DailyActivitySnapshot"}), 0, 24),
    ("durationHours", "duration_hours", frozenset({"DailySleepSnapshot"}), 0, 24),
    ("sampleCount", "sample_count", frozenset({"DailyVitalReading"}), 0, None),
    ("conditionCount", "condition_count", frozenset({"RecordSummary"}), 0, None),
    ("medicationCount", "medication_count", frozenset({"RecordSummary"}), 0, None),
    ("allergyCount", "allergy_count", frozenset({"RecordSummary"}), 0, None),
    ("labResultCount", "lab_result_count", frozenset({"RecordSummary"}), 0, None),
    ("immunizationCount", "immunization_count", frozenset({"RecordSummary"}), 0, None),
    ("coverageCount", "coverage_count", frozenset({"RecordSummary"}), 0, None),
    ("supplementCount", "supplement_count", frozenset({"RecordSummary"}), 0, None),
    ("vitalSignDays", "vital_sign_days", frozenset({"RecordSummary"}), 0, 36500),
    ("heartRateDays", "heart_rate_days", frozenset({"RecordSummary"}), 0, 36500),
    ("bloodPressureDays", "blood_pressure_days", frozenset({"RecordSummary"}), 0, 36500),
    ("activityDays", "activity_days", frozenset({"RecordSummary"}), 0, 36500),
    ("sleepDays", "sleep_days", frozenset({"RecordSummary"}), 0, 36500),
]

# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


class ValidationError(Exception):
    """
    Raised when a record fails validation.

    The ``errors`` attribute contains a list of human-readable error messages.
    """

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


@dataclass
class ValidationResult:
    """
    Result of a validation operation.

    Attributes:
        is_valid: True if the record passed all validation checks.
        errors: List of human-readable error messages (empty if valid).
        warnings: List of advisory messages (non-blocking).
        shacl_report: Raw SHACL validation report text (if pyshacl was used).
    """

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    shacl_report: str | None = None


# ---------------------------------------------------------------------------
# Structural validation
# ---------------------------------------------------------------------------

def _validate_dict_structural(data: dict[str, Any]) -> tuple[list[str], list[str]]:
    """
    Validate a record dict (camelCase or snake_case) for required fields.

    Returns ``(errors, warnings)``; an empty error list means valid. Warnings
    mirror ``sh:Warning`` shape results, which are reported without
    withholding conformance.
    """
    import re

    errors: list[str] = []
    warnings: list[str] = []
    record_type = data.get("type") or data.get("type")

    if not record_type:
        errors.append("Missing required field: 'type'")
        return errors, warnings

    # Try camelCase required fields first, then snake_case
    required_camel = _REQUIRED_FIELDS_CAMEL.get(str(record_type))
    required_snake = _REQUIRED_FIELDS_SNAKE.get(str(record_type))

    if required_camel is None and required_snake is None:
        errors.append(f"Unknown record type: {record_type!r}")
        return errors, warnings

    # Determine which field convention is used
    if required_camel:
        for f in required_camel:
            if f not in data or data[f] is None or data[f] == "":
                # Try snake_case fallback for the same field
                errors.append(f"Missing required field: '{f}'")

    if required_snake:
        # Check if snake_case keys are present instead
        snake_errors: list[str] = []
        for f in required_snake:
            if f not in data or data[f] is None or data[f] == "":
                snake_errors.append(f)
        # If snake_case check produces fewer errors, use those
        if required_camel and len(snake_errors) < len(errors):
            errors = [f"Missing required field: '{f}'" for f in snake_errors]
        elif not required_camel:
            errors = [f"Missing required field: '{f}'" for f in snake_errors]

    # Validate schema version format
    sv = data.get("schemaVersion") or data.get("schema_version")
    if sv is not None and not re.match(_SCHEMA_VERSION_PATTERN, str(sv)):
        errors.append(
            f"Invalid schemaVersion: {sv!r}. Must match pattern: {_SCHEMA_VERSION_PATTERN}"
        )

    # Validate provenance type
    prov = data.get("dataProvenance") or data.get("data_provenance")
    if prov and str(prov) not in _VALID_PROVENANCE_TYPES:
        errors.append(
            f"Invalid dataProvenance: {prov!r}. "
            f"Must be one of: {sorted(_VALID_PROVENANCE_TYPES)}"
        )

    # Validate vitalType enum constraint for VitalSign records
    if str(record_type) == "VitalSign":
        vital_type = data.get("vitalType") or data.get("vital_type")
        if vital_type and str(vital_type) not in _VALID_VITAL_TYPES:
            errors.append(
                f"Invalid vitalType: {vital_type!r}. "
                f"Must be one of: {sorted(_VALID_VITAL_TYPES)}"
            )

    enum_errors, enum_warnings = _validate_enums_and_bounds(str(record_type), data)
    errors.extend(enum_errors)
    warnings.extend(enum_warnings)
    return errors, warnings


def _get_either(data: dict[str, Any], camel: str, snake: str) -> Any:
    """Return the camelCase value if present, else the snake_case one."""
    if camel in data and data[camel] is not None:
        return data[camel]
    return data.get(snake)


def _validate_enums_and_bounds(
    record_type: str, data: dict[str, Any]
) -> tuple[list[str], list[str]]:
    """
    Enumeration and numeric-range checks lifted from the SHACL shapes.

    Kept separate from the required-field pass because these are constraints
    on a value that IS present, which is the class of defect a required-field
    check cannot see: a record with every field populated and one of them
    out of range validates clean without them.

    Returns ``(errors, warnings)``. A warning does NOT make the record
    invalid: it mirrors an ``sh:Warning`` result, which a conforming SHACL
    processor reports without withholding conformance.
    """
    errors: list[str] = []
    warnings: list[str] = []

    # Keyed on the PROPERTY, not on the record type: health: and clinical:
    # social history records are both spelled "SocialHistoryRecord" in the
    # type field, and only the clinical: one carries socialHistoryCategory.
    # The shape constrains the property, so the check follows the property.
    category = _get_either(data, "socialHistoryCategory", "social_history_category")
    if category and str(category) not in _VALID_SOCIAL_HISTORY_CATEGORIES:
        errors.append(
            f"Invalid socialHistoryCategory: {category!r}. "
            f"Must be one of: {sorted(_VALID_SOCIAL_HISTORY_CATEGORIES)}"
        )

    # Membership keyed on the property, severity keyed on the record type, for
    # the reason given at _VALID_INTERPRETATIONS.
    interpretation = data.get("interpretation")
    if interpretation and str(interpretation) not in _VALID_INTERPRETATIONS:
        message = (
            f"interpretation {interpretation!r} is outside the ratified value set. "
            f"Expected a code from the HL7 v3 ObservationInterpretation code system "
            f"(http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation), "
            f"a code from http://terminology.hl7.org/CodeSystem/data-absent-reason, "
            f"or one of the retained words normal / high / low / abnormal / critical. "
            f"Carry a code in none of those verbatim on interpretationSourceCode and "
            f"put the nearest ratified reading here"
        )
        if record_type in _WARNING_ONLY_INTERPRETATION_TYPES:
            warnings.append(message)
        else:
            errors.append(f"Invalid {message}")

    # health:interpretationSourceCode / clinical:interpretationSourceCode
    # (health v2.7 / clinical v1.15). The VALUE is unconstrained by design: it
    # is the source's own code, and a value set or a pattern here would
    # recreate exactly the loss the property exists to prevent. The CARDINALITY
    # is not: interpretation is 0..1, so the verbatim code that explains it is
    # 0..1 too, and two source codes on one interpretation is a merge artefact.
    source_code = _get_either(
        data, "interpretationSourceCode", "interpretation_source_code"
    )
    if isinstance(source_code, (list, tuple, set)) and len(source_code) > 1:
        errors.append(
            f"Invalid interpretationSourceCode: {list(source_code)!r}. At most one "
            f"value is permitted, because the interpretation it explains is itself "
            f"single-valued"
        )

    # cascade:dataAbsentReason (core v3.6): single-valued, and bound to the 15
    # data-absent-reason codes. A value is absent for ONE reason; two reasons
    # is a merge artefact a reader cannot choose between.
    absent_reason = _get_either(data, "dataAbsentReason", "data_absent_reason")
    if isinstance(absent_reason, (list, tuple, set)):
        if len(absent_reason) > 1:
            errors.append(
                f"Invalid dataAbsentReason: {list(absent_reason)!r}. A value is "
                f"absent for one reason; at most one code is permitted"
            )
        absent_values = list(absent_reason)
    elif absent_reason is not None:
        absent_values = [absent_reason]
    else:
        absent_values = []
    for absent_value in absent_values:
        if str(absent_value) not in _VALID_DATA_ABSENT_REASONS:
            errors.append(
                f"Invalid dataAbsentReason: {absent_value!r}. Must be a code from "
                f"http://terminology.hl7.org/CodeSystem/data-absent-reason. A raw "
                f"HL7 v3 NullFlavor code (UNK, NAV, NASK, ASKU, ...) is not "
                f"accepted: map it on import"
            )

    if record_type == "DailySleepSnapshot":
        quality = _get_either(data, "sleepQuality", "sleep_quality")
        if quality and str(quality) not in _VALID_SLEEP_QUALITY:
            errors.append(
                f"Invalid sleepQuality: {quality!r}. "
                f"Must be one of: {sorted(_VALID_SLEEP_QUALITY)}"
            )

    if record_type == "DailyVitalReading":
        # health:DailyVitalReadingShape requires a timestamp through a
        # node-level sh:or over cascade:date and health:date, because two live
        # emitters spell it differently. Omitting BOTH is the only violation,
        # and it is exactly the failure that drops a reading out of the time
        # series it belongs to.
        if not _get_either(data, "date", "date"):
            errors.append(
                "Missing timestamp: a DailyVitalReading must carry a date "
                "(serialized as either cascade:date or health:date)"
            )

    if record_type == "Procedure":
        # clinical:ProcedureShape's sh:or over the two name spellings. Omitting
        # BOTH is the only violation. clinical:procedureName is canonical and
        # health:procedureName is the deprecated import spelling accepted for
        # the clinical v1.15 migration window; a C-CDA import path writes the
        # health: spelling on records it types clinical:Procedure, so demanding
        # the canonical one would reject a record that carries a name.
        canonical = _get_either(data, "procedureName", "procedure_name")
        migration = _get_either(data, "healthProcedureName", "health_procedure_name")
        if not canonical and not migration:
            errors.append(
                "Missing procedure name: a Procedure must carry a name "
                "(serialized as either clinical:procedureName or, during the "
                "migration window, health:procedureName)"
            )
        elif migration and not canonical:
            warnings.append(
                "Procedure carries the deprecated health:procedureName spelling. "
                "clinical:procedureName is canonical; the health: spelling is "
                "accepted for the migration window only"
            )

    if record_type == "InteractionScenario":
        severity = data.get("severity")
        if severity and str(severity) not in _VALID_INTERACTION_SEVERITY:
            errors.append(
                f"Invalid severity: {severity!r}. "
                f"Must be one of: {sorted(_VALID_INTERACTION_SEVERITY)}"
            )

    for camel, snake, types, low, high in _NUMERIC_BOUNDS:
        if record_type not in types:
            continue
        raw = _get_either(data, camel, snake)
        if raw is None:
            continue
        try:
            num = float(raw)
        except (TypeError, ValueError):
            errors.append(f"Invalid {camel}: {raw!r} is not numeric")
            continue
        if num < low:
            errors.append(f"Invalid {camel}: {raw!r} is below the minimum of {low}")
        elif high is not None and num > high:
            errors.append(f"Invalid {camel}: {raw!r} exceeds the maximum of {high}")

    return errors, warnings


def _validate_turtle_structural(turtle: str) -> tuple[list[str], list[str]]:
    """
    Parse Turtle and validate extracted records structurally.

    Returns ``(errors, warnings)``.
    """
    try:
        import rdflib
        from rdflib import Graph, RDF, URIRef, Literal
        from rdflib.namespace import XSD
        from cascade_protocol.vocabularies.namespaces import NAMESPACES, TYPE_MAPPING, build_reverse_predicate_map

        g = Graph()
        g.parse(data=turtle, format="turtle")

        RDF_TYPE = RDF.type
        CASCADE_NS = NAMESPACES["cascade"]

        # Build reverse type map (RDF type URI -> record type string)
        from cascade_protocol.vocabularies.namespaces import TYPE_TO_MAPPING_KEY
        # Reverse lookup: mapping_key -> canonical record type string
        _mk_to_rt: dict[str, str] = {}
        for _rt, _mk in TYPE_TO_MAPPING_KEY.items():
            _mk_to_rt.setdefault(_mk, _rt)
        reverse_type: dict[str, str] = {}
        for mapping_key, mapping in TYPE_MAPPING.items():
            rdf_type = mapping["rdf_type"]
            colon_idx = rdf_type.find(":")
            if colon_idx >= 0:
                ns_prefix = rdf_type[:colon_idx]
                local_name = rdf_type[colon_idx + 1:]
                ns_uri = NAMESPACES.get(ns_prefix)
                if ns_uri:
                    record_type_str = _mk_to_rt.get(mapping_key, local_name)
                    reverse_type[f"{ns_uri}{local_name}"] = record_type_str

        reverse_pred = build_reverse_predicate_map()
        errors: list[str] = []
        warnings: list[str] = []

        for subj in set(g.subjects()):
            # Find type
            types = list(g.objects(subj, RDF_TYPE))
            if not types:
                continue
            type_uri = str(types[0])
            record_type = reverse_type.get(type_uri)
            if not record_type:
                continue

            # Build record dict
            record: dict[str, Any] = {"id": str(subj), "type": record_type}
            for p, o in g.predicate_objects(subj):
                p_uri = str(p)
                if p_uri == str(RDF_TYPE):
                    continue
                py_key = reverse_pred.get(p_uri)
                if not py_key:
                    continue
                if py_key == "data_provenance":
                    obj_str = str(o)
                    if obj_str.startswith(CASCADE_NS):
                        record["data_provenance"] = obj_str[len(CASCADE_NS):]
                    else:
                        record["data_provenance"] = obj_str
                elif isinstance(o, Literal):
                    record[py_key] = str(o)
                else:
                    record[py_key] = str(o)

            field_errors, field_warnings = _validate_dict_structural(record)
            for e in field_errors:
                errors.append(f"Subject <{subj}>: {e}")
            for w in field_warnings:
                warnings.append(f"Subject <{subj}>: {w}")

        return errors, warnings

    except Exception as exc:
        return [f"Turtle parse error: {exc}"], []


def validate(
    turtle_or_record: "str | Any",
    use_shacl: bool = False,
    shapes_file: str | None = None,
) -> ValidationResult:
    """
    Validate a Cascade Protocol record or Turtle document.

    Args:
        turtle_or_record: Either a Turtle string or a CascadeRecord dataclass instance.
        use_shacl: If True, run SHACL validation using pyshacl (requires
            ``pip install "cascade-protocol[validation]"``).
        shapes_file: Path to a SHACL shapes TTL file. Required when
            ``use_shacl=True`` and you want to use a specific shapes file.

    Returns:
        A :class:`ValidationResult` with ``is_valid``, ``errors``, and
        optionally ``shacl_report``.

    Raises:
        ImportError: If ``use_shacl=True`` but pyshacl is not installed.
    """
    from dataclasses import fields as dc_fields

    # Convert dataclass to dict if needed
    if hasattr(turtle_or_record, "__dataclass_fields__"):
        # It's a dataclass
        data: dict[str, Any] = {}
        for f in dc_fields(turtle_or_record):
            val = getattr(turtle_or_record, f.name)
            if val is not None:
                data[f.name] = val
        errors, warnings = _validate_dict_structural(data)
        return ValidationResult(is_valid=not errors, errors=errors, warnings=warnings)

    # It's a Turtle string
    turtle = str(turtle_or_record)

    # Structural validation always runs
    errors, warnings = _validate_turtle_structural(turtle)

    if errors:
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

    # Optional SHACL validation
    if use_shacl:
        result = _run_shacl(turtle, shapes_file)
        result.warnings = warnings + result.warnings
        return result

    return ValidationResult(is_valid=True, warnings=warnings)


def _run_shacl(turtle: str, shapes_file: str | None = None) -> ValidationResult:
    """Run pyshacl validation against the provided shapes file."""
    try:
        import pyshacl  # type: ignore[import]
    except ImportError:
        raise ImportError(
            "pyshacl is required for SHACL validation. "
            "Install it with: pip install \"cascade-protocol[validation]\""
        )

    if shapes_file is None:
        return ValidationResult(
            is_valid=True,
            warnings=["SHACL validation requested but no shapes_file provided; skipping SHACL check."],
        )

    conforms, results_graph, results_text = pyshacl.validate(
        turtle,
        shacl_graph=shapes_file,
        data_graph_format="turtle",
        shacl_graph_format="turtle",
        inference="rdfs",
        raise_if_not_conforms=False,
    )

    errors: list[str] = []
    if not conforms:
        # Extract violation messages
        try:
            from rdflib import Graph as RDFGraph, URIRef as RDFURIRef
            from rdflib.namespace import SH
            rg = results_graph if isinstance(results_graph, RDFGraph) else RDFGraph().parse(data=str(results_graph), format="turtle")
            for result in rg.subjects(predicate=SH.resultSeverity, object=SH.Violation):
                msg_node = rg.value(result, SH.resultMessage)
                if msg_node:
                    errors.append(str(msg_node))
        except Exception:
            errors.append("SHACL validation failed (see shacl_report for details)")

    return ValidationResult(
        is_valid=conforms,
        errors=errors,
        shacl_report=str(results_text),
    )


def validate_dict(data: dict[str, Any]) -> ValidationResult:
    """
    Validate a raw dict (camelCase or snake_case) without serializing to Turtle.

    Useful for validating conformance fixture inputs before serialization.

    Args:
        data: Record dict with either camelCase (TypeScript convention)
            or snake_case (Python convention) keys.

    Returns:
        A :class:`ValidationResult`.
    """
    errors, warnings = _validate_dict_structural(data)
    return ValidationResult(is_valid=not errors, errors=errors, warnings=warnings)
