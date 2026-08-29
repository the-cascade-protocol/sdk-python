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
from cascade_protocol.models.wellness import (
    ActivitySnapshot,
    SleepSnapshot,
    DailyActivitySnapshot,
    DailySleepSnapshot,
    DailyVitalReading,
    ActivityData,
    SleepData,
    HeartRateData,
    BloodPressureData,
    HRVData,
    BodyMeasurements,
    WellnessContainer,
)
from cascade_protocol.models.export_manifest import (
    ExportManifest,
    RecordSummary,
    InteractionScenario,
    DeviceSource,
)
from cascade_protocol.models.attachment import Attachment
from cascade_protocol.models.encounter import Encounter, EncounterParticipant
from cascade_protocol.models.social_history import SocialHistoryRecord
from cascade_protocol.models.advisory import (
    AdvisoryApplicationActivity,
    AIGenerationActivity,
    ProxyAgent,
)
from cascade_protocol.vocabularies.namespaces import (
    NAMESPACES,
    TYPE_MAPPING,
    TYPE_TO_MAPPING_KEY,
    DEPRECATED_TYPE_ALIASES,
    READ_ONLY_TYPE_ALIASES,
    ADDITIONAL_PREDICATE_SPELLINGS,
    WELLNESS_HISTORY_PROPERTIES,
    build_reverse_predicate_map,
)

# ---------------------------------------------------------------------------
# Reverse mappings
# ---------------------------------------------------------------------------

# Predicates whose full URI does not fall out of PROPERTY_PREDICATES, because
# the same Python field is written under different namespaces by different
# classes. A reader has to accept every live spelling; only the writer gets to
# pick one.
# The table lives in the vocabularies module so the validator builds its
# reverse map from the same one.
_ADDITIONAL_REVERSE = ADDITIONAL_PREDICATE_SPELLINGS

_REVERSE_PREDICATE_MAP = build_reverse_predicate_map(_ADDITIONAL_REVERSE)

# Build reverse lookup: mapping_key -> record_type_string (from TYPE_TO_MAPPING_KEY)
_MAPPING_KEY_TO_RECORD_TYPE: dict[str, str] = {}
for _rt, _mk in TYPE_TO_MAPPING_KEY.items():
    _MAPPING_KEY_TO_RECORD_TYPE.setdefault(_mk, _rt)

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
                # Use the canonical record type string from TYPE_TO_MAPPING_KEY
                # (e.g. "MedicationRecord" for mapping_key "medications")
                # rather than the RDF local name (which may differ, e.g. "Medication").
                record_type_str = _MAPPING_KEY_TO_RECORD_TYPE.get(mapping_key, local_name)
                result[f"{ns_uri}{local_name}"] = (record_type_str, mapping_key)

    # clinical v1.13 deprecated spellings. Four clinical: classes carry
    # owl:deprecated true with rdfs:seeAlso pointing at the health: class this
    # SDK writes. They were NOT removed: the pod export path is still their
    # sole emitter and existing pods contain them, so a reader that ignored
    # them would silently return zero records for data that is right there in
    # the file. Both spellings resolve to the same record type.
    # Read-only spellings that are NOT deprecations: coverage:InsurancePlan is
    # current, is what the coverage fixtures and the other SDKs write, and
    # resolved to no known type here until it was registered -- so such a
    # subject was skipped in silence by every reader and by the validator.
    for deprecated, replacement in (
        list(DEPRECATED_TYPE_ALIASES.items()) + list(READ_ONLY_TYPE_ALIASES.items())
    ):
        dep_prefix, dep_local = deprecated.split(":", 1)
        rep_prefix, rep_local = replacement.split(":", 1)
        dep_uri = f"{NAMESPACES[dep_prefix]}{dep_local}"
        rep_uri = f"{NAMESPACES[rep_prefix]}{rep_local}"
        if rep_uri in result and dep_uri not in result:
            result[dep_uri] = result[rep_uri]
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
    "applied_triples_count",
    # -- health v2.5 / core v3.4 --
    "exercise_minutes", "stand_hours", "sample_count",
    # -- core v3.7 -- cascade:byteSize is xsd:integer with sh:minInclusive 0.
    "byte_size",
    # -- core v3.4 record summary counts --
    "condition_count", "medication_count", "allergy_count", "lab_result_count",
    "immunization_count", "coverage_count", "supplement_count",
    "vital_sign_days", "heart_rate_days", "blood_pressure_days",
    "activity_days", "sleep_days",
}

