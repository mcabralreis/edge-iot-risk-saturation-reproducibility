#!/usr/bin/env python3
"""Exploratory flow-record service fixture. No oracle access, no 5G or detector-validation claim."""
import argparse,csv,hashlib,json,math,subprocess
from collections import defaultdict,deque
from pathlib import Path
POLICIES=('B2','P4','A1','B5')
FIELDS=('tick','state','counter','risk','pressure','filter','traffic','edge','cadence')
FILTERS={'AUTHENTICATION_REJECTION_ONLY':0.0,'SOURCE_TOKEN_BUCKET':0.9978600094336023,'QUARANTINE_AND_STRICT_TOKEN_BUCKET':0.9978600094336023,'CONSERVATIVE_RESIDUAL_FILTERING':0.9978600094336023}
# These actions are explicitly toy-proxy semantics, NOT implementations of token buckets/crypto.
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def require(cond,message):
 if not cond:raise RuntimeError(message)
class Controller:
 def __init__(self,binary,policy):
  self.p=subprocess.Popen([str(Path(binary).resolve()),policy],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,bufsize=1)
  require(self.p.stdout.readline().strip()==','.join(FIELDS),'CONTROLLER_HEADER_MISMATCH')
 def step(self,t,obs):
  self.p.stdin.write(' '.join(map(str,(t,*obs)))+'\n');self.p.stdin.flush()
  row=self.p.stdout.readline().strip().split(',')
  require(len(row)==len(FIELDS),'CONTROLLER_STEP_FAILED')
  return dict(zip(FIELDS,row))
 def close(self):
  self.p.stdin.close();require(self.p.wait()==0,'CONTROLLER_EXIT_FAILED');self.p.stdout.close()
def read_input(bridge):
 m=json.loads((bridge/'replay_manifest.json').read_text(encoding='utf-8-sig'))
 require(m['status']=='EXPLORATORY_REPLAY_EXPORTED_NOT_M3' and m['D4_TEST_READ_OR_SCORED'] is False,'BRIDGE_SCOPE')
 p=bridge/'policy_observations.csv';require(sha(p)==m['policy_observations_sha256'],'INPUT_SHA_MISMATCH')
 bins=defaultdict(list);last=None;ids=set();n=0
 with p.open(newline='',encoding='utf-8-sig') as f:
  r=csv.DictReader(f);heads=set(r.fieldnames or [])
  require({'event_id','decision_ts','prior_bin_end','ddos_score','alarm_at_frozen_threshold'}.issubset(heads),'BAD_INPUT_SCHEMA')
  require(not heads.intersection({'label','type','ground_truth','kind'}),'ORACLE_IN_POLICY_INPUT')
  for x in r:
   eid=x['event_id'];require(eid not in ids,'DUPLICATE_ID');ids.add(eid)
   t=float(x['decision_ts']);pt=float(x['prior_bin_end']);score=float(x['ddos_score']);alarm=int(x['alarm_at_frozen_threshold'])
   require(math.isfinite(t) and m['interval_lower_inclusive']<=t<m['interval_upper_exclusive'],'OUT_OF_SCOPE_TIME')
   require(pt<=t and math.isfinite(score) and 0<=score<=1,'FUTURE_OR_INVALID_SCORE')
   require(alarm==int(score>=m['threshold_frozen']),'ALARM_MISMATCH')
   b=math.floor(t/60)*60;bins[b].append((eid,t,score,alarm));n+=1
 require(n==m['rows'],'ROW_COUNT_MISMATCH')
 return m,bins
