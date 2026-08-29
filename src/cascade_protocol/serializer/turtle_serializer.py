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
from cascade_protocol.models.wellness import (
    ActivitySnapshot,
    SleepSnapshot,
    DailyActivitySnapshot,
    DailySleepSnapshot,
    DailyVitalReading,
)
from cascade_protocol.models.export_manifest import (
    ExportManifest,
    RecordSummary,
    InteractionScenario,
    DeviceSource,
)
from cascade_protocol.models.attachment import Attachment
from cascade_protocol.models.encounter import EncounterParticipant
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
        # health v2.7 / clinical v1.15: the escape hatch follows the property
        # it explains into the clinical: namespace on a vital sign.
        "interpretation_source_code": "clinical:interpretationSourceCode",
    },
    # Camel variants
    "_camel_VitalSign": {
        "snomedCode": "clinical:snomedCode",
        "interpretation": "clinical:interpretation",
        "interpretationSourceCode": "clinical:interpretationSourceCode",
    },
    # -- health v2.5 daily entries --------------------------------------------
    # The daily snapshots carry their timestamp on cascade:date, not the
    # health:date the aggregate snapshots use. Both spellings are live; the
    # entry type decides which one is written.
    "DailyActivitySnapshot": {"date": "cascade:date"},
    "_camel_DailyActivitySnapshot": {"date": "cascade:date"},
    "DailySleepSnapshot": {"date": "cascade:date"},
    "_camel_DailySleepSnapshot": {"date": "cascade:date"},
    # DailyVitalReading writes health:date / health:value / health:unit (the
    # spelling health:DailyVitalReadingShape accepts through its sh:or), with
    # the reading-level cascade: terms for sample count and LOINC reference.
    "DailyVitalReading": {
        "date": "health:date",
        "value": "health:value",
        "unit": "health:unit",
        "loinc_code": "cascade:loincCode",
    },
    "_camel_DailyVitalReading": {
        "date": "health:date",
        "value": "health:value",
        "unit": "health:unit",
        "loincCode": "cascade:loincCode",
    },
    # -- core v3.4 record summary ---------------------------------------------
    # cascade:notes, not health:notes: the manifest spelling is the core one.
    "RecordSummary": {"notes": "cascade:notes"},
    "_camel_RecordSummary": {"notes": "cascade:notes"},
    # -- coverage v1.5 --------------------------------------------------------
    # "status" is bound to health:status globally (a Condition's clinical
    # status). On a coverage record the same field name carries a DIFFERENT
    # FHIR element -- Coverage.status, a modifier element bound REQUIRED to
    # fm-status -- so the predicate is overridden per record type rather than
    # the field being renamed. Both accepted type spellings are listed: the
    # Coverage dataclass defaults to "InsurancePlan", but "CoverageRecord" is a
    # live spelling in TYPE_TO_MAPPING_KEY and a caller may set it.
    "InsurancePlan": {"status": "coverage:status"},
    "_camel_InsurancePlan": {"status": "coverage:status"},
    "CoverageRecord": {"status": "coverage:status"},
    "_camel_CoverageRecord": {"status": "coverage:status"},
}

# Fields whose values should be serialized as URI references (angle-bracket enclosed)
# rather than string literals, when the value looks like a full URI.
_URI_FIELDS_SNAKE: set[str] = {
    "rx_norm_code",
    "icd10_code",
    "snomed_code",
    "loinc_code",
    "test_code",
    # clinical v1.10: the record-to-encounter edge is an IRI reference.
    "has_encounter",
}

_URI_FIELDS_CAMEL: set[str] = {
    "rxNormCode",
    "icd10Code",
    "snomedCode",
    "loincCode",
    "testCode",
    "hasEncounter",
}

