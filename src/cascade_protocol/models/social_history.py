"""
Consumer-reported social history data model for the Cascade Protocol.

Represents lifestyle and social history that the patient self-reports
(Apple Health import, in-app questionnaire, user entry). This is
**distinct** from ``clinical:SocialHistoryRecord`` /
``ClinicalSocialHistoryRecord``, which is EHR-extracted clinical-grade
social history subject to 42 CFR Part 2 sensitivity handling.

RDF type: ``health:SocialHistoryRecord``
Vocabulary: https://ns.cascadeprotocol.org/health/v1#

See: https://cascadeprotocol.org/docs/cascade-protocol-schemas
"""

from __future__ import annotations

from dataclasses import dataclass, field

from cascade_protocol.models.common import CascadeRecord


@dataclass
class SocialHistoryRecord(CascadeRecord):
    """
    A consumer-reported social history record in the Cascade Protocol.

    Captures self-reported lifestyle information such as smoking status,
    alcohol use, exercise frequency, and occupational exposures. Because the
    data is patient-asserted (not EHR-sourced), it carries the ``health:``
    vocabulary and is **not** the same class as the EHR-extracted
    ``clinical:SocialHistoryRecord``.

    Serializes as ``health:SocialHistoryRecord`` in Turtle.
    """

    type: str = field(default="SocialHistoryRecord", init=True)

    smoking_status: str | None = None
    """
    Self-reported smoking status (e.g., ``"never"``, ``"former"``,
    ``"current"``).
    Maps to ``health:smokingStatus`` in Turtle serialization.
    """

    alcohol_use: str | None = None
    """
    Self-reported alcohol use (e.g., ``"none"``, ``"occasional"``,
    ``"2-3 drinks/week"``).
    Maps to ``health:alcoholUse`` in Turtle serialization.
    """

    exercise_frequency: str | None = None
    """
    Self-reported exercise frequency (e.g., ``"daily"``, ``"3x/week"``,
    ``"sedentary"``).
    Maps to ``health:exerciseFrequency`` in Turtle serialization.
    """

    occupational_exposure: str | None = None
    """
    Self-reported occupational or environmental exposures (e.g.,
    ``"asbestos"``, ``"none"``).
    Maps to ``health:occupationalExposure`` in Turtle serialization.
    """
