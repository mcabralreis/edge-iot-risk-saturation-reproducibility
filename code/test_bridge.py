"""Controlled synthetic test of replay export, oracle isolation and D4-test exclusion."""
import csv,hashlib,importlib.util,io,json,tempfile,zipfile
from pathlib import Path
import joblib
import numpy as np
from sklearn.feature_extraction import FeatureHasher
from sklearn.linear_model import SGDClassifier
from export_d6_replay import export
from audit_bridge import audit

def run():
 d6path=Path(__file__).resolve().parents[1]/'COMNET_TON_D6'/'d6_causal_detector.py'
 if not d6path.exists():
  import os
  d6path=Path(os.environ['COMNET_D6_SCRIPT'])
 spec=importlib.util.spec_from_file_location('d6_original',d6path);d6=importlib.util.module_from_spec(spec);spec.loader.exec_module(d6)
 with tempfile.TemporaryDirectory() as tmp:
  p=Path(tmp);data=p/'data'/'source_downloads';data.mkdir(parents=True)
  zpath=data/'Processed_Network_dataset.zip'
  cols=['ts','src_ip','dst_ip','proto','dst_port','label','type']
  rows=[(110,'a','x','tcp','80','0','normal'),(121,'b','y','udp','53','1','ddos'),
        (181,'c','x','tcp','80','0','normal'),(241,'d','z','udp','53','1','ddos'),
        (301,'e','z','tcp','443','1','scanning'),(311,'f','z','tcp','80','0','normal'),
        (361,'g','z','tcp','80','1','ddos'),(421,'h','z','udp','53','1','ddos'),
        (491,'i','z','tcp','80','1','ddos')]
  s=io.StringIO();w=csv.writer(s);w.writerow(cols);w.writerows(rows)
  with zipfile.ZipFile(zpath,'w') as z:z.writestr('Processed_Network_dataset/Network_dataset_1.csv',s.getvalue())
  digest=hashlib.sha256(zpath.read_bytes()).hexdigest()
  lock={'source_sha256':digest,'split_edges':[100,280,460,550],'purge_seconds':10}
  lp=p/'lock.json';lp.write_text(json.dumps(lock))
  hasher=FeatureHasher(n_features=8192,input_type='dict',alternate_sign=False)
  X=hasher.transform([{'proto=tcp':1},{'proto=udp':1},{'proto=tcp':1},{'proto=udp':1}]);Y=np.array([0,1,0,1]);model=SGDClassifier(loss='log_loss',random_state=1).fit(X,Y)
  mp=p/'model.joblib';joblib.dump({'model':model,'hasher':hasher,'threshold':0.6,'protocol':{'upper_exclusive':450,'d4_edges':lock['split_edges']}},mp)
  m=export(p/'data',lp,mp,p/'out',d6,allow_noncanonical=True)
  a=audit(p/'out')
  with (p/'out'/'policy_observations.csv').open(newline='') as f:rows=list(csv.DictReader(f))
  with (p/'out'/'SEALED_oracle_evaluation_only.csv').open(newline='') as f:oracle=list(csv.DictReader(f))
  assert len(rows)==len(oracle)==4, (rows,oracle)
  assert all(float(r['decision_ts'])<450 for r in rows)
  assert any(o['type']=='scanning' for o in oracle), 'must not select by target class'
  assert all(float(r['prior_bin_end'])<=float(r['decision_ts']) for r in rows)
  assert not any('label' in r or 'type' in r for r in rows)
  print('SMOKE_TEST=PASS')
  print('REPLAY_ROWS='+str(m['rows']))
  print('ORACLE_ISOLATION=PASS')
  print('PREVIOUS_COMPLETED_WINDOW=PASS')
  print('NO_TEST_ROWS_SCORED=PASS')
  print('ALL_CLASSES_UNFILTERED=PASS')
  print('INDEPENDENT_AUDIT='+a['status'])
if __name__=='__main__':run()
