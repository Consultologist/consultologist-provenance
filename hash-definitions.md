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
| **2** | specVersion 5, 6 | The canonical JSON object `{"consultDraft": <draft>}` — the draft only. Sections are package data and are covered by `workflowPackage`. Strings escaped by the default .NET JSON encoder (non-ASCII and `<`, `>`, `&`, `'`, `+` as `\uXXXX`, hex digits uppercase). |
| **3** | specVersion 7 | The supplied inputs as a canonical JSON object `{id: text}`, ids ordinal-sorted, every value a string, absent optional inputs omitted (never empty-string-filled). Same encoder as 2. |
| **4** | specVersion 8 | The supplied inputs as a canonical JSON object `{id: value}`, ids ordinal-sorted, each value **typed**: a boolean is `true`/`false`, text is a string. Same encoder as 2. Definition 4 covers text and booleans only; an engine asked to hash structure under 4 refuses rather than stamping a wrong number. |
| **5** | specVersion 9 | The supplied inputs as a canonical JSON object of **structured values**: ids ordinal-sorted at every level (top-level slot ids and object field ids — UTF-16 code-unit order, as RFC 8785); array elements in the caller's order; a number as the digits the caller sent; a boolean as `true`/`false`; text as a string; absent optionals omitted; **UTF-8 written as-is**, with only what JSON requires escaped (`"`, `\`, control characters). |
| **6** | specVersion 10 | Definition 5 **recursed**. A field may itself be an object or an array, and an array's element an object or an array, to any depth the package declares; every rule of definition 5 applies at every level — field ids ordinal-sorted inside every object, elements in the caller's order inside every array, numbers as sent, UTF-8 as-is, absent optionals omitted. A v10 map with no nested structure hashes byte-identically under 5 and 6: the recursion never enters, and that is the control. |

Definitions 4 and 5 agree byte for byte on an ASCII map of scalars and on nothing wider, which is fine: they are never compared. Definitions 5 and 6 agree byte for byte on any map one level deep — by construction, since 6 is 5 applied again beneath — and are still never compared: the record says which number it stamped.

Worked examples (the string is the exact bytes hashed):

| Definition | Input | Bytes | SHA-256 |
|---|---|---|---|
| 2 | draft `Hello` | `{"consultDraft":"Hello"}` | `b18720c3b2a3f220df2570021d79cb18ceaa4b1531ea0d1ea1ef9f91bb4e5c79` |
| 3 | `b` = `two`, `a` = `one` | `{"a":"one","b":"two"}` | `8f770258ab53f8b20001e6ba82ae42d66479db3053a3b74776bafa2a92674514` |
| 3 | `accent` = `café` (definitions 2–4 escape non-ASCII, uppercase hex) | `{"accent":"caf\u00E9"}` | `3849b4da05d4d8716eca76c57d1d952e687bd164ef2e3dd53e31b1f1666ca979` |
| 4 | `reason` = `follow-up`, `billable` = true | `{"billable":true,"reason":"follow-up"}` | `cba13032e0d21f1098f9c60b8253ace104e399ff0a9c0ded9a26a356ce172756` |
| 5 | `patient` = `{name: Ada, age: 36}`, `notes` = `[x, y]`, `accent` = `café` | `{"accent":"café","notes":["x","y"],"patient":{"age":36,"name":"Ada"}}` | `52593837462725201bb86daf11e60f1aee9374ec207aaf234457c4713835032b` |
| 6 | `family_history` = `[{relative: mother, contact: {preferred: email, phone: 555}, conditions: [b, a]}]` — a nested object and a nested array inside an array element | `{"family_history":[{"conditions":["b","a"],"contact":{"phone":"555","preferred":"email"},"relative":"mother"}]}` | `b6a313365b611c7ec0be83d67237876ae56d4fe5fac3b77e758985551f59037d` |
| 6 | definition 5's own example, hashed under 6 — the control: no nesting, the same bytes | `{"accent":"café","notes":["x","y"],"patient":{"age":36,"name":"Ada"}}` | `52593837462725201bb86daf11e60f1aee9374ec207aaf234457c4713835032b` |

## 3. The workflow-output hash (`workflowOutputHash`, `workflowOutputHashVersion`)

