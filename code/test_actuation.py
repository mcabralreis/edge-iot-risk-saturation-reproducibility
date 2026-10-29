import csv,hashlib,json,tempfile
from pathlib import Path
from actuation import run,sha

def fixture(root):
 b=root/'bridge';b.mkdir();p=b/'policy_observations.csv'
 cols=['event_id','decision_ts','prior_bin_end','ddos_score','alarm_at_frozen_threshold']
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
  for i in range(191):
   for j in range(8):
    w.writerow(dict(event_id=f'{i}-{j}',decision_ts=i*60+j,prior_bin_end=i*60,ddos_score='0.999' if j<4 else '0.01',alarm_at_frozen_threshold=int(j<4)))
 m=dict(status='EXPLORATORY_REPLAY_EXPORTED_NOT_M3',D4_TEST_READ_OR_SCORED=False,policy_observations_sha256=sha(p),interval_lower_inclusive=0,interval_upper_exclusive=191*60,threshold_frozen=0.9978600094336023,rows=191*8)
 (b/'replay_manifest.json').write_text(json.dumps(m));return b

def test(binary):
 with tempfile.TemporaryDirectory() as td:
  root=Path(td);b=fixture(root)
  report=run(binary,b,root/'out',3,12,1)
  assert report['oracle_opened'] is False and report['d4_test_scored'] is False
  assert report['bins']==191 and report['rows_per_policy']==1528
  for r in report['results']:
   assert sum(r[k] for k in ('served','filter_denied','queue_overflow','censored_in_queue'))==1528
  assert len(set(x['policy'] for x in report['results']))==4
  try:run(binary,b,root/'out',3,12,1)
  except RuntimeError as e:assert 'PRESERVE_EXISTING_OUTPUT' in str(e)
  else:raise AssertionError('OVERWRITE_ALLOWED')
  p=b/'policy_observations.csv';s=p.read_text();p.write_text(s.replace('event_id,decision_ts','label,event_id,decision_ts',1))
  m=json.loads((b/'replay_manifest.json').read_text());m['policy_observations_sha256']=sha(p);(b/'replay_manifest.json').write_text(json.dumps(m))
  try:run(binary,b,root/'rejected',3,12,1)
  except RuntimeError as e:assert 'ORACLE_IN_POLICY_INPUT' in str(e)
  else:raise AssertionError('ORACLE_ACCEPTED')
  print('ACTUATION_TESTS=PASS')
  print('FOUR_POLICIES=PASS')
  print('CONSERVATION=PASS')
  print('SAME_EXOGENOUS_RECORDS=PASS')
  print('ORACLE_REJECTION=PASS')
  print('OVERWRITE_REJECTION=PASS')
  print('TEST_SCOPE=SYNTHETIC_FIXTURE_NOT_M3')
if __name__=='__main__':
 import sys;test(Path(sys.argv[1]))
