#!/usr/bin/env python3
"""Export D6 exploratory development-validation observations, with a sealed oracle.

No D4 test time, no model fitting, no treatment simulation, no online claim.
Use only locally generated/trusted joblib. D6 functions are imported verbatim.
"""
import argparse,csv,hashlib,io,json,math,sys,zipfile
from pathlib import Path
import joblib


def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def export(root,lock_file,model_file,out,d6,allow_noncanonical=False):
 root,lock_file,model_file,out=map(Path,(root,lock_file,model_file,out))
 if out.exists():raise RuntimeError('PRESERVE_EXISTING_OUTPUT '+str(out))
 archive=root/'source_downloads'/'Processed_Network_dataset.zip'
 lock=json.loads(lock_file.read_text(encoding='utf-8-sig'))
 digest=sha(archive)
 if digest!=lock['source_sha256'] or (not allow_noncanonical and digest!=d6.EXPECTED):raise RuntimeError('SOURCE_SHA_MISMATCH')
 edges=lock['split_edges'];purge=int(lock['purge_seconds']);upper=edges[2]-purge
 if not(len(edges)==4 and edges[0]<edges[1]-purge<edges[1]+purge<upper<edges[2]):raise RuntimeError('BAD_SPLIT')
 # trusted local D6 joblib only. No model fit or threshold adjustment.
 obj=joblib.load(model_file)
 if set(('model','hasher','threshold','protocol'))-set(obj):raise RuntimeError('BAD_D6_MODEL_ARTIFACT')
 if obj['protocol'].get('upper_exclusive')!=upper or obj['protocol'].get('d4_edges')!=edges:raise RuntimeError('MODEL_SPLIT_MISMATCH')
 windows,_=d6.inventory(archive,edges,purge)
 out.mkdir(parents=True)
 inputs=out/'policy_observations.csv';oracle=out/'SEALED_oracle_evaluation_only.csv'
 columns=['event_id','event_ts','decision_ts','prior_bin_start','prior_bin_end','prior_bin_n','proto','dst_port','ddos_score','alarm_at_frozen_threshold','model_scope']
 N=0; counts={}; last_ts=None
 with inputs.open('w',newline='',encoding='utf-8') as fo,oracle.open('w',newline='',encoding='utf-8') as ft:
  wo=csv.DictWriter(fo,fieldnames=columns);wt=csv.DictWriter(ft,fieldnames=['event_id','label','type']);wo.writeheader();wt.writeheader()
  with zipfile.ZipFile(archive) as z:
   batch=[];meta=[]
   def flush():
    nonlocal N,last_ts
    if not batch:return
    prob=obj['model'].predict_proba(obj['hasher'].transform(batch))[:,1]
    if len(prob)!=len(meta):raise RuntimeError('SCORE_COUNT_MISMATCH')
    for (eid,t,r,prior,prior_n),score in zip(meta,prob):
     if not math.isfinite(float(score)) or not 0<=float(score)<=1:raise RuntimeError('BAD_SCORE')
     wo.writerow({'event_id':eid,'event_ts':format(t,'.9f'),'decision_ts':format(t,'.9f'),
       'prior_bin_start':prior,'prior_bin_end':prior+60,'prior_bin_n':prior_n,
       'proto':d6.proto(r.get('proto')),'dst_port':d6.port(r.get('dst_port')),
       'ddos_score':format(float(score),'.17g'),'alarm_at_frozen_threshold':int(float(score)>=float(obj['threshold'])),
       'model_scope':'D6_EXPLORATORY_SAME_CAMPAIGN_NOT_VALIDATED'})
     wt.writerow({'event_id':eid,'label':r.get('label',''),'type':r.get('type','')})
     N+=1;last_ts=t
    batch.clear();meta.clear()
   # All raw rows are eligible: do not select by type or label before policy observation.
   for name,idx,t,r in d6.each_row(z,upper):
    if d6.split(t,edges,purge)!='validation':continue
    eid=hashlib.sha256((name+'::'+str(idx)).encode()).hexdigest()[:24]
    prior=d6.bin_id(t)-60
    if prior+60>t:raise RuntimeError('FUTURE_FEATURE')
    w=windows.get(prior);prior_n=w['n'] if w else 0
    batch.append(d6.features(r,t,windows));meta.append((eid,t,r,prior,prior_n))
    if len(batch)>=10000:flush()
   flush()
 if not N:raise RuntimeError('EMPTY_VALIDATION')
 manifest={'status':'EXPLORATORY_REPLAY_EXPORTED_NOT_M3','input_source_sha256':digest,'d4_lock_sha256':sha(lock_file),
 'd6_model_sha256':sha(model_file),'threshold_frozen':float(obj['threshold']),'rows':N,
 'interval_lower_inclusive':edges[1]+purge,'interval_upper_exclusive':upper,
 'D4_TEST_READ_OR_SCORED':False,'policy_observations_sha256':sha(inputs),'sealed_oracle_sha256':sha(oracle),
 'scope':'flow-record observation proxy; not per-packet causal attribution, not measured 5G/NR, no policy efficacy',
 'important':'ALL traffic types exported without oracle filtering; oracle CSV must be inaccessible to the policies. A held-out independent campaign is still required for confirmatory detector validation.'}
 (out/'replay_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
 return manifest

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--d4-lock',required=True);p.add_argument('--d6-model',required=True);p.add_argument('--d6-script',required=True);p.add_argument('--out',required=True)
 a=p.parse_args();import importlib.util
 spec=importlib.util.spec_from_file_location('d6_original',a.d6_script);d6=importlib.util.module_from_spec(spec);spec.loader.exec_module(d6)
 m=export(a.root,a.d4_lock,a.d6_model,a.out,d6)
 print('BRIDGE_STATUS='+m['status']);print('ROWS='+str(m['rows']));print('D4_TEST_READ_OR_SCORED=NO');print('OUTPUT='+str(a.out))
if __name__=='__main__':main()
