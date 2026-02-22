"""
High-level serialization functions for converting Cascade Protocol
data model objects to Turtle (RDF) format.

Produces output conforming to the Cascade Protocol conformance fixtures.

Example:
    >>> from cascade_protocol import Medication, serialize
    >>> med = Medication(
    ...     id="urn:uuid:med0-0001-aaaa-bbbb-ccccddddeeee",
    ...     medication_name="Lisinopril",
    ...     is_active=True,
    ...     data_provenance="ClinicalGenerated",
    ...     schema_version="1.3",
    ... )
    >>> turtle = serialize(med)

This module also exposes ``serialize_from_dict()`` for serializing
conformance fixture ``input`` objects (which use camelCase JSON keys).
"""

from __future__ import annotations

import re
from dataclasses import fields, asdict
from typing import Any

from cascade_protocol.models.common import CascadeRecord
from cascade_protocol.models.medication import Medication
from cascade_protocol.models.condition import Condition
from cascade_protocol.models.allergy import Allergy
from cascade_protocol.models.lab_result import LabResult
from cascade_protocol.models.vital_sign import VitalSign
from cascade_protocol.models.immunization import Immunization
from cascade_protocol.models.procedure import Procedure
from cascade_protocol.models.family_history import FamilyHistory
from cascade_protocol.models.coverage import Coverage
from cascade_protocol.models.patient_profile import PatientProfile, EmergencyContact, Address, PharmacyInfo
from cascade_protocol.models.wellness import ActivitySnapshot, SleepSnapshot
from cascade_protocol.vocabularies.namespaces import (
    NAMESPACES,
    TYPE_MAPPING,
    TYPE_TO_MAPPING_KEY,
    PROPERTY_PREDICATES,
    PROPERTY_PREDICATES_CAMEL,
)

# ---------------------------------------------------------------------------
# Type-specific predicate overrides
# ---------------------------------------------------------------------------

# When a Python field name maps to different RDF predicates depending on the
# record type, these overrides take precedence over PROPERTY_PREDICATES.
_TYPE_PREDICATE_OVERRIDES: dict[str, dict[str, str]] = {
    "VitalSign": {
        "snomed_code": "clinical:snomedCode",
        "interpretation": "clinical:interpretation",
    },
    # Camel variants
    "_camel_VitalSign": {
        "snomedCode": "clinical:snomedCode",
        "interpretation": "clinical:interpretation",
    },
}

# Fields whose values should be serialized as URI references (angle-bracket enclosed)
# rather than string literals, when the value looks like a full URI.
_URI_FIELDS_SNAKE: set[str] = {
    "rx_norm_code",
    "icd10_code",
    "snomed_code",
    "loinc_code",
    "test_code",
}

_URI_FIELDS_CAMEL: set[str] = {
    "rxNormCode",
    "icd10Code",
    "snomedCode",
    "loincCode",
    "testCode",
}

# Fields whose values are arrays and should be serialized as repeated predicates
# (for URI arrays) or RDF lists (for string arrays).
_ARRAY_FIELDS_SNAKE: set[str] = {
    "drug_codes",
    "affects_vital_signs",
    "monitored_vital_signs",
}

_ARRAY_FIELDS_CAMEL: set[str] = {
    "drugCodes",
    "affectsVitalSigns",
    "monitoredVitalSigns",
}

# Fields that are date-only typed (xsd:date).
_DATE_ONLY_FIELDS_SNAKE: set[str] = {"date_of_birth"}
_DATE_ONLY_FIELDS_CAMEL: set[str] = {"dateOfBirth"}

# date field from activity/sleep (plain string, no datatype).
_NO_DATATYPE_DATE_FIELDS_SNAKE: set[str] = {"date"}
_NO_DATATYPE_DATE_FIELDS_CAMEL: set[str] = {"date"}

# Fields that are dateTime typed (xsd:dateTime).
_EXPLICIT_DATETIME_FIELDS_SNAKE: set[str] = {
    "effective_period_start",
    "effective_period_end",
    "effective_start",
    "effective_end",
}
_EXPLICIT_DATETIME_FIELDS_CAMEL: set[str] = {
    "effectivePeriodStart",
    "effectivePeriodEnd",
    "effectiveStart",
    "effectiveEnd",
}

# Fields that are typed as xsd:integer (not just plain numeric).
_INTEGER_TYPED_FIELDS_SNAKE: set[str] = {
    "computed_age",
    "refills_allowed",
    "supply_duration_days",
    "onset_age",
}
_INTEGER_TYPED_FIELDS_CAMEL: set[str] = {
    "computedAge",
    "refillsAllowed",
    "supplyDurationDays",
    "onsetAge",
}

