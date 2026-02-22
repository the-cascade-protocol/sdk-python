"""
Cascade Pod reader — Linked Data Platform container layout.

A Cascade Pod is a local directory structured as an LDP BasicContainer,
with Turtle files organized by data type. This module provides a ``Pod``
class for reading pod directories and querying records by type.

Pod directory layout (reference patient pod structure):
    my-pod/
        index.ttl            -- Root container manifest
        manifest.ttl         -- Full resource list
        profile/
            card.ttl
        clinical/
            medications.ttl
            conditions.ttl
            allergies.ttl
            lab-results.ttl
            vital-signs.ttl
            immunizations.ttl
            insurance.ttl
            patient-profile.ttl
        wellness/
            heart-rate.ttl
            blood-pressure.ttl
            activity.ttl
            sleep.ttl

Example:
    >>> from cascade_protocol import Pod
    >>> pod = Pod.open("./my-pod")
    >>> meds = pod.query("medications")
    >>> df = meds.to_dataframe()
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterator, TYPE_CHECKING

from cascade_protocol.models.common import CascadeRecord
from cascade_protocol.vocabularies.namespaces import TYPE_TO_MAPPING_KEY, TYPE_MAPPING

if TYPE_CHECKING:
    import pandas as pd

# ---------------------------------------------------------------------------
# Mapping from query key to (directory, filename, record_type)
# ---------------------------------------------------------------------------

# Each entry maps a user-facing query key to the TTL file path and record type
# expected inside it.
_QUERY_MAP: dict[str, dict[str, Any]] = {
    "medications": {
        "paths": ["clinical/medications.ttl", "wellness/medications.ttl"],
        "record_type": "MedicationRecord",
    },
    "conditions": {
        "paths": ["clinical/conditions.ttl"],
        "record_type": "ConditionRecord",
    },
    "allergies": {
        "paths": ["clinical/allergies.ttl"],
        "record_type": "AllergyRecord",
    },
    "lab-results": {
        "paths": ["clinical/lab-results.ttl"],
        "record_type": "LabResultRecord",
    },
    "vital-signs": {
        "paths": [
            "clinical/vital-signs.ttl",
            "wellness/heart-rate.ttl",
            "wellness/blood-pressure.ttl",
        ],
        "record_type": "VitalSign",
    },
    "immunizations": {
        "paths": ["clinical/immunizations.ttl"],
        "record_type": "ImmunizationRecord",
    },
    "procedures": {
        "paths": ["clinical/procedures.ttl"],
        "record_type": "ProcedureRecord",
    },
    "family-history": {
        "paths": ["clinical/family-history.ttl"],
        "record_type": "FamilyHistoryRecord",
    },
    "insurance": {
        "paths": ["clinical/insurance.ttl"],
        "record_type": "InsurancePlan",
    },
    "patient-profile": {
        "paths": ["clinical/patient-profile.ttl", "profile/card.ttl"],
        "record_type": "PatientProfile",
    },
    "activity": {
        "paths": ["wellness/activity.ttl"],
        "record_type": "ActivitySnapshot",
    },
    "sleep": {
        "paths": ["wellness/sleep.ttl"],
        "record_type": "SleepSnapshot",
    },
    "heart-rate": {
        "paths": ["wellness/heart-rate.ttl"],
        "record_type": "VitalSign",
    },
    "blood-pressure": {
        "paths": ["wellness/blood-pressure.ttl"],
        "record_type": "VitalSign",
    },
}

# Aliases
_QUERY_ALIASES: dict[str, str] = {
    "meds": "medications",
    "drugs": "medications",
    "conditions": "conditions",
    "diagnoses": "conditions",
    "labs": "lab-results",
    "lab_results": "lab-results",
    "vitals": "vital-signs",
    "vital_signs": "vital-signs",
    "immunizations": "immunizations",
    "vaccinations": "immunizations",
    "family_history": "family-history",
    "coverage": "insurance",
    "profile": "patient-profile",
}


class RecordSet:
    """
    A collection of Cascade Protocol records resulting from a Pod query.

    Supports iteration and optional pandas DataFrame conversion.
    """

    def __init__(self, records: list[CascadeRecord], data_type: str) -> None:
        self._records = records
        self._data_type = data_type

    def __iter__(self) -> Iterator[CascadeRecord]:
        return iter(self._records)

    def __len__(self) -> int:
        return len(self._records)

    def __repr__(self) -> str:
        return f"RecordSet(data_type={self._data_type!r}, count={len(self._records)})"

    def all(self) -> list[CascadeRecord]:
        """Return all records as a list."""
        return list(self._records)

    def first(self) -> CascadeRecord | None:
        """Return the first record, or None if empty."""
        return self._records[0] if self._records else None

    def to_dataframe(self) -> "pd.DataFrame":
        """
        Convert the record set to a pandas DataFrame.

        Requires: ``pip install "cascade-protocol[pandas]"``

        Returns:
            A pandas DataFrame with one row per record.

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

        if not self._records:
            return pd.DataFrame()

        from dataclasses import fields as dc_fields
        rows: list[dict[str, Any]] = []
        for rec in self._records:
            row: dict[str, Any] = {}
            for f in dc_fields(rec):
                val = getattr(rec, f.name)
                # Flatten nested dataclasses
                if hasattr(val, "__dataclass_fields__"):
                    for nf in dc_fields(val):
                        row[f"{f.name}__{nf.name}"] = getattr(val, nf.name)
                elif val is not None:
                    row[f.name] = val
            rows.append(row)
        return pd.DataFrame(rows)


