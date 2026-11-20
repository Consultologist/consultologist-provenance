#!/usr/bin/env python3
"""Checks the specVersion 31 preview additions to this repo.

Run from the repository root, with origin/main fetched:  python3 scripts/check-v31.py
Exits 1 and prints one line per failure.
"""
import json
import pathlib
import re
import subprocess
import sys

BASE = "origin/main"
PREVIEW = {
    "recordStorageVersions": [12],
    "effectiveInputHashVersions": [7],
    "workflowOutputHashVersions": [4],
    "nodeHashVersions": [7],
}
UNCHANGED = ("version", "documents", "recordStorageVersions", "effectiveInputHashVersions",
             "workflowOutputHashVersions", "nodeHashVersions")
PINNED_PREFIXES = (
    "| `fileSha256` |", "| `textSha256` |", "| `documentHash` |", "| `documentHash` (specVersion 12) |",
    "| 6 (composed output) |", "| 6 (agentOutputHash) |",
)
# Every member name in part 08's tables, by table.
MEMBERS = {
    "job header": "resolveHash lockHash versionsRan recordHash runFacts limits startedAtUtc "
                  "signatureBlockId signatureChosen decisions",
    "limits": "maxAgentCalls capacityWaitMinutes serviceAttempts jobMinutes deliveryMinutes "
              "deliveryAttempts loopItems jobAgentCalls renderSteps",
    "input origin": "converter parser ocr",
    "node row": "nodeId kind producer formatHash typeHash sentFormatHash notSent agent itemName "
                "runDependent modelDerived profileCarrying runNeutralHash runSpots renders macros "
                "invalid retries profileReads stateReason",
    "agent": "name version binding",
    "renderer sub-row": "id renderer templateHash source inputHash inputSize outputHash outputLength",
    "macro row": "macro offered decisions classifier placed form contentHash",
    "decision": "owner site condition expressionHash result reads decidedAtUtc",
    "check row": "key label status alignedWith checked pass failWith effect count",
    "call row": "function arguments depth",
    "run facts": "date id package engine",
    "run spot": "site valueHash output",
    "deliverable row": "templateHash format state check delivery sites substitutions",
    "delivery row": "kind result reason atUtc attempts",
}

errors = []


def git_show(path):
    return subprocess.run(["git", "show", f"{BASE}:{path}"], capture_output=True, text=True, check=True).stdout


index = json.load(open("provenance-versions.json"))
base_index = json.loads(git_show("provenance-versions.json"))

for key in UNCHANGED:
    if index.get(key) != base_index.get(key):
        errors.append(f"provenance-versions.json: {key} differs from {BASE}")
if index.get("preview") != PREVIEW:
    errors.append(f"provenance-versions.json: preview is {index.get('preview')!r}, not {PREVIEW!r}")
extra = set(index) - set(base_index) - {"preview"}
if extra:
    errors.append(f"provenance-versions.json: unexpected members {sorted(extra)}")

record = pathlib.Path("provenance-record.md").read_text()
if "storage versions 2, 6, 7, 8, 9, 10 and 11" not in record:
    errors.append("provenance-record.md no longer says 'storage versions 2, 6, 7, 8, 9, 10 and 11'")

start = record.find("## 6. Storage 12 (specVersion 31, preview)")
if start < 0:
    errors.append("provenance-record.md has no '## 6. Storage 12 (specVersion 31, preview)'")
    section = ""
else:
    section = record[start:]
    for sentence in ("Storage 2–11 records read as before; nothing is converted.",
                     "can be reversed by hashing likely candidates"):
        if sentence not in section:
            errors.append(f"section 6 never says: {sentence}")
    for table, names in MEMBERS.items():
        for name in names.split():
            if f"`{name}`" not in section:
                errors.append(f"section 6: the {table} member `{name}` does not appear in backticks")

hashes = pathlib.Path("hash-definitions.md").read_text()
if "## 7. Definitions specVersion 31 adds (preview)" not in hashes:
    errors.append("hash-definitions.md has no '## 7. Definitions specVersion 31 adds (preview)'")
layout = pathlib.Path("registry-layout.md").read_text()
if "## 10. A specVersion 31 version folder (preview)" not in layout:
    errors.append("registry-layout.md has no '## 10. A specVersion 31 version folder (preview)'")

# The three contract files only gain lines: nothing a storage 2-11 reader relies on changes.
for name in ("hash-definitions.md", "provenance-record.md", "registry-layout.md"):
    diff = subprocess.run(["git", "diff", BASE, "--unified=0", "--", name],
                          capture_output=True, text=True, check=True).stdout
    for line in diff.splitlines():
        if line.startswith("-") and not line.startswith("---"):
            errors.append(f"{name}: a line of {BASE} was removed or changed: {line[1:60]}")

diff = subprocess.run(["git", "diff", BASE, "--unified=0", "--", "hash-definitions.md"],
                      capture_output=True, text=True, check=True).stdout
for line in diff.splitlines():
    if line.startswith("+") and not line.startswith("+++"):
        added = line[1:]
        if added.startswith(PINNED_PREFIXES) or added.startswith("| **"):
            errors.append(f"hash-definitions.md: added line starts with a pinned prefix: {added[:60]}")

for doc in sorted(pathlib.Path(".").glob("*.md")):
    for number, line in enumerate(doc.read_text().splitlines(), 1):
        for target in re.findall(r"\]\(([^)]+)\)", line):
            if target.startswith("http"):
                if "/blob/main/" in target or "/tree/main/" in target:
                    errors.append(f"{doc}:{number} links to main: {target}")
            elif target.startswith("#"):
                continue
            elif not pathlib.Path(target.split("#")[0]).is_file():
                errors.append(f"{doc}:{number} dangling relative link: {target}")

for error in errors:
    print(f"::error::{error}")
print("check-v31: " + (f"{len(errors)} failures" if errors else "ok"))
sys.exit(1 if errors else 0)
