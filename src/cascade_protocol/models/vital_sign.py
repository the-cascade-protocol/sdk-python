"""
Vital sign data model for the Cascade Protocol.

Represents a single vital sign measurement from clinical encounters
or device-generated readings.

RDF type: ``clinical:VitalSign``
Vocabulary: https://ns.cascadeprotocol.org/clinical/v1#

See: https://cascadeprotocol.org/docs/cascade-protocol-schemas
"""

from __future__ import annotations

from dataclasses import dataclass, field

from cascade_protocol.models.common import CascadeRecord


@dataclass
class VitalSign(CascadeRecord):
    """
    A vital sign record in the Cascade Protocol.

    Required fields: ``vital_type``, ``value``, ``unit``, ``data_provenance``, ``schema_version``.
    All date fields use ISO 8601 string format.

    Serializes as ``clinical:VitalSign`` in Turtle.
    """

    type: str = field(default="VitalSign", init=True)

    vital_type: str = ""
    """
    Enumerated vital sign type identifier.
    Maps to ``clinical:vitalType`` in Turtle serialization.
    """

    vital_type_name: str | None = None
    """
    Human-readable name for the vital sign type (e.g., ``"Systolic Blood Pressure"``).
    Maps to ``clinical:vitalTypeName`` in Turtle serialization.
    """

    value: float = 0.0
    """
    Numeric value of the measurement.
    Maps to ``clinical:value`` in Turtle serialization.
    """

    unit: str = ""
    """
    Unit of measurement (e.g., ``"mmHg"``, ``"bpm"``, ``"degF"``, ``"%"``).
    Maps to ``clinical:unit`` in Turtle serialization.
    """

    effective_date: str | None = None
    """
    Date and time when the measurement was taken (ISO 8601).
    Maps to ``clinical:effectiveDate`` in Turtle serialization.
    """

    loinc_code: str | None = None
    """
    LOINC code URI for this vital sign type.
    Maps to ``clinical:loincCode`` in Turtle serialization as a URI reference.
    """

    snomed_code: str | None = None
    """
    SNOMED CT code URI for this vital sign type.
    Maps to ``clinical:snomedCode`` in Turtle serialization as a URI reference.
    Note: VitalSign uses the clinical: namespace for snomedCode.
    """

    reference_range_low: float | None = None
    """
    Lower bound of the normal reference range.
    Maps to ``clinical:referenceRangeLow`` in Turtle serialization.
    """

    reference_range_high: float | None = None
    """
    Upper bound of the normal reference range.
    Maps to ``clinical:referenceRangeHigh`` in Turtle serialization.
    """

    interpretation: str | None = None
    """
    Clinical interpretation of the vital sign value (normal, elevated, low, critical).
    Maps to ``clinical:interpretation`` in Turtle serialization.
    Note: VitalSign uses the clinical: namespace for interpretation.
    """

    @classmethod
    def from_dataframe(cls, df: "pd.DataFrame") -> list["VitalSign"]:  # type: ignore[name-defined]
        """Reconstruct a list of VitalSign records from a pandas DataFrame."""
        from cascade_protocol.pandas_integration.dataframe import dataframe_to_records
        return dataframe_to_records(df, cls)  # type: ignore[return-value]
