# The registry layout

*Published as part of `provenance@vYYYY.MM.N`; the version this document belongs to is in `provenance-versions.json`.*

A provenance record cites artifacts by reference — `general@v2026.08.1`, `output-contracts@v2026.07.2`, `provenance@v2026.08.1`. This document is the contract that turns a reference into bytes: where every Consultologist registry lives, how a version is laid out, what may change and what may not. A reader who knows it can resolve any ref with a plain HTTP GET and no credential, and can rely on what they fetched never changing under them.

## 1. Where the registries are

Every public registry is one container in the storage account `consultologistpublic`, reachable at

```
https://consultologistpublic.blob.core.windows.net/{container}/{blob}
```

with **container-level anonymous read, including listing**: a reader may enumerate a container as well as fetch from it, which is what lets a reader discover the names a registry holds without an index of indexes. Nothing in a public registry requires a credential to read.

| Registry | Container | Family | Index blob per version | `LICENSE` travels | Version comes from | Published by |
|---|---|---|---|---|---|---|
| Workflow packages | `workflow-packages` | named | `manifest.json` | no | the manifest's `version`, and the git tag `{name}-vYYYY.MM.N` must equal it | tag push in `consultologist-workflows` |
| Output-contract catalog | `output-contracts` | single-artifact | `output-contracts.json` | no | the catalog's `version` | merge to `main` in `consultologist-agents` |
| Agent definitions | `agent-definitions` | named | `definition.yaml` | no | the definition's `version` — a Foundry integer (§ 3) | merge to `main` in `consultologist-agents` |
| Package format | `package-format` | single-artifact | `spec-versions.json` | yes | the index's `version` | merge to `main` in `consultologist-package-format` |
| Provenance | `provenance` | single-artifact | `provenance-versions.json` | yes | the index's `version` | merge to `main` in `consultologist-provenance` |

There is one more registry, which is **not public**: an account's own workflow packages (`acct-<12 hex>…` names) live in the same layout in a private account, written only by the engine on an authorised publish and readable only by the owning account. A reader of the public registries cannot reach them; a record that cites one is resolvable only by its owner.

## 2. Two layout families

**Named** registries hold many artifacts, each with its own versions and its own pointer:

```
{name}/{version}/{index blob}
{name}/{version}/…            the files that version references
{name}/latest.json
```

**Single-artifact** registries hold one artifact; the version is the first path segment and the pointer sits at the container root:

```
{version}/{index blob}
{version}/…
latest.json
```

`{name}` follows the package name grammar published by the package-format registry (`v2026.08.6` and later): up to four segments of `[a-z0-9][a-z0-9-]*` joined by `/`. A name is read from the right of a blob path — the index blob's parent is the version, everything before it is the name — so a nested name groups as itself.

## 3. The version

A version is CalVer, `vYYYY.MM.N`:

```
^v[0-9]{4}\.(0[1-9]|1[0-2])\.[1-9][0-9]*$
```

Four-digit year, two-digit month `01`–`12`, and a counter from `1` with no leading zero. Versions of one artifact order by year, month, counter. The version is **declared inside the artifact** — the index blob names it — and the path repeats it; a reader that fetches `{version}/{index blob}` and finds a different version inside has found a corrupt publish, and the engine refuses such a catalog ("path and content disagree"). Where a git tag exists (workflow packages) it must equal the declared version; where none does, merging is publishing.

*Exception, by design:* an agent definition's version is the integer the Foundry platform assigns when the agent is published there, and the definition's `version` must equal it. Those integers order numerically and are not CalVer.

## 4. Immutability

A published version is never rewritten. **The rule is enforced by refusal, not by a storage policy**: a publisher checks whether the version's index blob already exists and, if it does, stops and says so — *"versions are immutable — bump the version"*. The engine's own publisher does the same thing atomically: it creates the index blob with an if-none-match condition and, on conflict, assigns the next counter and tries again. Either way, once a reader has fetched `{version}/…`, those bytes are what that version is, forever.

## 5. Dependencies before the index

Every file a version references uploads **before** the version's index blob, and the index blob before the pointer. A reader resolves the index first, so a publish that stops halfway leaves nothing a reader can find — never a version whose index names a file that is not there. (The engine's publisher goes one further: a package's publication stamp, `publish.json`, uploads before the manifest, so no version is reachable without it.)

## 6. `latest.json`

The only mutable blob in a registry. It is a JSON object with one member:

```json
{"version": "vYYYY.MM.N"}
```

Whitespace inside it is insignificant; the member name is `version`, lowercase; the value is a version string of the registry's ladder (§ 3). It is written last, with overwrite, and it is a **pointer, not content**: what `latest` names today is not what it named yesterday, which is exactly why —

## 7. Records cite concrete versions

A provenance record, a package's `publish.json`, and a manifest's `derivedFrom` name concrete versions — `name@vYYYY.MM.N` — never `name@latest`. `@latest` is for a caller choosing what to run next; it is never what a record says ran. The engine refuses a stamp or a lineage that says `@latest`, and its operator tooling refuses a candidate catalog given as `@latest`.

## 8. What is not in a public registry

Account packages (§ 1). Agent plumbing: a published agent definition is the git manifest with its tool endpoints and connection ids removed, and the publisher refuses to upload one that still carries them. Anything an account wrote.

## 9. Known departures, as of this version

Stated rather than hidden. Each has a home.

- The `consultologist-agents` repo's publish has no manual dispatch door, no pre-merge "already published" warning, and no post-publish anonymous smoke check — the other registries have all three. Tracked in that repo.
- Shell publishers write `latest.json` as `{"version": "v…"}` with a space and a trailing newline; the engine writes it without. Same object; § 6 says the whitespace is insignificant, and every reader agrees.
- Public workflow packages published by CI carry no `publish.json` (the engine's publisher writes one for account packages). Tracked as consultologist-workflows#19.
