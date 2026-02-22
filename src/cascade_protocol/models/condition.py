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

    icd10_code: str | None = None
    """
    ICD-10-CM code URI for this condition.
    Maps to ``health:icd10Code`` in Turtle serialization as a URI reference.
    """

    snomed_code: str | None = None
    """
    SNOMED CT code URI for this condition.
    Maps to ``health:snomedCode`` in Turtle serialization as a URI reference.
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

    @classmethod
    def from_dataframe(cls, df: "pd.DataFrame") -> list["Condition"]:  # type: ignore[name-defined]
        """Reconstruct a list of Condition records from a pandas DataFrame."""
        from cascade_protocol.pandas_integration.dataframe import dataframe_to_records
        return dataframe_to_records(df, cls)  # type: ignore[return-value]
