# Local validation of this repository package

Validated in the packaging environment on 29 October 2026; **not** a new scientific replay.

| Check | Observed outcome | Interpretation |
| --- | --- | --- |
| `python verify_191bins.py` | PASS; P4/A1 191 bins, 23 positive-pressure bins, no recorded differences | Archive audit only |
| C++17 compile interface and reference checks | PASS | Compiler can build bundled component |
| C++ interface check | PASS; 59 positive checks, 45 negative cases, two one-window recovery cases | Synthetic conformance only |
| C++ independent reference comparison | PASS; 500,001 risk, 500,001 pressure, 400,000 transition cases | Software-level test, not a policy replay |
| Build controller stream | PASS | Does not establish binary identity with original compiled controller |
| `python code/test_23_windows.py` | PASS | Synthetic 191-bin fixture only |
| `python code/test_actuation.py build/controller_stream` | PASS | Synthetic 1,528-event/policy fixture only |
| `python code/test_bridge.py` | PASS | Synthetic four-row bridge fixture only |
| Article/manuscript files packaged | None | No PDF, TEX, DOCX or reviewer correspondence |

The bundled data are unchanged relative to the supplied R10 Supplementary Software archive. Neither a raw third-party dataset, a frozen D6 model, nor the 226-MB score stream is bundled here. Full end-to-end replication **has not been run**.
