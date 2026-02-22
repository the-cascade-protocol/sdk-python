"""
Health profile aggregate data model for the Cascade Protocol.

Represents a complete health profile containing arrays of all
clinical and wellness record types. This is the top-level container
corresponding to a Cascade Pod's data inventory.

See: https://cascadeprotocol.org/docs/cascade-protocol-schemas
"""

from __future__ import annotations

from dataclasses import dataclass, field

from cascade_protocol.models.medication import Medication
from cascade_protocol.models.condition import Condition
from cascade_protocol.models.allergy import Allergy
from cascade_protocol.models.lab_result import LabResult
from cascade_protocol.models.vital_sign import VitalSign
from cascade_protocol.models.immunization import Immunization
from cascade_protocol.models.procedure import Procedure
from cascade_protocol.models.family_history import FamilyHistory
from cascade_protocol.models.coverage import Coverage
from cascade_protocol.models.patient_profile import PatientProfile
from cascade_protocol.models.wellness import ActivitySnapshot, SleepSnapshot


@dataclass
class HealthProfile:
    """
    A complete health profile aggregating all Cascade Protocol record types.

    This dataclass mirrors the structure of a Cascade Pod, providing
    typed access to all clinical and wellness data categories.
    """

    patient_profile: PatientProfile | None = None
    """Patient demographic and identification data."""

    medications: list[Medication] = field(default_factory=list)
    """Active and historical medication records."""

    conditions: list[Condition] = field(default_factory=list)
    """Active and resolved medical conditions."""

    allergies: list[Allergy] = field(default_factory=list)
    """Known allergies and intolerances."""

    lab_results: list[LabResult] = field(default_factory=list)
    """Laboratory test results."""

    vital_signs: list[VitalSign] = field(default_factory=list)
    """Clinical and device-generated vital sign measurements."""

    immunizations: list[Immunization] = field(default_factory=list)
    """Vaccine administration records."""

    procedures: list[Procedure] = field(default_factory=list)
    """Clinical procedure records."""

    family_history: list[FamilyHistory] = field(default_factory=list)
    """Family health history entries."""

    coverage: list[Coverage] = field(default_factory=list)
    """Insurance coverage and plan records."""

    activity_snapshots: list[ActivitySnapshot] = field(default_factory=list)
    """Daily activity summaries from wearable devices."""

    sleep_snapshots: list[SleepSnapshot] = field(default_factory=list)
    """Nightly sleep summaries from wearable devices."""

    def summary(self) -> dict[str, int]:
        """Return a summary count of all record types."""
        return {
            "medications": len(self.medications),
            "conditions": len(self.conditions),
            "allergies": len(self.allergies),
            "lab_results": len(self.lab_results),
            "vital_signs": len(self.vital_signs),
            "immunizations": len(self.immunizations),
            "procedures": len(self.procedures),
            "family_history": len(self.family_history),
            "coverage": len(self.coverage),
            "activity_snapshots": len(self.activity_snapshots),
            "sleep_snapshots": len(self.sleep_snapshots),
        }