_FLOAT_FIELDS = {
    "value", "reference_range_low", "reference_range_high", "distance",
    "extraction_confidence", "generation_temperature",
    # -- health v2.5 --
    "active_energy_kcal", "duration_hours",
}

_ARRAY_FIELDS = {
    "drug_codes", "affects_vital_signs", "monitored_vital_signs",
    # -- clinical v1.10-1.12 graph edges --
    "indication_reference", "parsed_indication_reference", "linked_condition",
    # -- health v2.6 / clinical v1.14 multi-valued codes --
    # These lost sh:maxCount 1: FHIR R4 CodeableConcept.coding and
    # Observation.category are both 0..*. Reading only the first object of a
    # repeated predicate silently discarded every coding after the first,
    # which is the failure that is invisible in the output rather than loud.
    "icd10_code", "snomed_code", "test_code", "lab_category",
    # -- clinical v1.16 / core v3.7 --
    # Repeatable because the FHIR element behind each is 0..*. Reading only the
    # first object of a repeated predicate is the failure this release exists to
    # end, and it is invisible in the output rather than loud.
    "encounter_reason", "business_identifier", "participant_role_code",
    "document_author_name", "has_participant", "has_attachment",
}

# Multi-valued fields whose parsed values are SORTED before they reach the
# model. rdflib's store yields the objects of a repeated predicate in neither
# document nor insertion order, and the order varies between processes, so
# there is no original order to recover, only an arbitrary one to propagate.
# The affected properties are FHIR codings and categories, which are sets:
# sorting loses nothing and makes two parses of one document compare equal.
#
# The v1.10-1.12 graph edges above are deliberately NOT in this set. Their
# order is equally arbitrary, but they have shipped unsorted since v1.5.0 and
# changing them is not part of this vocabulary sync.
#
# The clinical v1.16 / core v3.7 fields below ARE sorted. They ship for the
# first time in this release, so there is no prior unsorted behaviour to
# preserve, and every one of them is a SET at source: Encounter.reasonCode,
# .identifier, Encounter.participant.type and Encounter.participant assert no
# order, so sorting loses nothing and makes two parses of one document compare
# equal.
#
# document_author_name is the one where order arguably carries meaning --
# clinical:providerName is written from the FIRST author where a source has
# several. It is sorted anyway, because repeated-predicate order is not
# recoverable from RDF in EITHER direction: rdflib yields the objects of a
# repeated predicate in neither document nor insertion order. An importer that
# needs the source's author order must carry it at import time; it cannot be
# recovered from the pod, sorted or not.
_SORTED_ARRAY_FIELDS = {
    "icd10_code", "snomed_code", "test_code", "lab_category",
    "encounter_reason", "business_identifier", "participant_role_code",
    "document_author_name", "has_participant", "has_attachment",
}

# Fields whose object is an IRI in the health: namespace carrying a bare local
# name (health:sleepQuality health:Good). Parsed back to the local name.
_HEALTH_IRI_ENUM_FIELDS = {"sleep_quality"}

# ---------------------------------------------------------------------------
# Record type -> model class mapping
# ---------------------------------------------------------------------------

