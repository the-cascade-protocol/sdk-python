"""
MedicationAdministration data model for the Cascade Protocol.

Represents a single administration event of a medication given at a specific
time by a provider (e.g., IV antibiotics pre-surgery, vaccine injection at
visit). Semantically distinct from Medication (ongoing regimens): this
represents a one-time event, not an ongoing regimen.

RDF type: ``clinical:MedicationAdministration``
Vocabulary: https://ns.cascadeprotocol.org/clinical/v1#

See: https://cascadeprotocol.org/docs/cascade-protocol-schemas
"""

from __future__ import annotations

from dataclasses import dataclass, field

from cascade_protocol.models.common import CascadeRecord


@dataclass
class MedicationAdministration(CascadeRecord):
    """
    A medication administration event in the Cascade Protocol.

    Required fields: ``medication_name``, ``data_provenance``, ``schema_version``.

    Serializes as ``clinical:MedicationAdministration`` in Turtle.
    """

    type: str = field(default="MedicationAdministration", init=True)

    medication_name: str = ""
    """
    Name of the medication administered.
    Maps to ``clinical:drugName`` in Turtle serialization.
    """

    administered_date: str | None = None
    """
    Date and time of administration (ISO 8601).
    Maps to ``clinical:administeredDate`` in Turtle serialization.
    """

    administered_dose: str | None = None
    """
    Dose administered (e.g., "1g", "500mg").
    Maps to ``clinical:administeredDose`` in Turtle serialization.
    """

    administered_route: str | None = None
    """
    Route of administration: oral, IV, IM, subcutaneous, topical.
    Maps to ``clinical:administeredRoute`` in Turtle serialization.
    """

    administration_status: str | None = None
    """
    Administration status: completed, not-done, in-progress.
    Maps to ``clinical:administrationStatus`` in Turtle serialization.
    """

    snomed_code: list[str] | None = None
    """
    SNOMED CT code URIs for the medication concept, one per coding.

    Multi-valued as of clinical v1.14: FHIR R4 CodeableConcept.coding is 0..*
    (https://hl7.org/fhir/R4/datatypes.html#CodeableConcept).

    Maps to ``health:snomedCode`` as one URI-object triple per value.
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
    def from_dataframe(cls, df: "pd.DataFrame") -> list["MedicationAdministration"]:  # type: ignore[name-defined]
        """Reconstruct a list of MedicationAdministration records from a pandas DataFrame."""
        from cascade_protocol.pandas_integration.dataframe import dataframe_to_records
        return dataframe_to_records(df, cls)  # type: ignore[return-value]
