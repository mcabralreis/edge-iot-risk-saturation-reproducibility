#!/usr/bin/env python3
"""D6: exploratory lagged-window ToN-IoT detector. Never touches D4 held-out region.
Labels are used exclusively for supervised targets and validation reporting, not features.
"""
import argparse, csv, hashlib, io, json, math, re, zipfile
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from sklearn.feature_extraction import FeatureHasher
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import roc_auc_score, average_precision_score
import joblib

EXPECTED='b024574780da5db96adf255c0a2effa71e1c31173d34eaaa80fbd4edc1b9010e'
SEED=20261002

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def ordered(z):
 n=[s for s in z.namelist() if re.search(r'/Network_dataset_\d+\.csv$',s)]
 return sorted(n,key=lambda s:int(re.search(r'Network_dataset_(\d+)',s).group(1)))

def port(s):
 try:
  v=float(s)
  return str(int(v)) if math.isfinite(v) and v.is_integer() and 0<=v<=65535 else 'missing'
 except (TypeError,ValueError,OverflowError):return 'missing'

def proto(s):return (s or 'missing').strip().lower() or 'missing'
def ts_of(r):
 try:
  t=float(r['ts']); return t if math.isfinite(t) else None
 except (KeyError,TypeError,ValueError):return None

def split(t,edges,purge):
 if edges[0]<=t<edges[1]-purge:return 'train'
 if edges[1]+purge<=t<edges[2]-purge:return 'validation'
 return None

def each_row(z,upper):
 """Read only CSVs with data earlier than upper, refuse to yield rows at/after upper.
 Physical archive may be scanned beyond upper inside boundary file; those rows are discarded
 without label or feature access. Output does not evaluate prior D4 test range.
 """
 for name in ordered(z):
  with z.open(name) as f:
   reader=csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig',errors='replace',newline=''))
   for ix,r in enumerate(reader):
    t=ts_of(r)
    if t is None or t>=upper:continue
    yield name,ix,t,r

