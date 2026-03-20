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
}

_REQUIRED_FIELDS_SNAKE: dict[str, list[str]] = {
    "MedicationRecord": ["id", "type", "medication_name", "is_active", "data_provenance", "schema_version"],
    "ConditionRecord": ["id", "type", "condition_name", "status", "data_provenance", "schema_version"],
    "AllergyRecord": ["id", "type", "allergen", "data_provenance", "schema_version"],
    "LabResultRecord": ["id", "type", "test_name", "data_provenance", "schema_version"],
    "VitalSign": ["id", "type", "vital_type", "value", "unit", "data_provenance", "schema_version"],
    "ImmunizationRecord": ["id", "type", "vaccine_name", "data_provenance", "schema_version"],
    "ProcedureRecord": ["id", "type", "procedure_name", "data_provenance", "schema_version"],
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
}

_VALID_PROVENANCE_TYPES = frozenset({
    "ClinicalGenerated",
    "DeviceGenerated",
    "SelfReported",
    "AIExtracted",
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

def _validate_dict_structural(data: dict[str, Any]) -> list[str]:
    """
    Validate a record dict (camelCase or snake_case) for required fields.

    Returns a list of error messages; empty list means valid.
    """
    import re

    errors: list[str] = []
    record_type = data.get("type") or data.get("type")

    if not record_type:
        errors.append("Missing required field: 'type'")
        return errors

    # Try camelCase required fields first, then snake_case
    required_camel = _REQUIRED_FIELDS_CAMEL.get(str(record_type))
    required_snake = _REQUIRED_FIELDS_SNAKE.get(str(record_type))

    if required_camel is None and required_snake is None:
        errors.append(f"Unknown record type: {record_type!r}")
        return errors

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

    return errors


def _validate_turtle_structural(turtle: str) -> list[str]:
    """
    Parse Turtle and validate extracted records structurally.

    Returns list of errors.
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

        # Build reverse type map
        reverse_type: dict[str, str] = {}
        for mapping in TYPE_MAPPING.values():
            rdf_type = mapping["rdf_type"]
            colon_idx = rdf_type.find(":")
            if colon_idx >= 0:
                ns_prefix = rdf_type[:colon_idx]
                local_name = rdf_type[colon_idx + 1:]
                ns_uri = NAMESPACES.get(ns_prefix)
                if ns_uri:
                    reverse_type[f"{ns_uri}{local_name}"] = local_name

        reverse_pred = build_reverse_predicate_map()
        errors: list[str] = []

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

            field_errors = _validate_dict_structural(record)
            for e in field_errors:
                errors.append(f"Subject <{subj}>: {e}")

        return errors

    except Exception as exc:
        return [f"Turtle parse error: {exc}"]


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
        errors = _validate_dict_structural(data)
        return ValidationResult(is_valid=not errors, errors=errors)

    # It's a Turtle string
    turtle = str(turtle_or_record)

    # Structural validation always runs
    errors = _validate_turtle_structural(turtle)

    if errors:
        return ValidationResult(is_valid=False, errors=errors)

    # Optional SHACL validation
    if use_shacl:
        return _run_shacl(turtle, shapes_file)

    return ValidationResult(is_valid=True)


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
    errors = _validate_dict_structural(data)
    return ValidationResult(is_valid=not errors, errors=errors)
