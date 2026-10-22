"""Reproduce every worked number in the detailed speed section."""
from pathlib import Path
import csv,json,numpy as np
R=Path(__file__).resolve().parent
P=json.loads((R/'scene_calibration.json').read_text('utf-8'))['projection']
OBS=json.loads((R/'assets/observations.json').read_text('utf-8'));O={o['frame']:o for o in OBS}
D=json.loads((R/'physics_results.json').read_text('utf-8'));S=D['scenarios'][0]['states']
old=list(csv.DictReader((R/'calibration_audit/tail_measurements_stabilized.csv').open()))
a=np.array([[float(r[k]) for k in ['frame_zero_based','pts_s','tail_mid_x','tail_mid_y','tail_chord_px']] for r in old])
roof=np.array([[344,411,442],[350,340,361],[355,303,319]],float)
L=2.70;offset=.30;W=1.88;h=0.;alpha=1/(roof[:,1]-h)-1/(roof[:,2]-h)
sigma=np.sqrt((1/(roof[:,1]-h)**2)**2+(1/(roof[:,2]-h)**2)**2);weights=1/sigma**2
kr=float(np.sum(weights*alpha*L)/np.sum(weights*alpha*alpha))
kt_samples=(kr/(roof[:,2]-h)-offset)*(a[:3,3]-h);kt=float(np.mean(kt_samples))
A=float(np.median(W*(a[:5,3]-h)/a[:5,4]));F=kt/A
assert np.isclose(kt,P['K'],rtol=0,atol=1e-8)
assert np.isclose(F,P['F'],rtol=0,atol=1e-8)
work=[]
for aa,bb in [(352,357),(357,362)]:
 z0=kt/O[aa]['tail_y_px'];z1=kt/O[bb]['tail_y_px'];dt=(bb-aa)/30
 work.append(dict(kind='conditional_image_depth_difference',start_frame=aa,end_frame=bb,y_start=O[aa]['tail_y_px'],y_end=O[bb]['tail_y_px'],z_start=z0,z_end=z1,distance=z1-z0,seconds=dt,kmh=(z1-z0)/dt*3.6))
for aa,bb in [(357,362),(344,393)]:
 ds=S[bb-344]['distance_m']-S[aa-344]['distance_m'];dt=(bb-aa)/30
 work.append(dict(kind='fitted_solver_path_length',start_frame=aa,end_frame=bb,distance=ds,seconds=dt,kmh=ds/dt*3.6))
assert round(work[0]['kmh'])==129 and round(work[1]['kmh'])==140
assert round(work[2]['kmh'])==134 and round(work[3]['kmh'])==126
report=dict(calibration_provenance=dict(roof_length_assumed_m=L,horizon_assumed_px=h,roof_to_tail_longitudinal_offset_assumed_m=offset,tail_width_assumed_m=W,roof_points=roof.tolist(),Kroof=kr,Ktail_per_sample=kt_samples.tolist(),Ktail=kt,A=A,F=F,all_metric_inputs_are_conditional=True),worked_examples=work,pixel_error_example=dict(y=327,depth=kt/327,depth_at_y_minus2=kt/325,depth_at_y_plus2=kt/329),validation='All displayed rounded numbers recomputed from the packaged inputs; does not validate the empirical calibration.')
(R/'速度推导计算.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
with (R/'速度推导逐帧表.csv').open('w',encoding='utf-8-sig',newline='') as f:
 writer=csv.writer(f);writer.writerow(['frame','time_s','observed_tail_y_px','conditional_inverse_depth_m','solver_tail_y_px','solver_speed_kmh','solver_cumulative_path_m','y_residual_px'])
 for o,st in zip(OBS,S):writer.writerow([o['frame'],o['frame']/30,o['tail_y_px'],kt/o['tail_y_px'],st['pixel'][1],st['speed_kmh'],st['distance_m'],st['pixel'][1]-o['tail_y_px']])
print(json.dumps(report,ensure_ascii=False,indent=2))
