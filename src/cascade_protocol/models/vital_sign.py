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

    snomed_code: list[str] | None = None
    """
    SNOMED CT code URIs for this vital sign type, one per coding.

    Multi-valued as of clinical v1.14: FHIR R4 CodeableConcept.coding is 0..*
    (https://hl7.org/fhir/R4/datatypes.html#CodeableConcept).

    Maps to ``clinical:snomedCode`` as one URI-object triple per value.
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
    Clinical interpretation of the value, from the HL7 v3
    ObservationInterpretation code system (e.g. ``"H"``, ``"HH"``, ``"N"``),
    the data-absent-reason code ``"unknown"``, or one of the ten words retained
    from clinical v1.13. Single-valued: clinical v1.14 widened the value set
    but kept ``sh:maxCount 1``.

    The 60 accepted values are
    :data:`~cascade_protocol.models.common.OBSERVATION_INTERPRETATION_CODES`;
    :data:`~cascade_protocol.models.common.VitalInterpretation` is the matching
    type alias. ``clinical:interpretation`` and ``health:interpretation`` carry
    identical value sets. Note that ``"elevated"``, which this SDK named
    through v1.5.0, is NOT among them and never was accepted by any Cascade
    shape.

    Maps to ``clinical:interpretation`` in Turtle serialization.
    Note: VitalSign uses the clinical: namespace for interpretation.
    """

    interpretation_source_code: str | None = None
    """
    The interpretation code the SOURCE wrote, copied verbatim, for the case
    where that code is a member of neither value set ``interpretation`` is
    bound to (clinical v1.15).

    Deliberately unconstrained in its VALUE: a value set or a pattern here
    would recreate exactly the loss the property exists to prevent. It is
    single-valued, because the interpretation it explains is single-valued and
    two source codes on one interpretation is a merge artefact.

    A producer that recognises the source code's intent should ALSO write its
    best ratified equivalent on ``interpretation``, so a consumer reading only
    the bound property still gets a usable reading. The pair
    ``interpretation="H"``, ``interpretation_source_code="elevated"`` says: the
    source said "elevated", and the nearest ratified code is H (High).

    Maps to ``clinical:interpretationSourceCode`` in Turtle serialization.
    """

    @classmethod
    def from_dataframe(cls, df: "pd.DataFrame") -> list["VitalSign"]:  # type: ignore[name-defined]
        """Reconstruct a list of VitalSign records from a pandas DataFrame."""
        from cascade_protocol.pandas_integration.dataframe import dataframe_to_records
        return dataframe_to_records(df, cls)  # type: ignore[return-value]
