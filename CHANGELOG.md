# Changelog

All notable changes to `cascade-protocol` (Python SDK) will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
