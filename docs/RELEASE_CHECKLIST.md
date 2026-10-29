# Public-release checklist (MIT approved; public release pending)

1. **DONE (29 October 2026):** Author explicitly approved MIT for original project software. `LICENSE` and `LICENSE_SCOPE.md` are included. The licence does not automatically grant rights to third-party datasets or archived evidence.
2. Review all source code, logs, JSON manifests, hashes and archived CSV data for sensitive material and third-party restrictions; permission to use a dataset is **not** automatically permission to redistribute it.
3. Confirm README statements and the DOI once the accepted paper is actually published. Do not invent an article DOI or repository URL.
4. Execute `python verify_191bins.py` from a clean checkout. Optionally execute `python scripts/run_conformance.py` and synthetic Python tests.
5. Inspect `git status` and `git ls-files` before publishing. Never commit large datasets, `.joblib` checkpoints, `policy_observations.csv`, `terminal_ledger.csv`, keys, `.env` files, or manuscript files.
6. Consider archiving a tagged release with Zenodo for a citable DOI, but only after the repository is public and its release has been checked.
7. Incorporate verified local provenance status without copying protected datasets or the accepted manuscript; see `docs/LOCAL_PROVENANCE_AUDIT_R4.md`.
8. Explicitly state in release notes that archived-result verification is available, while complete end-to-end replication depends on missing artefacts.

9. R5 source-archive locator produced zero filename matches, but one search root hit the directory cap; present this outcome as **not located**, never **absent**.
10. Remove any source inventories containing personal local paths (R6 removed the historical R10-A6 path inventory). Run `python scripts/verify_public_contents.py` before publication.
11. Run the Windows smoke-check on the extracted distribution from a fresh directory and review its compact report.

12. Review `docs/PUBLIC_DISTRIBUTION_INTEGRITY.md` and distinguish the 39
    packaged historical inputs from the 40-entry provenance inventory with
    one intentionally excluded personal path listing.
13. Independently review `code/`, `evidence/` and third-party provenance
    **before making this repository public**; MIT authorisation for the code is
    complete but the automatic content scan cannot constitute full legal/security review.
14. If enabling GitHub Actions, check its permissions and runs; the
    workflow only checks archived materials and does not run scientific campaigns.