# Preferred prefix declaration order.
_PREFIX_ORDER = [
    "cascade", "health", "clinical", "coverage", "checkup", "pots",
    "fhir", "rxnorm", "sct", "loinc", "icd10", "ucum",
    "prov", "foaf", "ldp", "dcterms", "xsd",
]


def _is_datetime_field(key: str, camel: bool = False) -> bool:
    """Return True if this field should be typed as xsd:dateTime."""
    explicit = _EXPLICIT_DATETIME_FIELDS_CAMEL if camel else _EXPLICIT_DATETIME_FIELDS_SNAKE
    if key in explicit:
        return True
    no_dtype = _NO_DATATYPE_DATE_FIELDS_CAMEL if camel else _NO_DATATYPE_DATE_FIELDS_SNAKE
    if key in no_dtype:
        return False
    date_only = _DATE_ONLY_FIELDS_CAMEL if camel else _DATE_ONLY_FIELDS_SNAKE
    if key in date_only:
        return False
    lower = key.lower()
    return "date" in lower or "time" in lower


def _is_date_only_field(key: str, camel: bool = False) -> bool:
    """Return True if this field should be typed as xsd:date."""
    s = _DATE_ONLY_FIELDS_CAMEL if camel else _DATE_ONLY_FIELDS_SNAKE
    return key in s


def _escape_turtle_string(s: str) -> str:
    """Escape special characters in a Turtle string literal."""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")


def _add_prefix_for_uri(uri: str, prefixes: dict[str, str]) -> None:
    """If ``uri`` starts with a known namespace, add its prefix to ``prefixes``."""
    for prefix, ns in NAMESPACES.items():
        if prefix in ("rdf",):
            continue  # never declare rdf in output
        if uri.startswith(ns):
            prefixes[prefix] = ns
            return


def _collect_prefixes_from_dict(
    record_dict: dict[str, Any],
    record_type: str,
    camel: bool,
) -> dict[str, str]:
    """Scan a record dict and collect all needed namespace prefixes."""
    prefixes: dict[str, str] = {}

    # Always include cascade and xsd
    prefixes["cascade"] = NAMESPACES["cascade"]
    prefixes["xsd"] = NAMESPACES["xsd"]

    # Add namespace for rdf:type
    mapping_key = TYPE_TO_MAPPING_KEY.get(record_type)
    if mapping_key:
        mapping = TYPE_MAPPING.get(mapping_key)
        if mapping:
            rdf_type = mapping["rdf_type"]
            ns_prefix = rdf_type.split(":")[0]
            if ns_prefix in NAMESPACES:
                prefixes[ns_prefix] = NAMESPACES[ns_prefix]

    pred_map = PROPERTY_PREDICATES_CAMEL if camel else PROPERTY_PREDICATES
    uri_fields = _URI_FIELDS_CAMEL if camel else _URI_FIELDS_SNAKE
    array_fields = _ARRAY_FIELDS_CAMEL if camel else _ARRAY_FIELDS_SNAKE
    overrides = _TYPE_PREDICATE_OVERRIDES.get(f"_camel_{record_type}" if camel else record_type, {})

    for key, value in record_dict.items():
        if key in ("id", "type") or value is None:
            continue

        pred = overrides.get(key) or pred_map.get(key)
        if pred:
            ns_prefix = pred.split(":")[0]
            if ns_prefix in NAMESPACES:
                prefixes[ns_prefix] = NAMESPACES[ns_prefix]

        if isinstance(value, str) and key in uri_fields:
            _add_prefix_for_uri(value, prefixes)

        if isinstance(value, list) and key in array_fields:
            for item in value:
                if isinstance(item, str) and item.startswith("http"):
                    _add_prefix_for_uri(item, prefixes)

    return prefixes


def _sorted_prefixes(prefixes: dict[str, str]) -> list[tuple[str, str]]:
    """Return prefix entries in stable canonical order."""
    def order_key(item: tuple[str, str]) -> int:
        try:
            return _PREFIX_ORDER.index(item[0])
        except ValueError:
            return len(_PREFIX_ORDER)

    return sorted(prefixes.items(), key=order_key)


class _TurtleWriter:
    """Minimal Turtle document builder."""

    def __init__(self) -> None:
        self._lines: list[str] = []

    def prefix(self, name: str, uri: str) -> None:
        self._lines.append(f"@prefix {name}: <{uri}> .")

    def blank_line(self) -> None:
        self._lines.append("")

    def raw(self, line: str) -> None:
        self._lines.append(line)

    def build(self) -> str:
        return "\n".join(self._lines) + "\n"