class Pod:
    """
    A Cascade Protocol Pod — a local directory of Turtle files.

    Provides a query API for reading records by data type without loading
    the entire pod into memory.

    Example:
        >>> pod = Pod.open("./my-pod")
        >>> meds = pod.query("medications")
        >>> for med in meds:
        ...     print(med.medication_name)
        >>> df = meds.to_dataframe()
    """

    def __init__(self, path: Path) -> None:
        self._path = path

    @classmethod
    def open(cls, path: str | Path) -> "Pod":
        """
        Open a Cascade Pod at the given directory path.

        Args:
            path: Path to the pod root directory. Can be absolute or relative.

        Returns:
            A ``Pod`` instance.

        Raises:
            FileNotFoundError: If the path does not exist or is not a directory.
        """
        resolved = Path(path).resolve()
        if not resolved.exists():
            raise FileNotFoundError(f"Pod path does not exist: {resolved}")
        if not resolved.is_dir():
            raise NotADirectoryError(f"Pod path is not a directory: {resolved}")
        return cls(resolved)

    @property
    def path(self) -> Path:
        """The resolved path to the pod root directory."""
        return self._path

    def list_files(self) -> list[Path]:
        """Return all .ttl files in the pod directory."""
        return sorted(self._path.rglob("*.ttl"))

    def query(self, data_type: str) -> RecordSet:
        """
        Query the pod for records of the given data type.

        Args:
            data_type: One of the supported query keys:
                ``"medications"``, ``"conditions"``, ``"allergies"``,
                ``"lab-results"``, ``"vital-signs"``, ``"immunizations"``,
                ``"procedures"``, ``"family-history"``, ``"insurance"``,
                ``"patient-profile"``, ``"activity"``, ``"sleep"``,
                ``"heart-rate"``, ``"blood-pressure"``

        Returns:
            A :class:`RecordSet` containing all matching records.

        Raises:
            ValueError: If the data type is not recognized.
            ImportError: If rdflib is not installed.
        """
        from cascade_protocol.deserializer.turtle_parser import parse

        # Resolve alias
        query_key = _QUERY_ALIASES.get(data_type, data_type)
        spec = _QUERY_MAP.get(query_key)
        if spec is None:
            valid = sorted(set(list(_QUERY_MAP.keys()) + list(_QUERY_ALIASES.keys())))
            raise ValueError(
                f"Unknown data type: {data_type!r}. "
                f"Valid types: {valid}"
            )

        record_type = spec["record_type"]
        all_records: list[CascadeRecord] = []

        for rel_path in spec["paths"]:
            ttl_file = self._path / rel_path
            if not ttl_file.exists():
                continue
            try:
                turtle = ttl_file.read_text(encoding="utf-8")
                records = parse(turtle, record_type)
                all_records.extend(records)
            except Exception as exc:
                # Log but don't fail if one file is malformed
                import warnings
                warnings.warn(
                    f"Failed to parse {ttl_file}: {exc}",
                    stacklevel=2,
                )

        return RecordSet(all_records, query_key)

    def query_file(self, file_path: str | Path, record_type: str) -> RecordSet:
        """
        Query a specific TTL file for records of the given type.

        Args:
            file_path: Path to a TTL file (relative to pod root, or absolute).
            record_type: RDF record type string (e.g., ``"MedicationRecord"``).

        Returns:
            A :class:`RecordSet` containing all matching records.
        """
        from cascade_protocol.deserializer.turtle_parser import parse

        path = Path(file_path)
        if not path.is_absolute():
            path = self._path / path

        turtle = path.read_text(encoding="utf-8")
        records = parse(turtle, record_type)
        return RecordSet(records, record_type)

    def __repr__(self) -> str:
        return f"Pod(path={self._path!r})"
