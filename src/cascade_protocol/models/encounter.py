"""
Encounter data model for the Cascade Protocol.

Represents a clinical encounter (office visit, consultation, procedure
appointment, etc.) sourced from EHR imports.

RDF type: ``clinical:Encounter``
Vocabulary: https://ns.cascadeprotocol.org/clinical/v1#

See: https://cascadeprotocol.org/docs/cascade-protocol-schemas
"""

from __future__ import annotations

from dataclasses import dataclass, field

from cascade_protocol.models.common import CascadeRecord


@dataclass
class Encounter(CascadeRecord):
    """
    A clinical encounter record in the Cascade Protocol.

    Required fields: ``encounter_type``, ``data_provenance``, ``schema_version``.
    All date fields use ISO 8601 string format.

    Serializes as ``clinical:Encounter`` in Turtle.
    """

    type: str = field(default="Encounter", init=True)

    encounter_type: str = ""
    """
    Human-readable description of the encounter type.
    Maps to ``clinical:encounterType`` in Turtle serialization.
    """

    encounter_class: str | None = None
    """
    Encounter class per HL7 ActCode (e.g., "AMB", "IMP", "EMER").
    Maps to ``clinical:encounterClass`` in Turtle serialization.
    """

    encounter_status: str | None = None
    """
    Status: finished, in-progress, cancelled.
    Maps to ``clinical:encounterStatus`` in Turtle serialization.
    """

    encounter_start: str | None = None
    """
    Date and time the encounter started (ISO 8601).
    Maps to ``clinical:encounterStart`` in Turtle serialization.
    """

    encounter_end: str | None = None
    """
    Date and time the encounter ended (ISO 8601).
    Maps to ``clinical:encounterEnd`` in Turtle serialization.
    """

    provider_name: str | None = None
    """
    Name and specialty of the provider who conducted the encounter.
    Maps to ``clinical:providerName`` in Turtle serialization.
    """

    facility_name: str | None = None
    """
    Name of the facility where the encounter occurred.
    Maps to ``clinical:facilityName`` in Turtle serialization.
    """

    snomed_code: str | None = None
    """
    SNOMED CT code URI for the encounter type.
    Maps to ``health:snomedCode`` in Turtle serialization.
    """

    @classmethod
    def from_dataframe(cls, df: "pd.DataFrame") -> list["Encounter"]:  # type: ignore[name-defined]
        """Reconstruct a list of Encounter records from a pandas DataFrame."""
        from cascade_protocol.pandas_integration.dataframe import dataframe_to_records
        return dataframe_to_records(df, cls)  # type: ignore[return-value]
