# Changelog

All notable changes to `cascade-protocol` (Python SDK) will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-08-10

Vocabulary sync: core v3.5, health v2.6, clinical v1.14, coverage v1.4, checkup v3.3.

Major, not minor: four record fields change type, and two exported type aliases change membership. Both are breaking for a published package, and the previous sync deliberately did not row these vocabularies because doing so without these model changes would have been a claim the models could not back.

### Changed (BREAKING)

- `LabResult.test_code`, `LabResult.lab_category`, `Condition.icd10_code`, `Condition.snomed_code`, `VitalSign.snomed_code`, `Procedure.snomed_code`, `Encounter.snomed_code` and `MedicationAdministration.snomed_code` are now `list[str] | None` instead of `str | None`. FHIR R4 `CodeableConcept.coding` is 0..* and `Observation.category` is 0..*, and health v2.6 / clinical v1.14 dropped `sh:maxCount 1` accordingly: a record that preserved every coding the source sent was being rejected for preserving it. `None` still means the property is absent, which is what a record that never carried the field reads back as.
- `LabInterpretation` and `VitalInterpretation` are now aliases of the new `ObservationInterpretation`, which is the 60-value set health v2.6 and clinical v1.14 accept. Both previously named `"elevated"`, which no Cascade shape has ever accepted, and omitted `"high"`, which every one of them has. Code annotated with either alias and assigning `"elevated"` will now fail type checking, correctly.

Migration: pass a list where you passed a string (`snomed_code=["http://snomed.info/sct/44054006"]`). A scalar is still serialized rather than dropped, so existing calls keep producing correct Turtle, but they no longer type-check. `parse()` always returns a list for these fields.

### Added

Core v3.5:
- `cascade:sourceIdentity` registered in `PROPERTY_PREDICATES` (snake and camel) and carried on `CascadeRecord`, so every record type has it. This is the ORIGIN axis: the canonical, transport-independent identity of the organization a record came from, as a scheme-prefixed `org:` / `ns:` / `transport:` token. It is deliberately distinct from `cascade:sourceSystem` (the ingestion batch) and `clinical:sourceEHR` (a display label), and it is the only one of the three usable as a reconciliation key. Carried and not validated: the slug normalization is defined in `core.ttl` and belongs to the producers that mint the value.

