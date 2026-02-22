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
