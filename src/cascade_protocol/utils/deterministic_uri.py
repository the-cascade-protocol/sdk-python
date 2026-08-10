"""
Deterministic URI generation for the Cascade Protocol Python SDK.

CDP-UUID: Cascade Protocol Deterministic UUID.

All Cascade Protocol SDKs generate identical URIs for equivalent records.
This module implements the same algorithm as cascade-cli's ``contentHashedUri()``.

Cross-SDK test vector:
    deterministic_uuid("hello") == "aaf4c61d-dcc5-58a2-9abe-de0f3b482cd9"
"""

from __future__ import annotations

import hashlib
import uuid as _uuid
from collections.abc import Sequence
from typing import Union

# A content field may now hold several codes: health v2.6 and clinical v1.14
# made icd10Code, snomedCode and testCode 0..*, and a caller holding a
# record's field passes whatever that field holds. Note that ``str`` is itself
# a ``Sequence[str]``, so every check below tests for ``str`` first.
CodeValue = Union[str, Sequence[str], None]


def deterministic_uuid(input_str: str) -> str:
    """Return a deterministic UUID-shaped string derived from *input_str*.

    Algorithm: SHA-1 of the UTF-8 encoded input, formatted using the UUID v5
    layout (version nibble = 5, variant bits = 10xx xxxx).

    This matches the ``contentHashedUri`` implementation in cascade-cli exactly.

    Args:
        input_str: Arbitrary string to hash.

    Returns:
        A lowercase UUID string, e.g. ``"aaf4c61d-dcc5-58a2-9abe-de0f3b482cd9"``.

    Example::

        >>> deterministic_uuid("hello")
        'aaf4c61d-dcc5-58a2-9abe-de0f3b482cd9'
    """
    h = hashlib.sha1(input_str.encode("utf-8")).hexdigest()
    # Layout matches TypeScript deterministicUuid(): h[12] is skipped (replaced by version '5')
    # Variant: bits from h[16:18]; then h[18:20]; then h[20:32]
    variant_byte = (int(h[16:18], 16) & 0x3F) | 0x80
    v = format(variant_byte, "02x")
    return f"{h[0:8]}-{h[8:12]}-5{h[13:16]}-{v}{h[18:20]}-{h[20:32]}"


def _canonical_field_value(value: CodeValue) -> str | None:
    """Reduce one content-field value to the string that enters the hash.

    A scalar passes through untouched, so every URI minted before multi-valued
    codes existed is minted identically now. A sequence is deduplicated,
    sorted and comma-joined.

    Sorting is not a formatting preference. These fields are FHIR codings,
    which are a set: two exports of one record that list the same codings in a
    different order are the same record, and an identity that depended on the
    order would split it in two. Sorting also keeps the value out of reach of
    iteration order: the set built here is consumed by ``sorted()`` and never
    iterated directly, so no hash seed can reach the identifier.

    A one-element sequence canonicalizes to exactly the scalar form, which is
    what keeps already-written identities from moving when a field that held
    one code becomes a list holding one code.
    """
    if value is None:
        return None
    if isinstance(value, str):
        return value
    codes = sorted({item.strip() for item in value if item is not None and item.strip()})
    return ",".join(codes) if codes else None


def content_hashed_uri(
    resource_type: str,
    content_fields: dict[str, CodeValue],
    fallback_id: str | None = None,
) -> str:
    """Generate a deterministic ``urn:uuid:`` URI from clinical content fields.

    This is the primary entry point for deterministic record identity across all
    Cascade Protocol SDKs.  Given the same *resource_type* and *content_fields*
    the function will always return the same URI, regardless of the SDK or
    platform used.

    Algorithm:
        0. Canonicalize each value: a string is used as-is; a sequence of
           strings is deduplicated, sorted and joined with ``","``. A
           one-element sequence therefore hashes identically to the bare
           string, so multi-valued codes did not move any existing identity.
        1. Filter entries where the value is non-``None`` and non-empty after
           ``str.strip()``.
        2. Sort the remaining entries by key (ascending, lexicographic).
        3. Map each entry to the string ``"key=value"``.
        4. Join with ``"|"``.
        5. Build an identity string ``"{resource_type}::{joined}"``.
        6. If the identity has content → ``"urn:uuid:" + deterministic_uuid(identity)``
        7. If identity is empty but *fallback_id* is provided →
           ``"urn:uuid:" + deterministic_uuid(f"{resource_type}:{fallback_id}")``
        8. Otherwise → ``"urn:uuid:" + str(uuid.uuid4())`` (random, non-deterministic)

    Args:
        resource_type: FHIR resource type string, e.g. ``"Patient"``,
            ``"Observation"``.
        content_fields: Mapping of field names to their values.  A value is
            either a string or a sequence of strings (a multi-valued code).
            ``None`` and empty values are excluded from the hash.

            Cross-SDK note: the scalar behaviour is byte-identical to
            cascade-cli's ``contentHashedUri()``. The sequence rule is an
            extension this SDK defines, and the other SDKs do not implement it
            yet, so a URI minted here from a MULTI-code field will not match
            one minted there until the rule is written into the shared
            conformance vectors.
        fallback_id: Optional opaque identifier used when *content_fields*
            produces no content.  Generates a deterministic URI from
            ``"{resource_type}:{fallback_id}"``.

    Returns:
        A ``urn:uuid:`` URI string.

    Example::

        >>> content_hashed_uri("Patient", {"dob": "1985-03-15", "given": "John"})
        'urn:uuid:...'
    """
    canonicalized = ((k, _canonical_field_value(v)) for k, v in content_fields.items())
    entries = [
        (k, v)
        for k, v in canonicalized
        if v is not None and v.strip()
    ]
    entries.sort(key=lambda x: x[0])
    content = "|".join(f"{k}={v}" for k, v in entries)

    if content:
        return f"urn:uuid:{deterministic_uuid(f'{resource_type}::{content}')}"
    if fallback_id:
        return f"urn:uuid:{deterministic_uuid(f'{resource_type}:{fallback_id}')}"
    return f"urn:uuid:{_uuid.uuid4()}"


