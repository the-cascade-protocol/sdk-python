# Contributing to sdk-python

The Python SDK for the Cascade Protocol, published on PyPI as `cascade-protocol`. It models each Cascade record type as a dataclass, maps it to RDF predicates, and serializes and deserializes Turtle. Contributions are typically support for a vocabulary class the SDK does not model yet, a deserializer registration, or a serialization fix.

## Before you start

- All open issues: <https://github.com/search?q=org%3Athe-cascade-protocol+is%3Aissue+is%3Aopen>
- Good first issues: <https://github.com/search?q=org%3Athe-cascade-protocol+is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22>

The "Known gaps" section of `CLAUDE.md` names the unmodelled classes and, more usefully, the classes that serialize correctly and are missing from `_TYPE_CLASS_MAP` in `deserializer/turtle_parser.py`. Those are the openings.

## Development setup

**`conformance` must be cloned as a sibling directory**, not inside this one. The suite resolves the cross-SDK determinism vectors at `../conformance/fixtures/`, and CI reproduces that layout exactly.

```
<parent>/
  sdk-python/
  conformance/
```

```bash
git clone https://github.com/the-cascade-protocol/sdk-python.git
git clone https://github.com/the-cascade-protocol/conformance.git
cd sdk-python

python -m pip install --upgrade pip
pip install -e .
pip install pytest
```

CI runs Python 3.10 and 3.13.

Install the hooks once: `sh scripts/install-hooks.sh`. The pre-commit hook blocks commits to `src/cascade_protocol/models/` or `vocabularies/` without updating `VOCAB_VERSIONS`.

## What must be green before review

```bash
pytest -q

# and the guard that proves the fixture-backed tests actually ran
pytest -q tests/test_deterministic_uri.py::test_conformance_vectors_are_loaded
```

The second command is not redundant. Without the sibling `conformance` checkout the vector tests do not merely fail, they stop exercising cross-SDK identity at all, which is exactly the failure the guard exists to catch. Run both, on 3.10 as well as 3.13 if you can.

## Commit messages

```
feat(sdk): add {ClassName} model (clinical v1.7)
feat(sdk): add Core v2.8 FHIR passthrough properties
fix(sdk): {description}
```

## Opening a pull request

1. Branch from `main`.
2. Run both commands above and confirm the guard passes as well as the suite.
3. Update `CHANGELOG.md` and bump the version in `pyproject.toml` (minor for new class support).
4. Push and open a PR. `.github/PULL_REQUEST_TEMPLATE.md` fills in with the checklist; keep the items and tick them.
5. Name in the PR body the conformance fixtures your change is proven against. "Tests pass" is not the same claim as "these fixtures pass", and only the second one is evidence.

### Adding support for a new vocabulary class

Read the class definition in `spec/ontologies/{name}/v1/{name}.ttl`, its required properties in the matching `.shapes.ttl`, and its fixtures in `conformance/fixtures/` before writing anything.

- [ ] `src/cascade_protocol/models/{class_name}.py` -- dataclass matching every TTL property
- [ ] Predicate URIs in `src/cascade_protocol/vocabularies/namespaces.py`
- [ ] Registered in the serializer **and** in `_TYPE_CLASS_MAP` in `deserializer/turtle_parser.py`
- [ ] Exported from `src/cascade_protocol/__init__.py`
- [ ] Conformance fixtures for the class pass
- [ ] `VOCAB_VERSIONS` bumped for the vocabulary you implemented
- [ ] `CHANGELOG.md`, and the version in `pyproject.toml`

**Read a round trip, not just a serialize.** This is the specific failure mode this SDK has had repeatedly: a class registered in the serializer and not the deserializer makes `parse()` return an **empty list rather than an error**. A pod full of records reads as an empty pod, and nothing reports it.

### Reading versus writing deprecated vocabulary

Deprecated is not removed. When a class or property is deprecated upstream, the deserializer keeps accepting it (see `DEPRECATED_TYPE_ALIASES`) and the serializer stops emitting it. Dropping read support turns a pod full of records into a pod that reads as empty, which is worse than an error because nothing reports it.

## Vocabulary changes

**Vocabulary is never authored here.** Classes and properties come from [`spec`](https://github.com/the-cascade-protocol/spec), and fixtures proving them come from [`conformance`](https://github.com/the-cascade-protocol/conformance). If your change needs a class that does not exist yet, it starts in `spec`: read [`spec/CONTRIBUTING.md`](https://github.com/the-cascade-protocol/spec/blob/main/CONTRIBUTING.md) for the full seven-step propagation sequence. This repository is step 6, and it is gated by step 3.

Record identity must match across SDKs: the same input derives the same URI in the Python SDK, the TypeScript SDK and the CLI. That is what the determinism vectors test. Do not change URI derivation here alone.

## Protocol context

<https://cascadeprotocol.org/llms.txt> is the protocol index: install, quick start, data types, MCP server, security model, vocabulary versions, deployment sequence. About 95 lines, meant to be read in full.

Do not load `llms-full.txt` from that site. It is roughly 1.3 MB, larger than most working contexts, and as of 2026-08-20 its ontology section is known to be incomplete. Read the TTL files in `spec` instead.

## Questions?

Open an issue on this repository, or a [discussion on `spec`](https://github.com/the-cascade-protocol/spec/discussions) for questions about the vocabulary itself.
