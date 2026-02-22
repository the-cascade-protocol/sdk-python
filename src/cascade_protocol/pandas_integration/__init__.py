"""
Cascade Protocol pandas integration.

Provides utilities for converting between Cascade Protocol record objects
and pandas DataFrames.
"""

from cascade_protocol.pandas_integration.dataframe import (
    records_to_dataframe,
    dataframe_to_records,
)

__all__ = ["records_to_dataframe", "dataframe_to_records"]
