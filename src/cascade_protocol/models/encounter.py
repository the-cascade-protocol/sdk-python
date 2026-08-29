"""
Encounter data model for the Cascade Protocol.

Represents a clinical encounter (office visit, consultation, procedure
appointment, etc.) sourced from EHR imports.

RDF types:
- ``clinical:Encounter``
- ``clinical:EncounterParticipant`` (clinical v1.16)

Vocabulary: https://ns.cascadeprotocol.org/clinical/v1#

See: https://cascadeprotocol.org/docs/cascade-protocol-schemas
"""

from __future__ import annotations

from dataclasses import dataclass, field

from cascade_protocol.models.common import CascadeRecord


@dataclass
class EncounterParticipant:
    """
    One participation in an encounter (clinical v1.16): a named person together
    with the role they played in that visit, and their specialty where the
    source states it.

    Mirrors the FHIR R4 ``Encounter.participant`` BackboneElement. Attached to
    the encounter with ``clinical:hasParticipant``.

    WHY A STRUCTURED NODE RATHER THAN ROLE-QUALIFIED PREDICATES. FHIR models
    participation as a repeating BackboneElement carrying a role AND an
    individual, and US Core marks the element, its type and its individual all
    Must Support. The alternative — a flat family of role-qualified predicates
    on the Encounter itself (an attending name, a referrer name, and so on) —
    fails on both axes of the real data: the role vocabulary is EXTENSIBLE, so
    any fixed family of predicates silently drops the local roles a server is
    entitled to send, and a visit routinely carries several participants in the
    SAME role, which one-predicate-per-role cannot represent.

    The node deliberately holds the participant's DISPLAY NAME rather than a
    reference to a practitioner record. This vocabulary defines no practitioner
    class, and inventing one to hold a display string would be a larger claim
    than the source supports.

    NOT a :class:`~cascade_protocol.models.common.CascadeRecord`. A
    participation is not a health record and is not an entity in the PROV sense:
    it carries no ``cascade:dataProvenance`` and no ``cascade:schemaVersion``,
    and ``clinical:EncounterParticipantShape`` requires neither. The shape in
    fact requires NO field at all, because FHIR makes every sub-element of
    ``Encounter.participant`` optional.

    IDENTIFIED BY IRI. ``clinical:EncounterParticipantShape`` does not demand
    ``sh:nodeKind sh:IRI`` — nothing references a participation from another
    file — so a blank node would also conform. This SDK writes an IRI anyway,
    matching the conformance fixtures and matching
    :class:`~cascade_protocol.models.attachment.Attachment`, whose edge shape
    does require one. One treatment for both sub-node classes beats two.
    """

    id: str = ""
    """RDF subject IRI for this participation."""

    type: str = field(default="EncounterParticipant", init=True)

    participant_name: str | None = None
    """
    Display name of the person who participated, verbatim from
    ``Encounter.participant.individual.display``. A display name, not a
    resolvable reference.

    Single-valued: ``Encounter.participant.individual`` is 0..1.

    Maps to ``clinical:participantName`` in Turtle serialization.
    """

    participant_role: str | None = None
    """
    Human-readable role this participant played, from
    ``Encounter.participant.type`` CodeableConcept.text or the first coding's
    display: ``"attender"``, ``"referrer"``, ``"consultant"``.

    The label is what makes a stored name interpretable; a name recorded with no
    role is indistinguishable from a treating clinician's and cannot be
    corrected by a reader.

    Maps to ``clinical:participantRole`` in Turtle serialization.
    """

    participant_role_code: list[str] | None = None
    """
    Coded role(s) from ``Encounter.participant.type``, verbatim.

    REPEATABLE, 0..*, because the source element is. NO value set is enforced in
    either direction: FHIR R4 binds this element EXTENSIBLY, so a server may
    send a local role code and remain conformant, and rejecting one would
    discard the participant along with it.

    Maps to ``clinical:participantRoleCode`` in Turtle serialization, one triple
    per value.
    """

    participant_specialty: str | None = None
    """
    The clinical specialty this participant acted in during the encounter, as a
    display string: ``"Dermatology"``, ``"Sleep Medicine"``.

    Recorded on the participation rather than on a practitioner because
    specialty in FHIR is a property of the ROLE
    (``PractitionerRole.specialty``), not of the person: the same clinician has
    different specialties in different roles, and it is the one they acted in on
    this visit that describes the visit.

    Maps to ``clinical:participantSpecialty`` in Turtle serialization.
    """


