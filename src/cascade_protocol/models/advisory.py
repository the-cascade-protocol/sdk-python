"""
Advisory, AI-generation, and proxy-agent provenance models for the
Cascade Protocol (core v3.1-3.3).

These classes extend the PROV-O provenance machinery introduced in core
v3.0 (``cascade:AIExtractionActivity``) to cover:

- ``cascade:AdvisoryApplicationActivity`` — a PROV-O Activity recording the
  application of advisory triples to a record set.
- ``cascade:AIGenerationActivity`` — a PROV-O Activity recording ungrounded
  general-AI generation (distinct from grounded AI *extraction*). Reuses the
  extraction-confidence/model/section/review fields and adds
  ``promptVersion`` and ``generationTemperature``.
- ``cascade:ProxyAgent`` — a PROV-O Agent acting on behalf of a patient
  (caregiver/proxy), with scope and grant/revoke metadata.

Vocabulary: https://ns.cascadeprotocol.org/core/v1#

See: https://cascadeprotocol.org/docs/cascade-protocol-schemas
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from cascade_protocol.models.common import CascadeRecord

# Enumerated values for the ``cascade:GenerationTrigger`` enum class.
# Each value corresponds to a named individual in the core vocabulary.
GenerationTrigger = Literal[
    "InitialGeneration",
    "RegenerationAfterReclassification",
    "AudienceRetargeting",
]


@dataclass
class AdvisoryApplicationActivity(CascadeRecord):
    """
    A PROV-O Activity recording the application of advisory triples to a
    patient's record set.

    Serializes as ``cascade:AdvisoryApplicationActivity`` in Turtle.
    """

    type: str = field(default="AdvisoryApplicationActivity", init=True)

    applied_triples_count: int | None = None
    """
    Number of advisory triples applied by this activity.
    Maps to ``cascade:appliedTriplesCount`` in Turtle serialization.
    """


@dataclass
class AIGenerationActivity(CascadeRecord):
    """
    A PROV-O Activity representing ungrounded general-AI content generation
    (as opposed to grounded AI *extraction* over a source document).

    Records produced by this activity carry ``cascade:AIAsserted`` provenance
    — never ``cascade:AIExtracted`` — so the two are never confused.

    Serializes as ``cascade:AIGenerationActivity`` in Turtle.
    """

    type: str = field(default="AIGenerationActivity", init=True)

    extraction_model: str | None = None
    """
    Identifier of the AI model used for generation
    (e.g., ``"qwen3.5-4b-q4_k_m"``).
    Maps to ``cascade:extractionModel`` in Turtle serialization.
    """

    extraction_confidence: float | None = None
    """
    Model confidence score for the generated content, in the range [0.0, 1.0].
    Maps to ``cascade:extractionConfidence`` in Turtle serialization.
    """

    source_narrative_section: str | None = None
    """
    The document section the generation pertains to, if any.
    Maps to ``cascade:sourceNarrativeSection`` in Turtle serialization.
    """

    requires_user_review: bool | None = None
    """
    True when the generated content must be reviewed by the patient before
    persisting.
    Maps to ``cascade:requiresUserReview`` in Turtle serialization.
    """

    prompt_version: str | None = None
    """
    Version identifier of the prompt template used for generation.
    Maps to ``cascade:promptVersion`` in Turtle serialization.
    """

    generation_temperature: float | None = None
    """
    Sampling temperature used during generation.
    Maps to ``cascade:generationTemperature`` in Turtle serialization.
    """

    trigger: str | None = None
    """
    What triggered this generation. One of the ``cascade:GenerationTrigger``
    individuals: ``InitialGeneration``, ``RegenerationAfterReclassification``,
    ``AudienceRetargeting``.
    Maps to ``cascade:trigger`` in Turtle serialization.
    """


@dataclass
class ProxyAgent(CascadeRecord):
    """
    A PROV-O Agent acting on behalf of a patient (e.g., a caregiver or legal
    proxy), with scope and grant/revoke metadata.

    Serializes as ``cascade:ProxyAgent`` in Turtle.
    """

    type: str = field(default="ProxyAgent", init=True)

    acts_for_patient: str | None = None
    """
    URI of the patient this agent acts on behalf of.
    Maps to ``cascade:actsForPatient`` in Turtle serialization.
    """

    proxy_web_id: str | None = None
    """
    WebID URI identifying the proxy agent.
    Maps to ``cascade:proxyWebID`` in Turtle serialization.
    """

    proxy_relationship: str | None = None
    """
    Relationship of the proxy to the patient (e.g., ``"parent"``,
    ``"spouse"``, ``"legal-guardian"``).
    Maps to ``cascade:proxyRelationship`` in Turtle serialization.
    """

    proxy_scope: str | None = None
    """
    Scope of the proxy authorization (e.g., ``"full"``, ``"read-only"``).
    Maps to ``cascade:proxyScope`` in Turtle serialization.
    """

    proxy_granted_at: str | None = None
    """
    Timestamp when the proxy authorization was granted (ISO 8601).
    Maps to ``cascade:proxyGrantedAt`` in Turtle serialization.
    """

    proxy_revoked_at: str | None = None
    """
    Timestamp when the proxy authorization was revoked (ISO 8601), if
    applicable.
    Maps to ``cascade:proxyRevokedAt`` in Turtle serialization.
    """
