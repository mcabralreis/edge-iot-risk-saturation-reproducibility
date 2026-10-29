import csv,hashlib,json,tempfile
from pathlib import Path
from analyze_23_windows import analyze,sha
src=Path(__file__).with_name('controller_stream_original.cc')
with tempfile.TemporaryDirectory() as td:
 d=Path(td); act=d/'actions.csv';man=d/'actuation_manifest.json';out=d/'report'
 fields=['policy','bin_start','observed_prior_count','observed_prior_mean_score','own_queue_pressure','state','filter','active_filter','arrivals','accepted','filter_denied','overflow','served','remaining']
 with act.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for pol in ('B2','P4','A1','B5'):
   for i in range(191):
    w.writerow(dict(policy=pol,bin_start=1000+i*60,observed_prior_count=100,observed_prior_mean_score=.99,own_queue_pressure=(2/3 if i<23 else 0),state='CRITICAL',filter='QUARANTINE_AND_STRICT_TOKEN_BUCKET',active_filter=1,arrivals=100,accepted=10,filter_denied=90,overflow=0,served=10,remaining=0))
 man.write_text(json.dumps(dict(status='EXPLORATORY_MODELED_ACTUATION_NOT_M3',rows_per_policy=1354253,bins=191,outputs={'actions.csv':sha(act)})))
 r=analyze(act,man,src,out)
 assert r['positive_pressure_bins']==23 and r['different_P4_A1_bins_all']==0
 assert r['threshold_exposure_categories']=={'RISK_ALREADY_CRITICAL_PRESSURE_CANNOT_RAISE_TRIGGER_LEVEL':23}
 try:analyze(act,man,src,out)
 except RuntimeError as e: assert 'OUTPUT_ALREADY_EXISTS' in str(e)
 else:raise AssertionError('overwrite not rejected')
 act.write_text(act.read_text()+'\n')
 try:analyze(act,man,src,d/'modified')
 except RuntimeError as e:assert 'SHA256_MISMATCH' in str(e)
 else:raise AssertionError('tampering not rejected')
 print('TEST=PASS synthetic 191 bins / 23 positive / 4 policies')
 print('TEST=PASS original-source thresholds and neutralization')
 print('TEST=PASS no overwrite; action-tamper SHA rejection')
