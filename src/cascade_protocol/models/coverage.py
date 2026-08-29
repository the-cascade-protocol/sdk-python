"""
Coverage / Insurance data model for the Cascade Protocol.

Represents an insurance coverage or plan record. Supports both the
clinical vocabulary (``clinical:CoverageRecord``) and the dedicated
coverage vocabulary (``coverage:InsurancePlan``).

RDF types: ``clinical:CoverageRecord`` or ``coverage:InsurancePlan``
Vocabularies:
- https://ns.cascadeprotocol.org/clinical/v1#
- https://ns.cascadeprotocol.org/coverage/v1#

See: https://cascadeprotocol.org/docs/cascade-protocol-schemas
"""

from __future__ import annotations

from dataclasses import dataclass, field

from cascade_protocol.models.common import CascadeRecord


@dataclass
class Coverage(CascadeRecord):
    """
    A coverage / insurance record in the Cascade Protocol.

    Required fields: ``provider_name``, ``data_provenance``, ``schema_version``.
    All date fields use ISO 8601 string format.

    Serializes as ``clinical:CoverageRecord`` or ``coverage:InsurancePlan`` in Turtle.
    """

    type: str = field(default="InsurancePlan", init=True)

    provider_name: str = ""
    """
    Name of the insurance provider.
    Maps to ``clinical:providerName`` in Turtle serialization.
    """

    status: str | None = None
    """
    Lifecycle state of the coverage record itself (coverage v1.5): whether the
    plan is in force, was cancelled, is still a draft, or was entered in error.

    FHIR alignment: ``Coverage.status``, code 1..1, REQUIRED binding to
    https://hl7.org/fhir/R4/valueset-fm-status.html — ``"active"``,
    ``"cancelled"``, ``"draft"``, ``"entered-in-error"``. FHIR marks the element
    a MODIFIER: a cancelled or erroneous Coverage must not be read as describing
    coverage the patient has. That is why this is not a nice-to-have — a
    cancelled plan read as an active one is a wrong answer to "am I covered",
    not a missing one.

    Through coverage v1.4 this vocabulary had no status property for
    ``coverage:InsurancePlan`` at all, so an importer reading a conformant
    Coverage resource had to discard the one element FHIR requires it to carry.

    NOT a substitute for, and not substituted by, ``coverage:claimStatus`` or
    ``coverage:adjudicationStatus``: those belong to the denial and appeal
    workflow and describe what happened to a CLAIM, not whether the plan is in
    force. Also distinct from :attr:`effective_start` / :attr:`effective_end` —
    a date range says when the plan is MEANT to apply, the status says what the
    payer currently ASSERTS about the record, and a plan whose effective period
    has not ended can still be cancelled.

    The VALUE is validated (the FHIR binding is required, and no pod has ever
    carried this property, so a constraint cannot invalidate existing data). Its
    PRESENCE deliberately is not: no producer has yet had the chance to write
    it.

    Maps to ``coverage:status`` in Turtle serialization — NOT the
    ``health:status`` the shared ``status`` field name is bound to elsewhere;
    see the serializer's type-specific overrides.
    """

    member_id: str | None = None
    """
    Member identifier for the insured individual.
    Maps to ``clinical:memberId`` in Turtle serialization.
    """

    group_number: str | None = None
    """
    Group number for the insurance plan.
    Maps to ``clinical:groupNumber`` in Turtle serialization.
    """

    plan_name: str | None = None
    """
    Name of the insurance plan.
    Maps to ``clinical:planName`` in Turtle serialization.
    """

    plan_type: str | None = None
    """
    Type of insurance plan (ppo, hmo, pos, epo, hdhp, medicare, medicaid).
    Maps to ``clinical:planType`` in Turtle serialization.
    """

    coverage_type: str | None = None
    """
    Coverage designation (primary, secondary, supplemental).
    Maps to ``clinical:coverageType`` in Turtle serialization.
    """

    relationship: str | None = None
    """
    Subscriber relationship to plan holder.
    Maps to ``clinical:relationship`` in Turtle serialization.
    """

    subscriber_relationship: str | None = None
    """
    Alias for ``relationship`` used in the coverage vocabulary.
    Maps to ``coverage:subscriberRelationship`` in Turtle serialization.
    """

    effective_period_start: str | None = None
    """
    Start date of the coverage period (ISO 8601).
    Maps to ``clinical:effectivePeriodStart`` in Turtle serialization.
    """

    effective_period_end: str | None = None
    """
    End date of the coverage period (ISO 8601).
    Maps to ``clinical:effectivePeriodEnd`` in Turtle serialization.
    """

    effective_start: str | None = None
    """
    Start date of effectiveness (ISO 8601, coverage vocabulary).
    Maps to ``coverage:effectiveStart`` in Turtle serialization.
    """

    effective_end: str | None = None
    """
    End date of effectiveness (ISO 8601, coverage vocabulary).
    Maps to ``coverage:effectiveEnd`` in Turtle serialization.
    """

    payor_name: str | None = None
    """
    Name of the payor organization.
    Maps to ``clinical:payorName`` in Turtle serialization.
    """

    subscriber_id: str | None = None
    """
    Subscriber identifier for the plan holder.
    Maps to ``clinical:subscriberId`` in Turtle serialization.
    """

    subscriber_name: str | None = None
    """
    Name of the primary subscriber on the plan.
    Maps to ``coverage:subscriberName`` in Turtle serialization.
    """

    rx_bin: str | None = None
    """
    Pharmacy BIN (Bank Identification Number) for prescription benefits.
    Maps to ``coverage:rxBin`` in Turtle serialization.
    """

    rx_pcn: str | None = None
    """
    Pharmacy PCN (Processor Control Number) for prescription benefits.
    Maps to ``coverage:rxPcn`` in Turtle serialization.
    """

    rx_group: str | None = None
    """
    Pharmacy group number for prescription benefits.
    Maps to ``coverage:rxGroup`` in Turtle serialization.
    """

    @classmethod
    def from_dataframe(cls, df: "pd.DataFrame") -> list["Coverage"]:  # type: ignore[name-defined]
        """Reconstruct a list of Coverage records from a pandas DataFrame."""
        from cascade_protocol.pandas_integration.dataframe import dataframe_to_records
        return dataframe_to_records(df, cls)  # type: ignore[return-value]