Defined only for a `Completed` job. Computed from the produced text once, when the job completes, and stored on the record (records from before 2026-08-25 derived it on every read; the served value is the same) — so it survives the text's deletion under the retention policy (`textDroppedAtUtc`, provenance-record.md § 4).

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

## 4. The per-node hashes (`nodeOutputs[].inputHash`, `nodeOutputs[].outputHash`, `nodeOutputs[].hashVersion`)

A node instance's `inputHash` is SHA-256 of the exact rendered prompt the agent received (template, prelude and variables rendered to text); its `outputHash` is SHA-256 of the raw text the agent returned. An aggregator node's `inputHash` is instead SHA-256 of the canonical JSON array of its sources' output hashes in aggregation order, and its `outputHash` is SHA-256 of the text it rendered.

**One number defines the pair.** `hashVersion` on a node instance names the definition both of its hashes were computed under. Across the ladder the output hash and the aggregator's input hash have never changed; every definition differs only in how the prompt renders — which is what `inputHash` is over, and why the number moves.

| Definition | From | What the rendered prompt is |
|---|---|---|
| **1** | 2026-07-14 (engine `260db91`) | The prelude with trailing whitespace removed, two newlines, then the template rendered with every variable as the string the caller supplied. |
| **2** | 2026-08-10 (engine `c4ad2a7`) | As 1, but a typed input renders from its typed value — a date in the renderer's default form (`10 Aug 2026`), a boolean as `true`/`false`. |
| **3** | 2026-08-13 (engine `964af19`) | As 2, but a date renders as the ISO date it was supplied as (`2026-08-10`). |
| **4** | 2026-08-13 (engine `5b12999`) | As 3, but an absent optional typed input renders nothing and is falsy in conditions (it was the empty string, and truthy). |
| **5** | 2026-08-22 (engine `a661a20`, `34224fa`) | As 4, but structured values (objects, arrays, numbers) materialise as structure, a fan item carries its typed value, and an empty array is falsy. **Current.** |

Records stamp `hashVersion` from 2026-08-25; the first stamped definition is 5. A record from before carries no `hashVersion`: by its `createdAtUtc` and the dates above it ran under one of 1–5, and its per-node hashes may not be compared with a record from the other side of any of those dates. Two records with the same `hashVersion`, package version and inputs whose first node's `inputHash` differs ran different prompt bytes — and that is the only conclusion a per-node hash supports across records.

**A classifier's pair** (specVersion 10, a node of kind `classifier`). `inputHash` is over what the agent received: the rendered prompt **plus** the classification trailer the engine appends — a blank line and *Answer with exactly one of: <the declared values, in declared order>.* — because that sentence is part of the prompt bytes. `outputHash` is the SHA-256 of the **normalised** answer — the declared value the agent's reply resolved to (lower-cased, trimmed, one of the values) — not of the raw text returned; two runs that answer the same value hash the same however the model spelled its reply. The value itself is on the record as `nodeOutputs[].classification` and `classifications`. `hashVersion` does not move for a classifier: 5 names the rendering, and the trailer is part of the prompt under 5.

| Definition | Input | Bytes | SHA-256 |
|---|---|---|---|
| 5 (classifier output) | the normalised answer `in_scope` | `in_scope` | `9464a24113872b892e176555598c34aa1a900ae21b2a7dadc4916b40a423d0cf` |

Worked examples, valid under every definition (the output side never moved): text `Hello` → `185f8db32271fe25f561a6fc938b2e264306ec304eda518007d1764826381969`; an aggregator over sources whose output hashes are `ce812380…c970` (`Consultation note`) then `2000345f…35d4` (`Patient letter`) hashes the bytes `["ce812380ce3cdf680340cb1b7e40d336685f0cc698b10a5e3277ba807361c970","2000345f16eab8ff9958974250359885ad24f13d5ffe1ea64c9ff8705fa035d4"]` → `d8429debeb9facdd005d84147a126b01bbb0b5ea60944dad1b96ee1bd2d73c8d`.

## 5. The per-document hash (`assembledDocuments[].documentHash`)

SHA-256 of the document's `text`. Unversioned by design: it is the primitive definition 3 composes, and a primitive's definition cannot change without being a different function. `Consultation note` → `ce812380ce3cdf680340cb1b7e40d336685f0cc698b10a5e3277ba807361c970`.
