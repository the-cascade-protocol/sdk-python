"""VOCAB_VERSIONS is the file downstream drift checks read.

``spec/scripts/check-downstream-versions.sh`` compares this repo's VOCAB_VERSIONS
against the canonical one. That check runs from the spec checkout, so nothing in
THIS suite notices when the file is edited to claim a version whose terms were
never implemented — the drift check would then read "in sync" and be wrong in the
direction that matters, because a claimed version is what stops the next sync
from looking at that vocabulary again.

These tests pin the two halves that must agree: the file parses to the versions
this repo claims, and each claimed version's terms are actually registered. They
are deliberately cheap and deliberately not a substitute for the per-vocabulary
suites, which check semantics.
"""

from __future__ import annotations

from pathlib import Path

from cascade_protocol.vocabularies.namespaces import (
    PROPERTY_PREDICATES,
    TYPE_MAPPING,
    TYPE_TO_MAPPING_KEY,
)

_REPO_ROOT = Path(__file__).resolve().parent.parent
_VOCAB_VERSIONS = _REPO_ROOT / "VOCAB_VERSIONS"


def _read_versions(path: Path) -> dict[str, str]:
    versions: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        versions[name.strip()] = value.strip()
    return versions


def test_vocab_versions_file_exists_and_parses() -> None:
    assert _VOCAB_VERSIONS.exists()
    versions = _read_versions(_VOCAB_VERSIONS)
    assert set(versions) >= {"core", "health", "clinical", "coverage"}


def test_the_wave_4_versions_are_claimed() -> None:
    versions = _read_versions(_VOCAB_VERSIONS)
    # core is 3.8, not 3.7: the wave-4 sync also picked up core v3.8's single
    # term, cascade:PatientReported. clinical and coverage deliberately do NOT
    # move to the v1.17 / v1.6 that ship alongside it upstream — that is a
    # shapes-only nested-severity fix this SDK has not implemented, and
    # claiming it would stop a later sync from looking at it.
    assert versions["core"] == "3.8"
    assert versions["health"] == "2.8"
    assert versions["clinical"] == "1.16"
    assert versions["coverage"] == "1.5"


def test_core_3_8_term_backs_the_claim() -> None:
    """The one term core v3.8 adds. Claiming the version without admitting it
    would leave this SDK rejecting a value every shape permits while reporting
    itself in sync."""
    from cascade_protocol.validator.validator import _VALID_PROVENANCE_TYPES

    assert "PatientReported" in _VALID_PROVENANCE_TYPES


def test_core_3_7_terms_back_the_claim() -> None:
    """Claiming core=3.7 with no cascade:Attachment support would make the
    downstream drift check report "in sync" and be wrong."""
    assert TYPE_MAPPING[TYPE_TO_MAPPING_KEY["Attachment"]]["rdf_type"] == "cascade:Attachment"
    for snake in (
        "has_attachment", "attachment_path", "attachment_media_type",
        "content_hash", "hash_algorithm", "byte_size", "attachment_title",
    ):
        assert snake in PROPERTY_PREDICATES


def test_clinical_1_16_terms_back_the_claim() -> None:
    assert (
        TYPE_MAPPING[TYPE_TO_MAPPING_KEY["EncounterParticipant"]]["rdf_type"]
        == "clinical:EncounterParticipant"
    )
    for snake in (
        "encounter_class_display", "encounter_class_system", "encounter_reason",
        "admit_source", "discharge_disposition", "has_participant",
        "participant_name", "participant_role", "participant_role_code",
        "participant_specialty", "business_identifier",
        "document_reference_status", "document_author_name", "authenticator_name",
    ):
        assert snake in PROPERTY_PREDICATES


def test_coverage_1_5_term_backs_the_claim() -> None:
    from cascade_protocol.serializer.turtle_serializer import _TYPE_PREDICATE_OVERRIDES

    assert _TYPE_PREDICATE_OVERRIDES["InsurancePlan"]["status"] == "coverage:status"


# A test comparing this file against spec/VOCAB_VERSIONS was written and then
# removed. CI does not check out spec, so it could only have been guarded with
# a skipif — and a check that skips in the one environment that gates merges is
# not a check, it is a green tick. That is the same reasoning models/common.py
# records for pinning the interpretation value set by CHECKSUM rather than
# reading the shape file.
#
# The literal assertions above are the gate. Drift against the canonical file is
# the spec repo's own job: `sh scripts/check-downstream-versions.sh`.