# What a parsed subject can become. Most types are CascadeRecord subclasses;
# the two core v3.7 / clinical v1.16 sub-node classes are deliberately not
# (neither carries provenance or a schema version), so the reader's return type
# is a union rather than a narrowing lie.
ParsedNode = CascadeRecord | Attachment | EncounterParticipant

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
    "SocialHistoryRecord": SocialHistoryRecord,
    "AdvisoryApplicationActivity": AdvisoryApplicationActivity,
    "AIGenerationActivity": AIGenerationActivity,
    "ProxyAgent": ProxyAgent,
    # -- health v2.5 --
    "DailyActivitySnapshot": DailyActivitySnapshot,
    "DailySleepSnapshot": DailySleepSnapshot,
    "DailyVitalReading": DailyVitalReading,
    # -- clinical v1.16 --
    # Encounter was serializable but NOT registered here, so parse() returned an
    # empty list -- not an error -- for a type this SDK writes correctly. That
    # gap is why the nine encounter facts v1.16 adds had to be registered before
    # they could be verified: without it they would be write-only, and a
    # round-trip test would pass vacuously against zero records.
    #
    # This closes the gap for Encounter only. The other types CLAUDE.md lists
    # under "Deserializer registration" are untouched and still read as empty.
    "Encounter": Encounter,
    # -- core v3.7 / clinical v1.16 sub-nodes --
    # NOT CascadeRecord subclasses: neither carries provenance or a schema
    # version, and neither shape requires them. They are registered here anyway,
    # rather than being reached only through the dedicated readers below,
    # because the alternative is exactly the silent-empty-list defect above:
    # parse(turtle, "Attachment") would resolve the type, match nothing, and
    # return [] for data sitting in the file.
    "Attachment": Attachment,
    "EncounterParticipant": EncounterParticipant,
}

# Wellness container classes (health v2.5). Not in _TYPE_CLASS_MAP: they are
# not CascadeRecord subclasses and are read through parse_wellness_container(),
# which preserves the rdf:List order the generic subject-at-a-time path cannot.
_CONTAINER_CLASS_MAP: dict[str, type] = {
    "ActivityData": ActivityData,
    "SleepData": SleepData,
    "HeartRateData": HeartRateData,
    "BloodPressureData": BloodPressureData,
    "HRVData": HRVData,
    "BodyMeasurements": BodyMeasurements,
}

# ---------------------------------------------------------------------------
# Resolve type URI
# ---------------------------------------------------------------------------

def _resolve_type_uri(type_str: str) -> str | None:
    """Resolve a record type string (e.g. 'MedicationRecord') to a full RDF type URI."""
    # First try direct match via local name of rdf_type
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
    # Fallback: look up via TYPE_TO_MAPPING_KEY (handles cases where the
    # internal type string differs from the RDF local name, e.g.
    # "MedicationRecord" -> mapping_key "medications" -> rdf_type "clinical:Medication")
    mapping_key = TYPE_TO_MAPPING_KEY.get(type_str)
    if mapping_key:
        mapping = TYPE_MAPPING.get(mapping_key)
        if mapping:
            rdf_type = mapping["rdf_type"]
            colon_idx = rdf_type.find(":")
            if colon_idx >= 0:
                ns_prefix = rdf_type[:colon_idx]
                local_name = rdf_type[colon_idx + 1:]
                ns_uri = NAMESPACES.get(ns_prefix)
                if ns_uri:
                    return f"{ns_uri}{local_name}"
    return None

# ---------------------------------------------------------------------------
# rdflib-based parsing
# ---------------------------------------------------------------------------

def _parse_with_rdflib(turtle: str, graph: Any = None) -> list[dict[str, Any]]:
    """
    Parse Turtle content using rdflib and extract all typed subjects.

    Args:
        turtle: Turtle document content.
        graph: An already-parsed graph of the same document. Pass this when
            the caller also needs to walk the graph itself: blank node
            identifiers are only stable WITHIN one parse, so re-parsing the
            same text produces different ``_:`` labels and the two views
            cannot be joined.

    Returns a list of dicts, one per unique subject.
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

    if graph is None:
        g = Graph()
        g.parse(data=turtle, format="turtle")
    else:
        g = graph

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
                record[py_key] = sorted(values) if py_key in _SORTED_ARRAY_FIELDS else values
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

            # trigger: cascade:trigger is a GenerationTrigger object property —
            # the value is a cascade: URI; extract the local name (mirrors the
            # serializer, which emits cascade:<value>).
            if py_key == "trigger":
                obj_str = str(obj)
                if obj_str.startswith(CASCADE_NS):
                    record[py_key] = obj_str[len(CASCADE_NS):]
                else:
                    record[py_key] = obj_str
                continue

            # health: IRI enums (health:sleepQuality health:Good) — strip the
            # namespace back to the bare local name the model holds.
            if py_key in _HEALTH_IRI_ENUM_FIELDS:
                obj_str = str(obj)
                health_ns = NAMESPACES["health"]
                if obj_str.startswith(health_ns):
                    record[py_key] = obj_str[len(health_ns):]
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


def _dict_to_record(data: dict[str, Any]) -> ParsedNode | None:
    """Convert a parsed dict to the model class registered for its type."""
    record_type = data.get("type", "")
    cls = _TYPE_CLASS_MAP.get(record_type)
    if cls is None:
        return None

    from dataclasses import fields as dc_fields
    valid_keys = {f.name for f in dc_fields(cls)}
    kwargs = {k: v for k, v in data.items() if k in valid_keys}
    return cls(**kwargs)  # type: ignore[call-arg]


def parse(turtle: str, record_type: str) -> list[ParsedNode]:
    """
    Parse Turtle content and return typed records matching the specified type.

    Args:
        turtle: Turtle document content.
        record_type: Record type string (e.g., ``"MedicationRecord"``, ``"VitalSign"``).

    Returns:
        List of parsed records of the specified type. Almost always
        ``CascadeRecord`` subclasses; ``"Attachment"`` and
        ``"EncounterParticipant"`` return the two sub-node classes, which are
        deliberately not records. Use :func:`parse_attachments` or
        :func:`parse_encounter_participants` when you want those narrowed.

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

    result: list[ParsedNode] = []
    for data in matching:
        rec = _dict_to_record(data)
        if rec is not None:
            result.append(rec)
    return result


