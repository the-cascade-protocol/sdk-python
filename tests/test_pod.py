"""
Tests for the Cascade Protocol Pod class.
"""

from __future__ import annotations

import os
import tempfile
import textwrap
from pathlib import Path

import pytest
from cascade_protocol import Pod, RecordSet


# ---------------------------------------------------------------------------
# Fixture: minimal pod directory
# ---------------------------------------------------------------------------

SAMPLE_MEDICATIONS_TTL = textwrap.dedent("""\
    @prefix cascade: <https://ns.cascadeprotocol.org/core/v1#> .
    @prefix health: <https://ns.cascadeprotocol.org/health/v1#> .
    @prefix clinical: <https://ns.cascadeprotocol.org/clinical/v1#> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

    <urn:uuid:med0-0001-aaaa-bbbb-ccccddddeeee> a health:MedicationRecord ;
        health:medicationName "Lisinopril" ;
        health:isActive true ;
        cascade:dataProvenance cascade:ClinicalGenerated ;
        cascade:schemaVersion "1.3" ;
        health:dose "20 mg" ;
        health:frequency "once daily" .
""")


@pytest.fixture
def temp_pod(tmp_path):
    """Create a minimal temporary pod directory structure."""
    clinical_dir = tmp_path / "clinical"
    clinical_dir.mkdir()
    (clinical_dir / "medications.ttl").write_text(SAMPLE_MEDICATIONS_TTL)
    return tmp_path


class TestPodOpen:
    def test_open_valid_directory(self, temp_pod):
        pod = Pod.open(temp_pod)
        assert pod.path == temp_pod

    def test_open_nonexistent_raises(self):
        with pytest.raises(FileNotFoundError):
            Pod.open("/nonexistent/path/that/does/not/exist")

    def test_open_file_raises(self, tmp_path):
        f = tmp_path / "not_a_dir.txt"
        f.write_text("hello")
        with pytest.raises(NotADirectoryError):
            Pod.open(f)

    def test_open_string_path(self, temp_pod):
        pod = Pod.open(str(temp_pod))
        assert pod.path == temp_pod


class TestPodQuery:
    def test_query_medications(self, temp_pod):
        pod = Pod.open(temp_pod)
        record_set = pod.query("medications")
        assert isinstance(record_set, RecordSet)
        assert len(record_set) == 1

    def test_query_missing_type_returns_empty(self, temp_pod):
        pod = Pod.open(temp_pod)
        record_set = pod.query("conditions")
        assert len(record_set) == 0

    def test_query_unknown_type_raises(self, temp_pod):
        pod = Pod.open(temp_pod)
        with pytest.raises(ValueError, match="Unknown data type"):
            pod.query("completely_unknown_type")

    def test_query_alias(self, temp_pod):
        pod = Pod.open(temp_pod)
        record_set = pod.query("meds")  # alias for "medications"
        assert len(record_set) == 1

    def test_record_set_iteration(self, temp_pod):
        pod = Pod.open(temp_pod)
        record_set = pod.query("medications")
        meds = list(record_set)
        assert len(meds) == 1
        from cascade_protocol import Medication
        assert isinstance(meds[0], Medication)

    def test_record_set_first(self, temp_pod):
        pod = Pod.open(temp_pod)
        record_set = pod.query("medications")
        first = record_set.first()
        assert first is not None

    def test_record_set_repr(self, temp_pod):
        pod = Pod.open(temp_pod)
        record_set = pod.query("medications")
        assert "medications" in repr(record_set)
        assert "1" in repr(record_set)


class TestPodListFiles:
    def test_list_files(self, temp_pod):
        pod = Pod.open(temp_pod)
        files = pod.list_files()
        assert len(files) == 1
        assert files[0].name == "medications.ttl"


class TestReferencePatientPod:
    """Integration tests against the actual reference patient pod."""

    REFERENCE_POD_PATH = Path(__file__).parent.parent.parent / "reference-patient-pod"

    @pytest.mark.skipif(
        not (Path(__file__).parent.parent.parent / "reference-patient-pod").exists(),
        reason="Reference patient pod not available",
    )
    def test_open_reference_pod(self):
        pod = Pod.open(self.REFERENCE_POD_PATH)
        assert pod.path.exists()

    @pytest.mark.skipif(
        not (Path(__file__).parent.parent.parent / "reference-patient-pod").exists(),
        reason="Reference patient pod not available",
    )
    def test_query_reference_medications(self):
        pod = Pod.open(self.REFERENCE_POD_PATH)
        meds = pod.query("medications")
        # Reference pod should have medications
        assert len(meds) >= 1

    @pytest.mark.skipif(
        not (Path(__file__).parent.parent.parent / "reference-patient-pod").exists(),
        reason="Reference patient pod not available",
    )
    def test_query_reference_conditions(self):
        pod = Pod.open(self.REFERENCE_POD_PATH)
        conditions = pod.query("conditions")
        assert len(conditions) >= 1