# Coded fields that are 0..* as of health v2.6 / clinical v1.14, carrying an
# IRI object per value. FHIR R4 CodeableConcept.coding is 0..*
# (https://hl7.org/fhir/R4/datatypes.html#CodeableConcept), so one record can
# state the same concept in several code systems, or the same code system
# twice.
#
# Kept separate from _ARRAY_FIELDS below because the two shapes of "array"
# serialize differently and the difference is not cosmetic: _ARRAY_FIELDS
# writes an rdf:List when the members are not IRIs, and a collection node is a
# single blank-node object. A property whose shape asserts sh:datatype on each
# value would fail against one. These write REPEATED PREDICATES, which is what
# a 0..* property with no ordering means in RDF.
#
# A scalar is still accepted on every one of these keys. The camelCase entry
# point takes external JSON (conformance fixture inputs, TypeScript-SDK
# output), all of which predates the cardinality change, and widening the model
# must not make that input unserializable.
_MULTI_VALUE_URI_FIELDS_SNAKE: set[str] = {
    "icd10_code",
    "snomed_code",
    "test_code",
}

_MULTI_VALUE_URI_FIELDS_CAMEL: set[str] = {
    "icd10Code",
    "snomedCode",
    "testCode",
}

# The same, for fields whose values are plain string literals rather than IRIs.
# FHIR R4 Observation.category is 0..*
# (https://hl7.org/fhir/R4/observation-definitions.html#Observation.category).
#
# clinical v1.16 adds four more repeatable string properties, each because the
# FHIR element behind it is 0..* and a single-valued predicate was discarding
# everything after the first:
#   encounter_reason        Encounter.reasonCode
#   business_identifier     .identifier, on every FHIR resource
#   participant_role_code   Encounter.participant.type (extensibly bound)
#   document_author_name    DocumentReference.author
_MULTI_VALUE_LITERAL_FIELDS_SNAKE: set[str] = {
    "lab_category",
    "encounter_reason",
    "business_identifier",
    "participant_role_code",
    "document_author_name",
}
_MULTI_VALUE_LITERAL_FIELDS_CAMEL: set[str] = {
    "labCategory",
    "encounterReason",
    "businessIdentifier",
    "participantRoleCode",
    "documentAuthorName",
}

# Fields whose values are arrays and should be serialized as repeated predicates
# (for URI arrays) or RDF lists (for string arrays).
_ARRAY_FIELDS_SNAKE: set[str] = {
    "drug_codes",
    "affects_vital_signs",
    "monitored_vital_signs",
    # clinical v1.10-1.12 graph edges: repeated IRI objects, not RDF lists.
    "indication_reference",
    "parsed_indication_reference",
    "linked_condition",
    # clinical v1.16 / core v3.7 sub-node edges. Same shape as the edges above:
    # repeated IRI objects. Both point at a node that lives in its own subject
    # block, and for hasAttachment the IRI is mandatory --
    # cascade:HasAttachmentEdgeShape asserts sh:nodeKind sh:IRI so the record
    # and the attachment can live in different files.
    "has_participant",
    "has_attachment",
}

_ARRAY_FIELDS_CAMEL: set[str] = {
    "drugCodes",
    "affectsVitalSigns",
    "monitoredVitalSigns",
    "indicationReference",
    "parsedIndicationReference",
    "linkedCondition",
    "hasParticipant",
    "hasAttachment",
}

# Fields that are date-only typed (xsd:date).
_DATE_ONLY_FIELDS_SNAKE: set[str] = {"date_of_birth"}
_DATE_ONLY_FIELDS_CAMEL: set[str] = {"dateOfBirth"}

# date field from activity/sleep (plain string, no datatype).
_NO_DATATYPE_DATE_FIELDS_SNAKE: set[str] = {"date"}
_NO_DATATYPE_DATE_FIELDS_CAMEL: set[str] = {"date"}

# Per-type escapes from the rule above. The 7-day aggregate snapshots carry a
# plain ISO date string, but the health v2.5 single-day entries carry a full
# xsd:dateTime that their shapes assert (sh:datatype xsd:dateTime on
# cascade:date / health:date). Same field name, different classes, different
# datatype — so the exception is keyed on the record type.
_TYPE_DATETIME_FIELDS: dict[str, set[str]] = {
    "DailyActivitySnapshot": {"date"},
    "DailySleepSnapshot": {"date"},
    "DailyVitalReading": {"date"},
}

