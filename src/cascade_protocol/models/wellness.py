"""
Wellness data models for the Cascade Protocol.

Represents daily activity and sleep snapshots typically sourced from
wearable devices or HealthKit data.

RDF types:
- ``health:ActivitySnapshot``
- ``health:SleepSnapshot``

Vocabulary: https://ns.cascadeprotocol.org/health/v1#

See: https://cascadeprotocol.org/docs/cascade-protocol-schemas
"""

from __future__ import annotations

from dataclasses import dataclass, field

from cascade_protocol.models.common import CascadeRecord


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
