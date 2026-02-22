"""
Cascade Protocol vocabulary constants.

Exports namespace URIs, type mappings, and property predicates used
in RDF/Turtle serialization.
"""

from cascade_protocol.vocabularies.namespaces import (
    NAMESPACES,
    TYPE_MAPPING,
    TYPE_TO_MAPPING_KEY,
    PROPERTY_PREDICATES,
    CURRENT_SCHEMA_VERSION,
    build_reverse_predicate_map,
)

__all__ = [
    "NAMESPACES",
    "TYPE_MAPPING",
    "TYPE_TO_MAPPING_KEY",
    "PROPERTY_PREDICATES",
    "CURRENT_SCHEMA_VERSION",
    "build_reverse_predicate_map",
]
