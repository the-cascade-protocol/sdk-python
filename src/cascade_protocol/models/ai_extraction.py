"""
AI extraction provenance models for the Cascade Protocol.

Represents PROV-O activities and audit records for AI/NLP extraction
passes over clinical documents.

RDF types: ``cascade:AIExtractionActivity``, ``cascade:AIDiscardedExtraction``,
           ``cascade:SocialHistoryConsent``
Vocabulary: https://ns.cascadeprotocol.org/core/v1#

See: https://cascadeprotocol.org/docs/cascade-protocol-schemas
"""

from __future__ import annotations

from dataclasses import dataclass, field

from cascade_protocol.models.common import CascadeRecord


@dataclass
class AIExtractionActivity(CascadeRecord):
    """
    A PROV-O Activity representing an AI/NLP extraction pass over a clinical
    document section. Linked to extracted records via ``prov:wasGeneratedBy``.

    Serializes as ``cascade:AIExtractionActivity`` in Turtle.
    """

    type: str = field(default="AIExtractionActivity", init=True)

    extraction_confidence: float | None = None
    """
    Model confidence score for the extracted value, in the range [0.0, 1.0].
    Maps to ``cascade:extractionConfidence`` in Turtle serialization.
    """

    extraction_model: str | None = None
    """
    Identifier of the AI/NLP model used for extraction
    (e.g., ``"qwen3.5-4b-q4_k_m"``).
    Maps to ``cascade:extractionModel`` in Turtle serialization.
    """

    source_narrative_section: str | None = None
    """
    The C-CDA or document section the AI extracted data from
    (e.g., ``"medications"``, ``"social-history"``).
    Maps to ``cascade:sourceNarrativeSection`` in Turtle serialization.
    """

    requires_user_review: bool | None = None
    """
    True when the extraction confidence is below the auto-accept threshold
    and the record must be reviewed by the patient before persisting.
    Maps to ``cascade:requiresUserReview`` in Turtle serialization.
    """


@dataclass
class AIDiscardedExtraction(CascadeRecord):
    """
    An extraction candidate that the AI model identified but discarded
    (low confidence, duplicate, or out-of-scope). Stored for audit and
    re-review purposes.

    Serializes as ``cascade:AIDiscardedExtraction`` in Turtle.
    """

    type: str = field(default="AIDiscardedExtraction", init=True)

    discard_reason: str | None = None
    """
    Human-readable reason the extraction candidate was discarded.
    Maps to ``cascade:discardReason`` in Turtle serialization.
    """


@dataclass
class SocialHistoryConsent(CascadeRecord):
    """
    Consent record governing the storage and processing of sensitive social
    history data under 42 CFR Part 2 and equivalent regulations.

    Serializes as ``cascade:SocialHistoryConsent`` in Turtle.
    """

    type: str = field(default="SocialHistoryConsent", init=True)

    consent_scope: str | None = None
    """
    Scope of the consent grant.
    Values: ``social-history``, ``substance-use``, ``mental-health``.
    Maps to ``cascade:consentScope`` in Turtle serialization.
    """

    consent_granted_at: str | None = None
    """
    Timestamp when the patient granted consent (ISO 8601).
    Maps to ``cascade:consentGrantedAt`` in Turtle serialization.
    """

    consent_revoked_at: str | None = None
    """
    Timestamp when the patient revoked consent (ISO 8601), if applicable.
    Maps to ``cascade:consentRevokedAt`` in Turtle serialization.
    """
