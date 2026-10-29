#!/usr/bin/env python3
"""Independent bridge integrity audit. Never supplies the oracle to a policy."""
import argparse,csv,hashlib,json,math
from pathlib import Path

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def audit(out):
 out=Path(out);manifest=json.loads((out/'replay_manifest.json').read_text());o=out/'policy_observations.csv';q=out/'SEALED_oracle_evaluation_only.csv'
 assert sha(o)==manifest['policy_observations_sha256'] and sha(q)==manifest['sealed_oracle_sha256']
 seen=set();n=0
 with o.open(newline='',encoding='utf-8') as f:
  r=csv.DictReader(f);assert not set(['label','type','ground_truth','kind'])&set(r.fieldnames)
  for x in r:
   eid=x['event_id'];assert eid not in seen;seen.add(eid)
   t=float(x['decision_ts']);assert float(x['prior_bin_end'])<=t
   assert manifest['interval_lower_inclusive']<=t<manifest['interval_upper_exclusive']
   score=float(x['ddos_score']);assert math.isfinite(score) and 0<=score<=1
   assert int(x['alarm_at_frozen_threshold'])==int(score>=manifest['threshold_frozen']);n+=1
 nq=0
 with q.open(newline='',encoding='utf-8') as f:
  for x in csv.DictReader(f):assert x['event_id'] in seen;nq+=1
 assert n==nq==manifest['rows'] and not manifest['D4_TEST_READ_OR_SCORED']
 return {'status':'PASS','rows':n,'no_oracle_in_policy_file':True,'prior_window_causal':True,'score_reconciled':True,'artifact_hashes_match':True}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();print(json.dumps(audit(a.out),sort_keys=True))
