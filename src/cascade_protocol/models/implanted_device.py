"""
ImplantedDevice data model for the Cascade Protocol.

Represents a medical device implanted in or attached to the patient as a
permanent part of their health profile (e.g., pacemaker, cardiac stent,
cochlear implant, insulin pump). Presence affects medication safety,
imaging eligibility (MRI contraindications), and surgical risk.

RDF type: ``clinical:ImplantedDevice``
Vocabulary: https://ns.cascadeprotocol.org/clinical/v1#

See: https://cascadeprotocol.org/docs/cascade-protocol-schemas
"""

from __future__ import annotations

from dataclasses import dataclass, field

from cascade_protocol.models.common import CascadeRecord


@dataclass
class ImplantedDevice(CascadeRecord):
    """
    An implanted device record in the Cascade Protocol.

    Required fields: ``device_type``, ``data_provenance``, ``schema_version``.

    Serializes as ``clinical:ImplantedDevice`` in Turtle.
    """

    type: str = field(default="ImplantedDevice", init=True)

    device_type: str = ""
    """
    Device category (e.g., "pacemaker", "stent", "cochlear-implant").
    Maps to ``clinical:deviceType`` in Turtle serialization.
    """

    implant_date: str | None = None
    """
    Date the device was implanted (ISO 8601).
    Maps to ``clinical:implantDate`` in Turtle serialization.
    """

    device_manufacturer: str | None = None
    """
    Device manufacturer name.
    Maps to ``clinical:deviceManufacturer`` in Turtle serialization.
    """

    udi_carrier: str | None = None
    """
    Unique Device Identifier (UDI) carrier string.
    Maps to ``clinical:udiCarrier`` in Turtle serialization.
    """

    device_status: str | None = None
    """
    Device status: active, inactive, entered-in-error.
    Maps to ``clinical:deviceStatus`` in Turtle serialization.
    """

    @classmethod
    def from_dataframe(cls, df: "pd.DataFrame") -> list["ImplantedDevice"]:  # type: ignore[name-defined]
        """Reconstruct a list of ImplantedDevice records from a pandas DataFrame."""
        from cascade_protocol.pandas_integration.dataframe import dataframe_to_records
        return dataframe_to_records(df, cls)  # type: ignore[return-value]
