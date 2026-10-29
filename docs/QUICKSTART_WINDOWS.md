# Windows 11 / PowerShell quick start

Use a **new working folder**, not the original scientific OneDrive tree.

1. Extract `edge-iot-risk-saturation-reproducibility.zip` to `Downloads` (or your preferred projects folder).
2. Open PowerShell in the extracted directory (the folder containing `verify_191bins.py`).
3. Verify archived results with:

```powershell
py -3 verify_191bins.py
```

This requires only Python 3.10+ and **does not access the raw ToN_IoT archive**.

For optional tests, set up an isolated environment (do not use the project's original virtual environment):

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-optional.txt
.\.venv\Scripts\python.exe code\test_23_windows.py
.\.venv\Scripts\python.exe code\test_bridge.py
```

To compile the controller on Windows, first install a C++17-compatible `g++` or `clang++` (for example via a trusted MinGW-w64/MSYS2 toolchain) and ensure it is on PATH, then:

```powershell
py -3 scripts\run_conformance.py
py -3 code\test_actuation.py build\controller_stream.exe
```

**Do not execute the original research replays to run these checks.** The three Python tests use synthetic fixtures; the C++ tests check software behavior only.

To discover which historical large inputs may still exist **locally**, without copying their contents (optional; scans many files):

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\find_missing_local_artifacts.ps1
```

The discovery command can print full personal file paths. Review its output before sharing it.

## Create a private GitHub repository (after final content review)

If Git and GitHub CLI (`gh`) are installed, from the repository root:

```powershell
git init -b main
git add .
git status --short
git commit -m "Initial bounded reproducibility release"
gh auth login
gh repo create edge-iot-risk-saturation-reproducibility --private --source . --remote origin --push
```

The `--private` flag intentionally creates a **private** repository so that the author can review its contents before explicitly making it public. Do not run `gh repo create` until you want a repository on your own GitHub account. The account URL is not known in advance and must not be invented.

After checking repository permissions, MIT scope, source artefacts and public-scope statements, make the repository public manually in GitHub Settings, if desired. An optional public tagged release can subsequently be archived with Zenodo for a software DOI.


## Compact R6 smoke-check

For a concise report, run `scripts/DiscoverIoT_REPO_R6_SMOKE_READONLY.ps1` with PowerShell from any working folder. This verifies the extracted package and executes only the independent 191-bin archive check; it does **not** execute a scientific replay.

## MIT licence

The original project code is MIT licensed. See `LICENSE` and `LICENSE_SCOPE.md`.
This is **not** a licence for the third-party dataset or for every archived
experimental-evidence record. The initial GitHub repository should be private.
