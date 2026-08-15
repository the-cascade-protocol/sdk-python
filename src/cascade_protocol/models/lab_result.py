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
    Clinical interpretation of the result, from the HL7 v3
    ObservationInterpretation code system (e.g. ``"H"``, ``"LL"``, ``"POS"``,
    ``"S"``), the data-absent-reason code ``"unknown"``, or one of the ten
    words retained from health v2.5. Single-valued: health v2.6 widened the
    value set but kept ``sh:maxCount 1``.

    The 60 accepted values are
    :data:`~cascade_protocol.models.common.OBSERVATION_INTERPRETATION_CODES`;
    :data:`~cascade_protocol.models.common.LabInterpretation` is the matching
    type alias. Note that ``"elevated"``, which this SDK named through v1.5.0,
    is NOT among them and never was accepted by any Cascade shape.

    Maps to ``health:interpretation`` in Turtle serialization.
    """


    interpretation_source_code: str | None = None
    """
    The interpretation code the SOURCE wrote, copied verbatim, for the case
    where that code is a member of neither value set ``interpretation`` is
    bound to (health v2.7).

    Deliberately unconstrained in its VALUE: a value set or a pattern here
    would recreate exactly the loss the property exists to prevent. It is
    single-valued, because the interpretation it explains is single-valued and
    two source codes on one interpretation is a merge artefact.

    A producer that recognises the source code's intent should ALSO write its
    best ratified equivalent on ``interpretation``, so a consumer reading only
    the bound property still gets a usable reading. The pair
    ``interpretation="H"``, ``interpretation_source_code="elevated"`` says: the
    source said "elevated", and the nearest ratified code is H (High).

    Maps to ``health:interpretationSourceCode`` in Turtle serialization.
    """
    performed_date: str | None = None
    """
    Date and time the test was performed (ISO 8601).
    Maps to ``health:performedDate`` in Turtle serialization.
    """

    test_code: list[str] | None = None
    """
    LOINC code URIs for this test, one per coding the source carried.

    Multi-valued as of health v2.6: FHIR R4 CodeableConcept.coding is 0..*
    (https://hl7.org/fhir/R4/datatypes.html#CodeableConcept) and an
    Observation.code routinely carries more than one LOINC coding for the same
    test. Bare codes are expanded against LOINC on serialization.

    ``None`` means the property is absent, which is not the same as a record
    that carries an empty list; both serialize to no triples, and ``None`` is
    what a record that never had the field reads back as.

    Maps to ``health:testCode`` as one URI-object triple per value.
    """

    lab_category: list[str] | None = None
    """
    Laboratory categories (e.g., ``["Chemistry"]``, ``["Chemistry", "Point of Care"]``).

    Multi-valued as of health v2.6: FHIR R4 Observation.category is 0..*
    (https://hl7.org/fhir/R4/observation-definitions.html#Observation.category)
    and real exports categorise one result several ways at once.

    Maps to ``health:labCategory`` as one string-literal triple per value.
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


    has_encounter: str | None = None
    """
    IRI of the ``clinical:Encounter`` (visit context) this record occurred
    within. Maps to ``clinical:hasEncounter`` (clinical v1.10).

    FHIR alignment: the ``.encounter`` Reference(Encounter) element.
    """

    @classmethod
    def from_dataframe(cls, df: "pd.DataFrame") -> list["LabResult"]:  # type: ignore[name-defined]
        """Reconstruct a list of LabResult records from a pandas DataFrame."""
        from cascade_protocol.pandas_integration.dataframe import dataframe_to_records
        return dataframe_to_records(df, cls)  # type: ignore[return-value]