# Fields that are dateTime typed (xsd:dateTime).
_EXPLICIT_DATETIME_FIELDS_SNAKE: set[str] = {
    "effective_period_start",
    "effective_period_end",
    "effective_start",
    "effective_end",
    # core v3.4: dcterms:created on an export manifest is xsd:dateTime
    # (cascade:ExportManifestShape asserts it). The name contains neither
    # "date" nor "time", so the heuristic would miss it.
    "created",
}
_EXPLICIT_DATETIME_FIELDS_CAMEL: set[str] = {
    "effectivePeriodStart",
    "effectivePeriodEnd",
    "effectiveStart",
    "effectiveEnd",
    "created",
}

# Fields that are typed as xsd:integer (not just plain numeric).
_INTEGER_TYPED_FIELDS_SNAKE: set[str] = {
    "computed_age",
    "refills_allowed",
    "supply_duration_days",
    "onset_age",
    "applied_triples_count",
}
_INTEGER_TYPED_FIELDS_CAMEL: set[str] = {
    "computedAge",
    "refillsAllowed",
    "supplyDurationDays",
    "onsetAge",
    "appliedTriplesCount",
}

# Fields whose SHACL shape asserts sh:datatype xsd:decimal. These MUST be
# written with an explicit ^^xsd:decimal: a whole-numbered float would
# otherwise emit as a bare Turtle integer, which is xsd:integer and violates
# the shape. health:DailyActivitySnapshotShape and DailySleepSnapshotShape
# both assert xsd:decimal on these.
_DECIMAL_TYPED_FIELDS_SNAKE: set[str] = {
    "active_energy_kcal",
    "duration_hours",
}
_DECIMAL_TYPED_FIELDS_CAMEL: set[str] = {
    "activeEnergyKcal",
    "durationHours",
}

# Fields whose SHACL shape declares xsd:anyURI. clinical:encounterClassSystem's
# rdfs:range is xsd:anyURI, and its property shape is an sh:or over anyURI and
# string "because serializers differ on which of the two they write for a
# URI-valued literal". This one writes the declared range: it is a code-system
# URI, and the conformance fixture carries it typed.
#
# A LITERAL, not an angle-bracket IRI. The value is the object of a
# DatatypeProperty, so emitting <...> would make it a resource reference and
# violate the shape's datatype constraint on both branches of the sh:or.
_ANYURI_TYPED_FIELDS_SNAKE: set[str] = {"encounter_class_system"}
_ANYURI_TYPED_FIELDS_CAMEL: set[str] = {"encounterClassSystem"}

# Fields whose value is a bare local name that must be emitted as an IRI in
# the health: namespace. health:sleepQuality is written ``health:Good`` by
# every known emitter and parsed as such by every known deserializer, even
# though health.ttl still declares the property xsd:string-ranged;
# health:DailySleepSnapshotShape asserts no sh:datatype for that reason and
# constrains the four permitted individuals instead.
_HEALTH_IRI_ENUM_FIELDS: set[str] = {"sleep_quality", "sleepQuality"}

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


# Code-system namespace for each coded URI field. Cascade emitters normally
# write the full IRI, but a bare code is also carried (health v2.5 daily
# readings do it for cascade:loincCode), and emitting <8867-4> would produce a
# relative IRI that resolves against the document base — a different resource
# on every host. Expanding against the field's own code system is the only
# reading that is stable.
_CODE_SYSTEM_FOR_FIELD: dict[str, str] = {
    "loinc_code": "loinc",
    "loincCode": "loinc",
    "test_code": "loinc",
    "testCode": "loinc",
    "snomed_code": "sct",
    "snomedCode": "sct",
    "icd10_code": "icd10",
    "icd10Code": "icd10",
    "rx_norm_code": "rxnorm",
    "rxNormCode": "rxnorm",
}


