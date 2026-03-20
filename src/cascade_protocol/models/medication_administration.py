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
    Maps to ``health:medicationName`` in Turtle serialization.
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

    snomed_code: str | None = None
    """
    SNOMED CT code URI for the medication concept.
    Maps to ``health:snomedCode`` in Turtle serialization.
    """

    @classmethod
    def from_dataframe(cls, df: "pd.DataFrame") -> list["MedicationAdministration"]:  # type: ignore[name-defined]
        """Reconstruct a list of MedicationAdministration records from a pandas DataFrame."""
        from cascade_protocol.pandas_integration.dataframe import dataframe_to_records
        return dataframe_to_records(df, cls)  # type: ignore[return-value]
