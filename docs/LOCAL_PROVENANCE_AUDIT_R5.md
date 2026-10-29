# R3–R5 provenance and source-archive search status

**All checks were executed locally by the author on 29 October 2026 in
read-only mode. The findings are *not* an independent scientific replay.**

| Item | Recorded provenance check | Status |
| --- | --- | --- |
| D6 `d6_exploratory_model.joblib` | SHA-256 `7ed193e382383db329c81dacc6299e16f0024a44b65cf056a078b9d14467b007` | MATCH |
| Original controller binary, Policy and Actuation copies | SHA-256 `b3d9abcb10f795b6c1b2b1653f5eebc421afae6c8016296457ebadd763e95a5f` | MATCH for both copies |
| Bridge `policy_observations.csv` | SHA-256 `bc70cb353ce64693f9783d76e092b1f097c5b34a1fec2e0eac27e6b7a710bcfc` | MATCH |
| Actuation `terminal_ledger.csv` | SHA-256 `79b35e4a3ccb34af6ee5583190300469a3cccafe0a946bfbb9a64663cae2918c` | MATCH |
| D4 `protocol_lock.json` | SHA-256 `f01acd65e10f52184d0f20f0cec6d2bab53cf513d787f032a07682d85b7ef875` | MATCH |
| Cross-stage metadata D6 → Bridge → Actuation | 11 cross-checks | 11 MATCH, 0 mismatch, 0 missing |
| Original source ZIP `Processed_Network_dataset.zip` | Expected SHA-256 `b024574780da5db96adf255c0a2effa71e1c31173d34eaaa80fbd4edc1b9010e` | NOT FOUND BY FILENAME; NOT HASHED |

## R5 search scope and its limits

- `Downloads`: 18 directories, 71 files; no filename matches; no errors.
- Author's OneDrive data tree: 8,000 directories, 52,789 files; no filename
  matches **within the inspected subset**; stopped at directory limit.
- `C:\teste`: 54 directories, 63 files; no filename matches; no errors.
- Total: **8,072 directories, 52,923 files** scanned, **0 filename matches**,
  **0 read errors** and **1 root stopped by limit**.
- Search compared **filenames**, not archive bytes or source data. Files
  with unrecognised names, excluded directories or unsearched locations
  could contain the original archive. A newly downloaded provider copy may
  have different bytes even when its contents are scientifically equivalent.

## Consequence for external reproducibility

The bounded 191-bin and conformance checks are independently runnable from
this repository; the exact full input provenance remains conditional on the
source archive and additional local data not distributed here.

There is **no need to continue broad recursive searching as a condition of
publishing a truthful bounded reproducibility package**. If an external
researcher obtains an authorized copy of the original dataset, its contents,
format and hash should be checked independently before claiming exact replay.

No original source files were modified. No model loading, training, traffic
simulation or new scientific campaign was conducted by R3–R5.
