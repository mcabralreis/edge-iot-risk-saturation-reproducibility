#!/usr/bin/env python3
"""Read-only audit of archived P4/A1 action log; never runs a controller."""
import csv, hashlib, pathlib, collections
D=pathlib.Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
base=D/'evidence'
a=base/'actions_original.csv'
assert sha(a)=='5346b3dc13d81b11ab3dbfb7bc65e563a18fd8b24ae49fbe65a6f553f5522c67'
assert sha(D/'code/controller_stream.cc')=='104e5f2675d2c813152ef8ca0977a48b4f068189eb0c19480a3e28de559f97d6'
rows=list(csv.DictReader(a.open(newline='')))
P=[r for r in rows if r['policy']=='P4'];A=[r for r in rows if r['policy']=='A1']
assert len(rows)==764 and len(P)==len(A)==191
assert [r['bin_start'] for r in P]==[r['bin_start'] for r in A]
fields=[k for k in P[0] if k!='policy']
assert all(all(p[f]==a[f] for f in fields) for p,a in zip(P,A))
assert sum(float(x['own_queue_pressure'])>0 for x in P)==23
assert max(float(x['own_queue_pressure']) for x in P)==2/3
assert max(int(x['remaining']) for x in P)==12000
match=list(csv.DictReader((base/'P4_A1_matched_actions_191bins.csv').open(newline='')))
assert len(match)==191
for p,a,m in zip(P,A,match):
 assert m['bin_start']==p['bin_start']==a['bin_start']
 assert m['all_recorded_fields_equal']=='1' and m['action_profile_equal']=='1'
 assert m['remaining_count_equal']=='1'
 assert m['P4_state']==p['state'] and m['A1_state']==a['state']
 assert m['P4_remaining_record_count']==p['remaining']
print('R10_READONLY_ACTION_AUDIT=PASS')
print('P4_A1_MATCHED_BINS=191')
print('ALL_RECORDED_FIELDS_EQUAL=YES')
print('DERIVED_ACTION_PROFILE_EQUAL=YES')
print('REMAINING_COUNT_EQUAL=YES')
print('POSITIVE_PRESSURE_BINS=23')
print('PRESSURE_MAX=0.6666666666666666')
print('SCIENTIFIC_RUN_EXECUTED=NO')