PASSIVE={'tick':'-1','state':'NORMAL','counter':'0','risk':'0','pressure':'0','filter':'AUTHENTICATION_REJECTION_ONLY','traffic':'NORMAL_SCHEDULING','edge':'PRIMARY_MEC','cadence':'0'}
def run(binary,bridge,out,capacity,queue_limit,central_delay):
 require(not out.exists(),'PRESERVE_EXISTING_OUTPUT')
 require(capacity>0 and queue_limit>=capacity and central_delay in (0,1,2),'INVALID_ASSUMPTIONS')
 manifest,bins=read_input(bridge);keys=list(range(min(bins),max(bins)+60,60));require(len(keys)==191,'UNEXPECTED_BIN_SPAN')
 out.mkdir(parents=True)
 summaries=[];actions=[];input_hash=manifest['policy_observations_sha256']
 # One immutable event list is shared by all treatments. The sealed oracle is NEVER opened.
 ledger_file=(out/'terminal_ledger.csv').open('w',newline='',encoding='utf-8')
 ledger=csv.DictWriter(ledger_file,fieldnames=['policy','event_id','decision_ts','terminal_status','completion_ts','ddos_score']);ledger.writeheader()
 for policy in POLICIES:
  ctl=Controller(binary,policy);q=deque();pending=[];history=[];result={};prior_count=0;prior_score=0.;peak_q=0
  try:
   for i,b in enumerate(keys):
    # Decision at start of b sees ONLY aggregates from completed b-60, plus OWN queues from end of b-60.
    load=min(1.,len(q)/queue_limit)
    obs=(prior_score/prior_count if prior_count else 0.,0.,0.,load,load,load)
    if policy=='B5':
     history.append(obs)
     seen=history[i-central_delay] if i>=central_delay else (0.,)*6
     proposed=ctl.step(i,seen);pending.append(proposed)
     action=pending[i-central_delay] if i>=central_delay else PASSIVE
    else:action=ctl.step(i,obs)
    require(action['filter'] in FILTERS,'UNKNOWN_FILTER')
    # Proxy filter: a flagged flow record is denied only in an active posture. Shared frozen threshold.
    active=action['filter']!='AUTHENTICATION_REJECTION_ONLY'
    this=bins.get(b,[]);accepted=denied=overflow=0
    for eid,t,score,alarm in this:
     if active and alarm:
      result[eid]=(t,'filter_denied',None,score);denied+=1
     elif len(q)>=queue_limit:
      result[eid]=(t,'queue_overflow',None,score);overflow+=1
     else:
      q.append((eid,t,score));accepted+=1
    served=min(capacity,len(q))
    for _ in range(served):
     eid,t,score=q.popleft();require(eid not in result,'DOUBLE_TERMINAL_EVENT');result[eid]=(t,'served',b+60,score)
    peak_q=max(peak_q,len(q))
    require(len(q)>=0 and served+len(q)==(len(q)+served),'IMPOSSIBLE_STATE')
    actions.append(dict(policy=policy,bin_start=b,observed_prior_count=prior_count,observed_prior_mean_score=obs[0],own_queue_pressure=load,state=action['state'],filter=action['filter'],active_filter=int(active),arrivals=len(this),accepted=accepted,filter_denied=denied,overflow=overflow,served=served,remaining=len(q)))
    prior_count=len(this);prior_score=sum(x[2] for x in this)
   for eid,t,score in q:
    require(eid not in result,'DOUBLE_TERMINAL_EVENT');result[eid]=(t,'censored_in_queue',None,score)
  finally:ctl.close()
  require(len(result)==manifest['rows'],'CONSERVATION_FAILURE')
  counts=defaultdict(int)
  for eid,(t,status,done,score) in result.items():
   counts[status]+=1;ledger.writerow(dict(policy=policy,event_id=eid,decision_ts=t,terminal_status=status,completion_ts='' if done is None else done,ddos_score=score))
  require(sum(counts.values())==manifest['rows'],'COUNT_CONSERVATION')
  summaries.append(dict(policy=policy,rows=manifest['rows'],**{k:counts[k] for k in ('served','filter_denied','queue_overflow','censored_in_queue')},peak_remaining_queue=peak_q))
 ledger_file.close()
 for filename,rows in [('actions.csv',actions),('summary.csv',summaries)]:
  with (out/filename).open('w',newline='',encoding='utf-8') as f:
   w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 report=dict(status='EXPLORATORY_MODELED_ACTUATION_NOT_M3',source_input_sha256=input_hash,controller_sha256=sha(binary),rows_per_policy=manifest['rows'],bins=len(keys),capacity_records_per_60s=capacity,queue_limit_records=queue_limit,central_observation_and_action_delay_bins=central_delay,b2='STATIC_ELEVATED_CANDIDATE',score_threshold=manifest['threshold_frozen'],model_semantics='frozen-score alarm gates filter, FIFO queue, unit-size flow-record service; capacity/queue are uncalibrated assumptions',oracle_opened=False,d4_test_scored=False,goodput_mbps_measured=False,latency_ms_measured=False,resource_feedback='OWN_QUEUE_BEFORE_CURRENT_ARRIVALS',filtering='SCORE_GATE_PROXY_NOT_TOKEN_BUCKET_IMPLEMENTATION',results=summaries,outputs={p:sha(out/p) for p in ('actions.csv','terminal_ledger.csv','summary.csv')})
 (out/'actuation_manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(report,sort_keys=True));return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--binary',type=Path,required=True);p.add_argument('--bridge',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--capacity',type=int,default=6000);p.add_argument('--queue-limit',type=int,default=18000);p.add_argument('--central-delay-bins',type=int,default=1);a=p.parse_args()
 run(a.binary,a.bridge,a.out,a.capacity,a.queue_limit,a.central_delay_bins)
