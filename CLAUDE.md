# sdk-python — Agent Context

## Repository Purpose

Python SDK for the Cascade Protocol.
Package: `cascade-protocol` (PyPI)

## Key Architecture

- `src/cascade_protocol/models/` — Python dataclasses for each Cascade record type
- `src/cascade_protocol/vocabularies/namespaces.py` — RDF namespace URIs and predicate mappings
- `src/cascade_protocol/serializer/` — TTL serialization
- `src/cascade_protocol/deserializer/` — TTL deserialization
- `src/cascade_protocol/validator/` — SHACL validation support

## MANDATORY: Deployment Discipline

### Before implementing support for a new vocabulary class:

Check `spec/ontologies/{name}/v1/{name}.ttl` for the authoritative class definition.
Check `spec/ontologies/{name}/v1/{name}.shapes.ttl` for required properties and constraints.
Check `conformance/fixtures/` for the canonical test fixtures that your implementation must pass.

### When adding a new vocabulary class, you MUST:

- [ ] Add `src/cascade_protocol/models/{class_name}.py` — dataclass matching all TTL properties
- [ ] Add predicate URIs to `src/cascade_protocol/vocabularies/namespaces.py`
- [ ] Register in serializer and deserializer
- [ ] Export from `src/cascade_protocol/__init__.py`
- [ ] Verify all conformance fixtures for this class pass
- [ ] Update `VOCAB_VERSIONS` — bump the entry for the vocabulary you just implemented
- [ ] Update CHANGELOG.md
- [ ] Bump version in `pyproject.toml` or `setup.py` (minor bump for new class support)
- [ ] Install hooks if not done: `sh scripts/install-hooks.sh`

The pre-commit hook will block commits to `src/cascade_protocol/models/` or `vocabularies/` without updating `VOCAB_VERSIONS`.

### Current vocabulary versions

Check `VOCAB_VERSIONS` at the repo root. Compare against `spec/VOCAB_VERSIONS` to see what's behind.

### Known gaps (as of 2026-08-28)

The clinical v1.7, coverage v1.3 and core v2.8 items previously listed here
have all shipped. What is actually missing now:

- **Deserializer registration.** `parse()` returns an EMPTY LIST — not an
  error — for several types that serialize correctly:
  `MedicationAdministration`, `ImplantedDevice`, `ImagingStudy`,
  `ClaimRecord`, `BenefitStatement`, `DenialNotice`, `AppealRecord`,
  `ClinicalSocialHistoryRecord`, `AIExtractionActivity`,
  `AIDiscardedExtraction`, `SocialHistoryConsent`. Each needs an entry in
  `_TYPE_CLASS_MAP` in `deserializer/turtle_parser.py`. Read a round trip,
  not just a serialize, when adding a class.
  (`Encounter` was on this list and was fixed in the clinical v1.16 sync,
  because the nine encounter fields that release adds would otherwise have
  been write-only and their round-trip tests would have passed vacuously
  against zero records. That is the general lesson: this gap makes any new
  field on an unregistered type unverifiable, not merely unreadable.)
- **`clinical:ClinicalDocument` is not modelled.** `clinical:
  documentReferenceStatus`, `clinical:documentAuthorName` and
  `clinical:authenticatorName` (clinical v1.16) are registered in
  `PROPERTY_PREDICATES` and resolve through `serialize_from_dict()` and the
  reverse map, but no dataclass carries them, so nothing writes or reads them
  from a model. A `ClinicalDocument` model closes this in one step.
- **`clinical:Supplement`** has a `TYPE_MAPPING` entry but no model class.
- **`health:BloodPressureReading` / `health:HRVReading`** are not modelled, so
  the `BloodPressureData` and `HRVData` wellness containers read with an empty
  history.
- **`clinical:LaboratoryReport`** is not modelled, so `clinical:hasLabResult`
  panel grouping is unimplemented.

### Reading vs writing deprecated vocabulary

Deprecated is not removed. When a class or property is deprecated upstream,
the deserializer keeps accepting it (see `DEPRECATED_TYPE_ALIASES`) and the
serializer stops emitting it. Dropping read support turns a pod full of
records into a pod that reads as empty, which is worse than an error because
nothing reports it.

### Reading every LIVE spelling, not just the one we write

The same rule applies where two spellings are BOTH current, which is the
commoner case and has no deprecation to signal it. Several fields are declared
by more than one vocabulary (`clinical:sourceRecordId` and
`health:sourceRecordId`; the `coverage:` and `clinical:` spellings of a plan's
fields), and `coverage:InsurancePlan` and `clinical:CoverageRecord` are both
live rdf:types for one record.

- Readers accept every live spelling: `ADDITIONAL_PREDICATE_SPELLINGS` and
  `READ_ONLY_TYPE_ALIASES` in `vocabularies/namespaces.py`. Both are consumed by
  the deserializer AND the validator; adding to one place covers both.
- Writers keep emitting exactly one.

An unregistered rdf:type is the dangerous half. A subject whose type resolves to
nothing is SKIPPED, so it is not merely unread — it is unvalidated, and a
fixture written in that spelling passes by never being checked. Before trusting
a green fixture, confirm the subject was actually reached.

## Commit Conventions

```
feat(sdk): add {ClassName} model (clinical v1.7)
feat(sdk): add Core v2.8 FHIR passthrough properties
fix(sdk): {description}
```

## Related Repositories

- **spec** — Authoritative TTL/shapes. Read these when implementing new classes.
- **conformance** — Test fixtures. Your implementation must pass these before releasing.
- **sdk-typescript** — Reference implementation; use as a guide for property mappings.
