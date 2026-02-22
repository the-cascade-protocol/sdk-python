"""
Lab result data model for the Cascade Protocol.

Represents a laboratory test result, typically sourced from EHR imports.

RDF type: ``health:LabResultRecord``
Vocabulary: https://ns.cascadeprotocol.org/health/v1#

See: https://cascadeprotocol.org/docs/cascade-protocol-schemas
"""

from __future__ import annotations

from dataclasses import dataclass, field

from cascade_protocol.models.common import CascadeRecord


@dataclass
class LabResult(CascadeRecord):
    """
    A lab result record in the Cascade Protocol.

    Required fields: ``test_name``, ``data_provenance``, ``schema_version``.
    All date fields use ISO 8601 string format.

    Serializes as ``health:LabResultRecord`` in Turtle.
    """

    type: str = field(default="LabResultRecord", init=True)

    test_name: str = ""
    """
    Name of the laboratory test (e.g., ``"Hemoglobin A1c"``).
    Maps to ``health:testName`` in Turtle serialization.
    """

    result_value: str | None = None
    """
    Numeric or string result value (e.g., ``"7.2"``, ``"112"``).
    Maps to ``health:resultValue`` in Turtle serialization.
    """

    result_unit: str | None = None
    """
    Unit of the result value (e.g., ``"%"``, ``"mg/dL"``, ``"mEq/L"``).
    Maps to ``health:resultUnit`` in Turtle serialization.
    """

    reference_range: str | None = None
    """
    Reference range for normal values (e.g., ``"4.0 - 5.6"``, ``"< 100"``).
    Maps to ``health:referenceRange`` in Turtle serialization.
    """

    interpretation: str | None = None
    """
    Clinical interpretation of the result (normal, abnormal, critical, elevated, low).
    Maps to ``health:interpretation`` in Turtle serialization.
    """

    performed_date: str | None = None
    """
    Date and time the test was performed (ISO 8601).
    Maps to ``health:performedDate`` in Turtle serialization.
    """

    test_code: str | None = None
    """
    LOINC code URI for this test.
    Maps to ``health:testCode`` in Turtle serialization as a URI reference.
    """

    lab_category: str | None = None
    """
    Laboratory category (e.g., ``"Chemistry"``, ``"Hematology"``).
    Maps to ``health:labCategory`` in Turtle serialization.
    """

    specimen_type: str | None = None
    """
    Type of specimen collected (e.g., ``"Whole Blood"``, ``"Serum"``).
    Maps to ``health:specimenType`` in Turtle serialization.
    """

    reported_date: str | None = None
    """
    Date and time the result was reported (ISO 8601).
    Maps to ``health:reportedDate`` in Turtle serialization.
    """

    ordering_provider: str | None = None
    """
    Name of the clinician who ordered the test.
    Maps to ``health:orderingProvider`` in Turtle serialization.
    """

    performing_lab: str | None = None
    """
    Name of the laboratory that performed the test.
    Maps to ``health:performingLab`` in Turtle serialization.
    """

    @classmethod
    def from_dataframe(cls, df: "pd.DataFrame") -> list["LabResult"]:  # type: ignore[name-defined]
        """Reconstruct a list of LabResult records from a pandas DataFrame."""
        from cascade_protocol.pandas_integration.dataframe import dataframe_to_records
        return dataframe_to_records(df, cls)  # type: ignore[return-value]
