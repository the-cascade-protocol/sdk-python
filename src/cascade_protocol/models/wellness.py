"""
Wellness data models for the Cascade Protocol.

Represents activity and sleep data typically sourced from wearable devices
or HealthKit.

RDF types:
- ``health:ActivitySnapshot``       -- 7-day aggregate
- ``health:SleepSnapshot``          -- 7-day aggregate
- ``health:DailyActivitySnapshot``  -- single day (health v2.5)
- ``health:DailySleepSnapshot``     -- single night (health v2.5)
- ``health:DailyVitalReading``      -- single day's aggregated vital (health v2.5)
- ``health:ActivityData``, ``health:SleepData``, ``health:HeartRateData``,
  ``health:BloodPressureData``, ``health:HRVData``,
  ``health:BodyMeasurements``      -- wellness containers (health v2.5)

The aggregate and single-day forms are deliberately distinct classes with
distinct properties, and both are emitted. They are not merged here either.

Vocabulary: https://ns.cascadeprotocol.org/health/v1#

See: https://cascadeprotocol.org/docs/cascade-protocol-schemas
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from cascade_protocol.models.common import CascadeRecord

# The four named individuals health:sleepQuality ranges over (health v2.5).
# The property is emitted with an IRI object (``health:sleepQuality
# health:Good``), never a string literal, so these are local names of IRIs.
SleepQuality = Literal["Excellent", "Good", "Fair", "Poor"]

SLEEP_QUALITY_VALUES: frozenset[str] = frozenset({"Excellent", "Good", "Fair", "Poor"})


@dataclass
class ActivitySnapshot(CascadeRecord):
    """
    A daily activity snapshot in the Cascade Protocol.

    Required fields: ``date``, ``data_provenance``, ``schema_version``.
    The ``date`` field uses ISO 8601 date format (YYYY-MM-DD).

    Serializes as ``health:ActivitySnapshot`` in Turtle.
    """

    type: str = field(default="ActivitySnapshot", init=True)

    date: str = ""
    """
    Date of the activity summary (ISO 8601 date: ``YYYY-MM-DD``).
    Maps to ``health:date`` in Turtle serialization.
    """

    steps: int | None = None
    """
    Total step count for the day.
    Maps to ``health:steps`` in Turtle serialization.
    """

    distance: float | None = None
    """
    Total distance covered in kilometers.
    Maps to ``health:distance`` in Turtle serialization.
    """

    active_minutes: int | None = None
    """
    Total active minutes for the day.
    Maps to ``health:activeMinutes`` in Turtle serialization.
    """

    calories: int | None = None
    """
    Total calories burned (active + basal).
    Maps to ``health:calories`` in Turtle serialization.
    """

    @classmethod
    def from_dataframe(cls, df: "pd.DataFrame") -> list["ActivitySnapshot"]:  # type: ignore[name-defined]
        """Reconstruct a list of ActivitySnapshot records from a pandas DataFrame."""
        from cascade_protocol.pandas_integration.dataframe import dataframe_to_records
        return dataframe_to_records(df, cls)  # type: ignore[return-value]


@dataclass
class SleepSnapshot(CascadeRecord):
    """
    A nightly sleep snapshot in the Cascade Protocol.

    Required fields: ``date``, ``data_provenance``, ``schema_version``.
    The ``date`` field uses ISO 8601 date format (YYYY-MM-DD).

    Serializes as ``health:SleepSnapshot`` in Turtle.
    """

    type: str = field(default="SleepSnapshot", init=True)

    date: str = ""
    """
    Date of the sleep session (ISO 8601 date: ``YYYY-MM-DD``).
    Maps to ``health:date`` in Turtle serialization.
    """

    total_sleep_minutes: int | None = None
    """
    Total sleep duration in minutes.
    Maps to ``health:totalSleepMinutes`` in Turtle serialization.
    """

    deep_sleep_minutes: int | None = None
    """
    Deep sleep duration in minutes.
    Maps to ``health:deepSleepMinutes`` in Turtle serialization.
    """

    rem_sleep_minutes: int | None = None
    """
    REM sleep duration in minutes.
    Maps to ``health:remSleepMinutes`` in Turtle serialization.
    """

    light_sleep_minutes: int | None = None
    """
    Light sleep duration in minutes.
    Maps to ``health:lightSleepMinutes`` in Turtle serialization.
    """

    awakenings: int | None = None
    """
    Number of awakenings during the sleep session.
    Maps to ``health:awakenings`` in Turtle serialization.
    """

    @classmethod
    def from_dataframe(cls, df: "pd.DataFrame") -> list["SleepSnapshot"]:  # type: ignore[name-defined]
        """Reconstruct a list of SleepSnapshot records from a pandas DataFrame."""
        from cascade_protocol.pandas_integration.dataframe import dataframe_to_records
        return dataframe_to_records(df, cls)  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Single-day entries inside the wellness history containers (health v2.5)
# ---------------------------------------------------------------------------


@dataclass
class DailyActivitySnapshot(CascadeRecord):
    """
    One day of activity metrics, as carried inside a
    ``health:dailyActivityHistory`` list.

    Serializes as ``health:DailyActivitySnapshot`` in Turtle, with the
    timestamp on ``cascade:date``.
    """

    type: str = field(default="DailyActivitySnapshot", init=True)

    date: str = ""
    """
    Timestamp the day's metrics apply to (ISO 8601 dateTime).
    Maps to ``cascade:date`` in Turtle serialization.
    """

    steps: int | None = None
    """Step count for the day. Maps to ``health:steps``."""

    active_energy_kcal: float | None = None
    """
    Active energy burned in kilocalories for the day.
    Maps to ``health:activeEnergyKcal`` (xsd:decimal).
    """

    exercise_minutes: int | None = None
    """
    Minutes of exercise recorded for the day, bounded 0-1440.
    Maps to ``health:exerciseMinutes``.
    """

    stand_hours: int | None = None
    """
    Hours in which standing was recorded, bounded 0-24.
    Maps to ``health:standHours``.
    """

    @classmethod
    def from_dataframe(cls, df: "pd.DataFrame") -> list["DailyActivitySnapshot"]:  # type: ignore[name-defined]
        """Reconstruct a list of DailyActivitySnapshot records from a DataFrame."""
        from cascade_protocol.pandas_integration.dataframe import dataframe_to_records
        return dataframe_to_records(df, cls)  # type: ignore[return-value]


@dataclass
class DailySleepSnapshot(CascadeRecord):
    """
    One night of sleep, as carried inside a ``health:dailySleepHistory`` list.

    Serializes as ``health:DailySleepSnapshot`` in Turtle, with the timestamp
    on ``cascade:date``.
    """

    type: str = field(default="DailySleepSnapshot", init=True)

    date: str = ""
    """
    Timestamp the night applies to (ISO 8601 dateTime).
    Maps to ``cascade:date`` in Turtle serialization.
    """

    duration_hours: float | None = None
    """
    Total sleep duration in hours, bounded 0-24.
    Maps to ``health:durationHours`` (xsd:decimal).
    """

    sleep_quality: str | None = None
    """
    One of ``"Excellent"``, ``"Good"``, ``"Fair"``, ``"Poor"``.

    Maps to ``health:sleepQuality`` as an IRI (``health:Good``), not a string
    literal: that is what every known emitter writes and what the Cascade
    deserializers parse. Held here as the bare local name.
    """

    @classmethod
    def from_dataframe(cls, df: "pd.DataFrame") -> list["DailySleepSnapshot"]:  # type: ignore[name-defined]
        """Reconstruct a list of DailySleepSnapshot records from a DataFrame."""
        from cascade_protocol.pandas_integration.dataframe import dataframe_to_records
        return dataframe_to_records(df, cls)  # type: ignore[return-value]


@dataclass
class DailyVitalReading(CascadeRecord):
    """
    One day's aggregated vital sign reading inside a wellness history
    container (resting/walking heart rate, blood pressure, HRV, body mass).

    Serializes as ``health:DailyVitalReading`` in Turtle.

    Two live emitters spell the timestamp differently — ``health:date`` and
    ``cascade:date`` — and ``health:DailyVitalReadingShape`` requires one of
    them through an ``sh:or`` rather than a ``sh:minCount``. This SDK writes
    ``health:date`` and reads both.
    """

    type: str = field(default="DailyVitalReading", init=True)

    date: str = ""
    """
    Timestamp the reading applies to (ISO 8601 dateTime).
    Maps to ``health:date`` on write; ``cascade:date`` is also accepted on read.
    """

    value: float | None = None
    """The measured value. Maps to ``health:value``."""

    unit: str | None = None
    """Unit of measure. Maps to ``health:unit``."""

    sample_count: int | None = None
    """
    Number of underlying samples aggregated into this reading.
    Maps to ``cascade:sampleCount``.
    """

    loinc_code: str | None = None
    """
    LOINC reference for the observation, as an IRI.
    Maps to ``cascade:loincCode``.
    """

    @classmethod
    def from_dataframe(cls, df: "pd.DataFrame") -> list["DailyVitalReading"]:  # type: ignore[name-defined]
        """Reconstruct a list of DailyVitalReading records from a DataFrame."""
        from cascade_protocol.pandas_integration.dataframe import dataframe_to_records
        return dataframe_to_records(df, cls)  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Wellness container classes (health v2.5)
# ---------------------------------------------------------------------------
#
# Six containers that wellness serializers have always emitted at /wellness/.
# health v2.5 declares each rdfs:subClassOf health:HealthProfile, which makes
# the rdfs:domain health:HealthProfile already asserted on the eight history
# container properties true rather than contradicted by every pod ever
# written, and brings these subjects under health:HealthProfileShape.
#
# ``history`` preserves ENTRY ORDER. The history properties are rdf:Lists and
# these are time series: reading them into an unordered collection loses
# information that is in the file.


@dataclass
class WellnessContainer:
    """
    Base for the six wellness container classes.

    Not a :class:`CascadeRecord`: a container carries no provenance or schema
    version of its own, only an identity and its ordered history entries.
    """

    id: str = ""
    """RDF subject of the container (e.g. ``"#activity"``)."""

    type: str = ""
    """Container record type (e.g. ``"ActivityData"``)."""

    history: list[Any] = field(default_factory=list)
    """
    Ordered history entries, in the order the rdf:List carries them.
    """

    def __len__(self) -> int:
        return len(self.history)


@dataclass
class ActivityData(WellnessContainer):
    """Wellness container for ``health:dailyActivityHistory``."""

    type: str = field(default="ActivityData", init=True)


@dataclass
class SleepData(WellnessContainer):
    """Wellness container for ``health:dailySleepHistory``."""

    type: str = field(default="SleepData", init=True)


@dataclass
class HeartRateData(WellnessContainer):
    """
    Wellness container for ``health:restingHeartRateHistory`` and
    ``health:walkingHeartRateHistory``.
    """

    type: str = field(default="HeartRateData", init=True)


@dataclass
class BloodPressureData(WellnessContainer):
    """Wellness container for ``health:bloodPressureHistory``."""

    type: str = field(default="BloodPressureData", init=True)


@dataclass
class HRVData(WellnessContainer):
    """Wellness container for ``health:hrvHistory``."""

    type: str = field(default="HRVData", init=True)


@dataclass
class BodyMeasurements(WellnessContainer):
    """Wellness container for ``health:bodyMassHistory``."""

    type: str = field(default="BodyMeasurements", init=True)
