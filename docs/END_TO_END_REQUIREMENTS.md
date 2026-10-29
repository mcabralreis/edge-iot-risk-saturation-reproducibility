# Inputs needed to rerun the full modeled pipeline

These are **not included** in the public release and no end-to-end replication is claimed.

| Required input | Expected evidence | Included? |
| --- | --- | --- |
| Original ToN_IoT network source ZIP | SHA-256 `b024574780da5db96adf255c0a2effa71e1c31173d34eaaa80fbd4edc1b9010e` | No |
| D6 model/checkpoint joblib | SHA-256 `7ed193e382383db329c81dacc6299e16f0024a44b65cf056a078b9d14467b007` | No |
| Complete bridge output `policy_observations.csv` | SHA-256 `bc70cb353ce64693f9783d76e092b1f097c5b34a1fec2e0eac27e6b7a710bcfc` | No |
| Original compiled controller | SHA-256 `b3d9abcb10f795b6c1b2b1653f5eebc421afae6c8016296457ebadd763e95a5f` | No |
| Original terminal-event ledger | SHA-256 `79b35e4a3ccb34af6ee5583190300469a3cccafe0a946bfbb9a64663cae2918c` | No |
| Archived `actions.csv`, matched P4/A1 191 bins and summary evidence | `evidence/` | Yes, bounded archival form |

The R5 filename-only search did not locate the upstream source ZIP in its inspected roots; the OneDrive scan stopped at a configured directory limit. This does not prove the source ZIP is absent. See `docs/LOCAL_PROVENANCE_AUDIT_R5.md`.

The original D6 source, bridge exporter and actuator scripts are under `code/`, with their command-line arguments visible through `--help` or in source. They are included for methods transparency, **not** as a single-click verified reproduction of the missing-input pipeline. `joblib.load` executes deserialization code: use **only trusted local model checkpoints**.

**Local discovery only:** `scripts/find_missing_local_artifacts.ps1` can inspect the project's `testesV2` tree and produce a small *local* report of matching paths and byte sizes. It does not copy or upload large files; the report is not intended for public release without reviewing paths.

To achieve a truly end-to-end executable public release, first recover the missing inputs, confirm distribution rights, lock toolchain versions, then independently test execution from a clean working directory and document all expected outputs and SHA-256. No such test is claimed in this version.