def parse_one(turtle: str, record_type: str) -> ParsedNode | None:
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


# ---------------------------------------------------------------------------
# Sub-nodes reached by edge (core v3.7 / clinical v1.16)
# ---------------------------------------------------------------------------
#
# cascade:Attachment and clinical:EncounterParticipant are structural sub-nodes:
# each is reached by an IRI edge from the record it belongs to
# (cascade:hasAttachment, clinical:hasParticipant) and neither stands alone as a
# health record. parse() reaches both through _TYPE_CLASS_MAP; these two
# functions are the precisely-typed accessors, and exist so a caller resolving
# an edge does not have to narrow a list it knows contains neither.


def parse_attachments(turtle: str) -> list[Attachment]:
    """
    Parse every ``cascade:Attachment`` node in a document (core v3.7).

    Use this to resolve the IRIs a record carries on
    :attr:`~cascade_protocol.models.common.CascadeRecord.has_attachment`. The
    attachment nodes may live in the same file or a different one -- the edge
    shape requires an IRI object precisely so that they can be separated -- so
    the caller supplies whichever document actually holds them.

    Args:
        turtle: Turtle document content.

    Returns:
        Every attachment node in the document, in no guaranteed order.
    """
    return [
        rec for rec in (
            _dict_to_record(data)
            for data in _parse_with_rdflib(turtle)
            if data.get("type") == "Attachment"
        )
        if isinstance(rec, Attachment)
    ]


def parse_encounter_participants(turtle: str) -> list[EncounterParticipant]:
    """
    Parse every ``clinical:EncounterParticipant`` node in a document
    (clinical v1.16).

    Use this to resolve the IRIs an encounter carries on
    :attr:`~cascade_protocol.models.encounter.Encounter.has_participant`.

    Args:
        turtle: Turtle document content.

    Returns:
        Every participation node in the document, in no guaranteed order.
    """
    return [
        rec for rec in (
            _dict_to_record(data)
            for data in _parse_with_rdflib(turtle)
            if data.get("type") == "EncounterParticipant"
        )
        if isinstance(rec, EncounterParticipant)
    ]


# ---------------------------------------------------------------------------
# Wellness containers (health v2.5)
# ---------------------------------------------------------------------------