def _serialize_dict(
    record_dict: dict[str, Any],
    camel: bool = False,
) -> str:
    """
    Core serialization logic for a record dict.

    Args:
        record_dict: Dict with either snake_case or camelCase keys.
        camel: True when dict uses camelCase keys (conformance fixture input).

    Returns:
        Turtle document as a string.
    """
    record_type = str(record_dict.get("type", ""))
    record_id = str(record_dict.get("id", ""))

    mapping_key = TYPE_TO_MAPPING_KEY.get(record_type)
    if not mapping_key:
        raise ValueError(
            f"Unknown record type: {record_type!r}. No TYPE_MAPPING found."
        )
    mapping = TYPE_MAPPING[mapping_key]
    rdf_type = mapping["rdf_type"]

    pred_map = PROPERTY_PREDICATES_CAMEL if camel else PROPERTY_PREDICATES
    uri_fields = _URI_FIELDS_CAMEL if camel else _URI_FIELDS_SNAKE
    array_fields = _ARRAY_FIELDS_CAMEL if camel else _ARRAY_FIELDS_SNAKE
    integer_typed = _INTEGER_TYPED_FIELDS_CAMEL if camel else _INTEGER_TYPED_FIELDS_SNAKE
    overrides = _TYPE_PREDICATE_OVERRIDES.get(f"_camel_{record_type}" if camel else record_type, {})

    # Collect prefixes
    prefixes = _collect_prefixes_from_dict(record_dict, record_type, camel)

    writer = _TurtleWriter()
    for name, uri in _sorted_prefixes(prefixes):
        writer.prefix(name, uri)
    writer.blank_line()

    subject_uri = f"<{record_id}>"

    triple_lines: list[str] = [f"    a {rdf_type}"]

    def _emit_field(key: str, value: Any) -> None:
        if key in ("id", "type") or value is None:
            return

        pred = overrides.get(key) or pred_map.get(key)
        if not pred:
            return

        # dataProvenance / data_provenance: emit as cascade: prefixed URI
        prov_key = "dataProvenance" if camel else "data_provenance"
        if key == prov_key:
            triple_lines.append(f"    {pred} cascade:{value}")
            return

        # Boolean
        if isinstance(value, bool):
            triple_lines.append(f"    {pred} {'true' if value else 'false'}")
            return

        # Integer typed fields (xsd:integer)
        if key in integer_typed and isinstance(value, (int, float)) and not isinstance(value, bool):
            int_val = int(value)
            triple_lines.append(f'    {pred} "{int_val}"^^xsd:integer')
            return

        # Numeric
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if isinstance(value, float) and not value.is_integer():
                triple_lines.append(f"    {pred} {value}")
            else:
                triple_lines.append(f"    {pred} {int(value)}")
            return

        # URI fields
        if key in uri_fields and isinstance(value, str):
            if value.startswith("http") or value.startswith("urn:"):
                triple_lines.append(f"    {pred} <{value}>")
            else:
                triple_lines.append(f"    {pred} <{value}>")
            return

        # Array fields (repeated predicates for URIs, RDF lists for strings)
        if key in array_fields and isinstance(value, list):
            if not value:
                return
            is_uri_list = all(
                isinstance(item, str) and (item.startswith("http") or item.startswith("urn:"))
                for item in value
            )
            if is_uri_list:
                for item in value:
                    triple_lines.append(f"    {pred} <{item}>")
            else:
                items_str = " ".join(f'"{_escape_turtle_string(str(item))}"' for item in value)
                triple_lines.append(f"    {pred} ( {items_str} )")
            return

        # Nested blank nodes (PatientProfile sub-objects)
        if isinstance(value, dict):
            _emit_blank_node(pred, key, value)
            return

        # Date-only fields (xsd:date)
        if isinstance(value, str) and _is_date_only_field(key, camel):
            triple_lines.append(f'    {pred} "{_escape_turtle_string(value)}"^^xsd:date')
            return

        # DateTime fields (xsd:dateTime)
        if isinstance(value, str) and _is_datetime_field(key, camel):
            triple_lines.append(f'    {pred} "{_escape_turtle_string(value)}"^^xsd:dateTime')
            return

        # Default: string literal
        if isinstance(value, str):
            triple_lines.append(f'    {pred} "{_escape_turtle_string(value)}"')
            return

    def _emit_blank_node(predicate: str, key: str, obj: dict[str, Any]) -> None:
        """Emit a blank node for nested PatientProfile objects."""
        bnode_type_map = {
            "emergency_contact": "cascade:EmergencyContact",
            "emergencyContact": "cascade:EmergencyContact",
            "address": "cascade:Address",
            "preferred_pharmacy": "cascade:PharmacyInfo",
            "preferredPharmacy": "cascade:PharmacyInfo",
        }
        bnode_type = bnode_type_map.get(key)
        inner_lines: list[str] = []
        if bnode_type:
            inner_lines.append(f"        a {bnode_type}")
        for k, v in obj.items():
            if v is None:
                continue
            # Nested keys use cascade: prefix
            nested_pred = f"cascade:{k}"
            if isinstance(v, str):
                inner_lines.append(f'        {nested_pred} "{_escape_turtle_string(v)}"')
            elif isinstance(v, bool):
                inner_lines.append(f"        {nested_pred} {'true' if v else 'false'}")
            elif isinstance(v, (int, float)) and not isinstance(v, bool):
                if isinstance(v, float) and not v.is_integer():
                    inner_lines.append(f"        {nested_pred} {v}")
                else:
                    inner_lines.append(f"        {nested_pred} {int(v)}")
        if inner_lines:
            inner_str = " ;\n".join(inner_lines)
            triple_lines.append(f"    {predicate} [\n{inner_str}\n    ]")

    # Emit all fields in their natural order
    for key, value in record_dict.items():
        _emit_field(key, value)

    # Compose the subject block
    if triple_lines:
        joined = " ;\n".join(triple_lines) + " ."
        writer.raw(f"{subject_uri} {joined}")

    return writer.build()


