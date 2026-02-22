"""
Allergy data model for the Cascade Protocol.

Represents an allergy or intolerance record, sourced from EHR imports
or self-reported by the patient.

RDF type: ``health:AllergyRecord``
Vocabulary: https://ns.cascadeprotocol.org/health/v1#

See: https://cascadeprotocol.org/docs/cascade-protocol-schemas
"""

from __future__ import annotations

from dataclasses import dataclass, field

from cascade_protocol.models.common import CascadeRecord


@dataclass
class Allergy(CascadeRecord):
    """
    An allergy record in the Cascade Protocol.

    Required fields: ``allergen``, ``data_provenance``, ``schema_version``.
    All date fields use ISO 8601 string format.

    Serializes as ``health:AllergyRecord`` in Turtle.
    """

    type: str = field(default="AllergyRecord", init=True)

    allergen: str = ""
    """
    Name of the allergen substance.
    Maps to ``health:allergen`` in Turtle serialization.
    """

    allergy_category: str | None = None
    """
    Category of the allergen (e.g., ``"medication"``, ``"food"``, ``"environmental"``).
    Maps to ``health:allergyCategory`` in Turtle serialization.
    """

    reaction: str | None = None
    """
    Description of the allergic reaction (e.g., ``"Hives (urticaria)"``).
    Maps to ``health:reaction`` in Turtle serialization.
    """

    allergy_severity: str | None = None
    """
    Severity of the allergic reaction (mild, moderate, severe, life-threatening).
    Maps to ``health:allergySeverity`` in Turtle serialization.
    """

    onset_date: str | None = None
    """
    Date of allergy onset (ISO 8601).
    Maps to ``health:onsetDate`` in Turtle serialization.
    """

    @classmethod
    def from_dataframe(cls, df: "pd.DataFrame") -> list["Allergy"]:  # type: ignore[name-defined]
        """Reconstruct a list of Allergy records from a pandas DataFrame."""
        from cascade_protocol.pandas_integration.dataframe import dataframe_to_records
        return dataframe_to_records(df, cls)  # type: ignore[return-value]