def parse_wellness_container(turtle: str, container_type: str) -> list[WellnessContainer]:
    """
    Parse wellness container subjects and their ORDERED history entries.

    The history properties are rdf:Lists and the entries are a time series, so
    order is part of the data. :func:`parse` returns entries in whatever order
    the triple store yields subjects, which is not the file order; this
    function walks the list and preserves it.

    Args:
        turtle: Turtle document content.
        container_type: One of ``"ActivityData"``, ``"SleepData"``,
            ``"HeartRateData"``, ``"BloodPressureData"``, ``"HRVData"``,
            ``"BodyMeasurements"``.

    Returns:
        A list of container objects, each with ``history`` in document order.

    Raises:
        ValueError: If the container type is unknown.
    """
    cls = _CONTAINER_CLASS_MAP.get(container_type)
    if cls is None:
        raise ValueError(
            f"Unknown wellness container type: {container_type!r}. "
            f"Valid types: {sorted(_CONTAINER_CLASS_MAP)}"
        )

    import rdflib
    from rdflib import Graph, BNode
    from rdflib.namespace import RDF

    g = Graph()
    g.parse(data=turtle, format="turtle")

    # Index every parseable record by its subject string so list entries can be
    # resolved without re-walking the graph per entry. The SAME graph is passed
    # through: blank node labels are only stable within one parse, and history
    # entries are blank nodes, so re-parsing would produce a lookup table whose
    # keys can never match the list items and a silently empty history.
    by_id: dict[str, dict[str, Any]] = {}
    for rec in _parse_with_rdflib(turtle, graph=g):
        by_id[str(rec["id"])] = rec

    container_uri = _resolve_type_uri(container_type)
    if container_uri is None:  # pragma: no cover - guarded by _CONTAINER_CLASS_MAP
        raise ValueError(f"Unknown wellness container type: {container_type!r}")

    history_props = WELLNESS_HISTORY_PROPERTIES.get(container_type, [])
    containers: list[WellnessContainer] = []

    for subj in g.subjects(RDF.type, rdflib.URIRef(container_uri)):
        history: list[CascadeRecord] = []
        for pred_shorthand, _entry_type in history_props:
            ns_prefix, local = pred_shorthand.split(":", 1)
            pred = rdflib.URIRef(f"{NAMESPACES[ns_prefix]}{local}")
            for list_node in g.objects(subj, pred):
                for item in g.items(list_node):
                    key = f"_:{item}" if isinstance(item, BNode) else str(item)
                    data = by_id.get(key)
                    if data is None:
                        continue
                    rec = _dict_to_record(data)
                    if rec is not None:
                        history.append(rec)
        containers.append(cls(id=str(subj), history=history))  # type: ignore[call-arg]

    return containers


# ---------------------------------------------------------------------------
# Pod export manifest (core v3.4)
# ---------------------------------------------------------------------------

# Sentinel base for resolving a manifest's relative IRIs. Must be hierarchical:
# a manifest carries pod-relative resource references (<clinical/medications.ttl>)
# and a urn: base cannot resolve those. ".invalid" is the RFC 2606 reserved TLD,
# guaranteed never to resolve, so this can never be mistaken for a real host.
# Both the manifest subject and the relative resource IRIs are stripped back to
# their document-relative form on the way out.
_MANIFEST_BASE = "https://pod.invalid/"


def _strip_manifest_base(iri: str) -> str:
    """Return a manifest IRI in the document-relative form the file carries."""
    if iri.startswith(_MANIFEST_BASE):
        return iri[len(_MANIFEST_BASE):]
    return iri