def _expand_code_uri(key: str, value: str) -> str:
    """Expand a bare code to a full IRI using the field's code system."""
    if value.startswith("http") or value.startswith("urn:"):
        return value
    prefix = _CODE_SYSTEM_FOR_FIELD.get(key)
    if prefix is None:
        return value
    return f"{NAMESPACES[prefix]}{value}"


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
    multi_uri_fields = (
        _MULTI_VALUE_URI_FIELDS_CAMEL if camel else _MULTI_VALUE_URI_FIELDS_SNAKE
    )
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
            _add_prefix_for_uri(_expand_code_uri(key, value), prefixes)

        # A multi-valued coded field declares the same prefixes as its scalar
        # form, once per value. Missing this would emit the values correctly
        # and lose the code-system prefix declaration for a record that
        # carries only list-shaped codes.
        if isinstance(value, list) and key in multi_uri_fields:
            for item in value:
                if isinstance(item, str):
                    _add_prefix_for_uri(_expand_code_uri(key, item), prefixes)

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
    multi_uri_fields = (
        _MULTI_VALUE_URI_FIELDS_CAMEL if camel else _MULTI_VALUE_URI_FIELDS_SNAKE
    )
    multi_literal_fields = (
        _MULTI_VALUE_LITERAL_FIELDS_CAMEL if camel else _MULTI_VALUE_LITERAL_FIELDS_SNAKE
    )
    integer_typed = _INTEGER_TYPED_FIELDS_CAMEL if camel else _INTEGER_TYPED_FIELDS_SNAKE
    decimal_typed = _DECIMAL_TYPED_FIELDS_CAMEL if camel else _DECIMAL_TYPED_FIELDS_SNAKE
    anyuri_typed = _ANYURI_TYPED_FIELDS_CAMEL if camel else _ANYURI_TYPED_FIELDS_SNAKE
    type_datetime = _TYPE_DATETIME_FIELDS.get(record_type, set())
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

        # trigger: cascade:trigger is an ObjectProperty whose range is the
        # cascade:GenerationTrigger enumeration — emit the value as a cascade:
        # prefixed URI (e.g. cascade:InitialGeneration), not a string literal.
        if key == "trigger":
            triple_lines.append(f"    {pred} cascade:{value}")
            return

        # health:sleepQuality takes an IRI object (health:Good), not a string
        # literal. Emitting the string form would produce data no known Cascade
        # deserializer reads and would fail the shape's sh:in over the four
        # health: individuals.
        if key in _HEALTH_IRI_ENUM_FIELDS and isinstance(value, str):
            triple_lines.append(f"    {pred} health:{value}")
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

        # Decimal typed fields (xsd:decimal). Explicit, because a bare Turtle
        # numeric for a whole-numbered value is xsd:integer, which the shape
        # rejects.
        if key in decimal_typed and isinstance(value, (int, float)) and not isinstance(value, bool):
            triple_lines.append(f'    {pred} "{float(value)}"^^xsd:decimal')
            return

        # Numeric
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if isinstance(value, float) and not value.is_integer():
                triple_lines.append(f"    {pred} {value}")
            else:
                triple_lines.append(f"    {pred} {int(value)}")
            return

        # Multi-valued coded fields (health v2.6 / clinical v1.14). One triple
        # per value, in the order the caller supplied: the RDF is a set, so no
        # order is asserted, and re-ordering the caller's list would discard
        # the only ordering information there is without gaining anything.
        # Checked before the scalar branches so that the scalar spelling of
        # the same key keeps working underneath.
        if key in multi_uri_fields and isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    triple_lines.append(f"    {pred} <{_expand_code_uri(key, item)}>")
            return

        if key in multi_literal_fields and isinstance(value, list):
            for item in value:
                triple_lines.append(f'    {pred} "{_escape_turtle_string(str(item))}"')
            return

        # URI fields
        if key in uri_fields and isinstance(value, str):
            triple_lines.append(f"    {pred} <{_expand_code_uri(key, value)}>")
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

        # xsd:anyURI-typed literals (clinical v1.16 encounterClassSystem).
        if isinstance(value, str) and key in anyuri_typed:
            triple_lines.append(f'    {pred} "{_escape_turtle_string(value)}"^^xsd:anyURI')
            return

        # Date-only fields (xsd:date)
        if isinstance(value, str) and _is_date_only_field(key, camel):
            triple_lines.append(f'    {pred} "{_escape_turtle_string(value)}"^^xsd:date')
            return

        # DateTime fields carried on a type that overrides the plain-string
        # default for that field name (health v2.5 daily entries).
        if isinstance(value, str) and key in type_datetime:
            triple_lines.append(f'    {pred} "{_escape_turtle_string(value)}"^^xsd:dateTime')
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


