# Dataset: ToN_IoT and redistribution

Official primary source: https://research.unsw.edu.au/projects/toniot-datasets

Use the original dataset provider's terms. The official source grants free use for academic research and requires contacting the rights holder for commercial use. It requests citations to the dataset papers; consult its current page for the complete citation list. **No third-party ToN_IoT data are included in this repository.**

The D6 source expects a specific `Processed_Network_dataset.zip` (see SHA-256 in `evidence/d6_development_report.json` and `evidence/replay_manifest.json`). Do not replace that archive with a superficially similar Kaggle/HuggingFace rehosting and claim exact replication. The original archive filename, folder layout, chronological split and hash are part of the scientific contract.

For a local end-to-end attempt, store the original archive **outside** this repository (`data/source_downloads/` is gitignored). Do not upload oracle labels inside public score-only replay inputs or put local datasets under version control. The exact locked model, score stream and original compiled binary are not present in this release.


## Original archive status

The author's R5 filename-only search (29 October 2026) located no matching
source ZIP filename, but the OneDrive scan reached its directory limit.
The expected upstream SHA-256 remains unverified locally. There is no claim
that an independently downloaded archive will have the same hash.
See `docs/LOCAL_PROVENANCE_AUDIT_R5.md`.
