# The provenance record

*provenance record, storage versions 2, 6 and 7 — published as part of `provenance@vYYYY.MM.N`; see `provenance-versions.json` for the version this document belongs to.*

Every consult the Consultologist engine generates leaves one **record**: the job. This document is the contract for what that record carries — which fields an outside reader will find, what each one means, and how to read them together. It describes what **is** recorded. What the engine intends to record one day is not a contract and is not here; it lives in the engine's design record.

The companion document, [hash-definitions.md](hash-definitions.md), defines every hash a record carries, byte for byte, so a holder of the record can recompute them.

## 1. What a record is

A record is one job: one package, one set of inputs, one set of deliverables, produced once. It is written by the engine, never by a person, and once the job is terminal it does not change. The record is served as one JSON object; the field names below are its wire names.

Its fields are of three kinds, and the kind says how to read the field:

- **Refs** name an artifact in a public registry — `workflowPackage`, `catalogRef`. A ref is always concrete, `name@vYYYY.MM.N`, never `name@latest`: a record that pointed at a moving target would not be a record. Resolve the ref through its registry and you hold the artifact the job used. The record stores refs, never copies.
- **Operational snapshots** are what the engine had in hand when the job ran, kept on the record so the job replays and reads the same way forever — `nodes`, `itemSteps`, `collections`, `inputOrigins`, `skippedDocuments`, `packageTitle`, `packageTags`, `startFailure`. They are facts about that run, not artifacts, and a reader takes them as stated.
- **Derived projections** are computed from the record every time it is read and never stored — `workflowOutputHash`, `assembledDocuments[].documentHash`. Anyone holding the record recomputes them by the definitions in hash-definitions.md, and a recomputation that disagrees with the served value is evidence about the server, not about the job.

## 2. Two version numbers that are not one ladder

A record carries two version numbers that happen to share the value 7 today and are unrelated:

- **`schemaVersion`** — the record's own *storage shape*: which fields below a reader should trust to be present and meaningful. Stamped by whichever engine path produced the record (2 for a job created before any node completed or under the earliest shape; 6 for a job whose deliverable was one assembled document; 7 for a job whose deliverables are a result set, and for every job created already failed). Never declared by anyone, never refused: a record at 2 is read forever. The values that exist are listed in `provenance-versions.json` as `recordStorageVersions`.
- **`packageSpecVersion`** — the *package format* the job's package was written against (`specVersion` in its manifest), defined by the [package-format registry](https://consultologistpublic.blob.core.windows.net/package-format/latest.json). This is the number an outside reader usually wants.

## 3. The fields

Field names are as served (camelCase). "Absent" means the field is null or omitted; the record never uses an empty string to mean absent.

### 3.1 Identity, status, timing

| Field | Meaning |
|---|---|
| `jobId` | 32 lowercase hex characters; unique. |
| `appUserId` | The account the job belongs to; 32 lowercase hex characters. Not a person's name. |
| `status` | One of `Queued`, `Scheduled`, `Running`, `Completed`, `Failed`, `Cancelled`. `Completed`, `Failed` and `Cancelled` are terminal. |
| `success` | `true` iff `status` is `Completed`. |
| `createdAtUtc`, `startedAtUtc`, `completedAtUtc` | ISO-8601 UTC instants; the latter two absent until they happen. |
| `scheduledAtUtc` | Present on a job that was asked to start later; the instant it was to start. |
| `source` | Where the job was created: absent for the app; `email` for the email door. |
| `schemaVersion` | § 2. |

### 3.2 Work and progress

| Field | Meaning |
|---|---|
| `totalBlockCount`, `completedBlockCount`, `failedBlockCount` | A block is one unit of deliverable work — one (deliverable × source × item). The total is fixed when the job starts and never changes; the other two count settled blocks. A job created already failed states a total of 0. |
| `generatedBlocks`, `failedBlocks` | Block id → generated text / error. Clinical content lives here; see § 4. |
| `completedStageCount`, `totalStageCount` | Nodes completed / nodes in the job. |
| `itemProgress` | Per fan item: `{ id, name, step, completedStepCount, totalStepCount }`. |
| `history` | Ordered events `{ kind, message, blockId?, atUtc }` the engine wrote as the job ran. |
| `analysisStatus`, `analysisError`, `runtimeFailureStage`, `runtimeFailureError` | How and where a job that ran failed, when it did. Absent on a job that failed before running (`startFailure` instead). |

### 3.3 Provenance