def serialize_daily_activity_snapshot(snapshot: DailyActivitySnapshot) -> str:
    """Serialize a DailyActivitySnapshot record to Turtle (health v2.5)."""
    return serialize(snapshot)


def serialize_daily_sleep_snapshot(snapshot: DailySleepSnapshot) -> str:
    """Serialize a DailySleepSnapshot record to Turtle (health v2.5)."""
    return serialize(snapshot)


def serialize_daily_vital_reading(reading: DailyVitalReading) -> str:
    """Serialize a DailyVitalReading record to Turtle (health v2.5)."""
    return serialize(reading)


def serialize_attachment(attachment: Attachment) -> str:
    """
    Serialize an :class:`Attachment` metadata node to Turtle (core v3.7).

    Written as its own subject block rather than inline, because
    ``cascade:HasAttachmentEdgeShape`` requires the object of
    ``cascade:hasAttachment`` to be an IRI so that the record and the
    attachment can live in different files.
    """
    return _serialize_dataclass(attachment)  # type: ignore[arg-type]


def serialize_encounter_participant(participant: EncounterParticipant) -> str:
    """
    Serialize an :class:`EncounterParticipant` node to Turtle (clinical v1.16).

    A participation is a structural sub-node of an encounter, reached by
    ``clinical:hasParticipant``. It is written as its own subject block for the
    reason given on the class: one treatment for both v3.7/v1.16 sub-node
    classes, and ``Attachment``'s edge shape leaves no choice for that one.
    """
    return _serialize_dataclass(participant)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Pod export manifest (core v3.4)
# ---------------------------------------------------------------------------

_MANIFEST_PREFIXES: list[tuple[str, str]] = [
    ("cascade", NAMESPACES["cascade"]),
    ("prov", NAMESPACES["prov"]),
    ("dcterms", NAMESPACES["dcterms"]),
    ("xsd", NAMESPACES["xsd"]),
]

# Order in which RecordSummary counts are written. Fixed so two manifests with
# the same content serialize identically.
_SUMMARY_COUNT_ORDER: list[tuple[str, str]] = [
    ("condition_count", "cascade:conditionCount"),
    ("medication_count", "cascade:medicationCount"),
    ("allergy_count", "cascade:allergyCount"),
    ("lab_result_count", "cascade:labResultCount"),
    ("immunization_count", "cascade:immunizationCount"),
    ("coverage_count", "cascade:coverageCount"),
    ("supplement_count", "cascade:supplementCount"),
    ("vital_sign_days", "cascade:vitalSignDays"),
    ("heart_rate_days", "cascade:heartRateDays"),
    ("blood_pressure_days", "cascade:bloodPressureDays"),
    ("activity_days", "cascade:activityDays"),
    ("sleep_days", "cascade:sleepDays"),
]


def _summary_block(summary: RecordSummary, indent: str) -> str:
    """Render a RecordSummary as an inline blank node."""
    lines = [f"{indent}a cascade:RecordSummary"]
    lines.append(f'{indent}cascade:domain "{_escape_turtle_string(summary.domain)}"')
    for attr, pred in _SUMMARY_COUNT_ORDER:
        val = getattr(summary, attr)
        if val is None:
            continue
        lines.append(f'{indent}{pred} "{int(val)}"^^xsd:integer')
    if summary.data_provenance:
        lines.append(f"{indent}cascade:dataProvenance cascade:{summary.data_provenance}")
    if summary.notes:
        # cascade:notes, not health:notes — the manifest spelling is the core one.
        lines.append(f'{indent}cascade:notes "{_escape_turtle_string(summary.notes)}"')
    return " ;\n".join(lines)


