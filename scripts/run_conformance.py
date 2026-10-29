#!/usr/bin/env python3
"""Build and run software-level checks; does NOT regenerate the policy replay."""
from pathlib import Path
import shutil,subprocess,sys
R=Path(__file__).resolve().parents[1]
C=R/'code'
cc=shutil.which('g++') or shutil.which('clang++')
if not cc:raise SystemExit('CXX_COMPILER_NOT_FOUND: install g++/clang++ and retry')
out=R/'build';out.mkdir(exist_ok=True)
suffix='.exe' if sys.platform=='win32' else ''
cmd0=[cc,'-std=c++17','-O2','-I'+str(C/'include'),str(C/'security-orchestrator.cc')]
for key,source in [('interface_test','security-orchestrator-interface-test-gate8ar.cc'),('reference_test','security-orchestrator-reference-comparison-gate8ar.cc'),('controller_stream','controller_stream.cc')]:
 target=out/(key+suffix)
 print('COMPILING='+key,flush=True)
 subprocess.run(cmd0+[str(C/source),'-o',str(target)],check=True)
 if key!='controller_stream':
  print('RUNNING='+key,flush=True)
  subprocess.run([str(target)],check=True)
print('CONTROLLER_COMPILATION=PASS')
print('SOFTWARE_CONFORMANCE_TESTS=PASS')
print('ORIGINAL_POLICY_REPLAY_EXECUTED=NO')
