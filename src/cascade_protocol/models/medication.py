"""
Medication data model for the Cascade Protocol.

Represents a medication record with fields sourced from EHR imports,
FHIR MedicationRequest/MedicationStatement resources, or self-reported data.

RDF type: ``clinical:Medication``
Vocabulary: https://ns.cascadeprotocol.org/clinical/v1#

See: https://cascadeprotocol.org/docs/cascade-protocol-schemas
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from cascade_protocol.models.common import CascadeRecord


@dataclass
class Medication(CascadeRecord):
    """
    A medication record in the Cascade Protocol.

    Required fields: ``medication_name``, ``is_active``, ``data_provenance``, ``schema_version``.
    All date fields use ISO 8601 string format.

    Serializes as ``clinical:Medication`` in Turtle.
    """

    type: str = field(default="MedicationRecord", init=True)

    medication_name: str = ""
    """
    Name of the medication.
    Maps to ``clinical:drugName`` in Turtle serialization.
    """

    is_active: bool = True
    """
    Whether the medication is currently active.
    Maps to ``clinical:status`` in Turtle serialization.
    """

    dose: str | None = None
    """
    Prescribed dose (e.g., ``"20 mg"``, ``"90 mcg/actuation"``).
    Maps to ``clinical:dosage`` in Turtle serialization.
    """

    frequency: str | None = None
    """
    Dosing frequency (e.g., ``"once daily"``, ``"twice daily"``, ``"as needed"``).
    Maps to ``health:frequency`` in Turtle serialization.
    """

    route: str | None = None
    """
    Route of administration (e.g., ``"oral"``, ``"inhalation"``).
    Maps to ``health:route`` in Turtle serialization.
    """

    prescriber: str | None = None
    """
    Name of the prescribing clinician.
    Maps to ``health:prescriber`` in Turtle serialization.
    """

    start_date: str | None = None
    """
    Date when the medication was started (ISO 8601).
    Maps to ``health:startDate`` in Turtle serialization.
    """

    end_date: str | None = None
    """
    Date when the medication was discontinued (ISO 8601).
    Maps to ``health:endDate`` in Turtle serialization.
    """

    rx_norm_code: str | None = None
    """
    RxNorm concept URI for this medication.
    Maps to ``clinical:rxNormCode`` in Turtle serialization as a URI reference.
    """

    drug_codes: list[str] | None = None
    """
    Array of drug code URIs from multiple coding systems (RxNorm, SNOMED CT, etc.).
    Maps to ``clinical:drugCode`` in Turtle serialization (repeated predicate).
    """

    provenance_class: str | None = None
    """
    Provenance class indicating the import mechanism.
    Maps to ``clinical:provenanceClass`` in Turtle serialization.
    """

    source_fhir_resource_type: str | None = None
    """
    The FHIR resource type from which this record was sourced.
    Maps to ``clinical:sourceFhirResourceType`` in Turtle serialization.
    """

    clinical_intent: str | None = None
    """
    Clinical intent for this medication.
    Maps to ``clinical:clinicalIntent`` in Turtle serialization.
    """

    indication: str | None = None
    """
    Clinical indication for prescribing this medication.
    Maps to ``clinical:indication`` in Turtle serialization.
    """

    course_of_therapy_type: str | None = None
    """
    Course of therapy type.
    Maps to ``clinical:courseOfTherapyType`` in Turtle serialization.
    """

    as_needed: bool | None = None
    """
    Whether this medication is taken on an as-needed (PRN) basis.
    Maps to ``clinical:asNeeded`` in Turtle serialization.
    """

    medication_form: str | None = None
    """
    Physical form of the medication (e.g., ``"tablet"``, ``"inhaler"``).
    Maps to ``clinical:medicationForm`` in Turtle serialization.
    """

    active_ingredient: str | None = None
    """
    Active pharmaceutical ingredient.
    Maps to ``clinical:activeIngredient`` in Turtle serialization.
    """

    ingredient_strength: str | None = None
    """
    Strength of the active ingredient (e.g., ``"1000 mg"``).
    Maps to ``clinical:ingredientStrength`` in Turtle serialization.
    """

    refills_allowed: int | None = None
    """
    Number of refills allowed on the prescription.
    Maps to ``clinical:refillsAllowed`` in Turtle serialization.
    """

    supply_duration_days: int | None = None
    """
    Number of days of medication supply per fill.
    Maps to ``clinical:supplyDurationDays`` in Turtle serialization.
    """

    prescription_category: str | None = None
    """
    Prescription category (e.g., ``"community"``, ``"inpatient"``).
    Maps to ``clinical:prescriptionCategory`` in Turtle serialization.
    """

    medication_class: str | None = None
    """
    Therapeutic class of the medication (e.g., ``"bronchodilator"``).
    Maps to ``health:medicationClass`` in Turtle serialization.
    """

    affects_vital_signs: list[str] | None = None
    """
    List of vital sign types that this medication may affect.
    Maps to ``health:affectsVitalSigns`` as an RDF list in Turtle serialization.
    """

    @classmethod
    def from_dataframe(cls, df: "pd.DataFrame") -> list["Medication"]:  # type: ignore[name-defined]
        """Reconstruct a list of Medication records from a pandas DataFrame."""
        from cascade_protocol.pandas_integration.dataframe import dataframe_to_records
        return dataframe_to_records(df, cls)  # type: ignore[return-value]
