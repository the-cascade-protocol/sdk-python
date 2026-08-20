# AGENTS.md

Python SDK for the Cascade Protocol, published on PyPI as `cascade-protocol`. Models, serializes and deserializes Cascade record types as Turtle.

## Start here

- `CLAUDE.md` -- architecture, the checklist for adding a vocabulary class, and the current known gaps class by class.
- `CONTRIBUTING.md` -- setup, what must be green, PR conventions.
- `README.md` -- user-facing API reference.

`CLAUDE.md` and this file describe the same repository. `CLAUDE.md` is loaded automatically by Claude Code; this file exists so any coding agent finds the same instructions.

## Protocol context

<https://cascadeprotocol.org/llms.txt> is the protocol index: install, quick start, data types, MCP server, security model, vocabulary versions, deployment sequence. About 95 lines, meant to be read in full.

Do **not** load `llms-full.txt` from that site. It is roughly 1.3 MB, larger than most working contexts, and as of 2026-08-20 its ontology section is known to be incomplete. Read the TTL files in [`spec`](https://github.com/the-cascade-protocol/spec) instead.

## Ground rules

- **Vocabulary is not authored here.** Read the class in `spec/ontologies/{name}/v1/{name}.ttl`, its constraints in the matching `.shapes.ttl`, and its fixtures in `conformance/fixtures/` before implementing anything.
- **Register every class in `_TYPE_CLASS_MAP` as well as the serializer, and read a round trip.** This SDK's recurring defect is a class that serializes correctly while `parse()` returns an **empty list rather than an error**, so a pod full of records reads as empty and nothing reports it.
- **Deprecated is not removed.** The deserializer keeps accepting deprecated spellings (`DEPRECATED_TYPE_ALIASES`); only the serializer stops emitting them. Dropping read support silently empties existing pods.
- **`conformance` must be a sibling checkout**, at `../conformance`. Without it the determinism vectors stop exercising cross-SDK identity rather than failing, which is why there is an explicit guard test for it.
- **Record identity is cross-SDK.** The same input must derive the same URI here, in the TypeScript SDK and in the CLI. Never change URI derivation in one of them alone.

## What must be green

```bash
pip install -e . && pip install pytest
pytest -q
pytest -q tests/test_deterministic_uri.py::test_conformance_vectors_are_loaded
```

CI runs Python 3.10 and 3.13. The second command is the guard that the fixture-backed tests actually ran; do not treat a green `pytest -q` alone as proof they did.

## Conventions

- Commits: `feat(sdk):`, `fix(sdk):`, naming the vocabulary version where relevant.
- Update `CHANGELOG.md` and bump the version in `pyproject.toml` (minor for new class support). The pre-commit hook blocks `models/` and `vocabularies/` changes that do not update `VOCAB_VERSIONS`.
- Branch from `main`; open a PR rather than pushing to it.
- Name the conformance fixtures your change is proven against in the PR body. "Tests pass" and "these fixtures pass" are different claims.