Health v2.6 and clinical v1.14:
- `ObservationInterpretation` type alias plus `OBSERVATION_INTERPRETATION_CODES` (ordered tuple) and `OBSERVATION_INTERPRETATION_VALUES` (frozenset), exported from the package root. The 49 selectable codes of the HL7 v3 ObservationInterpretation code system (version 3.0.0, in the code system's own order), plus the data-absent-reason code `"unknown"`, plus the ten retained legacy words. Laboratories report susceptibility (`S`/`I`/`R`), detection (`POS`/`NEG`/`DET`/`ND`/`IND`), reactivity (`RR`/`WR`/`NR`) and change (`B`/`D`/`U`/`W`) results, all conformant FHIR, and none of them had any representation here.
- The value set is enforced by `validate()` / `validate_dict()`, keyed on the property so it covers `health:interpretation` and `clinical:interpretation` alike. An out-of-vocabulary value was previously accepted silently.
- The list is pinned by a SHA-256 checksum recorded next to the constant and recomputed from the constant in the test suite. This package's CI has no `spec` checkout, so a test that read the shape file would have to skip when the checkout is absent, and a check that can skip is not a check.
- The serializer writes one repeated predicate per value for the multi-valued code fields, not an `rdf:List`. A collection is a single blank-node object, which fails a shape asserting `sh:datatype` on each value.
- The deserializer groups repeated predicates back into a list and sorts it. rdflib yields the objects of a repeated predicate in an order that is neither document nor insertion order and varies between processes, so there is no original order to recover, and these properties are FHIR codings, which are a set.
- `content_hashed_uri()` accepts a sequence for any content field, deduplicating, sorting and comma-joining it. A one-element sequence hashes identically to the bare string, so no identity already written moves. `condition_uri()` and `observation_uri()` take sequences on their coded parameters.

### Fixed
- `interpretation` docstrings on `LabResult` and `VitalSign` named a value set that was wrong in both directions.

### Known gaps
- `validator.py` accepts one value the ratified shapes reject: `"elevated"`. This package's own `LabInterpretation` and `VitalInterpretation` named it through v1.5.0 and the conformance corpus still asserts it must be accepted (`vital-001` and `vital-004` are positive fixtures carrying it), so rejecting it would break data this SDK called valid and fail this SDK against the ecosystem's own oracle. Isolated in `_SDK_LEGACY_INTERPRETATIONS` with its removal trigger recorded; a record carrying it still fails SHACL validation.
- The `content_hashed_uri()` sequence rule is defined by this SDK and is not yet in the shared cross-SDK vectors, so a URI minted from a multi-code field will not match one minted by another SDK until it is.
- `Encounter` and `MedicationAdministration` carry the multi-valued field but remain serialize-only: neither is registered in the deserializer. Predates this release.

## [1.5.0] - 2026-08-04

### Added

Core v3.4 — pod export manifest (all 32 terms):
- `ExportManifest`, `RecordSummary`, `InteractionScenario` and `DeviceSource` models.
- `serialize_export_manifest()`, `parse_export_manifest()` and `Pod.manifest()`. A pod's `manifest.ttl` was previously unreadable: none of the 32 terms was registered, so the file parsed to nothing.
- `ExportManifest` is modelled on `dcat:Dataset`, so its descriptive fields map to `dcterms:title` / `description` / `created` / `creator` rather than to Cascade-specific inventions.
- `RECORD_SUMMARY_COUNT_CLASSES` pairs each entity count with the `void:class` it counts (`cascade:RecordSummary` is a `void:Dataset` and the counts are `void:entities` subproperties). `RECORD_SUMMARY_DAY_COUNTS` holds the five day counts, which are deliberately not entity counts: a 30-day heart rate history holds far more than 30 readings.
- Reading-level `cascade:date`, `cascade:sampleCount` and `cascade:loincCode`.

Health v2.5:
- `DailyActivitySnapshot`, `DailySleepSnapshot`, `DailyVitalReading` models — the single-day history entries, kept distinct from the 7-day `ActivitySnapshot` / `SleepSnapshot` aggregates.
- The five daily-snapshot properties (`steps`, `activeEnergyKcal`, `exerciseMinutes`, `standHours`, `durationHours`). The other 35 properties v2.5 defines were already supported.
- The four `health:sleepQuality` named individuals, read and written as `health:` IRIs (`health:sleepQuality health:Good`) rather than string literals.
- Six wellness container models (`ActivityData`, `SleepData`, `HeartRateData`, `BloodPressureData`, `HRVData`, `BodyMeasurements`) with `parse_wellness_container()` and `Pod.containers()`, which preserve `rdf:List` entry order — the histories are time series and order is part of the data.
- `Pod` query keys `daily-activity`, `daily-sleep`, `daily-vitals`.

Clinical v1.10-v1.13:
- `has_encounter`, `indication_reference`, `parsed_indication_reference` and `linked_condition` as traversable IRI edges on `Condition`, `Medication`, `Procedure`, `LabResult` and `MedicationAdministration`.
- `linked_condition_ids` registered for read only (deprecated in v1.10, retained so existing data is not dropped on parse; never written).
- `DEPRECATED_TYPE_ALIASES`: the deserializer accepts `clinical:LabResult`, `clinical:Condition`, `clinical:Allergy` and `clinical:Immunization` (deprecated in v1.13, not removed — existing pods contain them). The serializer emits only the `health:` forms.

### Fixed
- `clinical:socialHistoryCategory` is now checked against its value set. The version file claimed clinical v1.9 support but the validator accepted any category.
- `health:activeEnergyKcal` and `health:durationHours` now serialize with an explicit `^^xsd:decimal`. A whole-numbered value emitted as a bare Turtle numeric is `xsd:integer`, which violates the shape — a defect that only appeared on round numbers.
- Bare code values on `loincCode` / `testCode` / `snomedCode` / `icd10Code` / `rxNormCode` are expanded against their code system instead of being written as relative IRIs, which resolved against the document base and denoted a different resource per host.

### Changed
- VOCAB_VERSIONS updated: core=3.4, health=2.5, clinical=1.13.
- `dcat` and `void` registered in `NAMESPACES` as URI constants for the core v3.4 superclass axioms. The SDK does no RDFS/OWL inference over them.

### Known gaps
- `health:BloodPressureReading` and `health:HRVReading` are not modelled, so `BloodPressureData` and `HRVData` containers read with an empty history.
- `parse()` returns an empty list for several record types that serialize correctly (`Encounter`, `MedicationAdministration`, `ImplantedDevice`, `ImagingStudy`, `ClaimRecord`, `BenefitStatement`, `DenialNotice`, `AppealRecord`, `ClinicalSocialHistoryRecord`, `AIExtractionActivity`, `AIDiscardedExtraction`, `SocialHistoryConsent`). Predates this release.

## [1.4.0] - 2026-06-22

### Added
- `SocialHistoryRecord` model (`health:SocialHistoryRecord`) — consumer-reported social history (smoking status, alcohol use, exercise frequency, occupational exposure). Distinct from the EHR-extracted `ClinicalSocialHistoryRecord` (`clinical:SocialHistoryRecord`).
- `AdvisoryApplicationActivity` model (`cascade:AdvisoryApplicationActivity`) — PROV-O Activity for advisory-triple application (`appliedTriplesCount`).
- `AIGenerationActivity` model (`cascade:AIGenerationActivity`) — PROV-O Activity for ungrounded general-AI generation; reuses `extractionModel`/`extractionConfidence`/`sourceNarrativeSection`/`requiresUserReview` and adds `promptVersion`, `generationTemperature`, `trigger`.
- `ProxyAgent` model (`cascade:ProxyAgent`) — PROV-O Agent acting on behalf of a patient (`actsForPatient`, `proxyWebID`, `proxyRelationship`, `proxyScope`, `proxyGrantedAt`, `proxyRevokedAt`).
- `GenerationTrigger` type alias for the `cascade:GenerationTrigger` enum individuals (`InitialGeneration`, `RegenerationAfterReclassification`, `AudienceRetargeting`).
- `AIAsserted` added as a valid `cascade:dataProvenance` value (DataProvenance leaf for ungrounded general-AI content; distinct from `AIExtracted`).
- TYPE_MAPPING / TYPE_TO_MAPPING_KEY entries and PROPERTY_PREDICATES (snake + camel) for all new classes and properties.
- All new classes and the previously model-only AI-extraction / clinical-social-history classes exported from the `cascade_protocol` package root.

### Changed
- VOCAB_VERSIONS updated: core=3.3, health=2.4, clinical=1.9 (clinical v1.9 permits `cascade:AIExtracted` provenance on clinical records — already accepted).
- Moved the inline comment off the `coverage=1.3` line in VOCAB_VERSIONS so the drift parser reads the version cleanly.

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
