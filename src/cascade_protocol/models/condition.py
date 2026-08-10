"""
Condition data model for the Cascade Protocol.

Represents a clinical condition or diagnosis, sourced from EHR imports
or self-reported by the patient.

RDF type: ``health:ConditionRecord``
Vocabulary: https://ns.cascadeprotocol.org/health/v1#

See: https://cascadeprotocol.org/docs/cascade-protocol-schemas
"""

from __future__ import annotations

from dataclasses import dataclass, field

from cascade_protocol.models.common import CascadeRecord


@dataclass
class Condition(CascadeRecord):
    """
    A condition record in the Cascade Protocol.

    Required fields: ``condition_name``, ``status``, ``data_provenance``, ``schema_version``.
    All date fields use ISO 8601 string format.

    Serializes as ``health:ConditionRecord`` in Turtle.
    """

    type: str = field(default="ConditionRecord", init=True)

    condition_name: str = ""
    """
    Name of the condition or diagnosis.
    Maps to ``health:conditionName`` in Turtle serialization.
    """

    status: str = "active"
    """
    Clinical status of the condition (active, resolved, remission, inactive).
    Maps to ``health:status`` in Turtle serialization.
    """

    onset_date: str | None = None
    """
    Date of condition onset (ISO 8601).
    Maps to ``health:onsetDate`` in Turtle serialization.
    """

    icd10_code: list[str] | None = None
    """
    ICD-10-CM code URIs for this condition, one per coding the source carried.

    Multi-valued as of health v2.6 / clinical v1.14: FHIR R4
    CodeableConcept.coding is 0..*
    (https://hl7.org/fhir/R4/datatypes.html#CodeableConcept), and dual-coded
    problem-list entries are ordinary EHR output.

    Maps to ``health:icd10Code`` as one URI-object triple per value.
    """

    snomed_code: list[str] | None = None
    """
    SNOMED CT code URIs for this condition, one per coding the source carried.

    Multi-valued as of health v2.6 / clinical v1.14; see :attr:`icd10_code`.

    Maps to ``health:snomedCode`` as one URI-object triple per value.
    """

    condition_class: str | None = None
    """
    Clinical classification of the condition (e.g., ``"cardiovascular"``, ``"endocrine"``).
    Maps to ``health:conditionClass`` in Turtle serialization.
    """

    monitored_vital_signs: list[str] | None = None
    """
    List of vital sign types that should be monitored for this condition.
    Maps to ``health:monitoredVitalSigns`` as an RDF list in Turtle serialization.
    """

    has_encounter: str | None = None
    """
    IRI of the ``clinical:Encounter`` (visit context) this condition was
    recorded within. Maps to ``clinical:hasEncounter`` (clinical v1.10).
    """

    linked_condition: list[str] | None = None
    """
    IRIs of related conditions (e.g. a complication and its root condition).
    Maps to ``clinical:linkedCondition`` (clinical v1.10) as repeated IRI
    objects — a real, traversable RDF edge.
    """

    linked_condition_ids: str | None = None
    """
    DEPRECATED (clinical v1.10, ``owl:deprecated true``). Related-condition
    UUIDs packed into one space-separated literal, which no graph query can
    follow. Use ``linked_condition`` instead.

    Read support only: the property is registered so existing data carrying it
    is not silently dropped on parse. Nothing in this SDK writes it.
    Maps to ``clinical:linkedConditionIds``.
    """

    @classmethod
    def from_dataframe(cls, df: "pd.DataFrame") -> list["Condition"]:  # type: ignore[name-defined]
        """Reconstruct a list of Condition records from a pandas DataFrame."""
        from cascade_protocol.pandas_integration.dataframe import dataframe_to_records
        return dataframe_to_records(df, cls)  # type: ignore[return-value]
