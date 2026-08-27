# The provenance record

*provenance record, storage versions 2, 6 and 7 — published as part of `provenance@vYYYY.MM.N`; see `provenance-versions.json` for the version this document belongs to.*

Every consult the Consultologist engine generates leaves one **record**: the job. This document is the contract for what that record carries — which fields an outside reader will find, what each one means, and how to read them together. It describes what **is** recorded. What the engine intends to record one day is not a contract and is not here; it lives in the engine's design record.

The companion document, [hash-definitions.md](hash-definitions.md), defines every hash a record carries, byte for byte, so a holder of the record can recompute them.

## 1. What a record is

A record is one job: one package, one set of inputs, one set of deliverables, produced once. It is written by the engine, never by a person, and once the job is terminal it does not change. The record is served as one JSON object; the field names below are its wire names.

Its fields are of three kinds, and the kind says how to read the field:

- **Refs** name an artifact in a public registry — `workflowPackage`, `catalogRef`. A ref is always concrete, `name@vYYYY.MM.N`, never `name@latest`: a record that pointed at a moving target would not be a record. Resolve the ref through its registry and you hold the artifact the job used. The record stores refs, never copies.
- **Operational snapshots** are what the engine had in hand when the job ran, kept on the record so the job replays and reads the same way forever — `nodes`, `itemSteps`, `collections`, `inputOrigins`, `skippedDocuments`, `classifications`, `packageTitle`, `packageTags`, `startFailure`. They are facts about that run, not artifacts, and a reader takes them as stated.
- **Derived projections, stored at completion** — `workflowOutputHash`, `workflowOutputHashVersion` and `assembledDocuments[].documentHash` are computed from the produced text once, when the job completes, and stored on the record. While the text is present a holder can recompute them and they must agree (§ 5); after the text is deleted under the retention policy (`textDroppedAtUtc`) they attest that *a* document with that digest was produced and can no longer be checked against one. Records from before 2026-08-25 derived them on every read; served values are the same.

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
| `deciding` | `true` while the job's fire set — which deliverables it will produce, and so `totalBlockCount` — is not yet known: a specVersion 10 package with classifier nodes runs those first and decides at the boundary. Absent or `false` otherwise. A job that is `deciding` with `decidedAtUtc` absent has a count that is not yet known, not a count of zero. |
| `decidedAtUtc` | The instant the fire set was decided. For every package without a classifier that is the job's start (equal to `createdAtUtc`); for a package with classifiers, the boundary. Absent on a job still deciding, on a job that ended in the deciding stage (`decisionFailureKind`), and on records from before 2026-08-27 — which read as decided at start. |
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
| `terminology` | snapshot | `{ edition, version, importDate }` — the SNOMED CT edition the terminology server had loaded when the job started, as the server reported it (`SNOMEDCT 20251130 import.`, `2025-11-30`, an ISO instant). This is what every concept's `isSnomedConcept` and `isActive` were answered against; editions retire and reactivate concepts, so two records that differ only here can differ in their deliverables. Absent when the server could not be read at start, and on records from before 2026-08-25. |
| `textDroppedAtUtc` | snapshot | Present once the app has deleted the produced text under its retention policy: the instant it did. After it, `assembledDocuments[].text`, `assembledDocument`, `generatedBlocks` and the extracted concepts are gone from the record; every hash, node, ref and label stays. Absent while the text is present. |
| `terminologyServerRef` | ref | `snomed-snowstorm-mcp@<commit>` — the build of the terminology server that served the run: a commit in that Apache-2.0 repository, not a registry version; resolve it on GitHub. A server deployed without a stamp reports its assembly version instead, and the ref carries that. Absent likewise. |
| `effectiveInputHash`, `effectiveInputHashVersion` | derived at start, stored | The hash of the inputs the job actually ran on, and the number of the definition that computed it (hash-definitions.md § 2). Computed once when the job starts and stored, because the inputs themselves are not on the record. |
| `inputOrigins` | snapshot | Input id → list of origins, positionally per supplied element: `{ kind, extractor?, pageCount?, trackedChangesResolved }`. `kind` is `document` for an element read from an uploaded file; `extractor` names the extractor build (`name/version+commit`). Absent means *not recorded*, never *typed by hand*. Recorded beside the input hash and never inside it. |
| `nodes` | snapshot | The nodes the job ran, in package order: `{ id, label, promptId?, bindings?, outputContract?, failIfEmpty?, forEach?, conceptSource?, aggregate? }`. `outputContract` names the catalog contract a node's output was parsed against; absent means the text contract. Nodes the package declared but the job did not need are not listed. |
| `itemSteps`, `collections` | snapshot | The fanned nodes (`{ id, label }`) and the fan rosters the job iterated (`{ collectionId, items: [{ id, name }] }`). |
| `nodeOutputs` | snapshot | Per node instance (`nodeId` or `nodeId:itemId`): `{ nodeId, label, status, inputHash?, outputHash?, hashVersion?, completedAtUtc?, error?, classification? }`. The two hashes are the per-node hashes and `hashVersion` names their definition (hash-definitions.md § 4); absent on records from before the ladder. `classification` is a classifier node's normalised answer — one of the values the package declared for it — and is what its `outputHash` is over; absent on every other node. |
| `classifications` | snapshot | Classifier node id → the value it answered, for every classifier that ran: `{ "scope": "out_of_scope" }`. Declared values, never free text — a classification is one of the words the package wrote, so it is printable where patient text is not. Present on a job with classifiers once they have answered, including a job that ended in the deciding stage; absent otherwise. |
| `decisionFailureKind` | snapshot | Why a job ended in the deciding stage, beside `startFailure`: `could-not-decide` (a classifier failed) or `nothing-applied` (every deliverable's condition, read with the classifiers' answers, refused). Absent on every other job. |
| `workflowOutputHash`, `workflowOutputHashVersion` | derived | The hash of the deliverable set of a **completed** job and its definition number (hash-definitions.md § 3). Absent on any job that is not `Completed`: the deliverable hash of a partial job is undefined. |
| `assembledDocuments` | snapshot + derived | The deliverables: `{ resultId, label, text, documentHash }`. `text` is clinical content (§ 4); `documentHash` is derived, SHA-256 of `text`, and is the per-document digest definition 3 is computed over. |
| `assembledDocument` | snapshot | Storage version 6 only: the single assembled document. |
| `skippedDocuments` | snapshot | Deliverables the package declared that this job did not produce: `{ resultId, label, reason }`. `reason` is composed of the package's own words — the input named, what was supplied, what the condition wanted. A condition of one clause reads *needs `<operand>` to be `<wanted>`; it is `<found>`*; a specVersion 10 expression of several reads *needs (`<what each clause wanted>`); `<what each found>`*, joined as the condition was — each clause under the same rule: a declared value, a count, a comparison outcome or *not supplied* is printed, a patient's text never is. A clause over a classifier not yet answered reads *it is not decided*. |
| `startFailure` | snapshot | Present only on a job created already `Failed`: because no deliverable applied to its inputs at start, or — with `decisionFailureKind` — because the deciding stage ended without a fire set. The refusal sentence, composed of package content (`No document applies after classification: …` names each skipped deliverable's reason). Nothing ran past the classifiers; there are no blocks. |
| `agentVersions` | legacy | Records written on or before 2026-07-17 only: contract id → agent version. Superseded by `catalogRef`, which resolves the same mapping through an immutable registry. Absent on every later record. |

## 4. What the contract does not cover

- **Clinical content.** `generatedBlocks`, `assembledDocuments[].text`, `assembledDocument`, `nodeOutputs` errors and `history` messages can carry the consult's text. It is on the record because the record is the account's; this contract says where it is, and says nothing about it. A verifier's inputs and outputs come from the record holder.
- **The inputs.** The record holds their hash and their origins, not the inputs.
- **The text, after its retention period.** The produced text is patient data and is deleted N days after the job completes (the operator's policy — 7 days at the time of writing); `textDroppedAtUtc` records the deletion. Nothing else on the record is ever deleted.
- **Legs the engine does not record.** The model checkpoint, sampling parameters and inference-stack fingerprint are not on the record; each is reachable through `catalogRef` → the agent definition, and the engine's design record names them as intended work. Until one is recorded it does not appear here.

## 5. Reading a record

1. Read `provenanceRef` and `packageFormatRef` first: they name the version of this contract and of the format specification to read everything else by. Then resolve `workflowPackage` and `catalogRef` through their registries. You now hold the package that ran and the catalog that mapped its contracts to agents.
2. Compare `catalogRef` with the package's `publish.json` (`catalogRef` there): equal means the package ran under the catalog it was published against.
3. Before comparing two records' deliverables, compare their `terminology.version`: a different edition explains a different deliverable on its own, and nothing else on the record will.
   Then, on a specVersion 10 package with classifiers, compare their `classifications`: a different answer is a different fire set — different deliverables, or none — before any prompt ran, and `skippedDocuments` says which conditions read it that way.
4. Recompute `workflowOutputHash` from `assembledDocuments` by the definition `workflowOutputHashVersion` names, and each `documentHash` from its `text`. They must match what is served. Once `textDroppedAtUtc` is present there is no text to recompute from: the stored hashes still say what was produced, and nothing on the record can be checked against them any more.
5. Recompute `effectiveInputHash` only if you hold the inputs, by the definition `effectiveInputHashVersion` names.
6. Read `nodes` with `catalogRef`: each node's `outputContract` (or the text contract) names the agent that produced its output, and `nodeOutputs` gives the hashes of what that agent received and returned.

Two records with the same `workflowPackage`, `catalogRef`, `effectiveInputHash` (same version) ran the same clinical input through the same prompts and agents. Whether they produced the same deliverable is what `workflowOutputHash` says.
