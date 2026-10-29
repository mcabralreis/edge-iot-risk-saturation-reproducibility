#!/usr/bin/env python3
"""Read-only post-hoc oracle evaluation of Actuation R1. Does not run controllers or modify outputs."""
import argparse,csv,hashlib,json,sqlite3,tempfile,collections,math
from pathlib import Path
POLICIES=('B2','P4','A1','B5'); STATUSES=('served','filter_denied','queue_overflow','censored_in_queue')
def need(x,msg):
 if not x:raise ValueError(msg)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def reader(p, required):
 f=p.open(newline='',encoding='utf-8-sig');r=csv.DictReader(f)
 need(set(required).issubset(r.fieldnames or []),f'INVALID_SCHEMA:{p.name}');return f,r
def run(bridge,act,out):
 need(not out.exists(),'PRESERVE_EXISTING_OUTPUT'); m=json.loads((bridge/'replay_manifest.json').read_text(encoding='utf-8-sig'));a=json.loads((act/'actuation_manifest.json').read_text(encoding='utf-8-sig'))
 need(m['status']=='EXPLORATORY_REPLAY_EXPORTED_NOT_M3' and a['status']=='EXPLORATORY_MODELED_ACTUATION_NOT_M3','SCOPE_MISMATCH')
 need(m['D4_TEST_READ_OR_SCORED'] is False and a['d4_test_scored'] is False and a['oracle_opened'] is False,'SOURCE_SCOPE_VIOLATION')
 need(a['source_input_sha256']==m['policy_observations_sha256'],'INPUT_LINEAGE_MISMATCH')
 need(a['rows_per_policy']==m['rows'],'ROW_EXPECTATION_MISMATCH')
 for filename,digest in a['outputs'].items():
  need(filename in ('actions.csv','summary.csv','terminal_ledger.csv'),'UNEXPECTED_OUTPUT');need(sha(act/filename)==digest,'ACTUATION_HASH_MISMATCH:'+filename)
 op=bridge/'SEALED_oracle_evaluation_only.csv';need(sha(op)==m['sealed_oracle_sha256'],'ORACLE_HASH_MISMATCH')
 out.mkdir(parents=True)
 # An SQLite index ensures one-to-one matching without loading the oracle/ledger in RAM.
 with tempfile.TemporaryDirectory(prefix='comnet_r2_') as tmp:
  db=sqlite3.connect(str(Path(tmp)/'join.db'));db.execute('PRAGMA journal_mode=OFF');db.execute('PRAGMA synchronous=OFF');db.execute('CREATE TABLE truth (eid TEXT PRIMARY KEY, class TEXT NOT NULL, kind TEXT NOT NULL) WITHOUT ROWID');db.execute('CREATE TABLE seen (policy TEXT NOT NULL, eid TEXT NOT NULL, PRIMARY KEY(policy,eid)) WITHOUT ROWID')
  f,r=reader(op,('event_id','label','type'));ntruth=0;truth_counts=collections.Counter()
  with f:
   batch=[]
   for row in r:
    eid=row['event_id'];lab=row['label'].strip();kind=row['type'].strip().lower();need(eid and lab in ('0','1') and kind,'INVALID_ORACLE_ROW')
    need((lab=='0')==(kind=='normal'),'LABEL_TYPE_CONFLICT')
    cls='normal' if lab=='0' else ('ddos' if kind=='ddos' else 'other_attack');batch.append((eid,cls,kind));truth_counts[cls]+=1;ntruth+=1
    if len(batch)>=50000:db.executemany('INSERT INTO truth VALUES(?,?,?)',batch);batch=[]
   if batch:db.executemany('INSERT INTO truth VALUES(?,?,?)',batch)
  need(ntruth==m['rows'],'ORACLE_ROW_COUNT_MISMATCH')
  counts=collections.Counter();totals=collections.Counter();seen_counts=collections.Counter();missing=0
  f,r=reader(act/'terminal_ledger.csv',('policy','event_id','decision_ts','terminal_status','completion_ts','ddos_score'))
  with f:
   for row in r:
    pol=row['policy'];eid=row['event_id'];status=row['terminal_status'];need(pol in POLICIES and status in STATUSES and eid,'BAD_LEDGER_ROW')
    hit=db.execute('SELECT class FROM truth WHERE eid=?',(eid,)).fetchone();need(hit is not None,'LEDGER_ID_NOT_IN_ORACLE:'+eid)
    try:db.execute('INSERT INTO seen VALUES(?,?)',(pol,eid))
    except sqlite3.IntegrityError:raise ValueError('DUPLICATE_POLICY_EVENT:'+pol+':'+eid)
    cls=hit[0];counts[(pol,cls,status)]+=1;totals[(pol,status)]+=1;seen_counts[pol]+=1
    t=float(row['decision_ts']);s=float(row['ddos_score']);need(math.isfinite(t) and math.isfinite(s) and 0<=s<=1,'BAD_LEDGER_NUMERIC')
    done=row['completion_ts'].strip()
    if status=='served':need(done and math.isfinite(float(done)) and float(done)>=t,'INVALID_COMPLETION_TS')
    else:need(not done,'NON_SERVED_WITH_COMPLETION_TS')
  for pol in POLICIES:
   need(seen_counts[pol]==ntruth,'POLICY_NOT_FULLY_COVERED:'+pol)
   s=next((x for x in a['results'] if x['policy']==pol),None);need(s is not None,'MISSING_SUMMARY:'+pol)
   for st in STATUSES:need(totals[(pol,st)]==s[st],'SUMMARY_MISMATCH:'+pol+':'+st)
  # Equal event sets follows from unique per-policy event IDs and each having N, all within oracle N.
  summary=[]
  for pol in POLICIES:
   d={'policy':pol,'rows':ntruth,'normal_total':truth_counts['normal'],'ddos_total':truth_counts['ddos'],'other_attack_total':truth_counts['other_attack']}
   for cls in ('normal','ddos','other_attack'):
    for st in STATUSES:d[cls+'_'+st]=counts[(pol,cls,st)]
   d['legitimate_served_fraction']=counts[(pol,'normal','served')]/truth_counts['normal'] if truth_counts['normal'] else None
   d['false_filter_denial_fraction']=counts[(pol,'normal','filter_denied')]/truth_counts['normal'] if truth_counts['normal'] else None
   d['ddos_served_fraction']=counts[(pol,'ddos','served')]/truth_counts['ddos'] if truth_counts['ddos'] else None
   summary.append(d)
  with (out/'class_outcomes.csv').open('w',newline='',encoding='utf-8') as f:
   w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
  f,r=reader(act/'actions.csv',('policy','bin_start','state','own_queue_pressure','filter','active_filter','remaining','observed_prior_mean_score'))
  actions={p:{} for p in POLICIES}
  with f:
   for row in r:
    p=row['policy'];b=int(row['bin_start']);need(p in actions and b not in actions[p],'DUPLICATE_OR_UNKNOWN_ACTION')
    actions[p][b]=row
  need(set(actions['P4'])==set(actions['A1']),'P4_A1_BIN_MISMATCH')
  differences=[];p_positive=0;max_pressure=0
  for b in sorted(actions['P4']):
   p=actions['P4'][b];q=actions['A1'][b];pressure=float(p['own_queue_pressure']);max_pressure=max(max_pressure,pressure);p_positive+=pressure>0
   changed=[k for k in ('state','filter','active_filter','remaining') if p[k]!=q[k]]
   if changed:differences.append(dict(bin_start=b,differing_fields=';'.join(changed),P4_state=p['state'],A1_state=q['state'],P4_filter=p['filter'],A1_filter=q['filter'],P4_pressure=p['own_queue_pressure'],A1_pressure=q['own_queue_pressure']))
  with (out/'p4_a1_differences.csv').open('w',newline='',encoding='utf-8') as f:
   w=csv.DictWriter(f,fieldnames=['bin_start','differing_fields','P4_state','A1_state','P4_filter','A1_filter','P4_pressure','A1_pressure']);w.writeheader();w.writerows(differences)
  report={'status':'POSTHOC_EXPLORATORY_ONLY_NOT_M3','oracle_access_stage':'AFTER_ACTUATION_SEPARATE_PROCESS','source_actuation_sha256':sha(act/'actuation_manifest.json'),'source_bridge_sha256':sha(bridge/'replay_manifest.json'),'source_oracle_sha256':sha(op),'rows_per_policy':ntruth,'truth_counts':dict(truth_counts),'policy_coverage':dict(seen_counts),'same_exact_oracle_event_set_each_policy':True,'p4_a1':{'compared_bins':len(actions['P4']),'positive_P4_queue_pressure_bins':p_positive,'max_P4_queue_pressure':max_pressure,'different_action_or_remaining_bins':len(differences)},'output_hashes':{f:sha(out/f) for f in ('class_outcomes.csv','p4_a1_differences.csv')},'limitations':['D6 validation region reused: exploratory only','unit-size records; uncalibrated capacity/queue; not Mbps or measured latency','static-ELEVATED proxy B2; score-gate filtering proxy; B5 delay sensitivity only','no causal identification of P4 effect from this single replay']}
  (out/'posthoc_manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,sort_keys=True));return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--bridge',type=Path,required=True);p.add_argument('--actuation',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();run(a.bridge,a.actuation,a.out)
