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

    snomed_code: list[str] | None = None
    """
    SNOMED CT code URIs for this procedure, one per coding.

    Multi-valued as of health v2.6 / clinical v1.14: FHIR R4
    CodeableConcept.coding is 0..*
    (https://hl7.org/fhir/R4/datatypes.html#CodeableConcept).

    Maps to ``health:snomedCode`` as one URI-object triple per value.
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


    has_encounter: str | None = None
    """
    IRI of the ``clinical:Encounter`` (visit context) this record occurred
    within. Maps to ``clinical:hasEncounter`` (clinical v1.10).

    FHIR alignment: the ``.encounter`` Reference(Encounter) element.
    """

    indication_reference: list[str] | None = None
    """
    IRIs of the conditions that are the clinical reason for this record: the
    traversable edge alongside the free-text ``clinical:indication`` and
    ``clinical:reasonForUse`` literals, which are retained.
    Maps to ``clinical:indicationReference`` (clinical v1.10, domain widened
    in v1.11 because FHIR carries reasonReference on Procedure and other event
    resources, not only medications).
    """

    parsed_indication_reference: list[str] | None = None
    """
    IRIs of conditions an importer DERIVED by parsing a coded or free-text
    reason on this record and matching it to a condition in the same pod.
    Maps to ``clinical:parsedIndicationReference`` (clinical v1.12), a
    subproperty of ``clinical:indicationReference``.

    Present these differently from ``indication_reference``: that one restates
    a reference the SOURCE carried, this one records a match that was
    computed, and a parsed match is only as good as the code or wording it
    matched on. It carries no confidence score by design: it is a
    deterministic parse of what the record already says, not an inference.
    """

    @classmethod
    def from_dataframe(cls, df: "pd.DataFrame") -> list["Procedure"]:  # type: ignore[name-defined]
        """Reconstruct a list of Procedure records from a pandas DataFrame."""
        from cascade_protocol.pandas_integration.dataframe import dataframe_to_records
        return dataframe_to_records(df, cls)  # type: ignore[return-value]
