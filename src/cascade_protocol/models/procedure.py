"""
Procedure data model for the Cascade Protocol.

Represents a clinical procedure record.

RDF type: ``health:ProcedureRecord``
Vocabulary: https://ns.cascadeprotocol.org/health/v1#

See: https://cascadeprotocol.org/docs/cascade-protocol-schemas
"""

from __future__ import annotations

from dataclasses import dataclass, field

from cascade_protocol.models.common import CascadeRecord


@dataclass
class Procedure(CascadeRecord):
    """
    A procedure record in the Cascade Protocol.

    Required fields: ``procedure_name``, ``data_provenance``, ``schema_version``.
    All date fields use ISO 8601 string format.

    Serializes as ``health:ProcedureRecord`` in Turtle.
    """

    type: str = field(default="ProcedureRecord", init=True)

    procedure_name: str = ""
    """
    Name of the procedure.
    Maps to ``health:procedureName`` in Turtle serialization.
    """

    performed_date: str | None = None
    """
    Date and time the procedure was performed (ISO 8601).
    Maps to ``health:performedDate`` in Turtle serialization.
    """

    status: str | None = None
    """
    Current status of the procedure (completed, in-progress, not-done, preparation, stopped).
    Maps to ``health:status`` in Turtle serialization.
    """

    snomed_code: str | None = None
    """
    SNOMED CT code URI for this procedure.
    Maps to ``health:snomedCode`` in Turtle serialization as a URI reference.
    """

    performer: str | None = None
    """
    Name of the clinician who performed the procedure.
    Maps to ``health:performer`` in Turtle serialization.
    """

    location: str | None = None
    """
    Location where the procedure was performed.
    Maps to ``health:location`` in Turtle serialization.
    """

    @classmethod
    def from_dataframe(cls, df: "pd.DataFrame") -> list["Procedure"]:  # type: ignore[name-defined]
        """Reconstruct a list of Procedure records from a pandas DataFrame."""
        from cascade_protocol.pandas_integration.dataframe import dataframe_to_records
        return dataframe_to_records(df, cls)  # type: ignore[return-value]
