# Hash definitions

*Published as part of `provenance@vYYYY.MM.N`; `provenance-versions.json` lists which definition numbers exist.*

Every hash on a provenance record is lowercase hexadecimal SHA-256 over UTF-8 bytes, and every hash that has a definition number is computed by exactly the definition that number names.

## 1. The rule

**Definitions are added beside their predecessors, never replaced, and never compared across versions.** A record carries the number of the definition that computed each of its hashes. Two hashes computed under different definitions are different functions of possibly the same bytes; that they differ says nothing. A hash whose definition number is absent from the record is interpretable only by the definition its storage era used, stated below.

Canonical JSON, where a definition calls for it, means: property names in the order the definition states, no insignificant whitespace, property names camelCase where the definition names them, and strings escaped as the definition states.

## 2. The effective-input hash (`effectiveInputHash`, `effectiveInputHashVersion`)

| Definition | Package format | Bytes hashed |
|---|---|---|
| **1** | before specVersion 5 | *Historical.* The draft and the package's section list together. No engine computes it and no record referencing it is re-runnable; it is listed so the number is never reused. |
| **2** | specVersion 5, 6 | The canonical JSON object `{"consultDraft": <draft>}` — the draft only. Sections are package data and are covered by `workflowPackage`. Strings escaped by the default .NET JSON encoder (non-ASCII and `<`, `>`, `&`, `'`, `+` as `\uXXXX`). |
| **3** | specVersion 7 | The supplied inputs as a canonical JSON object `{id: text}`, ids ordinal-sorted, every value a string, absent optional inputs omitted (never empty-string-filled). Same encoder as 2. |
| **4** | specVersion 8 | The supplied inputs as a canonical JSON object `{id: value}`, ids ordinal-sorted, each value **typed**: a boolean is `true`/`false`, text is a string. Same encoder as 2. Definition 4 covers text and booleans only; an engine asked to hash structure under 4 refuses rather than stamping a wrong number. |
| **5** | specVersion 9 | The supplied inputs as a canonical JSON object of **structured values**: ids ordinal-sorted at every level (top-level slot ids and object field ids — UTF-16 code-unit order, as RFC 8785); array elements in the caller's order; a number as the digits the caller sent; a boolean as `true`/`false`; text as a string; absent optionals omitted; **UTF-8 written as-is**, with only what JSON requires escaped (`"`, `\`, control characters). |

Definitions 4 and 5 agree byte for byte on an ASCII map of scalars and on nothing wider, which is fine: they are never compared.

Worked examples (the string is the exact bytes hashed):

| Definition | Input | Bytes | SHA-256 |
|---|---|---|---|
| 2 | draft `Hello` | `{"consultDraft":"Hello"}` | `b18720c3b2a3f220df2570021d79cb18ceaa4b1531ea0d1ea1ef9f91bb4e5c79` |
| 3 | `b` = `two`, `a` = `one` | `{"a":"one","b":"two"}` | `8f770258ab53f8b20001e6ba82ae42d66479db3053a3b74776bafa2a92674514` |
| 3 | `accent` = `café` (definitions 2–4 escape non-ASCII) | `{"accent":"caf\u00e9"}` | `7a8a9123d6f8d59a0800fc5ee88f14034c7dcf8aa08cc9132630071fcc6f9779` |
| 4 | `reason` = `follow-up`, `billable` = true | `{"billable":true,"reason":"follow-up"}` | `cba13032e0d21f1098f9c60b8253ace104e399ff0a9c0ded9a26a356ce172756` |
| 5 | `patient` = `{name: Ada, age: 36}`, `notes` = `[x, y]`, `accent` = `café` | `{"accent":"café","notes":["x","y"],"patient":{"age":36,"name":"Ada"}}` | `52593837462725201bb86daf11e60f1aee9374ec207aaf234457c4713835032b` |

## 3. The workflow-output hash (`workflowOutputHash`, `workflowOutputHashVersion`)

Defined only for a `Completed` job; derived from the record, never stored.

| Definition | Storage version | Bytes hashed |
|---|---|---|
| **1** | records whose deliverable was per-section text (specVersion 5) | The canonical JSON object `{sectionId: sha256hex(sectionText)}`, ids ordinal-sorted — a Merkle-style root over the sections. |
| **2** | 6 | The assembled document's UTF-8 bytes, exactly as served in `assembledDocument`. |
| **3** | 7 | The canonical JSON object `{resultId: sha256hex(documentText)}`, ids ordinal-sorted — definition 1's recipe over the result set. Each inner digest is the record's `assembledDocuments[].documentHash`. |

Worked examples:

| Definition | Input | Bytes | SHA-256 |
|---|---|---|---|
| 1 | sections `hpi` = `History`, `plan` = `Plan` | `{"hpi":"0e769600933790607b2a13b33ddfade0fa17810eb62c3b28ee23e59516516491","plan":"fa8ed0bdabdd6bcb1c0746f1d3e15212f7f3439d74339fbaaf16c60c0a80fb8e"}` | `208471a047a8964edc58a50d8317ad24a711e04b59445006ec06e8e44dc38f85` |
| 2 | document `Consultation note` followed by a newline | `Consultation note\n` | `480ef298782bf4aab9a0b181ed6e0a22e049c1f0c51d85cf9659ae6220c23149` |
| 3 | results `note` = `Consultation note`, `letter` = `Patient letter` | `{"letter":"2000345f16eab8ff9958974250359885ad24f13d5ffe1ea64c9ff8705fa035d4","note":"ce812380ce3cdf680340cb1b7e40d336685f0cc698b10a5e3277ba807361c970"}` | `c8f784623550f4da6037fa84eab103b246880be1be5ed5cb8ba061d08c45d6e5` |

## 4. The per-node hashes (`nodeOutputs[].inputHash`, `nodeOutputs[].outputHash`)

A node instance's `inputHash` is SHA-256 of the exact rendered prompt the agent received (template, prelude and variables rendered to text); its `outputHash` is SHA-256 of the raw text the agent returned. An aggregator node's `inputHash` is instead SHA-256 of the canonical JSON array of its sources' output hashes in aggregation order, and its `outputHash` is SHA-256 of the text it rendered.

**These hashes carry no definition number.** `provenance-versions.json` says so with an empty `nodeHashVersions`. The bytes of a rendered prompt have changed at least twice without a number moving (a date rendering as `2026-08-10` rather than `10 Aug 2026`; an absent optional boolean rendering as nothing rather than an empty string), so a per-node hash is comparable only between runs of the same engine build — which the engine attests at `GET /api/Public/Engine`. Giving them a ladder is tracked in the engine repo.

Worked examples: text `Hello` → `185f8db32271fe25f561a6fc938b2e264306ec304eda518007d1764826381969`; an aggregator over sources whose output hashes are `ce812380…c970` (`Consultation note`) then `2000345f…35d4` (`Patient letter`) hashes the bytes `["ce812380ce3cdf680340cb1b7e40d336685f0cc698b10a5e3277ba807361c970","2000345f16eab8ff9958974250359885ad24f13d5ffe1ea64c9ff8705fa035d4"]` → `d8429debeb9facdd005d84147a126b01bbb0b5ea60944dad1b96ee1bd2d73c8d`.

## 5. The per-document hash (`assembledDocuments[].documentHash`)

SHA-256 of the document's `text`, unversioned by the same token as § 4 — it is the primitive definition 3 composes. `Consultation note` → `ce812380ce3cdf680340cb1b7e40d336685f0cc698b10a5e3277ba807361c970`.
