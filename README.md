# consultologist-provenance

The contract for the **provenance record** the Consultologist engine writes for
every consult, the **hash definitions** a holder of a record recomputes with,
and the **registry layout** that turns a record's refs into bytes — published
as a versioned registry.

An outside verifier reads two things before checking anything: what a record
carries, and how its hashes were computed. This repo is where both live.

| File | Defines |
| --- | --- |
| `provenance-versions.json` | which record storage versions and hash-definition numbers exist, and the document defining each |
| `provenance-record.md` | the record: its fields, the three kinds they come in (refs, snapshots, derived projections), the two version ladders that are not one, and how to read a record |
| `hash-definitions.md` | every hash on a record, byte for byte, with worked examples — effective-input definitions 1–6, workflow-output definitions 1–3, the per-node and per-document hashes |
| `registry-layout.md` | how a ref resolves to bytes: where every registry lives, the two layout families, CalVer, immutability by refusal, dependencies before the index, `latest.json` as a pointer, concrete refs in records — and the departures the current registries still have |

## Reading it from the registry

Every version is published to the public registry and is fetchable with no
credential:

```
https://consultologistpublic.blob.core.windows.net/provenance/latest.json
https://consultologistpublic.blob.core.windows.net/provenance/v2026.08.12/provenance-versions.json
https://consultologistpublic.blob.core.windows.net/provenance/v2026.08.12/provenance-record.md
https://consultologistpublic.blob.core.windows.net/provenance/v2026.08.12/hash-definitions.md
https://consultologistpublic.blob.core.windows.net/provenance/v2026.08.12/registry-layout.md
https://consultologistpublic.blob.core.windows.net/provenance/v2026.08.12/LICENSE
```

`latest.json` is the only mutable blob — `{"version": "vYYYY.MM.N"}`. Published
versions are **immutable**: the publish script refuses to overwrite one.

## Publishing a change

`provenance-versions.json` carries its own CalVer version (`vYYYY.MM.N`,
zero-padded month, counter ≥ 1). Bump it in the same commit as whatever you
changed, and merging to `main` publishes — there is no tag. Forgetting the
bump fails the publish rather than overwriting a published version.

Documents upload before `provenance-versions.json`, so a partial upload is
never visible as a complete version.

## Two conventions worth knowing

**Outbound links are commit-pinned.** These documents cite design records that
live in the engine repo. Those links point at a specific commit rather than at
`main`, so a published version resolves to the same words forever.

**The ladders are published facts, not code constants.** The engine vendors
this repo as a submodule, and a test there asserts that its own hash-definition
constants and record storage versions equal `provenance-versions.json`, and
that the worked examples in `hash-definitions.md` recompute byte for byte
through the engine's own code. The documents and the engine cannot silently
disagree.

## Licence

These documents are licensed **[CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/)**
— © 2026 Tauheed Elahee. Read them, cite them, and share them unchanged with
attribution.

- **Recomputing a hash or reading a record is unaffected.** A verifier's code
  is not a derivative work of this prose.
- **NoDerivatives** covers this text: no translations, and no redistribution of
  the documents in modified form. Quoting them — a definition, a worked example
  and its digest as a test vector — within fair dealing is fine and is what
  "cite them" means.
- **NonCommercial** covers redistribution of the documents, not use of the
  definitions.

The licence covers the documents and `provenance-versions.json` only. It grants
no rights to the Consultologist engine, which is separately licensed, and no
patent or trademark rights.

**Consultologist clients hold a licence that goes beyond this one.** Every
client may use these documents commercially — inside the app, and in their own
environment outside it — and holds the copyright in what they author. That
permission is part of the client agreement, not this file; this licence is
the public default for everyone else. Anyone who needs more than it grants
can ask.
Recomputing a record's hashes, and running a consult from the artifacts a
record names in your own harness, needs no permission from this licence.

## Related registries

- [consultologist-package-format](https://github.com/Consultologist/consultologist-package-format) — the package format a record's `packageSpecVersion` names
- [consultologist-workflows](https://github.com/Consultologist/consultologist-workflows) — the packages a record's `workflowPackage` names
- [consultologist-agents](https://github.com/Consultologist/consultologist-agents) — the output-contract catalog a record's `catalogRef` names
- [Consultologist-Blazor](https://github.com/Consultologist/Consultologist-Blazor) — the engine, and the design record these documents came from
