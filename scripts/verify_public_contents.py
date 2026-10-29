#!/usr/bin/env python3
"""Conservative, read-only prepublication checks. A PASS is NOT legal approval."""
from pathlib import Path
import sys
root = Path(__file__).resolve().parents[1]
issues = []
scanned = 0
for file in sorted(root.rglob('*')):
    if not file.is_file():
        continue
    rel = file.relative_to(root).as_posix()
    scanned += 1
    fn = file.name.lower()
    if (fn.endswith(('.joblib','.pkl','.pickle','.pdf','.tex','.exe','.dll','.pyc'))
        or fn in {'policy_observations.csv','terminal_ledger.csv','processed_network_dataset.zip'}
        or '__pycache__' in file.parts or '.venv' in file.parts):
        issues.append(f'DISALLOWED_FILE={rel}')
    try:
        txt = file.read_text(encoding='utf-8') if file.stat().st_size < 5_000_000 else ''
    except (UnicodeError, OSError):
        continue
    if file.resolve() == Path(__file__).resolve():
        continue  # scanner code itself embeds the prohibited-path signatures
    for phrase in ('C:\\Users\\', '/home/manuel/', '/mnt/c/Users/'):
        if phrase.lower() in txt.lower():
            issues.append(f'POSSIBLE_PRIVATE_PATH={rel}')
print('===== REPOSITORY READ-ONLY CONTENT CHECK =====')
print(f'FILES_SCANNED={scanned}')
print(f'ISSUES_FOUND={len(issues)}')
for item in issues[:30]:print(item)
print('NO_MANUSCRIPT_OR_RESTRICTED_BINARY_FILE=' + ('YES' if not issues else 'REVIEW_REQUIRED'))
print('LEGAL_AND_PUBLIC_RELEASE_APPROVED=NO')
print('ORIGINAL_SCIENTIFIC_FILES_MODIFIED=NO')
sys.exit(1 if issues else 0)
