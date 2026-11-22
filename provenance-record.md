# The provenance record

*provenance record, storage versions 2, 6, 7, 8, 9, 10 and 11 — published as part of `provenance@vYYYY.MM.N`; see `provenance-versions.json` for the version this document belongs to.*

Every consult the Consultologist engine generates leaves one **record**: the job. This document is the contract for what that record carries — which fields an outside reader will find, what each one means, and how to read them together. It describes what **is** recorded. What the engine intends to record one day is not a contract and is not here; it lives in the engine's design record.

The companion document, [hash-definitions.md](hash-definitions.md), defines every hash a record carries, byte for byte, so a holder of the record can recompute them.

## 1. What a record is

A record is one job: one package, one set of inputs, one set of deliverables, produced once. It is written by the engine, never by a person, and once the job is terminal it does not change. The record is served as one JSON object; the field names below are its wire names.

Its fields are of three kinds, and the kind says how to read the field:

- **Refs** name an artifact in a public registry — `workflowPackage`, `catalogRef`. A ref is always concrete, `name@vYYYY.MM.N`, never `name@latest`: a record that pointed at a moving target would not be a record. Resolve the ref through its registry and you hold the artifact the job used. The record stores refs, never copies.
- **Operational snapshots** are what the engine had in hand when the job ran, kept on the record so the job replays and reads the same way forever — `nodes`, `itemSteps`, `collections`, `inputOrigins`, `resolvedInputTypes`, `skippedDocuments`, `classifications`, `packageTitle`, `packageTags`, `startFailure`. They are facts about that run, not artifacts, and a reader takes them as stated.
- **Derived projections, stored at completion** — `workflowOutputHash`, `workflowOutputHashVersion` and `assembledDocuments[].documentHash` are computed from the produced text once, when the job completes, and stored on the record. While the text is present a holder can recompute them and they must agree (§ 5); after the text is deleted under the retention policy (`textDroppedAtUtc`) they attest that *a* document with that digest was produced and can no longer be checked against one. Records from before 2026-08-25 derived them on every read; served values are the same.

## 2. Two version numbers that are not one ladder

A record carries two version numbers that happen to share the value 7 today and are unrelated:

