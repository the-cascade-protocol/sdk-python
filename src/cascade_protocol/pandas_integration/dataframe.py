"""
pandas DataFrame integration for Cascade Protocol records.

Provides bidirectional conversion between Cascade Protocol model objects
and pandas DataFrames. Requires: ``pip install "cascade-protocol[pandas]"``

Example:
    >>> from cascade_protocol import Medication
    >>> from cascade_protocol.pandas_integration import records_to_dataframe, dataframe_to_records
    >>>
    >>> meds = [Medication(id="urn:uuid:1", medication_name="Aspirin", ...)]
    >>> df = records_to_dataframe(meds)
    >>> restored = dataframe_to_records(df, Medication)
"""

from __future__ import annotations

from dataclasses import fields as dc_fields
from typing import Any, TypeVar, Type, overload

T = TypeVar("T")


def records_to_dataframe(records: list[Any]) -> "pd.DataFrame":
    """
    Convert a list of Cascade Protocol records to a pandas DataFrame.

    Each record becomes one row. Optional (``None``) fields are included
    as ``NaN`` / ``None`` in the DataFrame. Nested dataclass fields
    (e.g., ``EmergencyContact``) are flattened using double-underscore
    naming (``emergency_contact__contact_name``).

    Args:
        records: List of :class:`~cascade_protocol.models.common.CascadeRecord` instances.

    Returns:
        A pandas DataFrame.

    Raises:
        ImportError: If pandas is not installed.
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError(
            "pandas is required for DataFrame conversion. "
            "Install it with: pip install \"cascade-protocol[pandas]\""
        )

    if not records:
        return pd.DataFrame()

    rows: list[dict[str, Any]] = []
    for rec in records:
        row: dict[str, Any] = {}
        if hasattr(rec, "__dataclass_fields__"):
            for f in dc_fields(rec):
                val = getattr(rec, f.name)
                if hasattr(val, "__dataclass_fields__"):
                    # Flatten nested dataclass
                    for nf in dc_fields(val):
                        row[f"{f.name}__{nf.name}"] = getattr(val, nf.name)
                elif isinstance(val, list):
                    # Store lists as-is (pandas can hold object columns)
                    row[f.name] = val if val else None
                else:
                    row[f.name] = val
        else:
            # Dict-like
            row = dict(rec)
        rows.append(row)

    return pd.DataFrame(rows)


def dataframe_to_records(df: "pd.DataFrame", cls: Type[T]) -> list[T]:
    """
    Convert a pandas DataFrame back to a list of Cascade Protocol record objects.

    The DataFrame column names must match the snake_case field names of the
    target class. Columns that don't correspond to known fields are ignored.
    ``NaN`` values are converted to ``None``.

    Args:
        df: A pandas DataFrame (typically produced by :func:`records_to_dataframe`
            or :meth:`RecordSet.to_dataframe`).
        cls: The target dataclass class (e.g., :class:`~cascade_protocol.models.Medication`).

    Returns:
        A list of instances of ``cls``.

    Raises:
        ImportError: If pandas is not installed.
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError(
            "pandas is required for DataFrame conversion. "
            "Install it with: pip install \"cascade-protocol[pandas]\""
        )

    if df.empty:
        return []

    if not hasattr(cls, "__dataclass_fields__"):
        raise TypeError(f"{cls} is not a dataclass")

    valid_fields = {f.name for f in dc_fields(cls)}
    results: list[T] = []

    for _, row in df.iterrows():
        kwargs: dict[str, Any] = {}
        for col, val in row.items():
            col_str = str(col)
            if col_str in valid_fields:
                # Convert NaN to None
                if _is_na(val):
                    kwargs[col_str] = None
                else:
                    kwargs[col_str] = val
        try:
            results.append(cls(**kwargs))  # type: ignore[call-arg]
        except TypeError:
            # If constructor fails, try with only valid non-None kwargs
            filtered = {k: v for k, v in kwargs.items() if v is not None}
            results.append(cls(**filtered))  # type: ignore[call-arg]

    return results


def _is_na(val: Any) -> bool:
    """Return True if the value is NaN or None."""
    if val is None:
        return True
    try:
        import math
        if isinstance(val, float) and math.isnan(val):
            return True
    except (TypeError, ValueError):
        pass
    return False
