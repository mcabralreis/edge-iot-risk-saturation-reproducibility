# Reproduction contract and limitations

## A. Archived-result verification (self-contained)

`python verify_191bins.py` checks immutable hashes and the 764 archived `actions_original.csv` rows (B2, P4, A1, B5; 191 bins each); verifies identical fields across P4/A1, cross-checks a separate 191-row matched CSV, asserts exactly 23 positive-pressure bins and maximum 2/3, and checks the post-service remaining queue bound. No retraining, external dataset, oracle or executable is used.

This confirms properties of **recorded actions and service-accounting fields**; it does not inspect each queued event's identity or recover the absent terminal event ledger. Matching `state`, `filter`, and derived profiles is a bounded software/record claim, not an inference of causal redundancy across deployments.

## B. Synthetic software-level checks (self-contained with compiler)

`python scripts/run_conformance.py` builds the archived `security-orchestrator.cc` and `gate8ar` interface/reference tests from source and executes both. The historical `gate8ar` stdout/stderr archives under `evidence/archived_gate8ar_and_gate8a/` reported PASS; new executions on other compilers are **fresh software tests**, not the historical scientific replay and should be labelled accordingly.

The synthetic tests exercise transitions, threshold and pressure cases, independent reference behavior, invalid inputs and hysteresis. They **do not** establish identity of the newly built binary with the original replay binary (original SHA-256 appears in `evidence/actuation_manifest.json`).

## C. Synthetic pipeline checks

With NumPy, scikit-learn and joblib (see `requirements-optional.txt`), the archived `test_bridge.py`, `test_actuation.py`, and `test_23_windows.py` use fabricated, isolated fixtures. They check oracle isolation, window lag handling, conservation, fail-closed output behavior, and description of positive-pressure bins. They are **not** empirical replications of the case study.

## D. End-to-end replay

The repository includes development code for D6 training/export and modeled actuation, but **does not** include: the exact ToN_IoT input archive, frozen D6 joblib artefact, large per-record score stream, original compiled controller binary, or original full terminal-event ledger. `evidence/replay_manifest.json` and `evidence/actuation_manifest.json` carry hashes and assumptions for comparison with locally held originals.

Without those artefacts, the complete 1,354,253-record-per-policy processing and terminal accounting **cannot be reproduced with this repository alone**. If exact inputs are recovered, use the original scripts and contracts as documented in `docs/END_TO_END_REQUIREMENTS.md`, preserve original evidence, and produce new outputs in a separate directory. Do not treat a new run as byte-for-byte identical until every upstream hash, software dependency and environment is verified.

## E. Scientific interpretation

The D6 development-validation macro-F1 target was missed; the same development-validation interval feeds the replay. Capacity, pressure, filter and queue are modeled flow-record proxies, not actual 5G scheduling, latency, goodput or cryptographic enforcement. The 23-bin post hoc inspection was planned **after observing the null P4/A1 contrast, but before inspecting each positive-pressure bin**.
