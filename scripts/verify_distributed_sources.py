#!/usr/bin/env python3
"""Verify copied historic source/evidence artefacts without executing scientific workflows.

Only paths shipped in this distribution are considered. This validates the
frozen-source import, not the numerical accuracy of published results.
"""
from pathlib import Path
import hashlib
import sys

root = Path(__file__).resolve().parents[1]
manifest = root / "provenance" / "DISTRIBUTED_SOURCE_SHA256.tsv"
lines = manifest.read_text(encoding="utf-8").splitlines()
if lines[0] != "relative_path\tsha256":
    raise SystemExit("MANIFEST_HEADER_INVALID")
checked = 0
issues = []
for entry in lines[1:]:
    if not entry.strip():
        continue
    parts = entry.split("\t")
    if len(parts) != 2:
        issues.append("MALFORMED_ENTRY")
        continue
    rel, expected = parts
    candidate = root / rel
    if candidate.is_symlink() or not candidate.is_file() or not candidate.resolve().is_relative_to(root.resolve()):
        issues.append("MISSING_OR_UNSAFE_ENTRY=" + rel)
        continue
    actual = hashlib.sha256(candidate.read_bytes()).hexdigest()
    checked += 1
    if actual != expected:
        issues.append("SHA256_MISMATCH=" + rel)
print("===== DISTRIBUTED SOURCE SHA256 VERIFICATION =====")
print("MANIFEST_ENTRIES=" + str(sum(bool(x.strip()) for x in lines[1:])))
print("FILES_HASHED=" + str(checked))
print("HASH_MISMATCHES_OR_ERRORS=" + str(len(issues)))
for item in issues:
    print(item)
print("INCLUDED_SOURCE_IDENTITY=" + ("PASS" if not issues else "FAIL"))
print("SCIENTIFIC_EXECUTION=NO")
raise SystemExit(0 if not issues else 1)
