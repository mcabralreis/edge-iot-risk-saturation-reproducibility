# Distributed-source identity and release limitations

## Run locally

From the extracted repository root:

```bash
python scripts/verify_distributed_sources.py
python verify_191bins.py
python scripts/verify_public_contents.py
```

The distributed-source verifier compares hashes of **39 source/evidence
files shipped in this repository** with the historical source imports.
It checks imported-file identity, not experiment equivalence.

`provenance/INPUT_ARCHIVE_SHA256.tsv` remains the original **40-entry
historical inventory**. One entry, `evidence/R10_A6_archived_test_log_search.txt`,
is **intentionally absent** from the public release candidate because it
contained a personal filesystem path inventory. The filtered
`provenance/DISTRIBUTED_SOURCE_SHA256.tsv` is the correct manifest for
checks performed on this distributed package.

The manifest does not include documentation and infrastructure created
for this packaging iteration. The Git revision and ZIP digest, once
publicly released, identify the package as a whole.

The checks do not certify privacy, licensing, non-infringement,
scientific validity, or whether the source code constitutes an end-to-end
reproduction of the journal article. The original ToN_IoT source archive,
frozen D6 model and complete observation and terminal ledger files remain
external to this candidate repository.
