"""
Clinical social history data model for the Cascade Protocol.

Represents an EHR-extracted social history observation sourced from a
C-CDA Social History section (LOINC 29762-2). Subject to 42 CFR Part 2
sensitivity handling — distinct from ``health:SocialHistoryRecord``
(consumer-reported lifestyle data).

RDF type: ``clinical:SocialHistoryRecord``
Vocabulary: https://ns.cascadeprotocol.org/clinical/v1#

See: https://cascadeprotocol.org/docs/cascade-protocol-schemas
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, Literal

from cascade_protocol.models.common import CascadeRecord

# Social history observation category values.
# Maps to FHIR Observation.category ``social-history``.
SocialHistoryCategory = Literal[
    "smokingStatus",
    "alcoholUse",
    "substanceUse",
    "occupation",
    "educationLevel",
    "sexualOrientation",
    "genderIdentity",
    "householdIncome",
    "housingStatus",
    "socialIsolation",
]


@dataclass
class ClinicalSocialHistoryRecord(CascadeRecord):
    """
    An EHR-extracted social history record in the Cascade Protocol.

    This class represents clinical-grade social history imported from an EHR
    system. It is **distinct** from ``health:SocialHistoryRecord``, which
    represents consumer-reported social history (Apple Health import, user
    entry). Records with ``social_history_category == 'substanceUse'`` require
    a linked ``cascade:SocialHistoryConsent`` record under 42 CFR Part 2.

    Serializes as ``clinical:SocialHistoryRecord`` in Turtle.
    """

    type: str = field(default="ClinicalSocialHistoryRecord", init=True)

    social_history_category: str = ""
    """
    Category of the social history observation.
    Maps to ``clinical:socialHistoryCategory`` in Turtle serialization.
    """

    packs_per_year: float | None = None
    """
    Cumulative smoking exposure in pack-years (packs/day x years smoked).
    Applicable when ``social_history_category`` is ``smokingStatus``.
    Maps to ``clinical:packsPerYear`` in Turtle serialization.
    """

    substance_type: str | None = None
    """
    Type of substance for substance-use records (e.g., ``"alcohol"``,
    ``"cannabis"``, ``"opioid"``).
    Applicable when ``social_history_category`` is ``substanceUse``.
    Maps to ``clinical:substanceType`` in Turtle serialization.
    """

    frequency_description: str | None = None
    """
    Free-text or coded frequency description (e.g., ``"2-3 drinks/week"``,
    ``"daily"``).
    Maps to ``clinical:frequencyDescription`` in Turtle serialization.
    """

    social_history_consent_uri: str | None = None
    """
    URI of the linked ``cascade:SocialHistoryConsent`` record governing
    storage and processing of this sensitive record.
    Required for ``substanceUse`` category records (42 CFR Part 2).
    Maps to ``clinical:socialHistoryConsent`` in Turtle serialization.
    """
