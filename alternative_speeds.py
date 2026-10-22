"""Independent initial-speed tests and explicitly local contact-speed experiments."""
from pathlib import Path
import json,copy,numpy as np
from scipy.optimize import brentq
import physics
R=Path(__file__).resolve().parent
old=json.loads((R/'physics_results.json').read_text('utf-8'));p=old['baseline_params']
base=physics.run(p,duration=3,capture_state=True)
assert np.max(np.abs(np.array([s['position'] for s in base['states']])-np.array([s['position'] for s in old['scenarios'][0]['states']])))<1e-9
out=[]
for k in [60,80]:
 q=p.copy();q[0]=k/3.6;d=physics.run(q,duration=6);d.update(id=f'initial{k}',label=f'初速{k} km/h',experiment='same initial position, braking time/torques, steering, and scene; change only initial speed',source_start_frame=344)
 d['stop']=next((dict(t=s['t'],speed_kmh=s['speed_kmh'],distance_m=s['distance_m']) for i,s in enumerate(d['states']) if s['speed_kmh']<.5 and all(x['speed_kmh']<.5 for x in d['states'][i:])),None)
 out.append(d);print(d['id'],'contacts',d['contacts'],'stop',d['stop'],flush=True)
# A local experiment begins at the baseline frame 390 pose (before first contact).
# It does NOT purport to recreate how a lower speed was reached earlier.
snap=base['states'][390-344];initial=copy.deepcopy(snap['restart_state'])
q=p.copy();q[4]=snap['steer_rad'];q[5]=-.55
def trial(v):
 z=copy.deepcopy(initial);z['velocity_scale']=v/snap['speed_kmh'];return physics.run(q,duration=2.5,brake_factor=0,initial_state=z,source_start_frame=390)
for target in [40,50]:
 def f(v):
  d=trial(v);c=d['contacts'].get('pole')
  if c is None:raise RuntimeError(f'No main pole contact at start {v}')
  return c['speed_kmh']-target
 lo,hi=target,target+25
 print('bracket',target,f(lo),f(hi),flush=True)
 v=brentq(f,lo,hi,xtol=.005);d=trial(v)
 d.update(id=f'impact{target}',label=f'主柱接触约{target} km/h',experiment='local restart from baseline frame 390 pose; scale initial velocities, hold steering and release brakes; target main-pole contact speed only',source_start_frame=390,restart_source_frame=390,restart_speed_kmh=v,restart_state=initial,target_pole_kmh=target)
 out.append(d);print(d['id'],v,{k:(v['t'],v['speed_kmh']) for k,v in d['contacts'].items()},flush=True)
result={'baseline_replay_position_error_m':0,'scenarios':out,'local_restart_note':'40/50 tests are local contact comparisons, not whole-event fits. Clock is aligned at source frame 390 (13.000s); altered prior history is not claimed.'}
(R/'alternative_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf-8')
# Contact ledger covers all seven original hypotheses and the new experiments.
rows=[]
for d in old['scenarios']+out:
 for obstacle,c in d['contacts'].items():rows.append(dict(id=d['id'],label=d['label'],obstacle=obstacle,elapsed_s=c['t'],source_time_s=c['source_time'],speed_kmh=c['speed_kmh'],distance_m=c.get('distance_m')))
(R/'contact_ledger.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),'utf-8')
print('ALTERNATIVES READY',flush=True)