@dataclass
class Encounter(CascadeRecord):
    """
    A clinical encounter record in the Cascade Protocol.

    Required fields: ``encounter_type``, ``data_provenance``, ``schema_version``.
    All date fields use ISO 8601 string format.

    Serializes as ``clinical:Encounter`` in Turtle.
    """

    type: str = field(default="Encounter", init=True)

    encounter_type: str = ""
    """
    Human-readable description of the encounter type.
    Maps to ``clinical:encounterType`` in Turtle serialization.
    """

    encounter_class: str | None = None
    """
    The CODE of ``Encounter.class``, verbatim as the source sent it (e.g.
    ``"AMB"``, ``"IMP"``, ``"EMER"`` — or a local code such as ``"5"``).

    FHIR R4 ``Encounter.class`` is a Coding, 1..1, bound only EXTENSIBLY to the
    v3-ActCode value set, so a conformant server may send a code from its own
    system. Both are stored here unchanged, because the code is what a
    round-trip export must put back.

    From clinical v1.16 the other two members of the Coding are stored too:
    :attr:`encounter_class_display` and :attr:`encounter_class_system`. Writers
    SHOULD emit all three when the source states them.

    Maps to ``clinical:encounterClass`` in Turtle serialization.
    """

    encounter_class_display: str | None = None
    """
    Human-readable display of ``Encounter.class``, verbatim from
    ``Coding.display`` (clinical v1.16).

    Added alongside, never instead of, :attr:`encounter_class`. The code stays
    because it is what a round-trip export must restore and what a code-system
    lookup keys on; the display is stored because where the code comes from a
    local system — and the extensible binding means it often does — the code
    alone is unreadable.

    Maps to ``clinical:encounterClassDisplay`` in Turtle serialization.
    """

    encounter_class_system: str | None = None
    """
    The code system ``Encounter.class``'s code is drawn from, verbatim from
    ``Coding.system`` (clinical v1.16). Typically
    ``http://terminology.hl7.org/CodeSystem/v3-ActCode``, or a ``urn:oid:`` URI
    where the source used a local system.

    Stored because it is the only thing that distinguishes a ratified
    ActEncounterCode from a locally-numbered category that happens to look like
    one. Without it a consumer cannot tell whether a stored class code is safe
    to map.

    Written as ``^^xsd:anyURI``, the property's declared range. The shape
    accepts ``xsd:string`` too, because serializers differ on which of the two
    they write for a URI-valued literal.

    Maps to ``clinical:encounterClassSystem`` in Turtle serialization.
    """

    encounter_reason: list[str] | None = None
    """
    Why the visit happened, in the chart's own words (clinical v1.16).

    FHIR alignment: ``Encounter.reasonCode``, CodeableConcept 0..*, which US
    Core marks Must Support. Value is CodeableConcept.text where the source
    states it, otherwise the first coding's display: the reason as written, not
    a normalization of it.

    REPEATABLE, 0..*, because the source element is.

    NO VALUE SET is bound to this property or its shape. The FHIR binding is
    PREFERRED, the weakest binding that still names a value set, and real
    exports carry local, free-text and SNOMED CT reasons in the same field. An
    enum here would reject conformant data.

    Maps to ``clinical:encounterReason`` in Turtle serialization, one triple per
    value.
    """

    admit_source: str | None = None
    """
    Where the patient came from before this encounter (clinical v1.16).

    FHIR alignment: ``Encounter.hospitalization.admitSource``, CodeableConcept
    0..1. Value is CodeableConcept.text or the first coding's display, verbatim.

    Presence of an ``Encounter.hospitalization`` element is itself the
    structured signal that an encounter was an admission rather than an office
    visit, and through clinical v1.15 this vocabulary had nowhere to put it, so
    that distinction was unrecoverable from the pod.

    Maps to ``clinical:admitSource`` in Turtle serialization.
    """

    discharge_disposition: str | None = None
    """
    Where the patient went after this encounter (clinical v1.16), e.g.
    ``"Home or Self Care"``.

    FHIR alignment: ``Encounter.hospitalization.dischargeDisposition``. The R4
    base binding is EXAMPLE strength; US Core marks the element Must Support.
    No value set is bound here, and an example-strength binding is the clearest
    possible case for not binding one.

    Maps to ``clinical:dischargeDisposition`` in Turtle serialization.
    """

    has_participant: list[str] | None = None
    """
    IRI references to this encounter's :class:`EncounterParticipant` nodes
    (clinical v1.16).

    REPEATABLE, 0..*, matching FHIR R4 ``Encounter.participant``. An encounter
    commonly carries an attender, a referrer and an authorizing physician at
    once, and which of them actually saw the patient is only answerable if all
    of them are kept with their roles attached.

    Traversable IRI edges rather than embedded objects, matching
    :attr:`has_encounter` and the other cross-node edges in this SDK. Resolve
    them with
    :func:`~cascade_protocol.deserializer.turtle_parser.parse_encounter_participants`.

    Maps to ``clinical:hasParticipant`` in Turtle serialization, one triple per
    value.
    """

    encounter_status: str | None = None
    """
    Status: finished, in-progress, cancelled.
    Maps to ``clinical:encounterStatus`` in Turtle serialization.
    """

    encounter_start: str | None = None
    """
    Date and time the encounter started (ISO 8601).
    Maps to ``clinical:encounterStart`` in Turtle serialization.
    """

    encounter_end: str | None = None
    """
    Date and time the encounter ended (ISO 8601).
    Maps to ``clinical:encounterEnd`` in Turtle serialization.
    """

    provider_name: str | None = None
    """
    Name and specialty of the provider who conducted the encounter.
    Maps to ``clinical:providerName`` in Turtle serialization.
    """

    facility_name: str | None = None
    """
    Name of the facility where the encounter occurred.
    Maps to ``clinical:facilityName`` in Turtle serialization.
    """

    snomed_code: list[str] | None = None
    """
    SNOMED CT code URIs for the encounter type, one per coding.

    Multi-valued as of clinical v1.14, which also gave ``clinical:Encounter``
    its first SHACL shape; that shape declares ``clinical:snomedCode``
    multi-valued from the start. FHIR R4 CodeableConcept.coding is 0..*
    (https://hl7.org/fhir/R4/datatypes.html#CodeableConcept).

    Maps to ``health:snomedCode`` as one URI-object triple per value.
    """

    @classmethod
    def from_dataframe(cls, df: "pd.DataFrame") -> list["Encounter"]:  # type: ignore[name-defined]
        """Reconstruct a list of Encounter records from a pandas DataFrame."""
        from cascade_protocol.pandas_integration.dataframe import dataframe_to_records
        return dataframe_to_records(df, cls)  # type: ignore[return-value]