# ---------------------------------------------------------------------------
# Convenience helpers — one per major FHIR resource type
# ---------------------------------------------------------------------------

def patient_uri(
    dob: str | None = None,
    sex: str | None = None,
    family: str | None = None,
    given: str | None = None,
) -> str:
    """Return a deterministic URI for a Patient record.

    Args:
        dob: Date of birth in ISO 8601 format (``"YYYY-MM-DD"``).
        sex: Biological sex string (e.g. ``"male"``, ``"female"``).
        family: Family (last) name.
        given: Given (first) name.

    Returns:
        A ``urn:uuid:`` URI string.
    """
    return content_hashed_uri(
        "Patient",
        {"dob": dob, "sex": sex, "family": family, "given": given},
    )


def immunization_uri(
    cvx_code: str | None = None,
    date: str | None = None,
    patient: str | None = None,
) -> str:
    """Return a deterministic URI for an Immunization record.

    Args:
        cvx_code: CVX vaccine code.
        date: Administration date in ISO 8601 format.
        patient: Patient URI (``urn:uuid:…``).

    Returns:
        A ``urn:uuid:`` URI string.
    """
    return content_hashed_uri(
        "Immunization",
        {"cvxCode": cvx_code, "date": date, "patient": patient},
    )


def observation_uri(
    loinc_code: CodeValue = None,
    date: str | None = None,
    patient: str | None = None,
) -> str:
    """Return a deterministic URI for an Observation record.

    Args:
        loinc_code: LOINC code, or a sequence of them. ``health:testCode``
            is 0..* as of health v2.6, so an Observation can carry several
            codings; they are deduplicated, sorted and joined before hashing.
        date: Observation date in ISO 8601 format.
        patient: Patient URI (``urn:uuid:…``).

    Returns:
        A ``urn:uuid:`` URI string.
    """
    return content_hashed_uri(
        "Observation",
        {"loincCode": loinc_code, "date": date, "patient": patient},
    )


def condition_uri(
    snomed_code: CodeValue = None,
    icd10_code: CodeValue = None,
    onset_date: str | None = None,
    patient: str | None = None,
) -> str:
    """Return a deterministic URI for a Condition record.

    Args:
        snomed_code: SNOMED CT code, or a sequence of them. ``snomedCode``
            and ``icd10Code`` are 0..* as of health v2.6 / clinical v1.14;
            values are deduplicated, sorted and joined before hashing, so the
            same condition coded in either order gets the same URI.
        icd10_code: ICD-10 code, or a sequence of them.
        onset_date: Condition onset date in ISO 8601 format.
        patient: Patient URI (``urn:uuid:…``).

    Returns:
        A ``urn:uuid:`` URI string.
    """
    return content_hashed_uri(
        "Condition",
        {
            "snomedCode": snomed_code,
            "icd10Code": icd10_code,
            "onsetDate": onset_date,
            "patient": patient,
        },
    )


def allergy_uri(
    allergen_code: str | None = None,
    allergen_name: str | None = None,
    patient: str | None = None,
) -> str:
    """Return a deterministic URI for an AllergyIntolerance record.

    Args:
        allergen_code: Coded allergen identifier (e.g. RxNorm, SNOMED).
        allergen_name: Free-text allergen name (used when no code is available).
        patient: Patient URI (``urn:uuid:…``).

    Returns:
        A ``urn:uuid:`` URI string.
    """
    return content_hashed_uri(
        "AllergyIntolerance",
        {"allergenCode": allergen_code, "allergenName": allergen_name, "patient": patient},
    )


def medication_uri(
    rx_norm_code: str | None = None,
    start_date: str | None = None,
    patient: str | None = None,
) -> str:
    """Return a deterministic URI for a MedicationRequest record.

    Args:
        rx_norm_code: RxNorm code string.
        start_date: Medication start date in ISO 8601 format.
        patient: Patient URI (``urn:uuid:…``).

    Returns:
        A ``urn:uuid:`` URI string.
    """
    return content_hashed_uri(
        "MedicationRequest",
        {"rxNormCode": rx_norm_code, "startDate": start_date, "patient": patient},
    )
