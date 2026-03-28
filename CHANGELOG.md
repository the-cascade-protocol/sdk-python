# Changelog

All notable changes to `cascade-protocol` (Python SDK) will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-03-27

### Added
- `content_hashed_uri(resource_type, content_fields, fallback_id=None)` — deterministic URI generator using CDP-UUID algorithm
- `deterministic_uuid(input_str)` — CDP-UUID hash function. Cross-SDK: `deterministic_uuid("hello") == "aaf4c61d-dcc5-58a2-9abe-de0f3b482cd9"`
- Typed convenience helpers: `patient_uri()`, `immunization_uri()`, `observation_uri()`, `condition_uri()`, `allergy_uri()`, `medication_uri()`
- All symbols exported from `cascade_protocol` package root
- Cross-SDK conformance test vectors
- 31 tests total

## [1.1.0] - 2026-03-20

### Added
- `Encounter` model (`clinical:Encounter`) — clinical encounters (office visits, consultations)
- `MedicationAdministration` model (`clinical:MedicationAdministration`) — single-event medication administration records
- `ImplantedDevice` model (`clinical:ImplantedDevice`) — permanent implanted medical devices
- `ImagingStudy` model (`clinical:ImagingStudy`) — diagnostic imaging metadata
- TYPE_MAPPING and TYPE_TO_MAPPING_KEY entries for all new types and coverage v1.3 classes
- PROPERTY_PREDICATES and PROPERTY_PREDICATES_CAMEL entries for all new clinical and coverage v1.3 properties
- Core v2.8 FHIR passthrough predicates: `layer_promotion_status`, `fhir_json`, `source_record_date`

### Changed
- VOCAB_VERSIONS updated: core=2.8, clinical=1.7, coverage=1.3

## [1.0.0] - 2026-02-22

### Added

- Initial release of the Cascade Protocol Python SDK.
- Full data model support for all Phase 1 record types:
  - `Medication` (`health:MedicationRecord`)
  - `Condition` (`health:ConditionRecord`)
  - `Allergy` (`health:AllergyRecord`)
  - `LabResult` (`health:LabResultRecord`)
  - `VitalSign` (`clinical:VitalSign`)
  - `Immunization` (`health:ImmunizationRecord`)
  - `Procedure` (`health:ProcedureRecord`)
  - `FamilyHistory` (`health:FamilyHistoryRecord`)
  - `Coverage` (`coverage:InsurancePlan`)
  - `PatientProfile` (`cascade:PatientProfile`)
  - `ActivitySnapshot` (`health:ActivitySnapshot`)
  - `SleepSnapshot` (`health:SleepSnapshot`)
  - `HealthProfile` (aggregate container)
- `serialize(record)` — converts any Cascade record to valid RDF/Turtle
- `validate(turtle)` — structural validation with optional SHACL support
- `parse(turtle, type)` — deserializes Turtle back to Python model objects
- `Pod` class for reading Cascade Pod directories (LDP container layout)
- `RecordSet.to_dataframe()` — pandas DataFrame conversion (optional dependency)
- `<ModelClass>.from_dataframe(df)` — reconstruct models from DataFrame
- Conformance test suite integration (`tests/test_conformance.py`)
- Three example Jupyter notebooks
- Namespace constants matching the TypeScript SDK exactly
- Zero network calls; all processing is local
- Apache 2.0 license

### Conformance

- Passes all positive conformance fixtures from the Cascade Protocol conformance suite v1.0
- Structural validation correctly rejects all negative conformance fixtures

[1.0.0]: https://github.com/cascade-protocol/sdk-python/releases/tag/v1.0.0
