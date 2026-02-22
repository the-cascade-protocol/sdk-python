"""
Patient profile data model for the Cascade Protocol.

Represents the core demographic and identification data for a patient,
including optional nested structures for emergency contact, address,
and preferred pharmacy.

RDF type: ``cascade:PatientProfile``
Vocabulary: https://ns.cascadeprotocol.org/core/v1#

See: https://cascadeprotocol.org/docs/cascade-protocol-schemas
"""

from __future__ import annotations

from dataclasses import dataclass, field

from cascade_protocol.models.common import CascadeRecord


@dataclass
class EmergencyContact:
    """
    Emergency contact information for a patient.

    Serializes as a blank node of type ``cascade:EmergencyContact`` in Turtle.
    """

    contact_name: str = ""
    """Name of the emergency contact. Maps to ``cascade:contactName``."""

    contact_relationship: str | None = None
    """Relationship of the contact to the patient. Maps to ``cascade:contactRelationship``."""

    contact_phone: str | None = None
    """Phone number of the emergency contact. Maps to ``cascade:contactPhone``."""


@dataclass
class Address:
    """
    Postal address for a patient.

    Serializes as a blank node of type ``cascade:Address`` in Turtle.
    """

    address_line: str | None = None
    """Street address line. Maps to ``cascade:addressLine``."""

    address_city: str | None = None
    """City name. Maps to ``cascade:addressCity``."""

    address_state: str | None = None
    """State or province code. Maps to ``cascade:addressState``."""

    address_postal_code: str | None = None
    """Postal / ZIP code. Maps to ``cascade:addressPostalCode``."""

    address_country: str | None = None
    """Country code (e.g., ``"US"``). Maps to ``cascade:addressCountry``."""

    address_use: str | None = None
    """Address use type (e.g., ``"home"``, ``"work"``). Maps to ``cascade:addressUse``."""


@dataclass
class PharmacyInfo:
    """
    Preferred pharmacy information for a patient.

    Serializes as a blank node of type ``cascade:PharmacyInfo`` in Turtle.
    """

    pharmacy_name: str = ""
    """Name of the pharmacy. Maps to ``cascade:pharmacyName``."""

    pharmacy_address: str | None = None
    """Full address of the pharmacy. Maps to ``cascade:pharmacyAddress``."""

    pharmacy_phone: str | None = None
    """Phone number of the pharmacy. Maps to ``cascade:pharmacyPhone``."""


@dataclass
class PatientProfile(CascadeRecord):
    """
    A patient profile record in the Cascade Protocol.

    Required fields: ``date_of_birth``, ``biological_sex``, ``data_provenance``, ``schema_version``.
    Date of birth uses ISO 8601 date format (YYYY-MM-DD).

    Serializes as ``cascade:PatientProfile`` in Turtle.
    """

    type: str = field(default="PatientProfile", init=True)

    date_of_birth: str = ""
    """
    Date of birth (ISO 8601 date: ``YYYY-MM-DD``).
    Maps to ``cascade:dateOfBirth`` in Turtle serialization.
    """

    biological_sex: str = ""
    """
    Biological sex for clinical calculations (male, female, intersex).
    Maps to ``cascade:biologicalSex`` in Turtle serialization.
    """

    computed_age: int | None = None
    """
    Computed age in years based on date of birth.
    Maps to ``cascade:computedAge`` in Turtle serialization.
    """

    age_group: str | None = None
    """
    Age group classification.
    Maps to ``cascade:ageGroup`` in Turtle serialization.
    """

    name: str | None = None
    """
    Full display name of the patient.
    Maps to ``foaf:name`` in Turtle serialization.
    """

    given_name: str | None = None
    """
    Given (first) name of the patient.
    Maps to ``foaf:givenName`` in Turtle serialization.
    """

    family_name: str | None = None
    """
    Family (last) name of the patient.
    Maps to ``foaf:familyName`` in Turtle serialization.
    """

    blood_type: str | None = None
    """
    Blood type classification.
    Maps to ``health:bloodType`` in Turtle serialization.
    """

    gender_identity: str | None = None
    """
    Gender identity as self-reported by the patient.
    Maps to ``cascade:genderIdentity`` in Turtle serialization.
    """

    profile_id: str | None = None
    """
    Unique profile identifier (typically a UUID).
    Maps to ``cascade:profileId`` in Turtle serialization.
    """

    emergency_contact: EmergencyContact | None = None
    """
    Emergency contact information.
    Maps to ``cascade:emergencyContact`` as a blank node in Turtle serialization.
    """

    address: Address | None = None
    """
    Patient address.
    Maps to ``cascade:address`` as a blank node in Turtle serialization.
    """

    preferred_pharmacy: PharmacyInfo | None = None
    """
    Preferred pharmacy information.
    Maps to ``cascade:preferredPharmacy`` as a blank node in Turtle serialization.
    """

    @classmethod
    def from_dataframe(cls, df: "pd.DataFrame") -> list["PatientProfile"]:  # type: ignore[name-defined]
        """Reconstruct a list of PatientProfile records from a pandas DataFrame."""
        from cascade_protocol.pandas_integration.dataframe import dataframe_to_records
        return dataframe_to_records(df, cls)  # type: ignore[return-value]