def serialize_export_manifest(manifest: ExportManifest) -> str:
    """
    Serialize a pod :class:`ExportManifest` to Turtle (core v3.4).

    The manifest is structurally unlike a flat record — nested blank nodes and
    rdf:Lists throughout — so it has its own writer rather than being forced
    through the generic record path.

    An empty ``manifest.id`` serializes as ``<>``, the empty relative IRI
    meaning "this document", which is what a pod's ``manifest.ttl`` carries.

    Args:
        manifest: The manifest to serialize.

    Returns:
        A complete Turtle document string.
    """
    writer = _TurtleWriter()
    for name, uri in _MANIFEST_PREFIXES:
        writer.prefix(name, uri)
    writer.blank_line()

    subject = f"<{manifest.id}>"
    lines: list[str] = ["    a cascade:ExportManifest"]

    if manifest.title:
        lines.append(f'    dcterms:title "{_escape_turtle_string(manifest.title)}"')
    if manifest.description:
        lines.append(f'    dcterms:description "{_escape_turtle_string(manifest.description)}"')
    if manifest.created:
        lines.append(f'    dcterms:created "{_escape_turtle_string(manifest.created)}"^^xsd:dateTime')
    if manifest.creator:
        lines.append(f'    dcterms:creator "{_escape_turtle_string(manifest.creator)}"')
    if manifest.schema_version:
        lines.append(f'    cascade:schemaVersion "{_escape_turtle_string(manifest.schema_version)}"')
    if manifest.patient_profile_version:
        lines.append(
            f'    cascade:patientProfileVersion "{_escape_turtle_string(manifest.patient_profile_version)}"'
        )

    if manifest.provenance_layers:
        # An rdf:List of cascade: provenance IRIs, not string literals.
        items = " ".join(f"cascade:{layer}" for layer in manifest.provenance_layers)
        lines.append(f"    cascade:provenanceLayers ( {items} )")

    if manifest.clinical_summary is not None:
        block = _summary_block(manifest.clinical_summary, "        ")
        lines.append(f"    cascade:clinicalSummary [\n{block}\n    ]")
    if manifest.wellness_summary is not None:
        block = _summary_block(manifest.wellness_summary, "        ")
        lines.append(f"    cascade:wellnessSummary [\n{block}\n    ]")

    if manifest.device_sources:
        entries = []
        for device in manifest.device_sources:
            parts = ["a prov:Agent", f'prov:label "{_escape_turtle_string(device.label)}"']
            if device.source_type:
                parts.append(f'cascade:sourceType "{_escape_turtle_string(device.source_type)}"')
            if device.data_types:
                parts.append(f'cascade:dataTypes "{_escape_turtle_string(device.data_types)}"')
            entries.append("        [ " + " ; ".join(parts) + " ]")
        joined = "\n".join(entries)
        lines.append(f"    cascade:deviceSources (\n{joined}\n    )")

    if manifest.interaction_scenarios:
        entries = []
        for scenario in manifest.interaction_scenarios:
            inner = ["            a cascade:InteractionScenario"]
            inner.append(f'            dcterms:title "{_escape_turtle_string(scenario.title)}"')
            if scenario.description:
                inner.append(
                    f'            dcterms:description "{_escape_turtle_string(scenario.description)}"'
                )
            resources = " ".join(f"<{r}>" for r in scenario.involved_resources)
            inner.append(f"            cascade:involvedResources ( {resources} )")
            if scenario.severity:
                inner.append(f'            cascade:severity "{_escape_turtle_string(scenario.severity)}"')
            if scenario.requires_cross_provenance is not None:
                flag = "true" if scenario.requires_cross_provenance else "false"
                inner.append(f"            cascade:requiresCrossProvenance {flag}")
            entries.append("        [\n" + " ;\n".join(inner) + "\n        ]")
        joined = "\n".join(entries)
        lines.append(f"    cascade:interactionScenarios (\n{joined}\n    )")

    writer.raw(f"{subject} " + " ;\n".join(lines) + " .")
    return writer.build()
