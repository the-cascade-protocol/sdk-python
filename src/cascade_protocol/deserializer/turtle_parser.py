"""
Turtle parser for deserializing Cascade Protocol records.

Uses rdflib for robust Turtle parsing, then maps RDF triples back
to Python model objects using the PROPERTY_PREDICATES reverse map.

Supports:
- @prefix declarations
- Subject-predicate-object triples
- Typed literals (xsd:dateTime, xsd:date, xsd:integer, xsd:double)
- URI references
- Boolean literals
- RDF lists
- Blank nodes (PatientProfile nested objects)
- Multi-value predicates (repeated predicate with different objects)

Example:
    >>> from cascade_protocol.deserializer import parse, parse_one
    >>> meds = parse(turtle_string, "MedicationRecord")
    >>> med = parse_one(turtle_string, "MedicationRecord")
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

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
    build_reverse_predicate_map,
)

# ---------------------------------------------------------------------------
# Reverse mappings
# ---------------------------------------------------------------------------

# VitalSign uses clinical: namespace for snomedCode and interpretation
_ADDITIONAL_REVERSE = {
    f"{NAMESPACES['clinical']}snomedCode": "snomed_code",
    f"{NAMESPACES['clinical']}interpretation": "interpretation",
}

_REVERSE_PREDICATE_MAP = build_reverse_predicate_map(_ADDITIONAL_REVERSE)

# Reverse type map: full RDF type URI -> (record_type_string, mapping_key)
def _build_reverse_type_map() -> dict[str, tuple[str, str]]:
    result: dict[str, tuple[str, str]] = {}
    for mapping_key, mapping in TYPE_MAPPING.items():
        rdf_type = mapping["rdf_type"]
        colon_idx = rdf_type.find(":")
        if colon_idx >= 0:
            ns_prefix = rdf_type[:colon_idx]
            local_name = rdf_type[colon_idx + 1:]
            ns_uri = NAMESPACES.get(ns_prefix)
            if ns_uri:
                result[f"{ns_uri}{local_name}"] = (local_name, mapping_key)
    return result

_REVERSE_TYPE_MAP = _build_reverse_type_map()

# ---------------------------------------------------------------------------
# Field type classification
# ---------------------------------------------------------------------------

_BOOLEAN_FIELDS = {"is_active", "as_needed"}

_INTEGER_FIELDS = {
    "computed_age", "refills_allowed", "supply_duration_days", "onset_age",
    "steps", "active_minutes", "calories", "awakenings",
    "total_sleep_minutes", "deep_sleep_minutes", "rem_sleep_minutes", "light_sleep_minutes",
}

_FLOAT_FIELDS = {
    "value", "reference_range_low", "reference_range_high", "distance",
}

_ARRAY_FIELDS = {
    "drug_codes", "affects_vital_signs", "monitored_vital_signs",
}

# ---------------------------------------------------------------------------
# Record type -> model class mapping
# ---------------------------------------------------------------------------

_TYPE_CLASS_MAP: dict[str, type] = {
    "MedicationRecord": Medication,
    "ConditionRecord": Condition,
    "AllergyRecord": Allergy,
    "LabResultRecord": LabResult,
    "VitalSign": VitalSign,
    "ImmunizationRecord": Immunization,
    "ProcedureRecord": Procedure,
    "FamilyHistoryRecord": FamilyHistory,
    "CoverageRecord": Coverage,
    "InsurancePlan": Coverage,
    "PatientProfile": PatientProfile,
    "ActivitySnapshot": ActivitySnapshot,
    "SleepSnapshot": SleepSnapshot,
}

# ---------------------------------------------------------------------------
# Resolve type URI
# ---------------------------------------------------------------------------

def _resolve_type_uri(type_str: str) -> str | None:
    """Resolve a record type string (e.g. 'MedicationRecord') to a full RDF type URI."""
    for mapping in TYPE_MAPPING.values():
        rdf_type = mapping["rdf_type"]
        colon_idx = rdf_type.find(":")
        if colon_idx >= 0:
            ns_prefix = rdf_type[:colon_idx]
            local_name = rdf_type[colon_idx + 1:]
            if local_name == type_str:
                ns_uri = NAMESPACES.get(ns_prefix)
                if ns_uri:
                    return f"{ns_uri}{local_name}"
    return None

# ---------------------------------------------------------------------------
# rdflib-based parsing
# ---------------------------------------------------------------------------

def _parse_with_rdflib(turtle: str) -> list[dict[str, Any]]:
    """
    Parse Turtle content using rdflib and extract all typed subjects.

    Returns a list of dicts, one per unique subject, with an internal
    ``_rdf_type`` key set to the full RDF type URI.
    """
    try:
        import rdflib
        from rdflib import Graph, URIRef, Literal, BNode
        from rdflib.namespace import RDF, XSD
    except ImportError:
        raise ImportError(
            "rdflib is required for Turtle parsing. "
            "Install it with: pip install rdflib"
        )

    g = Graph()
    g.parse(data=turtle, format="turtle")

    RDF_TYPE = RDF.type
    CASCADE_NS = NAMESPACES["cascade"]

    # Group triples by subject
    subject_triples: dict[str, list[tuple[str, Any, str]]] = {}
    for s, p, o in g:
        subj_str = str(s)
        if isinstance(s, BNode):
            subj_str = f"_:{s}"
        subject_triples.setdefault(subj_str, [])
        subject_triples[subj_str].append((str(p), o, subj_str))

    results: list[dict[str, Any]] = []

    for subj_str, triples in subject_triples.items():
        # Find rdf:type
        rdf_type_uri: str | None = None
        for pred_uri, obj, _ in triples:
            if pred_uri == str(RDF_TYPE):
                rdf_type_uri = str(obj)
                break

        if rdf_type_uri is None:
            continue  # Skip subjects without a type

        # Check if it's a known Cascade type
        type_info = _REVERSE_TYPE_MAP.get(rdf_type_uri)
        if type_info is None:
            continue

        record_type, _ = type_info

        record: dict[str, Any] = {
            "id": subj_str,
            "type": record_type,
        }

        # Group by predicate (for repeated predicates -> arrays)
        pred_values: dict[str, list[Any]] = {}
        for pred_uri, obj, _ in triples:
            if pred_uri == str(RDF_TYPE):
                continue
            pred_values.setdefault(pred_uri, [])
            pred_values[pred_uri].append(obj)

        for pred_uri, objects in pred_values.items():
            py_key = _REVERSE_PREDICATE_MAP.get(pred_uri)
            if not py_key:
                continue

            # Array fields
            if py_key in _ARRAY_FIELDS:
                values: list[Any] = []
                for obj in objects:
                    if isinstance(obj, (rdflib.URIRef,)):
                        values.append(str(obj))
                    elif isinstance(obj, Literal):
                        values.append(str(obj))
                    elif hasattr(obj, "__iter__"):
                        # RDF collection
                        try:
                            for item in obj:
                                values.append(str(item))
                        except Exception:
                            values.append(str(obj))
                    else:
                        values.append(str(obj))
                record[py_key] = values
                continue

            # Single-value fields: use first object
            obj = objects[0]

            # dataProvenance: extract local name from cascade namespace
            if py_key == "data_provenance":
                obj_str = str(obj)
                if obj_str.startswith(CASCADE_NS):
                    record[py_key] = obj_str[len(CASCADE_NS):]
                else:
                    record[py_key] = obj_str
                continue

            # Boolean fields
            if py_key in _BOOLEAN_FIELDS:
                if isinstance(obj, Literal):
                    record[py_key] = str(obj).lower() == "true"
                else:
                    record[py_key] = str(obj).lower() == "true"
                continue

            # Integer fields
            if py_key in _INTEGER_FIELDS:
                try:
                    record[py_key] = int(str(obj))
                except (ValueError, TypeError):
                    record[py_key] = str(obj)
                continue

            # Float fields
            if py_key in _FLOAT_FIELDS:
                try:
                    record[py_key] = float(str(obj))
                except (ValueError, TypeError):
                    record[py_key] = str(obj)
                continue

            # Typed literals
            if isinstance(obj, Literal):
                if obj.datatype == XSD.integer:
                    try:
                        record[py_key] = int(str(obj))
                    except ValueError:
                        record[py_key] = str(obj)
                elif obj.datatype in (XSD.double, XSD.decimal, XSD.float):
                    try:
                        record[py_key] = float(str(obj))
                    except ValueError:
                        record[py_key] = str(obj)
                elif obj.datatype == XSD.boolean:
                    record[py_key] = str(obj).lower() == "true"
                else:
                    record[py_key] = str(obj)
                continue

            # URI reference
            if isinstance(obj, rdflib.URIRef):
                record[py_key] = str(obj)
                continue

            # Default
            record[py_key] = str(obj)

        results.append(record)

    return results


def _dict_to_record(data: dict[str, Any]) -> CascadeRecord | None:
    """Convert a parsed dict to the appropriate CascadeRecord subclass."""
    record_type = data.get("type", "")
    cls = _TYPE_CLASS_MAP.get(record_type)
    if cls is None:
        return None

    from dataclasses import fields as dc_fields
    valid_keys = {f.name for f in dc_fields(cls)}
    kwargs = {k: v for k, v in data.items() if k in valid_keys}
    return cls(**kwargs)  # type: ignore[call-arg]


def parse(turtle: str, record_type: str) -> list[CascadeRecord]:
    """
    Parse Turtle content and return typed records matching the specified type.

    Args:
        turtle: Turtle document content.
        record_type: Record type string (e.g., ``"MedicationRecord"``, ``"VitalSign"``).

    Returns:
        List of parsed records of the specified type.

    Raises:
        ValueError: If the record type is unknown.
        ImportError: If rdflib is not installed.

    Example:
        >>> meds = parse(turtle_string, "MedicationRecord")
    """
    type_uri = _resolve_type_uri(record_type)
    if type_uri is None:
        raise ValueError(f"Unknown record type: {record_type!r}")

    all_records = _parse_with_rdflib(turtle)
    matching = [r for r in all_records if r.get("type") == record_type]

    result: list[CascadeRecord] = []
    for data in matching:
        rec = _dict_to_record(data)
        if rec is not None:
            result.append(rec)
    return result


def parse_one(turtle: str, record_type: str) -> CascadeRecord | None:
    """
    Parse a single record from Turtle content.

    Returns the first record matching the specified type, or ``None`` if none found.

    Args:
        turtle: Turtle document content.
        record_type: Record type string.

    Returns:
        The parsed record, or None.
    """
    results = parse(turtle, record_type)
    return results[0] if results else None
