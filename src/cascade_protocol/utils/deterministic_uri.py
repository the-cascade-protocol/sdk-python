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


def content_hashed_uri(
    resource_type: str,
    content_fields: dict[str, str | None],
    fallback_id: str | None = None,
) -> str:
    """Generate a deterministic ``urn:uuid:`` URI from clinical content fields.

    This is the primary entry point for deterministic record identity across all
    Cascade Protocol SDKs.  Given the same *resource_type* and *content_fields*
    the function will always return the same URI, regardless of the SDK or
    platform used.

    Algorithm:
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
        content_fields: Mapping of field names to their string values.  ``None``
            and empty-string values are excluded from the hash.
        fallback_id: Optional opaque identifier used when *content_fields*
            produces no content.  Generates a deterministic URI from
            ``"{resource_type}:{fallback_id}"``.

    Returns:
        A ``urn:uuid:`` URI string.

    Example::

        >>> content_hashed_uri("Patient", {"dob": "1985-03-15", "given": "John"})
        'urn:uuid:...'
    """
    entries = [
        (k, v)
        for k, v in content_fields.items()
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
    loinc_code: str | None = None,
    date: str | None = None,
    patient: str | None = None,
) -> str:
    """Return a deterministic URI for an Observation record.

    Args:
        loinc_code: LOINC code string.
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
    snomed_code: str | None = None,
    icd10_code: str | None = None,
    onset_date: str | None = None,
    patient: str | None = None,
) -> str:
    """Return a deterministic URI for a Condition record.

    Args:
        snomed_code: SNOMED CT code string.
        icd10_code: ICD-10 code string.
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
