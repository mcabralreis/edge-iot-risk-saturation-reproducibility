#!/usr/bin/env python3
"""Read-only, bounded post-hoc inspection of P4/A1 positive-pressure windows.
No oracle, no model fitting, no simulation, no invocation of the controller.
"""
import argparse,csv,hashlib,json,math,re
from collections import Counter
from pathlib import Path

TH={'recovery':.20,'elevated':.40,'critical':.75,'recovery_windows':3}
REQUIRED={'policy','bin_start','observed_prior_count','observed_prior_mean_score','own_queue_pressure','state','filter','active_filter','arrivals','accepted','filter_denied','overflow','served','remaining'}
COMPARE=('state','filter','active_filter','remaining','accepted','filter_denied','overflow','served')

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def need(c,msg):
 if not c:raise RuntimeError(msg)
def num(x):
 z=float(x);need(math.isfinite(z),'NONFINITE_NUMBER');return z

def analyze(actions,manifest,source,out,expected=23):
 need(not out.exists(),'OUTPUT_ALREADY_EXISTS_PRESERVE_EVIDENCE')
 m=json.loads(manifest.read_text(encoding='utf-8-sig'))
 need(m['status']=='EXPLORATORY_MODELED_ACTUATION_NOT_M3','BAD_ACTUATION_SCOPE')
 need(sha(actions)==m['outputs']['actions.csv'],'ACTIONS_SHA256_MISMATCH')
 need(m['rows_per_policy']==1354253 and m['bins']==191,'UNEXPECTED_ORIGINAL_REPLAY')
 src=source.read_text(encoding='utf-8-sig')
 # Verify the cited threshold and neutralization contract against the provided, fixed source.
 need(bool(re.search(r'OrchestratorThresholds\s+th\s*\{\s*\.20\s*,\s*\.40\s*,\s*\.75\s*,\s*\.20\s*,\s*\.40\s*,\s*\.75\s*,\s*3\s*\}',src)),'CONTROLLER_SOURCE_THRESHOLDS_NOT_MATCHED')
 need('if(policy=="A1")' in src and 'o.queuePressure=0' in src and 'o.latencyPressure=0' in src and 'o.securityProcessingPressure=0' in src,'A1_CONTRACT_NOT_MATCHED')
 rows={'P4':{},'A1':{}};npol=Counter()
 with actions.open(newline='',encoding='utf-8-sig') as f:
  rd=csv.DictReader(f);need(REQUIRED.issubset(rd.fieldnames or []),'ACTIONS_SCHEMA_MISMATCH')
  for r in rd:
   p=r['policy'];npol[p]+=1
   if p not in rows:continue
   b=int(r['bin_start']);need(b not in rows[p],'DUPLICATE_BIN_'+p)
   rows[p][b]=r
 need(npol=={'B2':191,'P4':191,'A1':191,'B5':191},'POLICY_COUNTS_UNEXPECTED')
 need(set(rows['P4'])==set(rows['A1']),'BIN_SET_MISMATCH')
 positives=[];any_diffs=[];bins=sorted(rows['P4']);classification=Counter();profile=Counter()
 for b in bins:
  p=rows['P4'][b];a=rows['A1'][b]
  risk=num(p['observed_prior_mean_score']);pr=num(p['own_queue_pressure'])
  need(0<=risk<=1 and 0<=pr<=1,'OUT_OF_RANGE')
  need(abs(risk-num(a['observed_prior_mean_score']))<1e-12,'RISK_STREAM_DIFFERS')
  need(p['observed_prior_count']==a['observed_prior_count'],'PRIOR_COUNT_DIFFERS')
  changed=[k for k in COMPARE if p[k]!=a[k]]
  if changed:any_diffs.append((b,changed))
  if pr<=0:continue
  critical_risk=risk>=TH['critical'];elevated_risk=risk>=TH['elevated']
  critical_pressure=pr>=TH['critical'];elevated_pressure=pr>=TH['elevated']
  if critical_risk:
   category='RISK_ALREADY_CRITICAL_PRESSURE_CANNOT_RAISE_TRIGGER_LEVEL'
  elif not elevated_pressure:
   category='PRESSURE_BELOW_ELEVATION_THRESHOLD'
  elif elevated_risk and not critical_pressure:
   category='RISK_ALREADY_ELEVATED_PRESSURE_ADDS_NO_HIGHER_THRESHOLD'
  elif critical_pressure:
   category='PRESSURE_CRITICAL_TRIGGER_CHECK_HYSTERESIS_AND_STATE'
  else:
   category='PRESSURE_ELEVATED_WITHOUT_EQUIVALENT_RISK_TRIGGER_CHECK_STATE_HISTORY'
  classification[category]+=1;profile[(p['state'],a['state'],p['filter'],a['filter'])]+=1
  positives.append(dict(bin_start=b,risk_previous_completed_bin=format(risk,'.17g'),P4_pressure_prior_queue=format(pr,'.17g'),A1_pressure_used_by_controller='0',risk_ge_elevated=int(elevated_risk),risk_ge_critical=int(critical_risk),pressure_ge_elevated=int(elevated_pressure),pressure_ge_critical=int(critical_pressure),P4_state=p['state'],A1_state=a['state'],P4_filter=p['filter'],A1_filter=a['filter'],P4_active_filter=p['active_filter'],A1_active_filter=a['active_filter'],P4_remaining=p['remaining'],A1_remaining=a['remaining'],P4_arrivals=p['arrivals'],A1_arrivals=a['arrivals'],different_fields=';'.join(changed),threshold_exposure_category=category))
 need(len(positives)==expected,'POSITIVE_PRESSURE_COUNT_NOT_EXPECTED:'+str(len(positives)))
 need(not any_diffs,'P4_A1_DIFFERENCES_FOUND_REQUIRES_NEW_ADJUDICATION')
 need(max(num(r['P4_pressure_prior_queue']) for r in positives)<=2/3+1e-12,'MAX_PRESSURE_UNEXPECTED')
 out.mkdir(parents=True)
 outcsv=out/'positive_pressure_23_windows.csv'
 with outcsv.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(positives[0]));w.writeheader();w.writerows(positives)
 report={'status':'READ_ONLY_23_POSITIVE_PRESSURE_WINDOWS_ANALYZED','scope':'One already-executed exploratory actuation replay; no new policy run, no oracle, no test, no inference of general no-effect','source_actions_sha256':sha(actions),'source_manifest_sha256':sha(manifest),'source_controller_stream_sha256':sha(source),'controller_development_thresholds':TH,'rows_per_policy':dict(npol),'total_decision_bins':len(bins),'positive_pressure_bins':len(positives),'max_positive_pressure':max(num(r['P4_pressure_prior_queue']) for r in positives),'different_P4_A1_bins_all':len(any_diffs),'threshold_exposure_categories':dict(classification),'observed_state_filter_profile_pairs':[{'P4_state':k[0],'A1_state':k[1],'P4_filter':k[2],'A1_filter':k[3],'n':v} for k,v in sorted(profile.items())],'output_sha256':{'positive_pressure_23_windows.csv':sha(outcsv)},'caution':'Threshold categories are sufficient-condition/descriptive classifications, not independent causal attribution; state history/hysteresis can be involved; equal states imply equal ActionProfile in this deterministic controller.'}
 (out/'analysis_23_windows.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print('STATUS='+report['status']);print('POSITIVE_PRESSURE_BINS='+str(len(positives)));print('P4_A1_DIFFERENT_BINS='+str(len(any_diffs)));print('CATEGORY_COUNTS='+json.dumps(dict(classification),sort_keys=True));print('OUTPUT='+str(out))
 return report
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--actions',required=True,type=Path);ap.add_argument('--manifest',required=True,type=Path);ap.add_argument('--controller-source',required=True,type=Path);ap.add_argument('--out',required=True,type=Path);x=ap.parse_args();analyze(x.actions,x.manifest,x.controller_source,x.out)
