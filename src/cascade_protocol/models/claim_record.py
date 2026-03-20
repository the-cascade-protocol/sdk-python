"""
Coverage workflow models for the Cascade Protocol.

ClaimRecord, BenefitStatement, DenialNotice, and AppealRecord.

RDF types: coverage:ClaimRecord, coverage:BenefitStatement,
           coverage:DenialNotice, coverage:AppealRecord
Vocabulary: https://ns.cascadeprotocol.org/coverage/v1#

See: https://cascadeprotocol.org/docs/cascade-protocol-schemas
"""

from __future__ import annotations

from dataclasses import dataclass, field

from cascade_protocol.models.common import CascadeRecord


@dataclass
class ClaimRecord(CascadeRecord):
    """
    A medical claim submitted to an insurer.
    Serializes as ``coverage:ClaimRecord`` in Turtle.
    """
    type: str = field(default="ClaimRecord", init=True)

    claim_type: str = ""
    """Values: professional, institutional, oral, pharmacy, vision.
    Maps to ``coverage:claimType``."""

    claim_date: str | None = None
    """ISO 8601 date. Maps to ``coverage:claimDate``."""

    claim_total: float | None = None
    """Total amount billed. Maps to ``coverage:claimTotal``."""

    claim_status: str | None = None
    """Values: active, cancelled, draft, entered-in-error. Maps to ``coverage:claimStatus``."""

    billing_provider: str | None = None
    """Name of the billing provider. Maps to ``coverage:billingProvider``."""

    @classmethod
    def from_dataframe(cls, df: "pd.DataFrame") -> list["ClaimRecord"]:  # type: ignore[name-defined]
        from cascade_protocol.pandas_integration.dataframe import dataframe_to_records
        return dataframe_to_records(df, cls)  # type: ignore[return-value]


@dataclass
class BenefitStatement(CascadeRecord):
    """
    An Explanation of Benefits document.
    Serializes as ``coverage:BenefitStatement`` in Turtle.
    """
    type: str = field(default="BenefitStatement", init=True)

    adjudication_status: str = ""
    """Values: completed, cancelled, entered-in-error. Maps to ``coverage:adjudicationStatus``."""

    adjudication_date: str | None = None
    """ISO 8601. Maps to ``coverage:adjudicationDate``."""

    outcome_code: str | None = None
    """Values: queued, complete, error, partial. Maps to ``coverage:outcomeCode``."""

    total_billed: float | None = None
    """Maps to ``coverage:totalBilled``."""

    total_allowed: float | None = None
    """Maps to ``coverage:totalAllowed``."""

    total_paid: float | None = None
    """Maps to ``coverage:totalPaid``."""

    patient_responsibility: float | None = None
    """Maps to ``coverage:patientResponsibility``."""

    denial_reason: str | None = None
    """Maps to ``coverage:denialReason``."""

    @classmethod
    def from_dataframe(cls, df: "pd.DataFrame") -> list["BenefitStatement"]:  # type: ignore[name-defined]
        from cascade_protocol.pandas_integration.dataframe import dataframe_to_records
        return dataframe_to_records(df, cls)  # type: ignore[return-value]


@dataclass
class DenialNotice(CascadeRecord):
    """
    A formal denial of coverage issued by an insurer.
    Serializes as ``coverage:DenialNotice`` in Turtle.
    """
    type: str = field(default="DenialNotice", init=True)

    denied_procedure_code: str = ""
    """CPT or HCPCS code of the denied service. Maps to ``coverage:deniedProcedureCode``."""

    denial_reason_code: str | None = None
    """Structured denial reason code URI. Maps to ``coverage:denialReasonCode``."""

    denial_letter_date: str | None = None
    """ISO 8601 date. Maps to ``coverage:denialLetterDate``."""

    appeal_deadline: str | None = None
    """ISO 8601 date. Maps to ``coverage:appealDeadline``."""

    coverage_policy_reference: str | None = None
    """LCD, NCD, or policy cited as basis. Maps to ``coverage:coveragePolicyReference``."""

    @classmethod
    def from_dataframe(cls, df: "pd.DataFrame") -> list["DenialNotice"]:  # type: ignore[name-defined]
        from cascade_protocol.pandas_integration.dataframe import dataframe_to_records
        return dataframe_to_records(df, cls)  # type: ignore[return-value]


@dataclass
class AppealRecord(CascadeRecord):
    """
    A formal appeal contesting a denial notice.
    Serializes as ``coverage:AppealRecord`` in Turtle.
    """
    type: str = field(default="AppealRecord", init=True)

    appeal_level: str = ""
    """Appeal level (e.g., redetermination, alj_hearing). Maps to ``coverage:appealLevel``."""

    appeal_filed_date: str | None = None
    """ISO 8601. Maps to ``coverage:appealFiledDate``."""

    appeal_outcome: str | None = None
    """Values: approved, denied, partial, withdrawn, pending. Maps to ``coverage:appealOutcome``."""

    appeal_outcome_date: str | None = None
    """ISO 8601. Maps to ``coverage:appealOutcomeDate``."""

    @classmethod
    def from_dataframe(cls, df: "pd.DataFrame") -> list["AppealRecord"]:  # type: ignore[name-defined]
        from cascade_protocol.pandas_integration.dataframe import dataframe_to_records
        return dataframe_to_records(df, cls)  # type: ignore[return-value]