def bin_id(t):return int(t//60)*60

def inventory(archive,edges,purge):
 windows=defaultdict(lambda: {'n':0,'protocol':Counter(),'port':Counter(),'pair':Counter(),'src':set(),'dst':set()})
 counters=Counter()
 upper=edges[2]-purge
 with zipfile.ZipFile(archive) as z:
  for name,ix,t,r in each_row(z,upper):
   k=bin_id(t); w=windows[k]; p=proto(r.get('proto')); d=port(r.get('dst_port'))
   w['n']+=1;w['protocol'][p]+=1;w['port'][d]+=1;w['pair'][(p,d)]+=1
   # Store unique addresses only in transient memory; never encode their literal values as features.
   if r.get('src_ip'):w['src'].add(r['src_ip'])
   if r.get('dst_ip'):w['dst'].add(r['dst_ip'])
   counters['observed_rows_before_validation_end']+=1
 return windows,counters

def features(r,t,windows):
 p=proto(r.get('proto'));d=port(r.get('dst_port'))
 prev=windows.get(bin_id(t)-60); out={'proto='+p:1.,'dst_port='+d:1.,'pair='+p+'/'+d:1.}
 if prev:
  n=prev['n'];
  numeric={'lag_total_rate':n/60., 'lag_proto_rate':prev['protocol'][p]/60.,
           'lag_port_rate':prev['port'][d]/60.,'lag_pair_rate':prev['pair'][(p,d)]/60.,
           'lag_unique_src':len(prev['src']), 'lag_unique_dst':len(prev['dst']),
           'lag_pair_fraction':prev['pair'][(p,d)]/max(1,n),
           'lag_src_concentration':n/max(1,len(prev['src']))}
  for key,v in numeric.items():out[key]=math.log1p(v)/10.
  out['lag_exists']=1.
 else:out['lag_missing']=1.
 return out

def metrics(y,score,threshold):
 yp=score>=threshold;neg=(y==0);pos=~neg
 tn=int(np.sum(~yp&neg));fp=int(np.sum(yp&neg));fn=int(np.sum(~yp&pos));tp=int(np.sum(yp&pos))
 f1pos=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.
 f1neg=2*tn/(2*tn+fp+fn) if 2*tn+fp+fn else 0.
 return {'tn':tn,'fp':fp,'fn':fn,'tp':tp,'fpr':fp/(tn+fp) if tn+fp else None,
         'recall_ddos':tp/(tp+fn) if tp+fn else None,'macro_f1':(f1pos+f1neg)/2}

def pick_threshold(y,score):
 # All distinct score groups are evaluated exactly, never a coarse fixed grid.
 order=np.argsort(-score,kind='stable');s=score[order]; yy=y[order]
 ends=np.r_[np.flatnonzero(np.diff(s)!=0),len(s)-1]
 tp=np.cumsum(yy,dtype=np.int64)[ends]; fp=(ends+1)-tp
 npos=int(y.sum());nneg=len(y)-npos
 fpr=fp/nneg;fn=npos-tp;tn=nneg-fp
 f1p=np.divide(2*tp,2*tp+fp+fn,out=np.zeros_like(tp,dtype=float),where=(2*tp+fp+fn)!=0)
 f1n=np.divide(2*tn,2*tn+fp+fn,out=np.zeros_like(tp,dtype=float),where=(2*tn+fp+fn)!=0)
 mf=(f1p+f1n)/2
 allowed=np.flatnonzero(fpr<=.05)
 # also permit predict-none with threshold above max, to expose genuinely infeasible model
 m0=metrics(y,score,float(np.nextafter(s[0],np.inf)))
 if len(allowed):
  best=allowed[np.argmax(mf[allowed])];threshold=float(s[ends[best]])
  mm=metrics(y,score,threshold)
  if mm['macro_f1']<m0['macro_f1']:return float(np.nextafter(s[0],np.inf)),m0
  return threshold,mm
 return float(np.nextafter(s[0],np.inf)),m0

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--d4-lock',required=True);ap.add_argument('--out',required=True);ap.add_argument('--allow-noncanonical-source',action='store_true',help='ONLY for isolated synthetic self-tests');args=ap.parse_args()
 archive=Path(args.root)/'source_downloads'/'Processed_Network_dataset.zip';out=Path(args.out)
 if out.exists():raise RuntimeError('PRESERVE_EXISTING_OUTPUT: '+str(out))
 if not archive.is_file():raise RuntimeError('ARCHIVE_MISSING')
 with open(args.d4_lock,encoding='utf-8-sig') as f: lock=json.load(f)
 edges=lock['split_edges'];purge=int(lock['purge_seconds']); upper=edges[2]-purge
 digest=sha(archive)
 if not args.allow_noncanonical_source and (digest!=EXPECTED or digest!=lock['source_sha256']):raise RuntimeError('SOURCE_SHA_MISMATCH')
 if len(edges)!=4 or not edges[0]<edges[1]-purge<edges[1]+purge<upper<edges[2]+purge:raise RuntimeError('BAD_SPLIT')
 windows,allcounts=inventory(archive,edges,purge)
 fh=FeatureHasher(n_features=8192,input_type='dict',alternate_sign=False)
 model=SGDClassifier(loss='log_loss',alpha=.0001,random_state=SEED,average=True)
 seen=False;batchx=[];batchy=[];val_groups=Counter();counts=Counter()
 def flush():
  nonlocal batchx,batchy,seen
  if batchy:
   xx=fh.transform(batchx);yy=np.asarray(batchy,dtype=np.int8)
   if not seen:model.partial_fit(xx,yy,classes=np.array([0,1],dtype=np.int8));seen=True
   else:model.partial_fit(xx,yy)
   batchx=[];batchy=[]
 # second pass. Fit only on development train, count development validation.
 with zipfile.ZipFile(archive) as z:
  for name,idx,t,r in each_row(z,upper):
   typ=(r.get('type') or '').strip().lower()
   if typ not in ('normal','ddos'):continue
   part=split(t,edges,purge)
   if part is None:continue
   y=int(typ=='ddos');counts[part+'_'+typ]+=1
   if part=='train':
    if y and idx%10:continue
    batchx.append(features(r,t,windows));batchy.append(y);counts['train_used_'+typ]+=1
    if len(batchy)>=10000:flush()
   elif part=='validation':val_groups[bin_id(t)]+=1
  flush()
 if not seen or counts['train_used_normal']<100 or counts['train_used_ddos']<100:raise RuntimeError('INSUFFICIENT_TRAIN_CLASSES')
 # Third pass: training is complete, score only development validation in bounded chunks.
 valy=[];valp=[];vx=[];vy=[]
 def val_flush():
  nonlocal vx,vy
  if vy:
   valp.extend(model.predict_proba(fh.transform(vx))[:,1].tolist());valy.extend(vy);vx=[];vy=[]
 with zipfile.ZipFile(archive) as z:
  for name,idx,t,r in each_row(z,upper):
   if split(t,edges,purge)!='validation':continue
   typ=(r.get('type') or '').strip().lower()
   if typ not in ('ddos','normal'):continue
   vx.append(features(r,t,windows));vy.append(int(typ=='ddos'))
   if len(vy)>=20000:val_flush()
  val_flush()
 if not valy or len(set(valy))<2:raise RuntimeError('INSUFFICIENT_VALIDATION_CLASSES')
 y=np.asarray(valy,dtype=np.int8);prob=np.asarray(valp,dtype=float)
 threshold,report=pick_threshold(y,prob)
 report.update({'n':int(len(y)), 'criterion_met':bool(report['macro_f1']>=.8 and report['fpr']<=.05),
                'roc_auc_descriptive':float(roc_auc_score(y,prob)),
                'average_precision_descriptive':float(average_precision_score(y,prob)),
                'distinct_score_groups':int(len(np.unique(prob))),'threshold':threshold})
 result={'status':'EXPLORATORY_DEVELOPMENT_ONLY', 'archive_sha256':digest,
  'protocol':{'features':'proto,dst_port and strictly previous completed 60-s raw-traffic aggregates; no label features',
    'decision_time':'record ts; prior-window aggregation with end <= floor(ts/60)*60',
    'd4_edges':edges,'embargo_seconds':purge,'upper_exclusive':upper,
    'd4_heldout_test_not_scored':True, 'same_campaign_and_validation_previously_opened':True,
    'trained_model':'SGDClassifier one streaming pass, FeatureHasher 8192, all normal + 1/10 DDoS training rows',
    'threshold':'exact distinct validation-score groups under FPR <= 0.05; no test use'},
  'counts':dict(counts), 'validation_windows':len(val_groups),'aggregate_windows':len(windows),'validation':report}
 out.mkdir(parents=True)
 (out/'d6_development_report.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 joblib.dump({'model':model,'hasher':fh,'threshold':threshold,'protocol':result['protocol']},out/'d6_exploratory_model.joblib')
 print('D6_STATUS=EXPLORATORY_DEVELOPMENT_COMPLETE');print('D4_TEST_SCORED=NO');print('VALIDATION_MACRO_F1=',report['macro_f1']);print('VALIDATION_FPR=',report['fpr']);print('VALIDATION_RECALL=',report['recall_ddos']);print('VALIDATION_CRITERION_MET=',report['criterion_met']);print('OUTPUT=',out)
if __name__=='__main__':main()