- **`schemaVersion`** — the record's own *storage shape*: which fields below a reader should trust to be present and meaningful. Stamped by whichever engine path produced the record (2 for a job created before any node completed or under the earliest shape; 6 for a job whose deliverable was one assembled document; 7 for a job whose deliverables are a result set, and for every job created already failed; **8 for a job whose package is at specVersion 26** — every path of such a job stamps it, from its creation, so a 26 record never says 6 or 7; **9 for a job whose package is at specVersion 27** or 28, from its creation likewise; **10 for a job whose package is at specVersion 29**, from its creation likewise; **11 for a job whose package is at specVersion 30**, from its creation likewise). The shape bumps to 8 for the rows a 26 run adds — the flow rows in `nodes` (whose `body` and `branch` name a pruned node for the first time), a deliverable's `sources` and `composedHash` — and to 9 (since v2026.10.10, Consultologist-Blazor#1235) for what an `if`/`case` inside a loop adds: its row's per-item `branches` map, its per-item `nodeOutputs` row *skipped by condition* with a `reason`, and a block `Skipped` with a `reason` — and to 10 (since v2026.11.1, Consultologist-Blazor#1307) for what a count the run discovers adds: `unresolvedLoops`, a loop row whose `count` is null until it settles, with `resolvedAtUtc` and `reason`, a `totalBlockCount` that is a floor while any loop is unresolved, and `heldDocuments` — and to 11 (since v2026.11.2, Consultologist-Blazor#1347) for what nesting, repeating and computing add: item keys that are paths, `loopInstances`, a `while` row's passes and how it stopped, an item *not run* because its loop stopped early, a `let` row `producer: computed`, `itemProgress` kept per loop, and item names that may be element text (a `labelField`) — not for any hash: the hash ladders are unchanged. Never declared by anyone, never refused: a record at 2 is read forever. The values that exist are listed in `provenance-versions.json` as `recordStorageVersions`.
- **`packageSpecVersion`** — the *package format* the job's package was written against (`specVersion` in its manifest), defined by the [package-format registry](https://consultpubcaeast.blob.core.windows.net/package-format/latest.json). This is the number an outside reader usually wants.

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
| `source` | How the job was initiated: `app` from the app (immediate or scheduled), `email` from the email door, `forms` from the forms door (since v2026.09.2) — a held form response the account chose to run at once: the response is the consult, the way an email is, and its slots carry `form-response` origins. Absent only on records from before 2026-07-27 (#158), which were all the app's. |
| `apiHost` | The canonical public host of the deployment that ran the job — `east.ca.api.consultologist.ai` — which is where the data was processed: the record's data-residency statement. The deployment's own declaration (`Public/Engine` attests the same name), one per region, never the hostname a client happened to call. Absent when the deployment named no host, and on records from before 2026-08-28. |
| `deciding` | `true` while the job's fire set — which deliverables it will produce, and so `totalBlockCount` — is not yet known: a specVersion 10 package with classifier nodes runs those first and decides at the boundary. Absent or `false` otherwise. A job that is `deciding` with `decidedAtUtc` absent has a count that is not yet known, not a count of zero. |
| `unresolvedLoops` | Storage 10 (specVersion 29): the ids of the loops over a node's value whose count is not yet known — a loop is listed from the job's start until its source node completes, and removed once, when its count settles. Empty or absent when every count is known. A loop still listed on a terminal job is *count never known* (its source failed, so the job did), not a loop of zero items. |
| `loopInstances` | Storage 11 (specVersion 30): one row per instance of a loop that runs inside another loop or a `while` — `{ loopId, path, count, resolvedAtUtc, reason?, failure?, passes?, stopped?, stopReason? }`. `path` is the outer item's path (`2`, `2/1`), so `paragraphs` under part 1 and under part 2 are two rows. `count` is that instance's items, settled once; `reason` names an empty list (*no items: node.outline.value.points was empty*), `failure` an instance whose source failed. When the instance stopped early or is a `while`'s, `passes`, `stopped` (`check`, `until`, `bound` or `end`) and `stopReason` (*its until held at item 1 (Paragraphs 1)*) say how. A top-level loop keeps its 29 row in `nodes` and has none here. Absent below 11. |
| `decidedAtUtc` | The instant the fire set was decided. For every package without a classifier that is the job's start (equal to `createdAtUtc`); for a package with classifiers, the boundary. Absent on a job still deciding, on a job that ended in the deciding stage (`decisionFailureKind`), and on records from before 2026-08-27 — which read as decided at start. |
| `schemaVersion` | § 2. |

### 3.2 Work and progress

| Field | Meaning |
|---|---|
| `totalBlockCount`, `completedBlockCount`, `failedBlockCount` | A block is one unit of deliverable work — one (deliverable × source × item). Below storage 10 the total is fixed when the job starts and never changes. At storage 10 it is the blocks laid out so far: a loop over a node's value adds its blocks once, when its count settles, so the total is final when `unresolvedLoops` is empty and a floor while it is not. The other two count settled blocks. A job created already failed states a total of 0. |
| `generatedBlocks`, `failedBlocks`, `skippedBlocks` | Block id → generated text / error / reason. Clinical content lives here; see § 4. `skippedBlocks` (storage 9) names the blocks an `if`/`case` inside a loop skipped by condition — a named state beside completed and failed, counted among the completed blocks (`completedBlockCount`), no text; the reason is the condition's text, never the value it read. At storage 11 a block id's item part is a path (`consult:paragraphs:1/2`), and a block an `until` or a `max` did not run is in `skippedBlocks` with *not run: stopped early at item 1 (Paragraphs 1)*. |
| `completedStageCount`, `totalStageCount` | Nodes completed / nodes in the job. |
| `itemProgress` | Per fan item: `{ id, name, step, completedStepCount, totalStepCount }`. Keyed by the item id below storage 11; at storage 11 by the loop's collection and the item's path (`<collection>|<path>`), so two loops whose items share ids — two lists numbered from 1 — keep apart. `name` may be element text at storage 11 (see `loopInstances`). |
| `history` | Ordered events `{ kind, message, blockId?, atUtc }` the engine wrote as the job ran. |
| `analysisStatus`, `analysisError`, `runtimeFailureStage`, `runtimeFailureError` | How and where a job that ran failed, when it did. Absent on a job that failed before running (`startFailure` instead). |

### 3.3 Provenance

| Field | Kind | Meaning |
|---|---|---|
| `workflowPackage` | ref | `name@vYYYY.MM.N` of the workflow package the job ran — the manifest, prompts, schemas and data that produced it. Resolve it through the [workflow-packages registry](https://consultpubcaeast.blob.core.windows.net/workflow-packages/) (public packages) or the account's own registry (`acct-…` packages, whose manifests carry a `derivedFrom` chain back to a public root). |
| `packageSpecVersion` | snapshot | § 2. |
| `packageTitle` | snapshot | The package's title as it was at that version; absent for an untitled package. A label for a person, never a substitute for `workflowPackage`. |
| `packageTags` | snapshot | The package's tags as they were; an empty list for a package that declared none; absent for a package whose format predates tags (specVersion < 9). |
| `catalogRef` | ref | `output-contracts@vYYYY.MM.N` — the output-contract catalog version the job ran under, which maps each contract id to the agent that produced structured output for it. Resolve it through the [output-contracts registry](https://consultpubcaeast.blob.core.windows.net/output-contracts/latest.json). Distinct from the catalog the *package* was published under, which the package's own `publish.json` records; comparing the two shows whether a contract was redefined between publish and run. |
| `formatsRef` | ref | `formats@vYYYY.MM.N` — the formats catalogue version the job ran under (since this contract version, engine v2026.10.3): the registry artifact that maps a specVersion 25 node's `format` to the agent that produced it (`nodes[].agentName`/`agentVersion` are copied from it at start), publishes each format's file (whose canonical JSON is the node's `formatHash`), and names the one generic agent every custom shape runs on (`producers.custom`). Resolve it through the [formats registry](https://consultpubcaeast.blob.core.windows.net/formats/latest.json). A package stamped with a formats version runs that version, so this equals the package's stamp; a package below 25 carries no stamp and the field names the engine's pinned catalogue — which still matters below 25, because since engine v2026.10.3 a 22–24 custom-schema node runs that catalogue's generic agent. Absent on records from before. |
| `engineCommit` | snapshot | The engine build that ran the job: the full commit in the engine's repository, the same value `Public/Engine` attested at the time. The attestation at that commit is the witness for every rule the record does not carry itself. Absent on records from before 2026-08-28; for those, `createdAtUtc` and the deploy log are the only witness. |
| `engineRelease` | snapshot | The GitHub Release the engine build was deployed from: a tag like `v2026.09.1` in the engine's repository, which `Public/Engine` attests beside the commit. The engine deploys from a tagged release, so a record names the release its `engineCommit` shipped under; resolve it on GitHub to the release page for that version. Absent when the deployment carried no release tag — a manual `workflow_dispatch` deploy stamps only the commit — and on records from before this contract version, for which `engineCommit` alone locates the build. |
| `packageFormatRef` | ref | `package-format@vYYYY.MM.N` — the format registry version whose documents define the rules the job's package was interpreted under. Resolve `packageSpecVersion` through that version's `spec-versions.json` to the document, not through the latest. Absent on records from before 2026-08-25; for those, the engine build that produced them is the only witness to the rules. |
| `provenanceRef` | ref | `provenance@vYYYY.MM.N` — the version of **this contract** the record conforms to. A reader opens that version's `provenance-record.md` and `hash-definitions.md`, not the latest. Absent on records from before 2026-08-25. |
| `terminology` | snapshot | `{ edition, version, importDate }` — the SNOMED CT edition the terminology server had loaded when the job started, as the server reported it (`SNOMEDCT 20251130 import.`, `2025-11-30`, an ISO instant). This is what every concept's `isSnomedConcept` and `isActive` were answered against; editions retire and reactivate concepts, so two records that differ only here can differ in their deliverables. Absent when the server could not be read at start, and on records from before 2026-08-25. |
| `textDroppedAtUtc` | snapshot | Present once the app has deleted the produced text under its retention policy: the instant it did. After it, `assembledDocuments[].text`, `assembledDocument`, `generatedBlocks` and the extracted concepts are gone from the record; every hash, node, ref and label stays. Absent while the text is present. |
| `terminologyServerRef` | ref | `snomed-snowstorm-mcp@<commit>` — the build of the terminology server that served the run: a commit in that Apache-2.0 repository, not a registry version; resolve it on GitHub. A server deployed without a stamp reports its assembly version instead, and the ref carries that. Absent likewise. |
| `terminologyServerRelease` | snapshot | The GitHub Release the terminology server was deployed from: a tag like `v2026.09.1` in that same repository, which the server attests at `Public/Terminology` beside its commit. The server deploys from a tagged release, so a record names the release its `terminologyServerRef` commit shipped under; resolve it on GitHub to the release page. Absent when the server carried no release tag (a hand deploy stamps only the commit), and on records from before this contract version — for those `terminologyServerRef` alone locates the build. |
| `effectiveInputHash`, `effectiveInputHashVersion` | derived at start, stored | The hash of the inputs the job actually ran on, and the number of the definition that computed it (hash-definitions.md § 2). Computed once when the job starts and stored, because the inputs themselves are not on the record. |
| `inputOrigins` | snapshot + derived | Input id → list of origins, positionally per supplied element: `{ kind, extractor?, pageCount?, trackedChangesResolved, fileSha256?, textSha256? }`. `kind` is `document` for an element read from an uploaded file; `extractor` names the extractor build (`name/version+commit`). Absent means *not recorded*, never *typed by hand*. Recorded beside the input hash and never inside it. The two digests (hash-definitions.md § 6) are derived and checkable: `fileSha256` is SHA-256 of the file's bytes as received — the bytes themselves are never kept — and `textSha256` of the text read from it as it entered the effective-input map. Equal file digests with unequal text digests say the extraction changed, not the document (compare `extractor`); unequal file digests say a different file. Absent on records from before 2026-08-28. Neither is a name. `kind` is `previous-run` (since 2026-08-29) for an element the app copied, when the job started, from one of the same account's own completed runs: `sourceJobId` names that run and `sourceResultId` its deliverable; `textSha256` is over the copy as it entered the effective-input map, and equals SHA-256 of that deliverable's canonical text (the source's `assembledDocuments[].documentHash` is over its raw text, so the two agree only when that text was already canonical). The reference resolves through the account's own records, never a public registry, and only while the source's text is held — after its `textDroppedAtUtc` the source's hashes remain and the copy stands on its own. A copy the user edited before submitting is not a copy: it carries no origin. `kind` is `rerun` (since 2026-08-31) when the app replayed a whole run from one of the same account's own completed runs' held inputs: every effective slot of the new job carries one, `sourceJobId` names the source run, and `textSha256` is SHA-256 of the slot's effective value verbatim — equal, slot for slot, to the source's effective values by construction, so the two records' `effectiveInputHash` agree or one of them is wrong. The reference resolves through the account's own records, never a public registry. A rerun could only start while the source's held inputs existed; the origin stands after they are deleted. `kind` is `form-response` (since 2026-09-01) for an element the app filled, when the job started, from one of the same account's held form responses — a questionnaire answer staged by the intake door: `sourceFormId` and `sourceResponseId` name the response; `textSha256` is over the value as it entered the effective-input map (the held answer string, coerced by the input's declaration). The start verified the held response still held that value — observed, as `previous-run` is — and the reference resolves through the account's own held responses, never a public registry, and only while the response's values are held; after its `deletedAtUtc` the origin stands on its own. A value the user edited after loading is not a fill: it is typed text and carries no origin. `kind` is `transcript` (since 2026-09-09) for an element read from an uploaded file the caller declared to be a meeting transcript: the server-observed fields are exactly a `document`'s — `extractor` names the extractor build, and `fileSha256`/`textSha256` are the same two derived, checkable digests over the file's bytes as received and the text read from it as it entered the effective-input map — but the `kind` label is the submitter's assertion about what the file is, not something the server observed, because whether a text is a clinical transcript cannot be read from its bytes. A satellite (the Zoom app of docs/ZOOM_SATELLITE_SPIKE.md in the engine repo) fetches a speaker-labeled transcript as the signed-in clinician and submits it like any document, so a transcript and a document carrying identical text have equal `effectiveInputHash` and differ only here; the assertion resolves nothing external — the bytes are inline and there is no reference to verify. A file the caller did not so declare is a `document`. `kind` is `image` (since 2026-09-16) for an element read from an uploaded raw image (PNG/JPEG/TIFF) whose text was produced by OCR: the server-observed fields are a `document`'s — `extractor` names the OCR build (Azure Document Intelligence), `pageCount` is the image's single page, and `fileSha256`/`textSha256` are the two derived, checkable digests over the image bytes as received and the OCR'd text as it entered the effective-input map. Unlike `transcript`, this label is a server fact, not a submitter assertion: the parser recognized the image's bytes, so an image and a document carrying the same recognized text differ here because the server saw an image. An image is refused, not stamped, when OCR is unconfigured. `kind` is `ambient-note` (since 2026-09-17) for an element read from an uploaded file declared to be an ambient-scribe clinical note (Dragon Copilot): the server-observed fields are exactly a `document`'s — `extractor` names the extractor build, and `fileSha256`/`textSha256` are the same two derived, checkable digests over the file's bytes as received and the text read from it as it entered the effective-input map — but, like `transcript` and unlike `image`, the `kind` label is an assertion, not something the server observed, because whether a text is an ambient-scribe note cannot be read from its bytes. The assertion is the package's (a slot declaring `expectedContent: ambient-note`, since specVersion 17) or the caller's (a submission marker), and it resolves nothing external — the bytes are inline. It is a distinct kind from `transcript` on purpose: an ambient note is an AI-summarized visit draft, not speaker turns, and keeping the kinds separate keeps the SaMD/anti-ambient boundary legible in the record. An ambient-note and a document carrying identical text have equal `effectiveInputHash` and differ only here. A file not so declared is a `document`. `kind` is `typed` (since 2026-09-28) for an array element the clinician entered as text in a slot whose array also carries documents or previous-run deliverables — a mixed array (#872): `textSha256` is the same derived, checkable digest over the canonical text as it entered the effective-input map; there is no `extractor`, `pageCount` or `fileSha256`, because nothing was read from a file. Recorded beside the effective-input hash, never inside it, like every origin kind. Stamped only for a mixed array — a slot whose every element is typed text carries no origin at all, as before; the origin exists only to tell a typed row apart from its document and previous-run neighbours within the same array. Two **variants by fields** (since this contract version; the kinds do not change): a `form-response` origin whose bytes came from a questionnaire file the clinician loaded on the Create page (engine #991) carries `fileSha256` over the file as received and `textSha256` over the object as it entered the effective-input map, and **no** `sourceFormId`/`sourceResponseId` — the bytes were inline, nothing was held and nothing external resolves; a `transcript` origin from a transcript file loaded on the Create page (engine #994) carries exactly a `transcript`'s fields, the assertion still the submitter's. For a VTT or SRT file the text the parser read is the conversation as **turns**, one line per turn — `Speaker: text` where the source labels a speaker (a WebVTT voice tag, or a `Name:` prefix on the cue), consecutive cues of one speaker merged into one turn — with everything that is container rather than speech removed: the `WEBVTT` header, `NOTE`/`STYLE`/`REGION` blocks, cue identifiers, timing lines and their cue settings, inline tags and timestamps; entities decoded; then canonicalised as every text is. So `textSha256` is over the turns, and one conversation hashes the same whichever container it arrived in; the timings survive only in the file `fileSha256` identifies; `extractor` names the parser build (`vtt/1`, `srt/1`), so a change in how turns are read is explained there, as a library change is for a PDF. A plain-text transcript has no container and is read as any text file (`text/1`), unchanged. A **recording** (WAV, MP3, M4A, OGG, FLAC — told by its bytes) loaded on the Create page or sent by a caller is transcribed by speech-to-text (engine #1063, specVersion 26's audio) and carries exactly the same fields: `fileSha256` over the audio bytes as received — never kept — and `textSha256` over the **turns** by the same rule, `Speaker N: text` per turn with the speakers as the service numbered them and consecutive phrases of one speaker merged, so a recording and the transcript file of the same conversation differ in `fileSha256` and `extractor` and may share a `textSha256`; `extractor` names the speech-to-text build (`speech/<version>+<commit>`, the client library the engine called). The recording's duration and the service's confidence are telemetry, not record: no field is added and no version moves. The `kind` is still the declaration's or the caller's assertion — a recording on a plain input is a `document` read by `speech/…`, as a transcript file is. A reader tells the file-sourced form response from a held one by the absence of the source ids. |
| `resolvedInputTypes` | snapshot | Input id → the value type its supplied value matched, for slots declaring a **union** of types (#729, since 2026-09-16): the first arm, in the union's declared order, whose value check passed. Recorded beside the input hash and never inside it — the `effectiveInputHash` is over the value bytes, so which arm matched is attribution, derivable from the stored value and the pinned declaration, not part of the hash. Absent for every slot with a single declared type, and on records predating the field. |
| `acknowledgedShortInputs` | snapshot | The required input ids whose content fell below the referral floor — fewer than the minimum meaningful characters, URLs and whitespace removed (hash-definitions.md § 6) — and which the submitter explicitly acknowledged as intentionally short, so the job started rather than being refused (#802, since 2026-09-20). The floor (the `does not contain a referral` refusal) exists to catch a body that carries no referral — a cloud link, an empty scan; this list records that a person overrode it, and on which slots, so a reader sees the floor was *consciously bypassed* rather than silently absent — the discipline the floor itself was written for. Only the ids actually below the floor **and** acknowledged appear; a run refused no slot carries no field. Recorded beside the input hash and never inside it — the `effectiveInputHash` is over the value bytes, so the acknowledgement is attribution. The acknowledgement waives the length floor only: a required input pointing at a cloud link is still refused (`refers to a file stored in the cloud`) even when acknowledged short, because a link is a missing document, not a terse one. An interactive-door fact — the app's Create page carries the toggle; the email and satellite doors have no one to acknowledge in-band and are refused as before. Absent on records predating the field. |
| `rerunOf` | snapshot | The completed run whose held inputs this job replayed — the same `sourceJobId` every slot's `rerun` origin carries, lifted to the job level. Absent on every non-rerun, and on reruns recorded before this field existed (their slot origins still name the source). |
| `rerunVerdict`, `rerunDivergence` | derived at completion, stored | Whether the replay reproduced the source, judged over the package's own claims: `pass` when every reproducible node's `outputHash` equals the source run's for the same `inputHash` and the same per-node `hashVersion`; `fail` with `rerunDivergence` naming the first stage that differs, in package order — or `effective-inputs`, the by-construction breach that means the replay itself is wrong; `no-reproducible-stages` when no stage was comparable (the package claims none reproducible, or every candidate's preconditions failed) — named, never a vacuous pass. Stages whose `inputHash` or `hashVersion` differ from the source's are shown, not counted; non-reproducible nodes likewise. Absent on non-reruns and on reruns that did not complete. |
| `tokens` | derived at completion, stored | The job's totals, `{ input, output }`: summed once, at completion (Completed or Failed — a failed run spent tokens too), over the node instances that recorded usage. Absent when none did, or when the record predates the field — never zero. The usage stores (#552) are written from this at completion and never re-derived from records. |
| `nodes` | snapshot | The nodes the job ran, in package order: `{ id, label, promptId?, bindings?, outputContract?, failIfEmpty?, forEach?, conceptSource?, aggregate?, values?, reproducible?, check?, template?, agentName?, agentVersion?, customSchemaHash?, macros?, format?, producer?, formatHash?, op?, reads?, with?, onInvalid? }`. `outputContract` names the catalog contract a node's output was parsed against; absent means the text contract. `values` (specVersion 10) is a classifier's declared answer set. `reproducible` (specVersion 11) is the package's claim that this node's output is the same for the same input — carried, never enforced at run time; true or absent, never false; the rerun verdict reads it. `check` (specVersion 12) is a check node's whole declaration — `{ op, of, in, failWith }` — and the explicit discriminator: a node is a check exactly when it is present. `template` (specVersion 12) is true or absent, never false: the node's prompt renders deterministically and the render is its output. `agentName` and `agentVersion` (since 2026-09-14, engine #923) are the agent the node ran, resolved at start from the catalogue version the package's own stamp names — the pair `catalogRef` would resolve `outputContract` to, copied onto the node so a reader need not resolve; absent on a template node. `customSchemaHash` (since 2026-10-04, #760) is on a custom-schema node, the digest its row repeats. `macros` (specVersion 23) lists the library macros placed on the node — `{ id, after?, when?, forItem?, reads? }` — composed into its **prompt** below specVersion 25 (so inside `inputHash`) and around its **output** at 25 (so inside `outputHash`, definition 6). **At specVersion 25** a node carries `format` (a catalogue id, or a package-local format's id), `formatHash` (SHA-256 of the format file's canonical JSON — the catalogue's at `formatsRef`, or the package's own file), `producer` (`attested` — a catalogue agent, named by `agentName`/`agentVersion`; `custom` — the package's own shape, run on the catalogue's generic agent named the same way, engine-validated against the file's schema; `rendered` — no model, the render is the output; `computed` — no prompt, `op` names the engine operation, today `terms-subset`), `reads` (the node ids the node's template and parameters read — the **derived edges**, closed over the snippets and macro texts the prompt reads and over the texts composed at its completion; sorted; this is the field `bindings` was below 25, which a 25 node does not carry), `with` (the format's parameters as resolved at start: a `node` parameter as the bare node id, a `text` parameter as its literal or the referenced input's value; a `values` parameter resolves into `values`), `onInvalid` (`fail` \| `retry` \| `flag` — the node's policy on a reply its format refuses; `retry` is reserved and runs as `fail`) and `failIfEmpty` at the node. `outputContract`, `check` (the v12 declaration) and `bindings` are absent at 25: the format and `reads` say what they said. Nodes the package declared but the job did not need are not listed. **At storage 8 (specVersion 26)** a node's row names its prompt by path — `prompt` (`prompts/assessment.md`) in place of `promptId`, which is absent — and `forEach` and `aggregate` are absent: a node that runs once per item is a body node of a loop, and its row says so with `in` (the flow node it runs inside); a node that composes items is the loop itself. `macros[]` entries carry `if` (the instance's gate, specVersion 26) where 25's carried `when`. A **flow node** has a row of its own: `{ id, label, kind, expression | collection, body, ret, branch?, count?, reads? }` — `kind` one of `for`, `if`, `case` (the discriminator: a row with `kind` is a flow node, and only a flow node has it); a `for` row carries `collection` (what it iterates, `snippet.<folder>` or `input.<id>`, the spelling a 25 `forEach` used) and `count` (the items the loop ran over, after their gates — the settled fan); an `if` row carries `expression` (its gate's text) and a `case` row the subject it switches on; `body` is the node ids inside it, every branch's; `ret` is the body node the flow node returns — a loop's, or the **taken** branch's for an `if`/`case`, absent while undecided and when no branch was taken; `branch` is the decision as the engine took it — `then`, `else`, the matched values as the package wrote them (`<v1, v2>`), or `none` — on an `if`/`case` row only. A pruned node below 26 had no row at all; at 26 it is a body node of the untaken branch — **not listed in `nodes`** and with no `nodeOutputs` entry, but named in its if/case row's `body`, with that row's `branch` saying which branch ran (since v2026.10.9, Consultologist-Blazor#1223: the engine never served a pruned node's own row) — the first time the record says why a node did not run. **At storage 9 (specVersion 27)** an `if`/`case` may run **inside a loop**: its row carries `in` (the loop, as a body node's does) and **`branches`** — a map `itemId → "then" \| "else" \| "<v1, v2>" \| "none"`, one entry per item of the loop, written as the items decide (the row is complete when the loop completes); it carries no `branch` and no `ret` (a row never carries both `branch` and `branches`; the returned node is per item, the taken branch's). A node of its branches has `in` naming the flow node; its loop is reached through the flow row's `in` (two levels: a reader walks `in` until it meets a `for`). A top-level flow row is unchanged. **At storage 10 (specVersion 29)** a `for` may iterate **a node's value**: its `collection` is the reference as written (`node.find_problems.value.problems`), its `count` is **null until the count settles** — when the source node completes — and then the items that node's list held, and it carries `resolvedAtUtc` (the instant the count settled) and, for a list that was empty, `reason` (*no items: node.find_problems.value.problems was empty*); a loop whose source never completed keeps `count` null, never zero. Its items are named by 1-based position (`draft_problem:1`), and the element values are never on the record — the source node's `outputHash` covers the list. A loop over a folder whose item's `if` reads a node keeps that item from the start; when the condition does not hold, the item's `nodeOutputs` row `<loop>:<item>` is `Skipped` with a `reason` that is the condition's text (never the value it read), and each sourcing deliverable's block is in `skippedBlocks`, as storage 9 records an item an inner `if` skipped. |
| `itemSteps`, `collections` | snapshot | The fanned nodes (`{ id, label }`) and the fan rosters the job iterated (`{ collectionId, items: [{ id, name }] }`). |
| `nodeOutputs` | snapshot | Per node instance (`nodeId` or `nodeId:itemId`): `{ nodeId, label, status, inputHash?, outputHash?, hashVersion?, completedAtUtc?, error?, classification?, tokens? }`. The two hashes are the per-node hashes and `hashVersion` names their definition (hash-definitions.md § 4); absent on records from before the ladder. `classification` is a classifier node's normalised answer — one of the values the package declared for it — and is what its `outputHash` is over; absent on every other node. `tokens` (since #551 in the engine) is `{ input, output }` — the token counts the model provider reported for this node's one response, as reported: the succeeding attempt's counts when the call was retried (a retried node under-reports billed spend), with reasoning tokens inside `output`. Counts are numbers, never text. Absent means *not recorded*, never zero — every aggregate and fan roll-up records none (no model ran), and every record from before this field says nothing. `check` (specVersion 12) is a check node's verdict and its evidence — `{ passed, uncovered?, untested? }`, the same evidence lists `failedDocuments` carries; only a check node's row has it, and a check row carries no hashes and no tokens: nothing was sent and no model ran. A **template** node's row (specVersion 12) has no new field but one stated shape: its `inputHash` equals its `outputHash` — nothing was sent to a model, and the message-that-would-have-been *is* the output — and it records no `tokens`. `startedAtUtc` and `durationMs` (since 2026-09-03) are the activity's own clock: the wall time it began and how long it executed, queue and retry wait excluded — with `completedAtUtc` (the record's write time) the run's per-row trace. Absent means *not recorded*, never zero: aggregate, check and roll-up rows run no activity and record none, and every record from before says nothing. `errorType` and `errorStack` (since 2026-09-03) are a failed row's exception type and its frames — code paths, never the exception's message beyond what `error` already carries. `unattested`, `customSchemaHash` and `customAgent` (since 2026-10-04, engine v2026.10.1 — the custom tier of the two-tier output-schema model) ride a node whose output shape is a package-defined **custom schema** (package-format v22 `customSchemas`): `unattested` is true or absent, never false — the node resolved to the reserved `custom` contract and ran on an engine-provisioned, content-addressed agent, not a catalog contract: not git-attested, not CI-published, not SNOMED-grounded; `customSchemaHash` is the SHA-256 of the schema the agent enforced and `customAgent` the `name@version` of that agent (`custom-<hash>@<n>`), so the output is reproducible — same schema and model ⇒ same agent ⇒ same contract — yet **unattested**, and a reader must show it as such, never as a catalog-contract deliverable. The marker is on the node-level row; a fanned custom node's item rows carry it from the node's `outputContract` (engine #980). **At specVersion 25 — custom shape, engine-validated.** A node whose `nodes[].producer` is `custom` carries **none** of `unattested`, `customSchemaHash` and `customAgent`: the shape is the package's own (its file's digest is `nodes[].formatHash`), the agent is the catalogue's generic `custom-json` (`nodes[].agentName`/`agentVersion`, attested and CI-published like every catalogue agent, resolved through `formatsRef`), and the engine validated the reply against the declared schema (`validation` below). A reader shows such output as a *custom shape, engine-validated* — a package-defined shape, not a catalogue contract, no terminology grounding — and never as unattested in the #760 sense: nothing ran that was not attested. `unattested` stays true-or-absent, never false; absence on a `producer: custom` node is the rule above, not an omission. `validation` (specVersion 25) is the reply's check against its format after parsing — `{ valid, errors[] }`, each error a path and a rule, never the reply's text; absent on a text format, on a rendered node, and on records from before; present with `valid: false` only when the node's `onInvalid` is `flag` (under `fail` the node failed instead). `agentOutputHash` (specVersion 25, hash-definitions.md § 4 definition 6) is the digest of the reply as returned, beside `outputHash`, which at 25 is over the node's composed output; equal when nothing composed and nothing was stripped. `appended[]` (specVersion 25) names what the node's completion placed into its output, in output order — `{ kind, id }`, `kind` one of `macro` (a before/after instance of the library macro `id`) or `inline` (the macro `id` whose text the reply itself read as `{{ macro.<id>.content }}` when it rendered — the inline macro the prompt instructed; one entry per read, in the order the render met them; a read inside a filled text is that text's, not an entry) — the text is already inside `outputHash`; the entries name it. `excluded[]` (specVersion 25) names what the completion withheld, by name — `{ kind, id, reason }`: a `macro` instance whose `when` refused (`reason` composed as `skippedDocuments` reasons are — at specVersion 25 their fixed form). Nothing in a rendered reply is withheld or removed: a reply that does not render fails the node (`error` carries the renderer's sentence). Both absent when empty and on records from before; on a fanned node each item row carries its own. **A flow node's instance (storage 8):** an `if`/`case` row is an alias of the branch it took — `status` and `completedAtUtc`, no hashes and no tokens (nothing was sent; its `ret` names the node whose output a reader of the flow node reads), and `Skipped` when it took no branch; a `for` row is the loop's composition and carries the pair the 25 aggregator carried — `inputHash` over its `ret` items' output hashes in the fan's order, `outputHash` over the text it composed, `hashVersion` 6 (hash-definitions.md § 4) — and no tokens. **An `if`/`case` inside a loop (storage 9):** its instances are per item; a taken item has **no row of its own** — the taken branch's returned node's row *is* its output, as a top-level flow node's alias is — and an item it **skipped by condition** (no `else`, no branch taken) has the row `<flow>:<item>` with `status: Skipped`, `completedAtUtc`, no hashes, no tokens, and **`reason`**: the condition's text in the fixed form (`needs \`<text>\`; it does not hold` for an `if`; `switches on \`<subject>\`; no branch lists its value` for a `case`) — never the value it read. The branch nodes of that item ran nothing and have no rows for it; the loop still counts the item (its `count`), composes the items that returned in item order, and its `inputHash` is over the returned items' output hashes — a 26 loop with no inner flow hashes byte-identically at 27. |
| `classifications` | snapshot | Classifier node id → the value it answered, for every classifier that ran: `{ "scope": "out_of_scope" }`. Declared values, never free text — a classification is one of the words the package wrote, so it is printable where patient text is not. Present on a job with classifiers once they have answered, including a job that ended in the deciding stage; absent otherwise. |
| `decisionFailureKind` | snapshot | Why a job ended in the deciding stage, beside `startFailure`: `could-not-decide` (a classifier failed) or `nothing-applied` (every deliverable's condition, read with the classifiers' answers, refused). Absent on every other job. |
| `workflowOutputHash`, `workflowOutputHashVersion` | derived | The hash of the deliverable set of a **completed** job and its definition number (hash-definitions.md § 3). Absent on any job that is not `Completed`: the deliverable hash of a partial job is undefined. |
| `assembledDocuments` | snapshot + derived | The deliverables: `{ resultId, label, text, documentHash, appended?, unsigned? }`. `text` is clinical content (§ 4); `documentHash` is derived, SHA-256 of `text`, and is the per-document digest definition 3 is computed over. `appended` (specVersion 11) names what the engine placed and appended, in **document order**: `{ kind, id, asOf? }`, `kind` one of `macro`, `signature` or `slot` (specVersion 20: a macro's text filled where the model emitted `[[slot:<id>]]` at document assembly; at specVersion 25 the macro is read inline — the reply renders its `{{ macro.<id>.content }}` read — and its entry sits on that node's row as `inline`, `nodeOutputs[].appended[]`, never here); `asOf` (yyyy-MM-dd, the signature block's edit date as snapshotted at the job's start) rides signature entries only. After the aggregated sections is the default position, not the definition: since specVersion 12 a macro may sit between sections, and an embedded signature where its macro put it — the entries carry no placement field, because the record's pinned package version already says where each macro sits. The appended text is already inside `text` — and therefore inside `documentHash` — when the hash is stamped: the entries name it, they add no bytes. `unsigned` is true or absent, never false: the package requested a signature and no block was chosen on the profile — the document is the work, produced unsigned and said so, here and in the job's history. **At storage 8 (specVersion 26)** a document carries `sources` — the node ids the package named for it, in the package's order: each a `for` node (its items in the fan's order) or a scalar node — and `composedHash`, SHA-256 of the text composed from those sources **before** the deliverable's own macros are appended: the digest the 25 aggregator's row carried as `agentOutputHash`, moved to the document it belongs to (`documentHash` stays the digest of `text`, macros inside). A 26 deliverable has no aggregator node; the two hashes bracket what its macros added. |
| `assembledDocument` | snapshot | Storage version 6 only: the single assembled document. |
| `skippedDocuments` | snapshot | Deliverables the package declared that this job did not produce: `{ resultId, label, reason }`. `reason` is composed of the package's own words — the input named, what was supplied, what the condition wanted. A condition of one clause reads *needs `<operand>` to be `<wanted>`; it is `<found>`*; a specVersion 10 expression of several reads *needs (`<what each clause wanted>`); `<what each found>`*, joined as the condition was — each clause under the same rule: a declared value, a count, a comparison outcome or *not supplied* is printed, a patient's text never is. A clause over a classifier not yet answered reads *it is not decided*. **At specVersion 25** a `when` is a Scriban boolean expression over the objects a template reads (an input, a node's value or text, a snippet, a fact), so no value is ever printed: the reason is the one fixed form *needs `<the when as the package wrote it>`; it does not hold* — the condition's own text, package-authored, between backticks — and a deliverable skipped because a node it reaches was gated reads *needs node '<id>', which needs `<that node's when>`; it does not hold*. The same no-PHI rule, met by printing nothing but the package's text. **At specVersion 26** the gate is keyed `if` and the fixed form reads it the same (*needs `<the if>`; it does not hold*); a deliverable whose source is a body of an `if`/`case` that took no branch reads *source node.<id> took no branch* — the flow node's id, the one row in `nodes` whose `branch` is `none`. |
| `heldDocuments` | snapshot | Storage 10 (specVersion 29): the deliverables composed and not released — `{ resultId, label, ordinal, composedHash?, sources?, composedAtUtc, reason? }`. A deliverable is listed when it is composed and leaves the list when it is released (to `assembledDocuments`) or refused by its check (to `failedDocuments`). One still listed on a terminal job carries `reason` — why it was held (a node its macros read did not complete, a deliverable it reads was never composed, its check never settled) — and the job is `Failed` saying so. No text: a held deliverable never had any, which is not text deleted under retention. |
| `nodes`, `nodeOutputs` at storage 11 | snapshot | Storage 11 (specVersion 30). **Paths:** a `nodeOutputs` key is `nodeId:path` — the item ids from the outermost loop inward, joined by `/` (`draft_paragraph:2/1`); at one level the path is the item id, as at 29; a `while`'s body rows take the pass number as the segment (`draft:2`). A loop row in `nodes` may carry `in` (the loop that holds it). **A `while` row:** `kind: while`, its check as `expression`, `body`, `ret`, `max`, `until?`, `checkFirst?`, and once it stops `passes`, `stopped` and `stopReason` (*its check stopped holding*; reaching `max` is `bound`, never silent). A `for` row may carry `max`, `until` and `labelField`, and the same three stop members. **An item not run:** the row `<node>:<path>` is `Skipped` with the reason *not run: stopped early at …*. **A `let` row:** `op: let` and `producer: computed`, its expression as `let` and its type as `letType` (package text, never a value), and on its `nodeOutputs` row `producer: computed`, `inputHash` over the expression and what it read, and `outputHash` over the value; the value itself is never on the record. **Names:** an item's name in `collections`, `itemProgress`, block labels, History and a *not run … (Name)* reason is the loop's label and position as at 29 — or, when the loop or its input declares `labelField`, that field's text, trimmed and cut to 120 characters. That name is kept for the life of the record: the retention sweep deletes produced text, concepts and held inputs, not names, as it keeps a folder item's `label`. It is the one element value the record may carry. |
| `failedDocuments` | snapshot | Since specVersion 12: deliverables the package declared, the job produced, and the deliverable's own check refused — the third state beside produced and skipped: `{ resultId, label, reason, uncovered?, untested? }`. `reason` is the package's own `failWith` sentence, verbatim. `uncovered` lists the terms of the input-side concepts whose SNOMED ids the document's terms did not cover — the check's evidence; `untested` lists the terms, from either side, the extraction could not code and the set test therefore never saw — named, never silently dropped. Terms here are model-extracted clinical vocabulary, the same class as the extracted concepts the record already carries. A failed document has no `assembledDocuments` entry, no text and no hash: it was refused before it shipped. At storage 8 it carries `composedHash` — the digest of the composed text the check refused, so a holder of that text can show it was the one judged. |
| `excludedMacros` | snapshot | Since specVersion 12: macros a `when` clause excluded from a deliverable that fired: `{ resultId, macroId, reason }`. `reason` is composed as `skippedDocuments` reasons are — the package's names, declared values, a classifier's answer or *not supplied*; a patient's text never; at specVersion 25 their fixed form (*needs `<when>`; it does not hold*). Independent of `macroChoices`: a macro can be out by the run's choice, out by its clause, or both — each fact is recorded on its own and the reader ANDs them. A `when`-skipped *document* records nothing here: its macros were never judged. At specVersion 26 the clause is the instance's `if`, and the reason carries its text in the same fixed form; a macro inert by its **own** gate (the macro file's header `if`) is recorded the same way, under the macro's id, on the node or deliverable that read it. |
| `macroChoices` | snapshot | Since specVersion 12: the run's resolution of every **optional** macro the package declares — `{ "<macroId>": { value, origin } }`, `origin` one of `chosen` (the request named the id) or `default` (the package's declared default applied). Stamped from the starter's resolution, before anything runs. Required macros carry no entry; a package that declares no optional macros writes no field at all — the byte-identical record. The negative is visible: `value: false, origin: "chosen"` is a run that declined, and says so. |
| `failureStack` | snapshot | Since 2026-09-03, on failed jobs whose failure carried an exception: the exception's type and frames, captured where it fell — the failed node's activity, the deciding stage, or the orchestrator itself. Code paths only; the message keeps its own fields and its own discipline. Absent on completed jobs and on failures with no exception (a condition that refused, an empty declared-required output). |
| `failedBlockStacks` | snapshot | Since 2026-09-03: section id → the frames of the exception that failed it, beside `failedBlocks`' messages. Only sections whose failure carried an exception appear — a `failIfEmpty` refusal has none and records none. |
| `startFailure` | snapshot | Present only on a job created already `Failed`: because no deliverable applied to its inputs at start, or — with `decisionFailureKind` — because the deciding stage ended without a fire set. The refusal sentence, composed of package content (`No document applies after classification: …` names each skipped deliverable's reason, in the form `skippedDocuments` defines — at specVersion 25 the fixed form). Nothing ran past the classifiers; there are no blocks. |
| `agentVersions` | legacy | Records written on or before 2026-07-17 only: contract id → agent version. Superseded by `catalogRef`, which resolves the same mapping through an immutable registry. Absent on every later record. |

## 4. What the contract does not cover

- **Clinical content.** `generatedBlocks`, `assembledDocuments[].text`, `assembledDocument`, `nodeOutputs` errors and `history` messages can carry the consult's text. It is on the record because the record is the account's; this contract says where it is, and says nothing about it. A verifier's inputs and outputs come from the record holder. Text a specVersion 11 or 12 package placed or appended — a macro's expansion, wherever it sits, a signature block — is inside `assembledDocuments[].text` like the rest and is covered by this same statement.
- **The inputs.** The record holds their hash and their origins, not the inputs.
- **The text, after its retention period.** The produced text is patient data and is deleted N days after the job completes (the operator's policy — 7 days at the time of writing); `textDroppedAtUtc` records the deletion. Nothing else on the record is ever deleted.
- **Legs the engine does not record.** The model checkpoint, sampling parameters and inference-stack fingerprint are not on the record; each is reachable through `catalogRef` → the agent definition, and the engine's design record names them as intended work. Until one is recorded it does not appear here. (The engine *build* is recorded since 2026-08-28 — `engineCommit`, and its release since this version — `engineRelease` — and the deployment that ran the job — `apiHost`.)

## 5. Reading a record

0. Read `apiHost` before comparing two records at all: two deployments are two places the data was processed, and a record without the field predates the statement — say so rather than assume one.
1. Read `provenanceRef` and `packageFormatRef` first: they name the version of this contract and of the format specification to read everything else by. Then resolve `workflowPackage` and `catalogRef` through their registries. You now hold the package that ran and the catalog that mapped its contracts to agents.
2. Compare `catalogRef` with the package's `publish.json` (`catalogRef` there): equal means the package ran under the catalog it was published against.
3. Before comparing two records' deliverables, compare their `terminology.version`: a different edition explains a different deliverable on its own, and nothing else on the record will.
   Then, on a specVersion 10 package with classifiers (a specVersion 25 node of an enum format — `classification` — is one), compare their `classifications`: a different answer is a different fire set — different deliverables, or none — before any prompt ran, and `skippedDocuments` says which conditions read it that way.
4. Recompute `workflowOutputHash` from `assembledDocuments` by the definition `workflowOutputHashVersion` names, and each `documentHash` from its `text`. They must match what is served. A specVersion 11 or 12 record's placed and appended text (macros wherever they sit, the signature however it landed) is inside `text` before either hash is stamped, so recomputation is unchanged — and a package that appends nothing hashes byte-identically to its specVersion 10 self. Once `textDroppedAtUtc` is present there is no text to recompute from: the stored hashes still say what was produced, and nothing on the record can be checked against them any more.
5. Recompute `effectiveInputHash` only if you hold the inputs, by the definition `effectiveInputHashVersion` names. If you hold a document that filled an input, recompute its `fileSha256` from the file: equal means the record is of that file. Two records of the same file whose `textSha256` differ were read by different extractors — *same file, different reading* — and their `extractor` values say which; that difference is the extraction's, not the referral's.
6. The run's trace is `history` read in order beside the node rows' clock: each row's `startedAtUtc`/`durationMs` (the activity's own execution) and `completedAtUtc` (when the record heard). Two records of the same package whose traces differ in shape ran different paths; ones that differ only in the clock ran the same path at different speeds — the trace is operational, and no hash covers it.
7. A deliverable absent from `assembledDocuments` is one of exactly three things, each said in its own field: skipped (`skippedDocuments` — its condition, read with the inputs and the classifiers' answers, refused before anything ran), failed (`failedDocuments`, specVersion 12 — it was produced and its own check refused to ship it; the evidence is on the entry and on the check node's row), or never declared at this package version (read the pinned package). At storage 10 there is a fourth: held (`heldDocuments` — it was composed and never released; its `reason` says why). Storage 11 adds no fifth. A record that names none of these for a missing deliverable is wrong.
8. Read `nodes` with `catalogRef`: each node's `outputContract` (or the text contract) names the agent that produced its output, and `nodeOutputs` gives the hashes of what that agent received and returned — and, since #551, the token counts it spent doing so. A node whose `outputContract` is `custom` names no catalog agent: its row's `customAgent` and `customSchemaHash` say what ran, and `unattested` says what that is not. **At specVersion 25** read `nodes` with `formatsRef` instead: each node's `format` and `producer` say what produced its output — an `attested` format's agent (`agentName`/`agentVersion`, the catalogue's), a `custom` shape run on the catalogue's generic agent and engine-validated (`validation`), a `rendered` node's own render, a `computed` node's `op` — and `formatHash` pins the exact format file; `reads` is the graph. The row's `agentOutputHash` is what the agent returned and `outputHash` what the node produced after its macros composed (hash-definitions.md § 4, definition 6); `appended[]` and `excluded[]` say what was placed and what was withheld. At storage 8 read a row with `kind` as a flow node: it ran no agent; its `body` and `ret` say which nodes it stood for, and an `if`/`case` row's `branch` says which it chose — `none` is the row to read when a deliverable was skipped for *source node.<id> took no branch*, and the body nodes of its untaken branch are the ones with no `nodeOutputs` entry. A `for` row's hashes are its composition's (the 25 aggregator's shape); the deliverable's `composedHash` is over the text its `sources` composed, which `documentHash` then covers with the macros appended.

Two records with the same `workflowPackage`, `catalogRef`, `effectiveInputHash` (same version) ran the same clinical input through the same prompts and agents. Whether they produced the same deliverable is what `workflowOutputHash` says.

## 6. Storage 12 (specVersion 31, preview)

*This section is the contract for the record a specVersion 31 job writes. Storage 12 is in `recordStorageVersions` in `provenance-versions.json`, and the definitions of [hash-definitions.md § 7](hash-definitions.md) are in theirs (its `preview` object now lists none). Nothing in sections 1–5 changes, and nothing the engine at specVersion 30 reads changes.*

Names are written in the record's JSON form (camelCase, as this document writes them everywhere). The record is **keyed with roots**, **kept as rows**, and **sealed into one document** whose hash is on its header. Each member below is given with its type and its null rule: *never* means the member is always written and never `null`; *allowed* means `null` is a value the engine writes; *null below 31* means a record of storage 2–11 has no such member and a reader reads it as `null`. **Every member is written** by a storage 12 record, even where its value is `null` or empty.

### 6.1 Storage 12

**Storage 12 is storage 11 plus additions, except that keys are written with their roots.**

- **A 31 job is stamped `schemaVersion` 12 from its creation,** on every path, as a 30 job is stamped 11.
- **Storage 2–11 records read as before; nothing is converted.** Jobs that ran before 31 carry no `resolveHash` or `lockHash`.
- **Everything storage 11 holds keeps its meaning:** paths for item keys, `loopInstances`, `while` rows with `passes` and `stopped`, the not-run state, item progress per loop, the 120-character item name. The `let` row of storage 11 is the `computed` row at 12, with `producer: computed` as before. At 12 **every row records the node's `producer`** (§ 6.4).
- **The record holds hashes, ids, counts, reasons and names, never element values,** with the exceptions storage 11 made (an item name, now only when it comes from package text) and the ones this section adds: run facts and the outputs of run spots that read raw `run.*` facts (§ 6.8), and printed conditions (§ 6.5), which are package text.

#### 6.1.1 Where the record is stored and sealed

At storage 11 the record lives in the job's Durable entity state. **At 12 it moves:**

- **Each record row is one table row,** written once when the row finishes and never rewritten. The partition key is the job id; the row key is the rooted row key (§ 6.2.1) escaped for Azure Tables, with the true key kept as a property (`key`). Node, check, call, deliverable and decision rows are all stored this way; sub-rows (§ 6.2.3) stay inside their row.
- **Retained text is never in a row.** Every text § 6.11's right-hand column names lives in the job's text blobs, beside the record. A row member that would hold such a text holds `null` and its hash instead (`itemName` with `itemNameHash`, § 6.4; a run spot's `output`, § 6.8.2). So the sweep deletes blobs and never rewrites a row, and `recordHash` can be proved for the record's whole life.
- **Where each thing is stored.** Rows are in the table `ConsultGenerationRecordRows`: partition key the job id, row key the escaped row key, and the properties `key`, `section` (`node`, `check`, `deliverable`, `delivery` or `decision`), `row` (the row's canonical JSON, continued in `row1`, `row2`… past 30,000 characters) and `hash`. Retained text is in the blobs `{appUserId}/{jobId}/text/{sha256 hex of the key}.{part}.json` in the account's outputs container, `part` being `produced` (written by the activity that made the text) or `settled` (written with the row). The canonical record document is the blob `{appUserId}/{jobId}/record.json` in the same container, which the sweep never deletes.
- **A row write is insert-if-absent,** keyed by job and rooted key: an identical second write (a Durable replay) is a no-op; a differing one is refused and recorded as an engine fault.
- **A job that has finished producing and has deliveries to make is `delivering`,** shown as *"Delivering…"*, between producing and its terminal state. The document is viewable throughout. Each delivery attempt is a row in the same record, keyed `delivery:<deliverable>/<destination>` (§ 6.10), so nothing is recorded on a deliverable's row after the job completes.
- **The record is sealed when delivery ends,** not before. At every terminal state (completed, failed, cancelled or timed out), **a canonical record document** is assembled from the rows into a blob: the job header (§ 6.3), noting the end state, and every row, in key order, as RFC 8785 JSON. It is what History's download and the export serve, and **one hash over the whole record** (`recordHash`) is taken over its bytes and written on the header ([hash-definitions.md § 7](hash-definitions.md)).
- **The Durable entity keeps only the job header and progress** (counts, the current step), never row contents. **Events carry keys, not row contents:** a browser following a job fetches a row by its key once the event says it finished.
- **Rows don't record a build.** Every deploy is preceded by a drain, so no job spans two builds; the header's `engineCommit` and `engineRelease` hold for every row.
- **Sealing is one idempotent operation,** reached whichever way a job ends (its orchestration's last step, a cancel, the retention sweep before it drops text, or the first read of a terminal job that has no `recordHash`); sealing twice gives the same document and the same hash, and the first hash written is the one kept.
- **A row key too long or holding a character a table refuses is kept whole as the `key` property;** two different keys never share a stored row key.

#### 6.1.2 The canonical record document

The sealed record is one JSON document, written as RFC 8785 canonical JSON in UTF-8 without a byte order mark. It holds the header (§ 6.3) as its first members, then four more:

| Member | Type | Meaning |
|---|---|---|
| `decisions` | array of decision | every decision row (§ 6.5), in ordinal order of its `id` |
| `nodeOutputs` | object | every node row (§ 6.4), keyed by its row key (§ 6.2.1) |
| `checks` | object | every check row (§ 6.6), keyed by its check row key |
| `deliverables` | array of deliverable row | every deliverable row (§ 6.10), in ordinal order of its `key`, each with one more member, `deliveries`: the delivery rows of that deliverable (§ 6.10), in ordinal order of their `key`; `[]` for none |

The document **leaves out** what changes after the end of the job, so it can be hashed once: `recordHash` itself, `textDroppedAtUtc`, and History's event log (`history`); and it never holds retained text (§ 6.11). The header notes the end state: `status` (`Completed`, `Failed` or `Cancelled`), `completedAtUtc` and `error`.

**`recordHash`** is `sha256:` and the lowercase hex of the SHA-256 over the document's UTF-8 bytes ([hash-definitions.md § 7](hash-definitions.md)). It is written once on the job header and never changes, before or after the text drop, since the document holds no retained text. Rows stored twice with the same bytes are one row. A second, different row under a key already stored is refused: the first row stays, the job fails as an engine fault, and its record is sealed with the first row. **Once a job is terminal its header never changes,** so a canonical document assembled again from the rows (when its blob is gone) hashes to the same `recordHash`.

### 6.2 Keys

#### 6.2.1 Every key with its root

Wherever storage 11 names a node by its bare id, storage 12 names it by its **rooted key**: the root (`node`, `check`, `deliverable`), then the ids of its enclosing flow folders and its own, joined by `.`. The same keys are used in `resolve.json`, test files and History links.

```
node.plan                                     a top-level node
node.sections.paragraphs.draft_paragraph      a node two loops down
node.hpi_section.standard_draft               a node inside a function, through its call node
node.standards.section.standard_draft         a call node inside a loop, then the function's node
check.part_coverage.coverage                  a check inside a check loop
deliverable.emr.note                          deliverables/emr/note.md
```

**A row key** is the rooted key, then `:` and the ids of the items the instance sits in, from the outermost loop inward, joined by `/`; and `#<n>` for a pass of a `while`, written where the `while` sits in that path: `node.sections.paragraphs.draft_paragraph:2/1`, `node.refine.judge#3` (the third pass of `refine`), `node.refine.sections#2:3` (item 3 of the second pass), `node.standards.section.standard_draft:3`, `check.part_coverage.coverage:2`. `.` separates scopes, `/` separates item ids, `:` separates the key from the path and `#` marks a pass; **no id or item id contains any of the four,** and item paths never contain `:` or `#`.

**Item ids are 1-based everywhere a person sees them:** a loop's items by position, array inputs included (an array input's first element is item `1`, as the other loops' items always were).

**Function calls:** inner rows are keyed through the call node's rooted key, never the function's name. The function's name is on the call's row (§ 6.7). Two calls to the same function get different keys from their call nodes.

**What moves to rooted keys:**

- `nodeOutputs` keys and each row's `nodeId`;
- block ids, `skippedBlocks`, `blocks`;
- item-step and block events, `itemProgress`, `collections`;
- the concept source, `nodes` (the descriptor rows), `loopInstances`, `unresolvedLoops`;
- deliverable ids, which are paths like node ids (`deliverables/emr/note.md` is `deliverable.emr.note`), so moving a deliverable changes its key;
- the run diagram's Mermaid ids (with `.` replaced by `__`), the rail, History and Editor links.

#### 6.2.2 Separate sections, separate roots

**Checks are kept in their own section** (§ 6.6), and **deliverables in their own list** (§ 6.10). Since every key carries its root, a node, a check and a deliverable may share an id and their keys never collide.

#### 6.2.3 Sub-row ids

Some rows have sub-rows that live **inside** their row, not in `nodeOutputs`. Each has an id for History's links, the lineage view and test expectations, formed as `<row key>/<sub kind>:<n or id>`. A sub-row id is never parsed as a row key; a segment holding `:` is always a sub-row, since item paths never contain `:`.

| Sub-row | Id |
|---|---|
| a renderer use | `<row key>/render:<n>`, `n` its 1-based number among the renderer uses of the whole entry, counted across every unit its text could place (the prompt, its parts, its snippets and macros), placed or not, so the ids of one row may have gaps: `node.identify_problem/render:1`, `node.sections.paragraphs.draft_paragraph:2/1/render:1` |
| a macro row | `<row key>/macro:<macro id>`: `node.assessment/macro:letrozole_prescription_text` |
| a run spot | `<row key>/spot:<n>`, `n` its 1-based order of filling |
| a decision | `<owner key>/if:<site>` (§ 6.5.2): `node.standards.assessment:7/if:macro.letrozole_prescription_text` |

**A renderer use or a run spot inside a template `for` repeats per iteration.** Each sub-row then carries `pass`, an array of integers or `null`: one number per enclosing template loop, 1-based, as a substitution's (§ 6.10). `render:<n>`'s `<n>` stays the use's number in the entry, and a run spot's id is `<row key>/spot:<n>` with `<n>` the 1-based order in which the spots were filled, its `site` staying the body's site number. An id and its `pass` name one sub-row.

### 6.3 The job header

New members at the job level, all **write-once at job start** except `recordHash`, beside the package name and version, and shown in History's job header:

| Member | Type | Null | Meaning |
|---|---|---|---|
| `resolveHash` | string (`sha256:…`) | null below 31 | the SHA-256 of the canonical `resolve.json` bytes the job ran |
| `lockHash` | string (`sha256:…`) | null below 31 | the SHA-256 of the canonical `lock.json` bytes |
| `versionsRan` | object | null below 31 | **the exact versions that actually ran,** which can differ from the lock within its range. It is `lock.json`'s **nested shape minus `documentVersion`, `package` and `resolve`** (the record already holds their hashes), so the two compare member by member: `{ resolver: { packageFormat, dialect }, libraries, evaluator, operations, builtins, culture, runtime: { dotnet, unicode }, catalogues: { agents, formats, outputContracts } }`. `libraries` holds `Scriban`, `Markdig`, `Corvus.Text.Json.JsonLogic` and `Corvus.JsonSchema`; `operations` those the package uses; `culture` is `"invariant"`; `runtime` the .NET runtime and its Unicode version; `catalogues` the three catalogue versions the job ran, `outputContracts` `null` when the package uses none; each as `lock.json` defines it |
| `recordHash` | string (`sha256:…`) | allowed | the hash of the canonical record document, sealed when delivery ends (§ 6.1.1); `null` until then, and below 31 |
| `runFacts` | object | null below 31 | the raw value of each run fact the package reads, once per run (§ 6.8.1); `{}` when it reads none |
| `limits` | object `{ maxAgentCalls, capacityWaitMinutes, serviceAttempts, jobMinutes, deliveryMinutes, deliveryAttempts, loopItems, jobAgentCalls, jobInstances, renderSteps }`, each an integer | null below 31 | every engine limit in force at job start, recorded once: the per-job ceiling on agent calls in flight (`maxAgentCalls`), the minutes a node may wait on 429s in all (`capacityWaitMinutes`), the attempts allowed for another service failure (`serviceAttempts`), the minutes a job may run from orchestration start (`jobMinutes`), the minutes delivery may take (`deliveryMinutes`) and the attempts each destination gets (`deliveryAttempts`), and the total-work limits: items per loop instance (`loopItems`), agent calls per job (`jobAgentCalls`), the instances one job may open (`jobInstances`: a node, check or deliverable instance, a loop item, a pass or a call) and steps per render (`renderSteps`) |
| `startedAtUtc` | string | never | when the job's orchestration started; the job limit is timed from here, not from creation or scheduling, so time queued or waiting behind a drain doesn't count |
| `signatureBlockId` | string | allowed | the profile signature block the job used, by **id**, never its text; `null` when the package doesn't read `profile.signature` |
| `signatureChosen` | `"default"` or `"job"` | allowed | whether the block was the account's chosen block (`ChosenId`) or picked on the Create page for this job; `null` with `signatureBlockId` |
| `decisions` | array of decision | never | every condition decision of the job (§ 6.5); `[]` for none. Each decision is stored as its own table row and gathered here in the canonical record document (§ 6.1.1) |

**`versionsRan`'s members** are `resolver` (`packageFormat` and `dialect`, the resolver's versions), `libraries` (library name to version), `evaluator`, `operations` and `builtins` (name to version), `culture`, `runtime` (`dotnet` and `unicode`) and `catalogues` (`agents`, `formats` and `outputContracts`). The keys of `libraries`, `operations` and `builtins` are names, not members.

**The header's own members** (written by every 31 job, in the canonical record document and on History's job header; a member with no value is `null`, never absent):

| Member | Type | Null | Meaning |
|---|---|---|---|
| `schemaVersion` | integer | never | `12` |
| `jobId` | string | never | the job's id |
| `status` | string | never | the job's state word; in a sealed record `Completed`, `Failed` or `Cancelled` |
| `error` | string | allowed | the sentence a failed job ended with, never an exception's message; `null` otherwise |
| `createdAtUtc`, `completedAtUtc` | string | `completedAtUtc` allowed | the job's clocks, as round-trip UTC text; `completedAtUtc` is `null` until the job ends |
| `effectiveInputHash` | string (`sha256:…`) | allowed | the hash of the job's inputs as storage 11 defines it, at `effectiveInputHashVersion` |
| `effectiveInputHashVersion` | integer | allowed | `7` at 31 ([hash-definitions.md § 7](hash-definitions.md)) |
| `inputs` | array of input | never | each input, by `id` in ordinal order (§ 6.3.1); `[]` for none |
| `tokens` | object `{ input: integer, output: integer, total: integer }` | allowed | the job's token totals: `input`, `output` and `total`, each the sum of its agent rows' `tokens` member of that name (§ 6.4); `null` when the job made no model call |

**Unchanged and still recorded:** `packageSpecVersion` (31), `workflowPackage`, `packageFormatRef`, `provenanceRef`, `formatsRef`, `catalogRef`, `engineCommit`, `engineRelease`, `apiHost`, the terminology snapshot (`terminology`; `null` at 31, since a 31 job's start reads no terminology server, and written all the same). `formatsRef` and the agents catalogue version now also appear in `lockHash`'s document; the header keeps them for readers of older records.

**Retired at 12** (never written by a 31 job; older records are read exactly as before): `macroChoices` and `excludedMacros`, since per-run macro choices are boolean inputs at 31 and their effect is recorded as decisions (§ 6.5), and `classifications`, since every classifier is an ordinary agent node with its own row.

#### 6.3.1 Inputs: extraction versions and lineage

Each **document-filled input**, and each document element of a mixed array, records beside its hash and origin:

| Member (on the input origin) | Type | Null | Meaning |
|---|---|---|---|
| `converter` | object `{ name: string, version: string }` | allowed | the document-to-Markdown converter and its version; `null` where the step wasn't used |
| `parser` | object `{ name: string, version: string }` | allowed | the parsing library and its version (PdfPig, DocumentFormat.OpenXml, …); `null` where the step wasn't used |
| `ocr` | object `{ service: string, model: string }` | allowed | the OCR service and model version, when OCR ran; `null` when it didn't |

An input in the header is `{ id, origin, hash }`: its `id`, its `origin` (below) and the hash of its value as `effectiveInputHash` takes it, never the value. An input a document filled adds the members above and `kind`, `extractor`, `pageCount`, `fileSha256` and `textSha256`; an input of several elements lists them, in order, as `elements`, each with its own `origin` and, for a document, those members. In an `ocr` object, `service` and `model` are the OCR service and its model. `extractor` (the extraction's name and version, as storage 11 writes it) stays, for readers of older records. A later milestone builds on them: [#1438](https://github.com/Consultologist/Consultologist-Blazor/issues/1438).

**An input element from a previous run's deliverable** starts out **model-derived**, and its origin links to the job it came from. Typed text and uploaded documents start clean.

**Input elements record their `origin`** (`typed`, `document`, `previous-run`, `transcript`), never a `producer`, which is a node's. The engine always knows the origin, so `null` is never written.

### 6.4 Node rows

A production node instance's row keeps storage 11's members (`label`, `status`, `inputHash`, `outputHash`, `hashVersion`, `tokens`, and the clock members `startedAtUtc`, `completedAtUtc` and `durationMs`), some under their storage 12 names: storage 11's `validation` is `invalid`, and its `reason` and failure members are `stateReason`. It gains the members below.

| Member | Type | Null | Meaning |
|---|---|---|---|
| `nodeId` | string | never | now the **rooted key** |
| `itemId` | string | allowed | the id of the innermost loop item the row sits in (`1` of `node.a.b:2/1`); `null` outside every item |
| `kind` | string | never | `agent`, `rendered`, `computed`, `for`, `while`, `if`, `case` or `call` |
| `producer` | string | never | the node's `producer` as written and checked: `generated` on agent rows, `computed` on every other |
| `formatHash` | string | allowed | the **full** hash of the node's resolved format (`resolve.json`'s `formatHashes`); `null` for flow kinds. With `agent`, it lets History say "the same type, served by a different agent" or the reverse |
| `typeHash` | string | allowed | the format's **type** hash (`resolve.json`'s `typeHashes`); `null` with `formatHash` |
| `sentFormatHash` | string | allowed | on agent rows, the hash of the **stripped** format, taken **before** it is wrapped: `title`, `$id` and the keywords strict mode rejects removed, by the attested agent definition's list, the copy prepared by the steps of [hash-definitions.md § 7.7](hash-definitions.md). The envelope is identified by the engine version, not by this hash, and an object root is sent unwrapped; only a non-object root is wrapped as `{ value: … }`. `null` on other rows |
| `notSent` | array of string | never | on agent rows, the removed keywords as JSON pointers into the format (`/properties/onset/format`); `[]` for none. History shows *"Not sent to the model: …"*, and the reply is still validated against the full format |
| `agent` | object | allowed | on agent rows only (§ 6.4.1); `null` otherwise |
| `units` | array of `{ site: string, hash: string, sent: boolean }` | never | on agent rows, each part and snippet the prompt placed, by its site and the hash of its rendered text; `[]` for none. `sent` is `false` for a snippet substituted into a body that is not sent to the model (a macro's), which History shows as *"substituted, not sent"*. The record keeps the whole of what an agent turn finishes with: `notSent`, `sentFormatHash`, `units`, the macro rows and the run spots |
| `tokens` | object `{ input: integer, output: integer, total: integer }` | allowed | on agent rows, the tokens the node's calls spent, summed over its attempts; `null` on other rows |
| `itemName` | string | allowed | the item's name from the loop's `itemLabel`, capped at 120 characters (storage 11's rule, renamed from `labelField`); **in the row only when the label comes from package text** (a snippet folder's header), and then kept for the life of the record. Otherwise it is `null` and the name is in the retained text, deleted 7 days after completion (§ 6.11); a row never holds retained text (§ 6.1.1). `null` on rows outside a loop. Reasons name items by position (*Sections 3*), never by `itemName` |
| `itemNameHash` | string | allowed | the hash of the item's name when `itemName` is `null` for the reason above; `null` when `itemName` holds the name or the row is outside a loop |
| `positionName` | boolean | never | `true` when `itemName` (or its hash) is the item's position (*Section 3*) rather than a name from the loop's label; `false` outside a loop |
| `function` | string | allowed | the id of the function the row runs in, `null` outside every function; on a call row, the function it calls (§ 6.7) |
| `depth` | integer | never | the nesting depth of the function calls the row runs in: `0` outside every function (§ 6.7) |
| `runDependent` | boolean | never | `true` when the row's value depends on `run.*`, transitively: the node's `runDependent` as written and checked |
| `modelDerived` | boolean | never | `true` when the row's value is computed from a model's output, directly or through other values. Every agent row is `true`. History, the diagram and the Editor show it (*"computed from model text: node.draft"*). The node's `modelDerived` as written and checked; requiring either flag in a read is later work, [#1478](https://github.com/Consultologist/Consultologist-Blazor/issues/1478) |
| `profileCarrying` | boolean | never | `true` when the row's value carries text a profile-reading macro body was substituted into, directly or through other values. The node's `profileCarrying` as written and checked |
| `runNeutralHash` | string | allowed | for a body with run spots, the hash of the body rendered with each run spot left as its marker; `null` when the body has none, so `inputHash` alone is the hash (§ 6.8.2) |
| `runSpots` | array of run spot | never | § 6.8.2; `[]` for none |
| `renders` | array of renderer sub-row | never | § 6.4.2; `[]` for none |
| `macros` | array of macro row | never | § 6.4.3; `[]` for none; agent rows only |
| `invalid` | object | allowed | the node's `onInvalid` outcome when a reply failed validation or the macro marker check: `{ reason: string, action: "retry" \| "fail", attempts: integer }`, where `reason` names what failed, for example `macro letrozole_prescription_text: missing`. `null` when the reply was valid. A retry message never quotes the reply; it names only what was wrong |
| `retries` | array of `{ atUtc: string, waitMs: integer, kind: "capacity" \| "service", error: string \| null }` | never | each retry the call needed, with its back-off: `kind` is `"capacity"` for a 429 and `"service"` for another service failure; `error` is that failure's kind (`"timeout"`, `"5xx"`, `"connection"`), never its content, and `null` for capacity. `[]` for none |
| `profileReads` | array of `{ field: string, hash: string }` | never | each `profile.*` read by a macro body placed in this node's prompt, by hash (§ 6.9); `[]` for none |
| `stateReason` | string | allowed | the sentence for a row that didn't complete: *skipped: …* (§ 6.5), *not run: beyond max <n>*, or a failure's reason (a `matches` text over 1 MiB; the model service's limits or a total-work limit); for a row still running when the job limit passed, `cancelled` with *cancelled: the job didn't finish within <n> minutes*; `null` when completed |
| `startedAtUtc` | string | allowed | storage 11's clock: when the instance started, as round-trip UTC text from the orchestration's replay-safe clock: an agent or render call sent, a computed node evaluated, a flow node first stepped, a loop item's or a pass's frame opened. `null` for a row that never started (skipped, not run, or refused by a limit before it started) |
| `completedAtUtc` | string | allowed | when the row settled, from the same clock; `null` with `startedAtUtc` |
| `durationMs` | integer | allowed | the whole milliseconds from `startedAtUtc` to `completedAtUtc`; `null` with them |

**`cancelled`** is a row state at 12: an activity still running when the job limit passes is recorded `cancelled`, and its late result, if one arrives, is ignored and never written.

A node that didn't complete reads `null` for `.value` and `.content`; `.state` says why.

For a `computed` row, `inputHash` covers the expression and the values it read. For a run-dependent `computed` value, the run-neutral hash covers its expression and its other reads, **not its value**. A `computed` row reading a model-derived value is `modelDerived: true`, still `reproducible`, and its producer is `computed`; its format is its operand's shape, unchanged.

#### 6.4.1 The agent: definition and binding

Agent rows **name their attested agent definition** (id and version) **and the binding that chose it**:

| Member of `agent` | Type | Null | Meaning |
|---|---|---|---|
| `name` | string | never | the attested agent definition's id in the agents catalogue (`consult-prose`) |
| `version` | integer | never | its version (`4`) |
| `binding` | object `{ format: string, producer: string, via: string }` | never | the format and producer whose binding chose the agent, and the route (`via`): `"format"` (a registry or catalogue format's binding) or `"custom"` (a package's own format, bound to the custom-format agent); `"producer"`, an agent chosen by producer alone, is reserved at 31 and refused until later work, [#1479](https://github.com/Consultologist/Consultologist-Blazor/issues/1479) (`resolve.json`'s `bindings`) |

The agents catalogue's version is in `lock.json`; the record doesn't repeat it per row. **The fuller recording** (each value's model, the settings read from the attested definition, tool calls) is later work: [#1439](https://github.com/Consultologist/Consultologist-Blazor/issues/1439) and [#1445](https://github.com/Consultologist/Consultologist-Blazor/issues/1445).

#### 6.4.2 Renderer sub-rows

**One sub-row per pipe step,** in the order the steps appear in the body, per instance (per item and pass), inside the consuming row's `renders`. A chain (`{{ node.extract.value | renderer.concept_list | renderer.bullets }}`) gives one sub-row per step (`…/render:1`, `…/render:2`). It's never a node row and never scheduled:

| Member | Type | Null | Meaning |
|---|---|---|---|
| `id` | string | never | `<row key>/render:<n>` (§ 6.2.3) |
| `renderer` | string | never | `renderer.<id>` |
| `templateHash` | string | never | the renderer's `bodyHash` in `resolve.json`, or for a built-in renderer its template's hash at the locked version |
| `source` | string | never | the path piped in (`node.extract.value`), or the previous step's sub-row id in a chain |
| `inputHash` | string | never | the hash of the piped value (canonical JSON for data, UTF-8 for text) |
| `pass` | array of integer | allowed | one number per enclosing template loop, 1-based; `null` when the use is in no template loop (§ 6.2.3) |
| `inputSize` | string | allowed | a size summary from the input's format, for example `"14 concepts"`; `null` when none applies |
| `outputHash` | string | never | the hash of the rendered text |
| `outputLength` | integer | never | the rendered text's length **in runes** |
| `runDependent` | boolean | never | `true` when the piped value is a `run.*` fact or run-dependent; the run spot then covers the whole pipeline |

The input value and rendered text are produced text, under the 7-day retention (§ 6.11).

#### 6.4.3 Macro rows

**A macro row per macro per node instance,** for every macro the node's prompt places, its parts' text included:

| Member | Type | Null | Meaning |
|---|---|---|---|
| `id` | string | never | `<row key>/macro:<macro id>` (§ 6.2.3) |
| `macro` | string | never | `macro.<id>` |
| `offered` | boolean | never | whether the macro's `if` (and its folder's) held, and, when a part's text places it, the part's `if` too, so its instruction was added to the prompt |
| `decisions` | array of string | never | the decision ids (§ 6.5) its offer depended on: the macro's `if`, its folder's, and the placing part's, when they're not `null`; `[]` when all are `null` |
| `classifier` | string | allowed | the row key of the classifier node its `if` read, linking to that row, where History shows the `judgement`'s `reason` beside its `answer`; **`null` unless the `if` reads exactly one node.** Several classifiers for one value is later work, [#1416](https://github.com/Consultologist/Consultologist-Blazor/issues/1416) |
| `placed` | boolean | never | `true` when the marker was found **exactly once**, in the form its instruction asked for; `false` when not offered, or when the check failed |
| `form` | `"block"` or `"inline"` | allowed | the form the instruction asked for; `null` when not offered |
| `contentHash` | string | allowed | the hash of the macro's rendered body as substituted, taken after the body's one final line ending is dropped; `null` when not offered |
| `runNeutralHash` | string | allowed | the hash of the body with each of its run spots left as its `{{run:<n>}}` marker; `null` when the body reads no `run.*`, so `contentHash` alone is the hash. A macro body's `run.*` is filled in directly, with no spot in the placing body, so the macro row carries its own (§ 6.8.2) |
| `runSpots` | array of run spot | never | the body's run spots (§ 6.8.2), each `<macro row id>/spot:<n>`; `[]` for none |

If the marker was missing, repeated or altered, the node's `onInvalid` outcome is on the node's row (`invalid`), not here. Profile reads in macro bodies are the node's `profileReads`. **The same macro used twice in one template** is later work: [#1457](https://github.com/Consultologist/Consultologist-Blazor/issues/1457).

#### 6.4.4 Loop, while and pass rows

A flow row keeps every member of § 6.4 (a loop's `formatHash`, `agent` and the rest are `null`, its lists `[]`) and adds the members of its kind:

| Row | Member | Type | Null | Meaning |
|---|---|---|---|---|
| `for` | `parallel` | boolean | never | the loop's `parallel` as written |
| `for` | `maxParallel` | integer | allowed | its `maxParallel` as written |
| `for` | `itemLabel` | string | allowed | the name of the field its items' names come from (the label field, not a name) |
| `for` | `count` | integer | allowed | the items its source gave; `null` when the source was never read |
| `for` | `stopped` | string | allowed | `until` (its `until` held), `bound` (items beyond `max` were not run) or `end`; `null` while it runs |
| `while` | `max`, `checkFirst` | integer, boolean | `max` allowed | its `max` and `checkFirst` as written |
| `while` | `passes` | integer | never | the passes that ran |
| `while` | `stopped` | string | allowed | `check` (the check stopped holding), `until` or `bound` (`max` passes ran with the check still holding) |
| `while` | `pass` | integer | allowed | on a **pass row** (below), the pass's number, 1-based; `null` on the loop's own row |
| `for`, `while` | `reason` | string | allowed | the sentence for a loop that did not run its items or passes in full: a `null` source, a stop at its `until`, items beyond `max`, or a `while` that stopped at its bound (*stopped at its bound of 3; the check never stopped holding*); `null` otherwise |
| `call` | `function`, `arguments`, `depth` | | | § 6.7 |

Each pass of a `while` is a row of its own, kind `while`, keyed `<while key>#<n>` (§ 6.2.1), whose state and `outputHash` are its `ret`'s; it carries `pass`.

### 6.5 Condition decisions

#### 6.5.1 The decision

**One job-level `decisions` list:** a decision for every condition the engine evaluates, holding its site, the printed condition, its result, the hashes of what it read, whether it's run-dependent, and an `expressionHash` of its canonical JSON Logic. Rows link to their decisions by id, and a decision can concern something that never got a row (a skipped node).

| Member | Type | Null | Meaning |
|---|---|---|---|
| `id` | string | never | `<owner key>/if:<site>` (§ 6.5.2) |
| `owner` | string | never | the row key, check row key or deliverable key the decision concerns |
| `site` | string | never | what was decided (§ 6.5.2) |
| `condition` | string | never | the condition **as printed** by the one printer: `input.kind.value = "table"`. A condition comparing a `.title` prints both the raw value and the title. Package text, kept for the life of the record |
| `expressionHash` | string | never | the hash of the canonical JSON Logic, which the printed text came from |
| `result` | boolean or string | never | `true` or `false`; for a `case`, the arm taken: **its 1-based position as text** (`"2"`) or `"else"`, since a `case`'s arms have no ids at 31; the `condition` is then the printed subject |
| `reads` | array of `{ path: string, hash: string }` | never | each value its own rule reads, as its `path` (the rule's variable, as `resolve.json` writes it) and the canonical `hash` of the value read (a `null` hashes as `null`); never the value itself |
| `runDependent` | boolean | never | `true` when it read `run.*` or a run-dependent value |
| `modelDerived` | boolean | never | `true` when it read a model-derived value. A decision's flags describe the decision only: they don't pass to what it chooses |
| `decidedAtUtc` | string | never | when the engine evaluated it, from the orchestration's replay-safe clock |

**How a decision's flags are found.** The flags follow earlier-pass reads. `runDependent` is `true` when a read is `run.*` or names an entry whose `runDependent` is `true`, and `modelDerived` is `true` likewise from the entries' `modelDerived`. A read through `item`, `pass` or `param` takes the flags of what it stands for: the loop's source, the body node, the call's argument reads. A read the runner cannot trace is `modelDerived: true` and `runDependent: true`, so the record never marks model output as not model-derived.

**Reasons read as sentences** built from the printed condition: *skipped: input.kind.value = "table" is false*. A row skipped by a decision has this sentence as its `stateReason`, and the decision's id is how History links the two.

#### 6.5.2 Which decisions, and their sites

Every condition the engine evaluates is recorded, per instance:

| Condition | `site` | Owner |
|---|---|---|
| a node's, check's, branch's or loop's header `if` | `self` | its row key |
| a `case` | `case` (result: the arm's position, or `"else"`) | its row key |
| a `while`'s condition, before or after pass *n* | `pass.<n>` | the `while`'s row key |
| a `for`'s `until`, after item *i* | `until.<i>` | the loop's row key |
| a macro's `if` | `macro.<id>` | the placing node's row key |
| a macro folder's `if` (both must hold; the record shows which was false) | `macro-folder.<folder id>` | the placing node's row key |
| a part's `if` | `part.<id>` | the node's row key |
| a snippet's header `if` | `snippet.<id>` | the placing row key |
| a deliverable's header `if` | `self` | its deliverable key (`deliverable.emr.note`) |

Snippet folder items have no `if`, so there's no per-item site. A body `if` in a template tests recorded facts only (loop position, `state`, whether a check passed), which are already rows; it makes no decision.

### 6.6 Check rows

**Checks have their own section,** `checks`, apart from `nodeOutputs`, keyed by check row key (§ 6.2.2), in the order the job runs: Inputs, Nodes, Checks, Deliverables. The record holds a check's result once; a deliverable refers to it.

| Member | Type | Null | Meaning |
|---|---|---|---|
| `key` | string | never | `check.coverage`, `check.part_coverage.coverage:2` |
| `kind` | string | never | `computed`, or `for` for a check loop's own row |
| `label` | string | never | the check's label |
| `status` | string | never | `Completed`, `Skipped`, `Failed`, as node rows |
| `itemName` | string | allowed | in a check loop, the item's name from the loop's `itemLabel`, capped at 120 |
| `alignedWith` | string | allowed | in a check loop, the row key of the production item with the same id (`node.sections:2` for `check.part_coverage.coverage:2`); `null` at the top level |
| `checked` | object `{ ref: string, hash: string }` | allowed | what it ran on, as its `ref` and that output's `hash`: the one `deliverable.*` the check reads, with its composed hash (`deliverable.consult`); else the one node it reads, with its output hash (`node.plan`); else `null` |
| `reads` | array of `{ path: string, hash: string }` | never | every other read, by hash |
| `inputHash`, `outputHash` | string | allowed | as on a `computed` row |
| `producer` | string | never | `computed`, as on node rows |
| `modelDerived`, `runDependent`, `profileCarrying` | boolean | never | as on node rows |
| `itemNameHash` | string | allowed | as on node rows: the hash of `itemName` when the name is not kept (§ 6.4) |
| `runNeutralHash` | string | allowed | as on computed node rows (§ 6.8.2) |
| `stateReason` | string | allowed | the sentence for a check that didn't complete: *skipped: …* or a failure's reason; `null` when completed |
| `pass` | boolean | allowed | the `check_result`'s verdict, under the same name; kept for the life of the record, as today's `checkPassed`; `null` while running or when skipped. `passed` only ever means a count |
| `failWith` | string | allowed | the `check_result`'s `message`, the operation's literal `failWith` sentence, when it failed (package text, kept); `null` when it passed |
| `effect` | string | allowed | what it caused, **written on its one row**: for a check that gates nothing and is read, `read by <ref>` (its first reader in key order); `null` when nothing reads it. For a gate, its row is recorded when the last deliverable it gates settles, with `released`, `held` or `blocked`, the deliverable's state word; with more than one deliverable, `<word> <deliverable key>` joined by `; ` in key order. A run that ends first records the gate's row with `effect: null` |
| `passed`, `total` | integer | allowed | the `check_result`'s counts (how many held, out of how many), kept for the life of the record; `null` when the check has no result |
| `uncoveredHash`, `untestedHash` | string | allowed | the canonical hash of the `check_result`'s `uncovered` and `untested` lists; `null` when the list is `null` |
| `uncoveredSize`, `untestedSize` | integer | allowed | the number of elements in those lists; `null` with the hash |
| `count` | integer | allowed | on a check loop's own row, its item count; `null` on others |
| `startedAtUtc`, `completedAtUtc`, `durationMs` | string, string, integer | allowed | as on node rows (§ 6.4) |

The `check_result`'s `uncovered` and `untested` lists come from inputs, so they follow the text retention rule: shown while retained, then deleted, with their hash kept for good (§ 6.11). Its `passed` and `total` counts are kept. This holds for every package. Check operations judge only `completed` items and always return a `check_result`.

Check loops are **scheduled per item** and never stop production; a failing item's effect comes only through what reads it.

### 6.7 Call rows

Each `call` instance is a row in `nodeOutputs` (`kind: call`), expanding to its inner rows like a loop item:

| Member | Type | Null | Meaning |
|---|---|---|---|
| `function` | string | never | the function's id; on the call's row, never in the key |
| `arguments` | array of `{ param: string, hash: string }` | never | each argument's hash: the call's input hashes are exactly its arguments' hashes |
| `outputHash` | string | allowed | the result's hash; one per call |
| `depth` | integer | never | the call's nesting depth: `0` for a call outside any function, *d*+1 for one inside a function reached at depth *d*, within `FormatBounds.depth` |

Inner rows are keyed through the call node (§ 6.2.1). A decision made outside and passed in is recorded once, at the caller; the `computed` node inside each call shows the value it received, and is model-derived when the value was.

### 6.8 Run facts and run spots

#### 6.8.1 Run facts

**Recorded once per run, kept permanently, shown in History's "Run facts" section.** `runFacts` holds the raw value of each fact the package reads (`resolve.json`'s `run`):

| Member | Type | Meaning |
|---|---|---|
| `date` | object `{ value: string, timeZone: string }` | the job's start date in the account's time zone (`value`, `"2026-11-16"`) and that zone's IANA name (`timeZone`, `"America/Toronto"`), recorded beside the value |
| `id` | string | the job's id |
| `package` | string | `<name>@<version>`, as `run.package` gives it |
| `engine` | string | the engine's release version, as `run.engine` gives it |

Only the facts read are present. Run facts aren't patient text, so they're outside the 7-day drop.

#### 6.8.2 Run spots and the two hashes

For a body that reads `run.*` (a prompt, a `rendered` node, a deliverable, or a snippet placed in one), the record carries **the sent-text hash** (the main hash, as today), **the run-neutral hash** (the same text with each run spot left as its `{{run:<n>}}` marker), and **each run spot**. A read of a run-dependent value is a run spot too, and a run spot that pipes into renderers covers the whole pipeline.

| Member of a run spot | Type | Null | Meaning |
|---|---|---|---|
| `id` | string | never | `<row key>/spot:<n>` |
| `site` | integer | never | the spot's position in the body (`resolve.json`'s `runSpots`) |
| `pass` | array of integer | allowed | one number per enclosing template loop, 1-based; `null` for a spot in no template loop (§ 6.2.3) |
| `start` | integer | never | where the spot's output begins in the sent text, in runes |
| `length` | integer | never | the output's length, in runes |
| `reads` | string | never | what it reads (`run.date`, or a run-dependent value's path) |
| `valueHash` | string | never | the hash of the value read |
| `output` | string | allowed | the formatted output (`"16 November 2026"`), **in the row only when the spot reads raw `run.*` facts**, and then kept for the life of the record; a spot that is also input- or model-derived (a run-dependent `computed` value that reads an input) has `output` `null`, its text is in the retained text under 7-day retention, and `outputHash` stays |
| `outputHash` | string | never | the output's hash |

- **The sent text is rebuilt exactly** from the run-neutral text and the spot outputs, each put at the position recorded while rendering (`start`, in runes), never found by searching the text, so the main hash stays provable.
- **Runs are compared on the run-neutral hash.** Beside any body whose two hashes differ, History says the difference is due to run facts.
- **A body with no run spots has one hash;** its `runNeutralHash` is `null`.
- **A macro body's `run.*` is filled in directly,** with no spot in the placing body: macro bodies are not among the bodies that carry spots in the body they are placed in. The macro's own row carries its `runNeutralHash` and `runSpots` (§ 6.4.3), so macro rows compare across runs.
- Deliverables carry the same members on their row (§ 6.10).

### 6.9 Profile reads

Each `profile.*` read is **a substitution recorded by hash**, and its text follows the 7-day retention; the record names the **signature block's id**, not its text. Reads happen only in deliverable templates, macro bodies and snippet bodies placed in them, so they appear in a deliverable's `substitutions` (§ 6.10) and a node's `profileReads` (§ 6.4). The header's `signatureBlockId` and `signatureChosen` (§ 6.3) name the block and how it was chosen. **No `ConsultSignatureSnapshot` at 31:** the signature is a profile read, recorded by hash with its block id; its text lives in the deliverable, under text retention.

### 6.10 Deliverable rows

A deliverable's row keeps storage 11's members (its id, state, `composedHash`) and adds the template's provenance:

| Member | Type | Null | Meaning |
|---|---|---|---|
| `key` | string | never | the deliverable key, its path: `deliverable.emr.note` |
| `label` | string | allowed | the deliverable's label |
| `hashVersion` | integer | never | `4`, the version of `composedHash` ([hash-definitions.md § 7](hash-definitions.md)) |
| `units` | array | never | as on node rows (§ 6.4); `[]` for none |
| `profileReads` | array | never | as on node rows (§ 6.4); `[]` for none |
| `templateHash` | string | never | the template's `bodyHash` in `resolve.json`; the text is shown from the pinned version, never copied |
| `format` | string | never | the deliverable's format (`markdown_block`, `plaintext` or an object format; never `markdown_inline`) |
| `state` | string | never | `released`, `held`, `failed`, `skipped` (its header `if`) or `blocked` (its gate check failed or errored) |
| `stateReason` | string | allowed | the sentence: *held: empty*, *skipped: <condition> is false*, *blocked: check '<id>' failed (<detail>)*, *blocked: check '<id>' could not run (<error>)*, *released: check '<id>' didn't apply (its if was false)*; `null` when released through a passing check or none |
| `delivery` | array of delivery row key | never | the delivery rows of a released deliverable, one per destination (below); `[]` for a deliverable that wasn't released. The results are on those rows, not on this one |
| `check` | string | allowed | the check row key that gated it, linking to the check's row; `null` when ungated |
| `sites` | array of `{ site: integer, at: string, expr: string, loop: string \| null }` | never | each expression in the template, in source order: `site` its number, `at` its line and column (`"3:1"`), `expr` its source text and `loop` the template loop it sits in, or `null`. Package text, kept |
| `substitutions` | array of substitution | never | each evaluation: `{ site, pass: integer[] \| null, reads: string, hash: string, start: integer, size: integer, renders: string \| null }`; `pass` holds one number per enclosing template loop. `start` and `size` say where its text sits in the composed text, in runes, `size` `0` for a value that writes nothing (a `null`) |
| `renders` | array of renderer sub-row | never | as on node rows (§ 6.4.2) |
| `runNeutralHash`, `runSpots` | | | as on node rows (§ 6.8.2) |
| `modelDerived`, `runDependent`, `profileCarrying` | boolean | never | as on node rows |
| `startedAtUtc`, `completedAtUtc`, `durationMs` | string, string, integer | allowed | as on node rows (§ 6.4): its render sent, and its outcome decided |

**A delivery row** is written for each destination of a released deliverable, keyed `delivery:<deliverable>/<destination>`, and is the one place a result is recorded:

| Member | Type | Null | Meaning |
|---|---|---|---|
| `key` | string | never | the row's key, as above |
| `deliverable` | string | never | the deliverable key it belongs to; the canonical document gathers it under that deliverable's `deliveries` (§ 6.1.2) |
| `kind` | string | never | the destination's kind |
| `result` | `"sent"`, `"not sent"` or `"failed"` | never | the outcome |
| `reason` | string | allowed | the sentence for a result other than `sent`; `null` for `sent` |
| `atUtc` | string | allowed | when the result was written; `null` until then |
| `attempts` | array of `{ atUtc: string, outcome: string }` | never | each attempt, in order, `outcome` its result word |

The results are written once the job has succeeded: *not sent: EMR isn't set up for this account*, *not sent: the job failed*; `failed` after the attempts ran out or the delivery window closed, each attempt in `attempts`. The canonical record gathers the delivery rows under their deliverable.

**Replay:** substituting the recorded values into the template, in site and pass order, must reproduce `composedHash`. It is checked by position, never by search: the composed text's slice at each substitution (`start`, for `size` runes) hashes to the substitution's `hash`, and substitutions never overlap. A deliverable row shows only a one-line check status; the check's row holds the result.

**A deliverable whose gating check was skipped by its own `if` is released,** and recorded with the reason above; an empty `all_pass`, by contrast, fails. **A `blocked` deliverable is kept:** its row holds `composedHash`, `check`, `stateReason`, `sites` and `substitutions` like any other, its composed text is in the retained text, under 7-day retention with the hashes kept, and it is never delivered (`delivery: []`). **A bundle holds released deliverables only;** History lists what was left out and why.

### 6.11 Retention

| Kept for the life of the record | Deleted 7 days after completion |
|---|---|
| every hash, key, id, status, count, clock and token figure | produced text: replies, prompts as sent, composed deliverables |
| labels, item names whose label comes from package text (capped at 120) | concepts |
| printed conditions, `failWith` sentences (a `check_result`'s `message`), template sites (package text) | input text and held inputs |
| decision results, check verdicts (`pass`), states and reasons | renderer inputs and outputs |
| run facts, and the outputs of run spots that read raw `run.*` facts only | a `check_result`'s `uncovered` and `untested` lists |
| `resolveHash`, `lockHash`, `versionsRan`, `recordHash`, extraction versions | the text behind profile reads, and profile-carrying text |
| the `modelDerived`, `runDependent` and `profileCarrying` flags, the removed-keyword pointers | item names drawn from inputs or model output; run spot outputs that are also input- or model-derived |
| the signature block's id | |

Retention goes by where text came from, not what it says, and holds for every package, medical or not. The sweep (`DropText`) deletes the text blobs that hold what the right-hand column names and stamps `textDroppedAtUtc`, as today; **no row is rewritten** (§ 6.1.1). Every hash stays, so a sub-row or substitution keeps its reference, format, size and hash and says the text was deleted under retention.

**Hashes of short values:** every hash stays, short values' included. A hash of a short value (a name, a credentials line, a yes or no) can be reversed by hashing likely candidates, and this document says so beside the hash definitions ([hash-definitions.md § 7](hash-definitions.md)). Long texts keep their hash for verification as before.

### 6.12 What the record never holds

- **In-package test results.** Tests run at publish, not in jobs; their results are in the publish report.
- **`resolve.json` or `lock.json` themselves.** The record pins their hashes; History fetches the documents from the registry by version and checks them against the hashes.
- **Element values,** apart from the exceptions in § 6.1.
- **The peak concurrency a job reached,** which goes to telemetry only.

### 6.13 Recorded sentences

The record refuses nothing itself; the refusals at start and load belong to the package format. The sentences it **records**, used as written:

- *skipped: <printed condition> is false* (a decision's reason, § 6.5)
- *case '<id>': arm for <value> does nothing* (a `case` whose subject took an explicitly empty branch)
- *not run: beyond max <n>* (an item past a loop's `max`; the loop's `.stopped` is `"bound"`)
- *held: empty* (a deliverable with `whenEmpty: hold`)
- *released: check '<id>' didn't apply (its if was false)* (a deliverable whose gating check was skipped)
- *not sent: <kind> isn't set up for this account* (an unconfigured delivery kind), for example *not sent: EMR isn't set up for this account*
- *not sent: the job failed* (each destination of a released deliverable in a job that failed; nothing is delivered until the job has succeeded)
- *failed: <kind>* (a destination whose delivery was retried and still didn't go, with each attempt on the result; the job stays completed)
- *blocked: check '<id>' failed (<detail>)* and *blocked: check '<id>' could not run (<error>)* (a deliverable whose gate check failed or errored)
- *cancelled: the job didn't finish within <n> minutes* (a row still running at the job limit)
- History's banner, built from the record: *<deliverable label> was blocked: check '<check id>' failed (<detail>).*, for example *Consultation note was blocked: check 'coverage' failed (10 of 12 terms present).*
- History, for a sent format with keywords removed: *Not sent to the model: <pointers>*
- A node's `invalid.reason` for the macro check: *macro <id>: missing*, *macro <id>: repeated*, *macro <id>: altered*; and the failure when `onInvalid` is `fail`: *Node '<row key>' failed: macro '<id>' was <missing | repeated | altered> in the reply.*
- A deliverable failed by `whenEmpty: fail`: *Deliverable '<id>' was empty, and the workflow fails an empty <label>.*
- A node failed by the model service's limits: *The model service stayed busy for <n> minutes.*, or *The model service <timed out | returned an error | couldn't be reached> <n> times in a row.*; and a job past its time limit: *The job didn't finish within <n> minutes.* History adds *Run the workflow again later.*

### 6.14 An example (abridged, fictional)

A `test/general` job at 31, the assessment node in the `standards` loop, with one macro offered and one renderer use. The example is hand-written to show the shape; its hashes are elided, and it is an example, not a recorded job:

```jsonc
{
  "schemaVersion": 12,
  "packageSpecVersion": 31,
  "workflowPackage": "test/general@v2026.12.1",
  "resolveHash": "sha256:9b41…",
  "lockHash": "sha256:07c2…",
  "versionsRan": { "resolver": { "packageFormat": "package-format@v2026.12.1", "dialect": "scriban-dialect@1.0.0" },
                   "libraries": { "Scriban": "7.2.6", "Markdig": "0.41.3",
                                  "Corvus.Text.Json.JsonLogic": "5.8.11", "Corvus.JsonSchema": "4.3.17" },
                   "evaluator": "1.0.0", "operations": { "terms_subset": "1.0.0" },
                   "builtins": { "concept_bullets": "1.0.0", "formats": "1.0.0", "markdown_escape": "1.0.0",
                                 "plain_conversion": "1.0.0", "printer": "1.0.0" },
                   "culture": "invariant",
                   "runtime": { "dotnet": "10.0.3", "unicode": "16.0" },
                   "catalogues": { "agents": "agents@v2026.12.1", "formats": "formats@v2026.12.1",
                                   "outputContracts": null } },
  "runFacts": { "date": { "value": "2026-11-16", "timeZone": "America/Toronto" } },
  "limits": { "maxAgentCalls": 16, "capacityWaitMinutes": 10, "serviceAttempts": 5, "jobMinutes": 30,
              "deliveryMinutes": 15, "deliveryAttempts": 3,
              "loopItems": 200, "jobAgentCalls": 500, "jobInstances": 10000, "renderSteps": 100000 },
  "signatureBlockId": "sig-2", "signatureChosen": "job",
  "decisions": [
    { "id": "node.standards.assessment:7/if:macro.letrozole_prescription_text",
      "owner": "node.standards.assessment:7", "site": "macro.letrozole_prescription_text",
      "condition": "node.standards.prescribes_letrozole.value.answer = true", "expressionHash": "sha256:…",
      "result": true,
      "reads": [ { "path": "node.standards.prescribes_letrozole.value.answer", "hash": "sha256:…" } ],
      "runDependent": false, "modelDerived": true, "decidedAtUtc": "2026-11-16T14:02:11Z" } ],
  "nodeOutputs": {
    "node.standards.assessment:7": {
      "nodeId": "node.standards.assessment", "itemId": "7", "kind": "agent", "producer": "generated",
      "itemName": "Assessment and plan", "itemNameHash": null,
      "status": "Completed", "stateReason": null,
      "inputHash": "sha256:…", "outputHash": "sha256:…", "hashVersion": 7,
      "formatHash": "sha256:…", "typeHash": "sha256:…", "sentFormatHash": "sha256:…", "notSent": [],
      "agent": { "name": "consult-prose", "version": 4,
                 "binding": { "format": "markdown_block", "producer": "generated", "via": "format" } },
      "units": [ { "site": "snippet.clinic_header", "hash": "sha256:…", "sent": true } ],
      "tokens": { "input": 1840, "output": 412, "total": 2252 },
      "runDependent": false, "profileCarrying": false, "modelDerived": true, "runNeutralHash": null, "runSpots": [],
      "renders": [ { "id": "node.standards.assessment:7/render:1", "renderer": "renderer.concept_bullets",
                     "templateHash": "sha256:b81…", "source": "node.extract.value",
                     "inputHash": "sha256:7d0…", "inputSize": "14 concepts",
                     "outputHash": "sha256:3f9…", "outputLength": 612, "runDependent": false } ],
      "macros": [ { "id": "node.standards.assessment:7/macro:letrozole_prescription_text",
                    "macro": "macro.letrozole_prescription_text", "offered": true,
                    "decisions": ["node.standards.assessment:7/if:macro.letrozole_prescription_text"],
                    "classifier": "node.standards.prescribes_letrozole:7", "placed": true, "form": "block",
                    "contentHash": "sha256:…", "runNeutralHash": null, "runSpots": [] } ],
      "invalid": null, "retries": [], "profileReads": []
    }
  },
  "checks": {
    "check.coverage": { "key": "check.coverage", "kind": "computed", "producer": "computed", "label": "Coverage",
                        "status": "Completed", "itemName": null, "alignedWith": null,
                        "checked": { "ref": "deliverable.consult", "hash": "sha256:9a3f…" },
                        "reads": [ { "path": "node.extract_input_terms.value", "hash": "sha256:…" } ],
                        "modelDerived": true, "runDependent": false, "profileCarrying": false,
                        "pass": true, "failWith": null, "effect": "released", "count": null } }
}
```
