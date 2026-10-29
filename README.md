# Edge-IoT security control: resource-pressure saturation replay

**Code, bounded evidence and reproducibility guidance for an accepted Case Study in *Discover Internet of Things* (Springer Nature).**

**Manuscript not distributed.** This repository contains **no article PDF, LaTeX manuscript, review correspondence or manuscript figures**. The peer-reviewed study is titled *Resource Pressure Feedback Becomes Behaviorally Redundant Under Risk Trigger Saturation in Edge IoT Security Control* (Manuel J. C. S. Reis). A journal DOI will be added **only after publication and verification**.

## Local provenance and source archive status (29 October 2026)

The author's read-only audits R3 and R4 established **five exact SHA-256
matches** for the D6 model, the two historical controller copies, the archived
Bridge observations and the terminal ledger. They also verified the D4
protocol lock and **11/11 manifest cross-checks** across D6, Bridge and
Actuation (zero mismatches). These results establish *local artefact identity*,
not independent experimental reproduction.

A further R5 filename-only search examined 8,072 directories and 52,923
files across Downloads, the OneDrive project tree and `C:\teste`:
**no matching source ZIP filename was found**. Crucially, OneDrive searching
stopped after 8,000 directories due to the configured limit; other filenames
or locations remain possible. The source archive's content hash has therefore
**not** been checked. The exact upstream `Processed_Network_dataset.zip`
remains an **unresolved prerequisite** for byte-identical end-to-end
reconstruction. This does not invalidate the bounded replay evidence already
archived. See [docs/LOCAL_PROVENANCE_AUDIT_R5.md](docs/LOCAL_PROVENANCE_AUDIT_R5.md).

**None of the author's large local files, trained checkpoints or third-party
source datasets has been copied into this candidate repository.**

## What can be reproduced today?

| Level | What the repository supports | Status |
| --- | --- | --- |
| 1 | Check the integrity and equality of the **191 archived P4/A1 decision bins** and inspect the 23 positive-pressure bins | **Ready: pure Python, no external dependencies** |
| 2 | Compile and run **synthetic controller conformance tests** and a reference comparison | **Ready where a C++17 compiler is available** |
| 3 | Run the *synthetic* Bridge, Actuation and 23-window safeguards | **Ready with extra Python dependencies and a compiled controller** |
| 4 | Repeat D6 fitting, score export and the full 1,354,253-record/policy modeled replay | **Not self-contained**: needs original licensed source dataset, exact D6 model, complete score/observation stream, locked inputs and original binary provenance |

**Do not describe Level 1 or 2 as independent end-to-end replication.** This is one deterministic, exploratory, development-validation replay; it is *not* measured 5G NR performance, nor evidence that resource feedback is ineffective generally.

## Independently verified local archive checks

The R6 draft passed the author's Windows smoke-test on 29 October 2026:
191/191 matched P4/A1 bins, zero differences in recorded common fields,
23 positive-pressure bins and zero public-content-scan issues.
See [docs/LOCAL_WINDOWS_SMOKE_R6.md](docs/LOCAL_WINDOWS_SMOKE_R6.md).

The R8 MIT release candidate includes [an automated SHA-256 checker](docs/PUBLIC_DISTRIBUTION_INTEGRITY.md)
for the 39 distributed historical source/evidence files, and a minimal
GitHub Actions workflow to run source identity, archived-result equality
and content-category checks on every commit. No dataset access or scientific
replay is needed for those checks. **MIT licensing for original code is now authorised; public release remains subject to a final content and third-party-rights review.**

## Quick start — Python 3.10+

```bash
python verify_191bins.py
python scripts/verify_distributed_sources.py
python scripts/verify_public_contents.py
```

Expected output includes:

```
R10_READONLY_ACTION_AUDIT=PASS
P4_A1_MATCHED_BINS=191
ALL_RECORDED_FIELDS_EQUAL=YES
POSITIVE_PRESSURE_BINS=23
SCIENTIFIC_RUN_EXECUTED=NO
```

This **rechecks archived results**; it does not refit D6 or regenerate the 1.35 million-record replay.

To compile/run the controller checks with a C++17 compiler, see [docs/CONFORMANCE.md](docs/CONFORMANCE.md) or run `python scripts/run_conformance.py`. The script builds into `build/` and prints outcomes; it does not touch any original scientific campaign output.

Optional synthetic Python checks (with isolated environment and packages in `requirements-optional.txt`):

```bash
python code/test_23_windows.py
python code/test_bridge.py
python code/test_actuation.py build/controller_stream
```

On Windows, `build/controller_stream` should be `build/controller_stream.exe`.

## Reported values and interpretation

- 1,354,253 flow records per modeled policy; 191 decision bins.
- D6 development-validation macro-F1 = **0.513605**; false-positive rate = **0.047662**. The predeclared macro-F1 target of 0.80 was **not met**.
- P4/A1: **0/191 differences** in recorded common decision and service fields; **23/191** bins had positive P4 queue pressure; maximum observed pressure **2/3**.
- All 23 positive-pressure bins had risk 0.9670–0.9959 (above the controller CRITICAL threshold 0.75); pressure never reached 0.75.
- The bounded post-service queue size is a **count of modeled unit flow records**, not the complete FIFO event-identity sequence. Equal terminal aggregates are not a general equivalence proof.
- The score gate, 6,000-record service capacity and 18,000-record FIFO limit are **model assumptions**, not real deployed edge/5G measurements.

## Repository map

```text
code/                    Original D6, bridge, controller, actuation and audit code
code/include/comnet/     Header layout for C++ builds
COMNET_TON_D6/           Compatibility copy needed by original synthetic bridge test
evidence/                Archived action log, matched 191-bin log, outcomes and manifests
docs/                    Reproduction scope, conformance, dataset, provenance
scripts/                 Local smoke/test runner and optional artefact-location audit
provenance/              SHA-256 inventory of material imported into this repository
verify_191bins.py        Dependency-free integrity and P4/A1 equality check
```

## Dataset and data rights

The third-party dataset is **ToN_IoT** (UNSW Canberra). It is **not redistributed** here. Obtain it from the [official ToN_IoT page](https://research.unsw.edu.au/projects/toniot-datasets) and comply with its citation and reuse terms. The official source states free academic research use but requires contacting the rightsholder for commercial use. Do **not** assume the repository's eventual code licence applies to that dataset.

## Licensing and publication gate

**Original author-developed project code is licensed under the MIT licence**, as expressly approved by the author on 29 October 2026. See [LICENSE](LICENSE) and [LICENSE_SCOPE.md](LICENSE_SCOPE.md). This grant does **not** extend to third-party ToN_IoT data, the accepted article or automatically to historical research datasets and evidence. Do not infer a public distribution permission from the inclusion of provenance information or SHA-256 hashes.

**The repository is not yet published.** Review the source code and archived evidence against [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md) before publishing; create the GitHub repository as **private** initially and confirm its contents before making it public.

## Reproducibility disclosures

See [docs/PUBLIC_DISTRIBUTION_INTEGRITY.md](docs/PUBLIC_DISTRIBUTION_INTEGRITY.md), [docs/REPRODUCIBILITY_LEVELS.md](docs/REPRODUCIBILITY_LEVELS.md), [docs/DATASET.md](docs/DATASET.md), [docs/PROVENANCE.md](docs/PROVENANCE.md) and [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md).

**Author:** Manuel J. C. S. Reis — University of Trás-os-Montes and Alto Douro (UTAD), Portugal. Contact: mcabral@utad.pt.
