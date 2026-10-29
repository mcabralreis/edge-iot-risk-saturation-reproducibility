# Evidence and provenance

The code and bounded data were copied without altering their bytes from the author's October 2026 R10 Supplementary Software package. The original historical actions, manifests and archived conformance logs are preserved under `evidence/`. `provenance/INPUT_ARCHIVE_SHA256.tsv` lists SHA-256 for imported files (including compatibility copies and restored original helper code). These checksums do not establish independent correctness of the original dataset.

`verify_191bins.py` additionally pins SHA-256 for the original actions CSV and controller stream; `evidence/R10_A7_SHA256_INVENTORY.txt` records the archived gate8ar test logs. D6 acceptance metric and complete input hashes are in the JSON manifests. The original compiled controller binary was not recovered, and a newly built executable cannot be asserted to match its archived binary hash.

Original event IDs in the policy stream, labels in the sealed oracle and the complete terminal ledger are **not published**. The 191-bin log compares recorded fields, while additional action-profile fields in the matched CSV were **derived using the deterministic `ActionProfile` mapping**; they were not originally logged as distinct columns.

No article, accepted-manuscript PDF, LaTeX or correspondence forms part of this distribution.
