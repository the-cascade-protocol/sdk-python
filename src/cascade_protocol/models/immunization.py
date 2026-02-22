"""
Immunization data model for the Cascade Protocol.

Represents a vaccine administration record, typically from EHR imports.

RDF type: ``health:ImmunizationRecord``
Vocabulary: https://ns.cascadeprotocol.org/health/v1#

See: https://cascadeprotocol.org/docs/cascade-protocol-schemas
"""

from __future__ import annotations

from dataclasses import dataclass, field

from cascade_protocol.models.common import CascadeRecord


@dataclass
class Immunization(CascadeRecord):
    """
    An immunization record in the Cascade Protocol.

    Required fields: ``vaccine_name``, ``data_provenance``, ``schema_version``.
    All date fields use ISO 8601 string format.

    Serializes as ``health:ImmunizationRecord`` in Turtle.
    """

    type: str = field(default="ImmunizationRecord", init=True)

    vaccine_name: str = ""
    """
    Name of the vaccine administered.
    Maps to ``health:vaccineName`` in Turtle serialization.
    """

    administration_date: str | None = None
    """
    Date and time of vaccine administration (ISO 8601).
    Maps to ``health:administrationDate`` in Turtle serialization.
    """

    status: str | None = None
    """
    Status of the immunization (completed, entered-in-error, not-done).
    Maps to ``health:status`` in Turtle serialization.
    """

    vaccine_code: str | None = None
    """
    Vaccine code identifier (e.g., ``"CVX-308"``).
    Maps to ``health:vaccineCode`` in Turtle serialization.
    """

    manufacturer: str | None = None
    """
    Vaccine manufacturer name.
    Maps to ``health:manufacturer`` in Turtle serialization.
    """

    lot_number: str | None = None
    """
    Lot number of the vaccine.
    Maps to ``health:lotNumber`` in Turtle serialization.
    """

    dose_quantity: str | None = None
    """
    Dose quantity administered (e.g., ``"0.3 mL"``).
    Maps to ``health:doseQuantity`` in Turtle serialization.
    """

    route: str | None = None
    """
    Route of administration (e.g., ``"intramuscular"``).
    Maps to ``health:route`` in Turtle serialization.
    """

    site: str | None = None
    """
    Anatomical site of administration (e.g., ``"Left deltoid"``).
    Maps to ``health:site`` in Turtle serialization.
    """

    administering_provider: str | None = None
    """
    Name of the healthcare provider who administered the vaccine.
    Maps to ``health:administeringProvider`` in Turtle serialization.
    """

    administering_location: str | None = None
    """
    Location where the vaccine was administered.
    Maps to ``health:administeringLocation`` in Turtle serialization.
    """

    @classmethod
    def from_dataframe(cls, df: "pd.DataFrame") -> list["Immunization"]:  # type: ignore[name-defined]
        """Reconstruct a list of Immunization records from a pandas DataFrame."""
        from cascade_protocol.pandas_integration.dataframe import dataframe_to_records
        return dataframe_to_records(df, cls)  # type: ignore[return-value]
