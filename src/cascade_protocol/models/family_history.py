"""
Family history data model for the Cascade Protocol.

Represents a family health history entry recording medical conditions
in the patient's relatives.

RDF type: ``health:FamilyHistoryRecord``
Vocabulary: https://ns.cascadeprotocol.org/health/v1#

See: https://cascadeprotocol.org/docs/cascade-protocol-schemas
"""

from __future__ import annotations

from dataclasses import dataclass, field

from cascade_protocol.models.common import CascadeRecord


@dataclass
class FamilyHistory(CascadeRecord):
    """
    A family history record in the Cascade Protocol.

    Required fields: ``relationship``, ``condition_name``, ``data_provenance``, ``schema_version``.

    Serializes as ``health:FamilyHistoryRecord`` in Turtle.
    """

    type: str = field(default="FamilyHistoryRecord", init=True)

    relationship: str = ""
    """
    Relationship of the family member to the patient (e.g., ``"mother"``, ``"father"``).
    Maps to ``health:relationship`` in Turtle serialization.
    Note: Uses ``clinical:relationship`` predicate shared with Coverage.
    """

    condition_name: str = ""
    """
    Name of the condition reported in the family member.
    Maps to ``health:conditionName`` in Turtle serialization.
    """

    onset_age: int | None = None
    """
    Age of onset for the family member's condition.
    Maps to ``health:onsetAge`` in Turtle serialization.
    """

    @classmethod
    def from_dataframe(cls, df: "pd.DataFrame") -> list["FamilyHistory"]:  # type: ignore[name-defined]
        """Reconstruct a list of FamilyHistory records from a pandas DataFrame."""
        from cascade_protocol.pandas_integration.dataframe import dataframe_to_records
        return dataframe_to_records(df, cls)  # type: ignore[return-value]
