# Controller checks

Requirements: **C++17** (`g++`, `clang++` or a suitable compiler) and Python 3.10+.

From the repository root:

```bash
python scripts/run_conformance.py
```

The script finds `g++` or `clang++`, compiles the controller, the interface test and the reference-comparison test under `build/`, then executes both. It separately verifies the original `controller_stream.cc` can compile; the controller executable is used only by the optional *synthetic* actuation test.

For manual builds (Linux, macOS or Windows with MinGW):

```bash
mkdir -p build
g++ -std=c++17 -O2 -Icode/include code/security-orchestrator.cc code/security-orchestrator-interface-test-gate8ar.cc -o build/interface_test
g++ -std=c++17 -O2 -Icode/include code/security-orchestrator.cc code/security-orchestrator-reference-comparison-gate8ar.cc -o build/reference_test
g++ -std=c++17 -O2 -Icode/include code/security-orchestrator.cc code/controller_stream.cc -o build/controller_stream
./build/interface_test
./build/reference_test
```

On Windows executables have `.exe`, and invocation should use that suffix. Outputs below were recorded in the archived tests and are reproduced only if the toolchain/behavior agree:

- `SecurityOrchestrator interface test: PASS`, `positive_checks=59`, `negative_cases=45`.
- `SecurityOrchestrator independent reference comparison: PASS`, `risk_cases=500001`, `pressure_cases=500001`, `transition_cases=400000`.

These tests are distinct from the previously described 13 synthetic cases; they have separate historical provenance and are **not** a rerun of the policy replay.
