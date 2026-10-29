# Windows verification of the extracted R6 draft (29 October 2026)

The author ran the `DiscoverIoT_REPO_R6_SMOKE_READONLY.ps1` command against a
freshly extracted R6 working directory on Windows 11. The supplied short
report gave the following results:

| Check | Observed result |
| --- | --- |
| `R10_READONLY_ACTION_AUDIT` | `PASS` |
| Matched P4/A1 decision bins | 191 |
| All compared recorded fields equal | Yes |
| Derived action profile equal | Yes |
| Remaining FIFO item count equal | Yes |
| Positive-pressure bins | 23 |
| Maximum pressure | 0.6666666666666666 |
| Archive verifier exit status | 0 |
| Content checker files scanned | 58 |
| Content checker issues | 0 |
| Content checker exit status | 0 |
| Scientific campaign rerun | No |
| Original files changed | No |

This is **independent local execution of an archived-result check**, not
independent generation of the original 1,354,253-record/policy experimental
outputs. This report contains no private path names.
