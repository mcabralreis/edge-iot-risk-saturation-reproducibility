# Author-side source and provenance audit (R3/R4, 29 October 2026)

This is a summary of **read-only local checks performed by the manuscript author**,
not an independently replicated scientific run. None of the files in the table
below is included in this repository merely because it was located on the
author's computer.

| Item | Size, bytes | SHA-256 comparison |
| --- | ---: | --- |
| D6 model (`d6_exploratory_model.joblib`) | 198,709 | MATCH: `7ed193e382383db329c81dacc6299e16f0024a44b65cf056a078b9d14467b007` |
| Compiled controller, Policy copy | 32,848 | MATCH: `b3d9abcb10f795b6c1b2b1653f5eebc421afae6c8016296457ebadd763e95a5f` |
| Compiled controller, Actuation copy | 32,848 | MATCH: same SHA-256 as Policy copy |
| Bridge `policy_observations.csv` | 226,790,406 | MATCH: `bc70cb353ce64693f9783d76e092b1f097c5b34a1fec2e0eac27e6b7a710bcfc` |
| Actuation `terminal_ledger.csv` | 415,304,717 | MATCH: `79b35e4a3ccb34af6ee5583190300469a3cccafe0a946bfbb9a64663cae2918c` |
| D4 `protocol_lock.json` | 860 | MATCH: `f01acd65e10f52184d0f20f0cec6d2bab53cf513d787f032a07682d85b7ef875` |
| Original ToN_IoT source ZIP | not located in searched `out2026` tree | **NOT VERIFIED**; expected `b024574780da5db96adf255c0a2effa71e1c31173d34eaaa80fbd4edc1b9010e` |

Manifest consistency: **11 matched, 0 mismatches, 0 missing**. This checks
cross-references in D6, Bridge and Actuation metadata, not the correctness of
every record nor a fresh run.

No model deserialisation, model fitting, scientific execution or modification of
original sources occurred during R3/R4. All large files remain local.

**Publication gate:** verify legal redistribution rights, remove private paths
and compiled artefacts, select an explicit licence, and conduct a clean-checkout
test before making any GitHub repository public. The full input stream and
model are not part of the current repository candidate.