def parse_export_manifest(turtle: str) -> ExportManifest | None:
    """
    Parse a pod ``manifest.ttl`` into an :class:`ExportManifest`.

    Returns the first ``cascade:ExportManifest`` subject in the document, or
    ``None`` if the document carries none.

    Note on timestamps: rdflib normalizes typed ``xsd:dateTime`` literals on
    parse (``2026-02-19T00:00:00Z`` reads back as
    ``2026-02-19T00:00:00+00:00``). The two denote the same instant and this
    applies to every dateTime this SDK parses, not just manifests, but a
    caller comparing timestamp STRINGS across a write/read cycle should
    compare them as instants instead.

    Args:
        turtle: Turtle content of a pod manifest.

    Returns:
        The parsed manifest, or None.
    """
    import rdflib
    from rdflib import Graph, BNode, Literal
    from rdflib.namespace import RDF

    # A pod manifest's subject is the empty relative IRI <>, meaning "this
    # document". rdflib resolves it against the document base, and with no
    # base supplied that is a machine- and cwd-dependent file: URI, so the same
    # manifest would parse to a different subject on every host. Pin the base
    # to a fixed sentinel and normalise it back to "" below.
    g = Graph()
    g.parse(data=turtle, format="turtle", publicID=_MANIFEST_BASE)

    CASCADE = NAMESPACES["cascade"]
    DCTERMS = NAMESPACES["dcterms"]
    PROV = NAMESPACES["prov"]

    def uri(ns: str, local: str) -> "rdflib.URIRef":
        return rdflib.URIRef(f"{ns}{local}")

    def literal(subj: Any, ns: str, local: str) -> str | None:
        val = g.value(subj, uri(ns, local))
        return None if val is None else str(val)

    def integer(subj: Any, local: str) -> int | None:
        val = g.value(subj, uri(CASCADE, local))
        if val is None:
            return None
        try:
            return int(str(val))
        except (TypeError, ValueError):
            return None

    def local_name(node: Any, ns: str) -> str:
        text = str(node)
        return text[len(ns):] if text.startswith(ns) else text

    def read_summary(node: Any) -> RecordSummary:
        provenance = g.value(node, uri(CASCADE, "dataProvenance"))
        return RecordSummary(
            domain=literal(node, CASCADE, "domain") or "",
            condition_count=integer(node, "conditionCount"),
            medication_count=integer(node, "medicationCount"),
            allergy_count=integer(node, "allergyCount"),
            lab_result_count=integer(node, "labResultCount"),
            immunization_count=integer(node, "immunizationCount"),
            coverage_count=integer(node, "coverageCount"),
            supplement_count=integer(node, "supplementCount"),
            vital_sign_days=integer(node, "vitalSignDays"),
            heart_rate_days=integer(node, "heartRateDays"),
            blood_pressure_days=integer(node, "bloodPressureDays"),
            activity_days=integer(node, "activityDays"),
            sleep_days=integer(node, "sleepDays"),
            data_provenance=None if provenance is None else local_name(provenance, CASCADE),
            # cascade:notes, not health:notes.
            notes=literal(node, CASCADE, "notes"),
        )

    subjects = list(g.subjects(RDF.type, uri(CASCADE, "ExportManifest")))
    if not subjects:
        return None
    subj = subjects[0]

    manifest = ExportManifest(
        id="" if str(subj) == _MANIFEST_BASE else str(subj),
        title=literal(subj, DCTERMS, "title") or "",
        description=literal(subj, DCTERMS, "description"),
        created=literal(subj, DCTERMS, "created"),
        creator=literal(subj, DCTERMS, "creator"),
        schema_version=literal(subj, CASCADE, "schemaVersion"),
        patient_profile_version=literal(subj, CASCADE, "patientProfileVersion"),
    )

    layers_node = g.value(subj, uri(CASCADE, "provenanceLayers"))
    if layers_node is not None:
        manifest.provenance_layers = [
            local_name(item, CASCADE) for item in g.items(layers_node)
        ]

    clinical_node = g.value(subj, uri(CASCADE, "clinicalSummary"))
    if clinical_node is not None:
        manifest.clinical_summary = read_summary(clinical_node)
    wellness_node = g.value(subj, uri(CASCADE, "wellnessSummary"))
    if wellness_node is not None:
        manifest.wellness_summary = read_summary(wellness_node)

    devices_node = g.value(subj, uri(CASCADE, "deviceSources"))
    if devices_node is not None:
        for item in g.items(devices_node):
            manifest.device_sources.append(
                DeviceSource(
                    label=literal(item, PROV, "label") or "",
                    source_type=literal(item, CASCADE, "sourceType"),
                    data_types=literal(item, CASCADE, "dataTypes"),
                )
            )

    scenarios_node = g.value(subj, uri(CASCADE, "interactionScenarios"))
    if scenarios_node is not None:
        for item in g.items(scenarios_node):
            resources_node = g.value(item, uri(CASCADE, "involvedResources"))
            resources = (
                [_strip_manifest_base(str(r)) for r in g.items(resources_node)]
                if resources_node is not None
                else []
            )
            flag = g.value(item, uri(CASCADE, "requiresCrossProvenance"))
            manifest.interaction_scenarios.append(
                InteractionScenario(
                    title=literal(item, DCTERMS, "title") or "",
                    description=literal(item, DCTERMS, "description"),
                    involved_resources=resources,
                    severity=literal(item, CASCADE, "severity"),
                    requires_cross_provenance=(
                        None if flag is None else str(flag).lower() == "true"
                    ),
                )
            )

    return manifest