def serialize(record: CascadeRecord) -> str:
    """
    Serialize any Cascade Protocol record to Turtle format.

    Dispatches based on the ``type`` field of the record. The output matches
    the conformance fixture expected Turtle format.

    Args:
        record: Any CascadeRecord (Medication, Condition, VitalSign, etc.)

    Returns:
        A complete Turtle document string.

    Raises:
        ValueError: If the record type is unknown.
    """
    return _serialize_dataclass(record)


def _serialize_dataclass(record: CascadeRecord) -> str:
    """Serialize a CascadeRecord dataclass to Turtle."""
    # Convert dataclass to dict, then call _serialize_dict with snake_case
    record_dict: dict[str, Any] = {}
    for f in fields(record):
        val = getattr(record, f.name)
        if val is None:
            continue
        # Convert nested dataclass objects to dict
        if hasattr(val, "__dataclass_fields__"):
            # Nested objects like EmergencyContact, Address, PharmacyInfo
            # Convert their field names from snake_case to camelCase for Turtle emission
            # Actually keep them as-is; the blank node emitter handles snake_case too
            nested = {}
            for nf in fields(val):
                nval = getattr(val, nf.name)
                if nval is not None:
                    nested[nf.name] = nval
            record_dict[f.name] = nested
        else:
            record_dict[f.name] = val
    return _serialize_dict(record_dict, camel=False)


def serialize_from_dict(data: dict[str, Any]) -> str:
    """
    Serialize a camelCase JSON dict (e.g. from a conformance fixture ``input``
    field) to Turtle format.

    This is the function used by conformance tests, which receive TypeScript-SDK-
    compatible camelCase JSON objects.

    Args:
        data: Dict with camelCase keys matching the TypeScript SDK model fields.

    Returns:
        A complete Turtle document string.

    Raises:
        ValueError: If the record type is unknown.
    """
    return _serialize_dict(data, camel=True)


# ---------------------------------------------------------------------------
# Type-specific convenience wrappers
# ---------------------------------------------------------------------------

def serialize_medication(med: Medication) -> str:
    """Serialize a Medication record to Turtle."""
    return serialize(med)


def serialize_condition(cond: Condition) -> str:
    """Serialize a Condition record to Turtle."""
    return serialize(cond)


def serialize_allergy(allergy: Allergy) -> str:
    """Serialize an Allergy record to Turtle."""
    return serialize(allergy)


def serialize_lab_result(lab: LabResult) -> str:
    """Serialize a LabResult record to Turtle."""
    return serialize(lab)


def serialize_vital_sign(vital: VitalSign) -> str:
    """Serialize a VitalSign record to Turtle."""
    return serialize(vital)


def serialize_immunization(imm: Immunization) -> str:
    """Serialize an Immunization record to Turtle."""
    return serialize(imm)


def serialize_procedure(proc: Procedure) -> str:
    """Serialize a Procedure record to Turtle."""
    return serialize(proc)


def serialize_family_history(fam: FamilyHistory) -> str:
    """Serialize a FamilyHistory record to Turtle."""
    return serialize(fam)


def serialize_coverage(cov: Coverage) -> str:
    """Serialize a Coverage record to Turtle."""
    return serialize(cov)


def serialize_patient_profile(profile: PatientProfile) -> str:
    """Serialize a PatientProfile record to Turtle."""
    return serialize(profile)


def serialize_activity_snapshot(activity: ActivitySnapshot) -> str:
    """Serialize an ActivitySnapshot record to Turtle."""
    return serialize(activity)


def serialize_sleep_snapshot(sleep: SleepSnapshot) -> str:
    """Serialize a SleepSnapshot record to Turtle."""
    return serialize(sleep)
