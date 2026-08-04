"""
Pod export manifest models for the Cascade Protocol (core v3.4).

Every pod export carries a ``manifest.ttl`` describing when it was generated,
which schema versions it uses, how many records of each kind it contains, and
which provenance layers are represented. Consumers should read it before
processing individual resources.

RDF types:
- ``cascade:ExportManifest``      (rdfs:subClassOf dcat:Dataset)
- ``cascade:RecordSummary``       (rdfs:subClassOf void:Dataset)
- ``cascade:InteractionScenario`` (deliberately Cascade-specific)

Modelling, and why:

``cascade:ExportManifest`` is a ``dcat:Dataset``. A pod export is a published
dataset with a title, description, creation date and publisher; DCAT 3 is a
W3C Recommendation that standardises exactly that, so the descriptive fields
below map to ``dcterms:`` predicates rather than to Cascade-specific
inventions. https://www.w3.org/TR/vocab-dcat-3/

``cascade:RecordSummary`` is a ``void:Dataset``. A record summary is a
statistical description of a subset of a dataset: how many instances of each
class it holds. Each entity count is ``rdfs:subPropertyOf void:entities`` and
names the ``void:class`` it counts, so a VoID-aware consumer reads Cascade
counts with no Cascade-specific code. The day counts are deliberately NOT
entity counts: a 30-day heart rate history holds far more than 30 readings.
See ``RECORD_SUMMARY_COUNT_CLASSES`` in the namespaces module.
https://www.w3.org/TR/void/

``cascade:InteractionScenario`` is novel on purpose. It describes a clinically
significant interaction detectable only by correlating resources of differing
provenance (an EHR-prescribed drug against a self-reported supplement against
a lab value). No ratified vocabulary models cross-provenance correlation as a
first-class thing, so it stays Cascade-specific rather than being bent onto
something that does not fit.

Vocabulary: https://ns.cascadeprotocol.org/core/v1#

See: https://cascadeprotocol.org/docs/cascade-protocol-schemas
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RecordSummary:
    """
    Per-domain record counts for one partition of a pod export.

    ``domain`` is required by ``cascade:RecordSummaryShape``. Every count is a
    single non-negative integer; a negative or repeated count silently
    corrupts any completeness check built on it.
    """

    domain: str = ""
    """Which partition this summarises, e.g. ``"clinical"`` or ``"wellness"``."""

    # -- Entity counts (rdfs:subPropertyOf void:entities) --------------------

    condition_count: int | None = None
    """Counts ``health:ConditionRecord``. Maps to ``cascade:conditionCount``."""

    medication_count: int | None = None
    """Counts ``clinical:Medication``. Maps to ``cascade:medicationCount``."""

    allergy_count: int | None = None
    """Counts ``health:AllergyRecord``. Maps to ``cascade:allergyCount``."""

    lab_result_count: int | None = None
    """Counts ``health:LabResultRecord``. Maps to ``cascade:labResultCount``."""

    immunization_count: int | None = None
    """Counts ``health:ImmunizationRecord``. Maps to ``cascade:immunizationCount``."""

    coverage_count: int | None = None
    """
    Insurance coverage records. A ``void:entities`` subproperty like the
    others, but the ontology names no ``void:class`` for it.
    Maps to ``cascade:coverageCount``.
    """

    supplement_count: int | None = None
    """Counts ``clinical:Supplement``. Maps to ``cascade:supplementCount``."""

    # -- Day counts (NOT void:entities subproperties) ------------------------

    vital_sign_days: int | None = None
    """Distinct days covered by vital sign records. Maps to ``cascade:vitalSignDays``."""

    heart_rate_days: int | None = None
    """Distinct days covered by heart rate history. Maps to ``cascade:heartRateDays``."""

    blood_pressure_days: int | None = None
    """Distinct days covered by blood pressure history. Maps to ``cascade:bloodPressureDays``."""

    activity_days: int | None = None
    """Distinct days covered by activity history. Maps to ``cascade:activityDays``."""

    sleep_days: int | None = None
    """Distinct nights covered by sleep history. Maps to ``cascade:sleepDays``."""

    # -- Descriptive ---------------------------------------------------------

    data_provenance: str | None = None
    """Predominant provenance of this partition. Maps to ``cascade:dataProvenance``."""

    notes: str | None = None
    """
    Free-text commentary. Maps to ``cascade:notes`` — NOT ``health:notes``,
    which is the record-level spelling.
    """


@dataclass
class InteractionScenario:
    """
    A flagged interaction that an agent can only detect by correlating
    resources of differing provenance.

    ``cascade:InteractionScenarioShape`` requires a title and exactly one list
    of involved resources: a scenario naming no resources states that a risk
    exists but gives a consumer nothing to check it against.
    """

    title: str = ""
    """Short name of the interaction. Maps to ``dcterms:title``."""

    description: str | None = None
    """What must be correlated and why. Maps to ``dcterms:description``."""

    involved_resources: list[str] = field(default_factory=list)
    """
    Ordered list of pod resources to read together, as an rdf:List.
    Maps to ``cascade:involvedResources``.
    """

    severity: str | None = None
    """One of ``"low"``, ``"moderate"``, ``"high"``, ``"critical"``."""

    requires_cross_provenance: bool | None = None
    """
    True when detection requires correlating differing
    ``cascade:dataProvenance``. The distinguishing property of this class: a
    single-source consumer cannot find it.
    Maps to ``cascade:requiresCrossProvenance``.
    """


@dataclass
class DeviceSource:
    """
    A device that contributed data to an export, carried as a ``prov:Agent``
    in the ``cascade:deviceSources`` list.
    """

    label: str = ""
    """Device name, e.g. ``"Apple Watch Series 9"``. Maps to ``prov:label``."""

    source_type: str | None = None
    """
    Mechanism the readings arrived through, e.g. ``"healthKit"``,
    ``"bluetoothDevice"``, ``"manualEntry"``. Maps to ``cascade:sourceType``.

    This describes the TRANSPORT, not the trustworthiness of the data.
    Trustworthiness is ``cascade:dataProvenance``.
    """

    data_types: str | None = None
    """
    Comma-separated data types contributed, e.g. ``"heartRate, activity, sleep"``.
    Maps to ``cascade:dataTypes``.
    """


@dataclass
class ExportManifest:
    """
    Provenance and completeness metadata for a complete pod export.

    ``cascade:ExportManifestShape`` requires a non-empty ``dcterms:title``, a
    ``dcterms:created`` timestamp, and a ``cascade:schemaVersion`` in
    major.minor form: without a schema version a consumer cannot decide
    whether it can read the export at all.

    The subject of a manifest is normally the empty relative IRI ``<>``,
    meaning "this document", so ``id`` defaults to the empty string.
    """

    id: str = ""
    """RDF subject. Empty string serializes as ``<>`` (this document)."""

    type: str = field(default="ExportManifest", init=True)

    title: str = ""
    """Human-readable name of the export. Maps to ``dcterms:title``."""

    description: str | None = None
    """What the export contains. Maps to ``dcterms:description``."""

    created: str | None = None
    """When the export was generated (ISO 8601). Maps to ``dcterms:created``."""

    creator: str | None = None
    """Who produced the export. Maps to ``dcterms:creator``."""

    schema_version: str | None = None
    """Cascade schema version, major.minor. Maps to ``cascade:schemaVersion``."""

    patient_profile_version: str | None = None
    """
    Version of the patient profile structure, independent of the schema
    version. Maps to ``cascade:patientProfileVersion``.
    """

    provenance_layers: list[str] = field(default_factory=list)
    """
    Ordered ``cascade:DataProvenance`` local names present anywhere in the
    export, e.g. ``["ClinicalGenerated", "DeviceGenerated", "SelfReported"]``.
    Lets a consumer tell, before reading any resource, whether the export
    holds device data, EHR data, self-reported data, or a mixture.
    Maps to ``cascade:provenanceLayers`` as an rdf:List of IRIs.
    """

    clinical_summary: RecordSummary | None = None
    """Record counts for the clinical partition. Maps to ``cascade:clinicalSummary``."""

    wellness_summary: RecordSummary | None = None
    """Record counts for the wellness partition. Maps to ``cascade:wellnessSummary``."""

    device_sources: list[DeviceSource] = field(default_factory=list)
    """Devices that contributed data. Maps to ``cascade:deviceSources``."""

    interaction_scenarios: list[InteractionScenario] = field(default_factory=list)
    """Flagged cross-provenance interactions. Maps to ``cascade:interactionScenarios``."""

    def summary_for(self, domain: str) -> RecordSummary | None:
        """
        Return the :class:`RecordSummary` whose ``domain`` matches, or None.

        Args:
            domain: Partition name, e.g. ``"clinical"`` or ``"wellness"``.
        """
        for summary in (self.clinical_summary, self.wellness_summary):
            if summary is not None and summary.domain == domain:
                return summary
        return None
