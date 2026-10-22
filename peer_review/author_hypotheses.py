"""Replay stated inputs without using the manufacturer's reported speed as a target."""
from pathlib import Path
import json,csv,math
import numpy as np
from scipy.interpolate import CubicSpline
R=Path(__file__).resolve().parent;P=R.parent
cal=json.loads((P/'scene_calibration.json').read_text('utf-8'))['projection']
obs=list(csv.DictReader((P/'calibration_audit/tail_measurements_stabilized.csv').open()))
obs=[r for r in obs if int(r['frame_zero_based'])>=350]
pixels=np.array([[float(r['tail_mid_x']),float(r['tail_mid_y'])] for r in obs])
stabilization=next(r for r in json.loads((P/'assets/stabilization.json').read_text('utf-8')) if r['n']==346)
# Manual midpoint of the farther (upper) rear-lamp exposure in raw frame 346.
# Two exposures are visible; choosing this one is an explicit synchronization assumption.
anchor_raw=np.array([850.5,447.5,1.0]);anchor_h=np.array(stabilization['H'])@anchor_raw
anchor=anchor_h[:2]/anchor_h[2]
pixels=np.vstack([anchor,pixels])
dep=cal['K']/pixels[:,1];lat=cal['A']*(pixels[:,0]-640)/pixels[:,1]
world=np.array(cal['world_offset'])+dep[:,None]*np.array(cal['forward'])+lat[:,None]*np.array(cal['right'])
# A geometric path only: its observed frame times do not prescribe replay speed.
arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(world,axis=0),axis=1))]
path=CubicSpline(arc,world,bc_type='natural')
def pose(s):
 if s<=arc[-1]:pt=path(s);tan=path(s,1)
 else:tan=path(arc[-1],1);tan/=np.linalg.norm(tan);pt=world[-1]+(s-arc[-1])*tan
 tan=tan/np.linalg.norm(tan);yaw=math.atan2(-tan[0],tan[1]);q=[math.cos(yaw/2),0,0,math.sin(yaw/2)]
 # Measured rear lamp point is 2.60 m behind root and 1.01 m above it.
 center=pt+tan*2.60
 return [float(center[0]),float(center[1]),.2],q
spec=[]
T=50/30;tm=27/30;S=21.2;fullT=58/30;offset=8/30
# A smooth, everywhere braking example satisfying ALL three measured segment integrals.
# 77 initial /22 final are explicit interpolation boundary choices, not measured instant speeds.
knots=np.array([8,35,58])/30
A=np.vstack([[z**i for i in range(1,6)] for z in knots]+[[1,0,0,0,0],[i*fullT**(i-1) for i in range(1,6)]])
coeff=np.linalg.solve(A,[5.5,20.2,26.7,77/3.6,22/3.6])
def whole(t,n=0):
 return sum(coeff[i-1]*math.factorial(i)/math.factorial(i-n)*t**(i-n) for i in range(max(1,n),6))
assert all(whole(float(t),2)<0 for t in np.linspace(0,fullT,500))
assert max(abs(whole(float(t))-s) for t,s in zip(knots,[5.5,20.2,26.7]))<1e-9
for factor in [1,1.5,2]:
 def state(t,f=factor):return f*(whole(t+offset)-5.5),f*whole(t+offset,1),f*whole(t+offset,2)
 rows=[]
 for n in range(51):
  t=n/50*T;s,v,a=state(t);loc,q=pose(s);rows.append(dict(frame=n+1,t=t,distance_m=s,speed_kmh=v*3.6,a_ms2=a,position=loc,quaternion=q))
 assert abs(state(tm)[0]-14.7*factor)<1e-9 and abs(state(T)[0]-21.2*factor)<1e-9
 assert all(x['speed_kmh']>0 and x['a_ms2']<0 for x in rows)
 spec.append(dict(id=f'teacher_{factor:g}',label=f'标尺 {3*factor:g} m',duration=T,scale_factor=factor,source='BV1U9nB6GEwD',model='Quintic distance curve satisfies all original segments:5.5m/8frames,14.7m/27frames,6.5m/23frames. Explicit boundary choices:full-entry77km/h and terminal22km/h. It brakes throughout; continuous speed/acceleration. Film shows portion after first8frames. Scale scenarios multiply distance/velocity/acceleration, retaining time.',terminal_speed_assumption_kmh=22*factor,full_entry_assumption_kmh=77*factor,full_polynomial_coefficients=(coeff*factor).tolist(),offset_s=offset,states=rows))
T=44.5/29.8;tb=7.5/29.8;S=52.2
for g in [.5,.65,.8]:
 a=g*9.81;v=(S+.5*a*(T-tb)**2)/T;rows=[]
 for n in range(51):
  t=n/50*T;bt=max(0,t-tb);s=v*t-.5*a*bt*bt;loc,q=pose(s);rows.append(dict(frame=n+1,t=t,distance_m=s,speed_kmh=(v-a*bt)*3.6,a_ms2=-a if t>tb else 0,position=loc,quaternion=q))
 assert abs(rows[-1]['distance_m']-S)<1e-9
 spec.append(dict(id=f'bird_{g:g}',label=f'制动 {g:g} g',duration=T,brake_on_s=tb,a_g=g,source='BV1SQn66HEjf',model='Original author constant-speed-then-constant-deceleration equation; midpoint52.2m, original44.5/29.8s and brake7.5/29.8s.',states=rows))
result={'source_frame_anchor':346,'anchor_note':'Author label61 matches local346. Common replay start uses farther/upper rear-lamp exposure, raw(850.5,447.5), background stabilized. Other exposure time remains unresolved. Teacher equations begin after original first8/30s. Bird is a common-start comparison, not an independently verified author start event.','anchor_raw_px':anchor_raw[:2].tolist(),'anchor_stabilized_px':anchor.tolist(),'anchor_homography':stabilization['H'],'geometry':'Observed rear-lamp path inverted through existing conditional camera calibration. No manufacturer speed input. Ground scale is not independent survey; discrepancy tests this combined geometry and motion hypothesis.','observed_path_length_m':float(arc[-1]),'frame_sampling':'51 render samples include both exact time endpoints; film maps physical seconds explicitly, never treats 51 samples as51/30seconds.','scenarios':spec}
(R/'author_hypotheses.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps([{k:s[k] for k in ['id','duration']}|{'distance':s['states'][-1]['distance_m'],'initial':s['states'][0]['speed_kmh'],'end':s['states'][-1]['speed_kmh']} for s in spec],ensure_ascii=False,indent=2))
