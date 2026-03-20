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

### Known gaps (as of 2026-03-20)

See `VOCAB_VERSIONS` comments. Priority items:
- **Clinical v1.7**: Encounter, MedicationAdministration, ImplantedDevice, ImagingStudy (all missing)
- **Coverage v1.3**: ClaimRecord, BenefitStatement, DenialNotice, AppealRecord, DenialReasonCode (all missing)
- **Core v2.8**: FHIR passthrough properties (`layerPromotionStatus`, `fhirJson`, `fhirResourceType`, `sourceRecordDate`)

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