| Field | Kind | Meaning |
|---|---|---|
| `workflowPackage` | ref | `name@vYYYY.MM.N` of the workflow package the job ran — the manifest, prompts, schemas and data that produced it. Resolve it through the [workflow-packages registry](https://consultologistpublic.blob.core.windows.net/workflow-packages/) (public packages) or the account's own registry (`acct-…` packages, whose manifests carry a `derivedFrom` chain back to a public root). |
| `packageSpecVersion` | snapshot | § 2. |
| `packageTitle` | snapshot | The package's title as it was at that version; absent for an untitled package. A label for a person, never a substitute for `workflowPackage`. |
| `packageTags` | snapshot | The package's tags as they were; an empty list for a package that declared none; absent for a package whose format predates tags (specVersion < 9). |
| `catalogRef` | ref | `output-contracts@vYYYY.MM.N` — the output-contract catalog version the job ran under, which maps each contract id to the agent that produced structured output for it. Resolve it through the [output-contracts registry](https://consultologistpublic.blob.core.windows.net/output-contracts/latest.json). Distinct from the catalog the *package* was published under, which the package's own `publish.json` records; comparing the two shows whether a contract was redefined between publish and run. |
| `packageFormatRef` | ref | `package-format@vYYYY.MM.N` — the format registry version whose documents define the rules the job's package was interpreted under. Resolve `packageSpecVersion` through that version's `spec-versions.json` to the document, not through the latest. Absent on records from before 2026-08-25; for those, the engine build that produced them is the only witness to the rules. |
| `provenanceRef` | ref | `provenance@vYYYY.MM.N` — the version of **this contract** the record conforms to. A reader opens that version's `provenance-record.md` and `hash-definitions.md`, not the latest. Absent on records from before 2026-08-25. |
| `effectiveInputHash`, `effectiveInputHashVersion` | derived at start, stored | The hash of the inputs the job actually ran on, and the number of the definition that computed it (hash-definitions.md § 2). Computed once when the job starts and stored, because the inputs themselves are not on the record. |
| `inputOrigins` | snapshot | Input id → list of origins, positionally per supplied element: `{ kind, extractor?, pageCount?, trackedChangesResolved }`. `kind` is `document` for an element read from an uploaded file; `extractor` names the extractor build (`name/version+commit`). Absent means *not recorded*, never *typed by hand*. Recorded beside the input hash and never inside it. |
| `nodes` | snapshot | The nodes the job ran, in package order: `{ id, label, promptId?, bindings?, outputContract?, failIfEmpty?, forEach?, conceptSource?, aggregate? }`. `outputContract` names the catalog contract a node's output was parsed against; absent means the text contract. Nodes the package declared but the job did not need are not listed. |
| `itemSteps`, `collections` | snapshot | The fanned nodes (`{ id, label }`) and the fan rosters the job iterated (`{ collectionId, items: [{ id, name }] }`). |
| `nodeOutputs` | snapshot | Per node instance (`nodeId` or `nodeId:itemId`): `{ nodeId, label, status, inputHash?, outputHash?, hashVersion?, completedAtUtc?, error? }`. The two hashes are the per-node hashes and `hashVersion` names their definition (hash-definitions.md § 4); absent on records from before the ladder. |
| `workflowOutputHash`, `workflowOutputHashVersion` | derived | The hash of the deliverable set of a **completed** job and its definition number (hash-definitions.md § 3). Absent on any job that is not `Completed`: the deliverable hash of a partial job is undefined. |
| `assembledDocuments` | snapshot + derived | The deliverables: `{ resultId, label, text, documentHash }`. `text` is clinical content (§ 4); `documentHash` is derived, SHA-256 of `text`, and is the per-document digest definition 3 is computed over. |
| `assembledDocument` | snapshot | Storage version 6 only: the single assembled document. |
| `skippedDocuments` | snapshot | Deliverables the package declared that this job did not produce: `{ resultId, label, reason }`. `reason` is composed of the package's own words — the input named, what was supplied, what the condition wanted. |
| `startFailure` | snapshot | Present only on a job created already `Failed` because no deliverable applied to its inputs: the refusal sentence, composed of package content. Nothing ran; there are no blocks. |
| `agentVersions` | legacy | Records written on or before 2026-07-17 only: contract id → agent version. Superseded by `catalogRef`, which resolves the same mapping through an immutable registry. Absent on every later record. |

## 4. What the contract does not cover

- **Clinical content.** `generatedBlocks`, `assembledDocuments[].text`, `assembledDocument`, `nodeOutputs` errors and `history` messages can carry the consult's text. It is on the record because the record is the account's; this contract says where it is, and says nothing about it. A verifier's inputs and outputs come from the record holder.
- **The inputs.** The record holds their hash and their origins, not the inputs.
- **Legs the engine does not record.** The model checkpoint, sampling parameters, inference-stack fingerprint, terminology edition and terminology-server release are not on the record. They are named in the engine's design record as intended work, with the issues tracking them; until one is recorded it does not appear here.

## 5. Reading a record

1. Read `provenanceRef` and `packageFormatRef` first: they name the version of this contract and of the format specification to read everything else by. Then resolve `workflowPackage` and `catalogRef` through their registries. You now hold the package that ran and the catalog that mapped its contracts to agents.
2. Compare `catalogRef` with the package's `publish.json` (`catalogRef` there): equal means the package ran under the catalog it was published against.
3. Recompute `workflowOutputHash` from `assembledDocuments` by the definition `workflowOutputHashVersion` names, and each `documentHash` from its `text`. They must match what is served.
4. Recompute `effectiveInputHash` only if you hold the inputs, by the definition `effectiveInputHashVersion` names.
5. Read `nodes` with `catalogRef`: each node's `outputContract` (or the text contract) names the agent that produced its output, and `nodeOutputs` gives the hashes of what that agent received and returned.

Two records with the same `workflowPackage`, `catalogRef`, `effectiveInputHash` (same version) ran the same clinical input through the same prompts and agents. Whether they produced the same deliverable is what `workflowOutputHash` says.
