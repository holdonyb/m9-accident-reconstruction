"""MuJoCo wheel/contact simulation: positions are solver outputs, never prescribed.
M9-sized generic rigid vehicle; suspension, tire friction and braking are hypotheses.
"""
from pathlib import Path
import json,math,time,sys
import numpy as np
import mujoco as mj
from scipy.optimize import least_squares
R=Path(__file__).resolve().parent;M=json.loads((R/'scene_calibration.json').read_text('utf-8'));P=M['projection']
FWD=np.array([*P['forward'],0]);RIGHT=np.array([*P['right'],0]);OFF=np.array([*P['world_offset'],0]);CAM=OFF+np.array([0,0,P['A']+1.21]);F=P['F'];DT=1/600
obs=json.loads((R/'assets/observations.json').read_text('utf-8'))
base0=M['initial_pose']
POLE=np.array(M['pole_position'])
ROAD_DIR=np.array([433.,-197.,0]);ROAD_DIR/=np.linalg.norm(ROAD_DIR)
OUTWARD=np.array([ROAD_DIR[1],-ROAD_DIR[0],0]);CURB_EDGE=POLE-OUTWARD*.85

def scene_xml(mu=.9,pole=True,curb_height=.16):
 wheel=[];act=[]
 for side in [-1,1]:
  for front in [-1,1]:
   tag=f'{side}_{front}';x=side*.855;y=front*1.555
   steer=f'<joint name="steer_{tag}" axis="0 0 1" range="-.55 .55" damping="20"/>' if front>0 else ''
   wheel.append(f'''<body name="susp_{tag}" pos="{x} {y} -.47"><joint name="susp_{tag}" type="slide" axis="0 0 1" stiffness="65000" damping="5000" range="-.17 .18"/>
     <inertial mass="5" pos="0 0 0" diaginertia=".04 .04 .04"/>
     <body name="knuckle_{tag}">{steer}<inertial mass="5" pos="0 0 0" diaginertia=".04 .04 .04"/>
     <body name="wheel_{tag}"><joint name="spin_{tag}" axis="1 0 0" damping=".04"/>
      <geom name="tire_{tag}" type="cylinder" size=".43 .14" quat=".70710678 0 .70710678 0" mass="35" contype="4" conaffinity="1" friction="{mu} .015 .001" condim="6" rgba=".025 .025 .03 1"/></body></body></body>''')
   act.append(f'<motor name="brake_{tag}" joint="spin_{tag}" gear="1" ctrllimited="true" ctrlrange="-4500 4500"/>')
   if front>0:act.append(f'<position name="steering_{tag}" joint="steer_{tag}" kp="30000" kv="1200" ctrlrange="-.55 .55"/>')
 pp=POLE
 polexml=f'<geom name="pole" type="box" pos="{pp[0]} {pp[1]} 3.9" size=".18 .18 3.7" rgba=".5 .5 .5 1" friction=".4 .01 .001"/>' if pole else ''
 if pole and curb_height>0:
  yaw=math.atan2(ROAD_DIR[1],ROAD_DIR[0]);quat=f'{math.cos(yaw/2)} 0 0 {math.sin(yaw/2)}';ce=CURB_EDGE+OUTWARD*.12;sw=CURB_EDGE+OUTWARD*2.12;sp=POLE-ROAD_DIR*1.6-OUTWARD*.10
  polexml+=f'<geom name="curb" type="box" pos="{ce[0]} {ce[1]} {.2+curb_height/2}" size="25 .12 {curb_height/2}" quat="{quat}" friction=".8 .01 .001"/>'
  polexml+=f'<geom name="sidewalk" type="box" pos="{sw[0]} {sw[1]} {.2+curb_height/2}" size="25 1.88 {curb_height/2}" quat="{quat}" friction=".8 .01 .001"/>'
  polexml+=f'<geom name="secondary_post" type="box" pos="{sp[0]} {sp[1]} 3.2" size=".075 .075 3" friction=".4 .01 .001"/>'
 return f'''<mujoco model="M9_conditional_vehicle"><compiler angle="radian"/><option timestep="{DT}" gravity="0 0 -9.81" integrator="implicitfast" cone="elliptic" iterations="60"/><default><joint armature=".02" limited="auto"/><geom solref=".008 1" solimp=".95 .99 .001"/></default>
 <worldbody><geom name="road" type="plane" pos="0 0 .2" size="500 500 .1" friction="{mu} .015 .001" condim="6"/>{polexml}
 <body name="car" pos="0 0 1.25"><freejoint/><inertial pos="0 0 0" mass="2470" diaginertia="6500 1800 6500"/>
 <geom name="chassis" type="box" pos="0 0 0" size=".95 2.55 .55" mass="0" contype="2" conaffinity="1" rgba=".65 .7 .75 1"/>
 {''.join(wheel)}</body></worldbody><actuator>{''.join(act)}</actuator></mujoco>'''
def smooth(q):q=np.clip(q,0,1);return q*q*(3-2*q)
MODELS={}
def run(params=None,mu=.9,brake_shift=0,brake_factor=1,duration=2.5,pole=True,export=False,curb_height=.16,initial_state=None,capture_state=False,source_start_frame=344):
 # v0, brake demand m/s2, initial depth displacement, initial yaw correction,
 # steering peak rad, steering start seconds. No path-following controller.
 if params is None:params=[38,7,0,0,.06,.35]
 v0,ade,depthshift,yawshift,steerpeak,steerstart=map(float,params)
 key=(mu,pole,curb_height)
 if key not in MODELS:
  mo=mj.MjModel.from_xml_string(scene_xml(mu,pole,curb_height));da=mj.MjData(mo)
  for _ in range(600):mj.mj_step(mo,da)
  MODELS[key]=(mo,da.qpos.copy())
 mo,settled=MODELS[key];da=mj.MjData(mo);da.qpos[:]=settled
 center=np.array(base0['center']);head=base0['heading']+yawshift
 da.qpos[:2]=(center+FWD*depthshift)[:2];da.qpos[3:7]=[math.cos(head/2),0,0,math.sin(head/2)]
 fwd=np.array([-math.sin(head),math.cos(head),0]);da.qvel[:3]=fwd*v0
 spins=[];steers=[];brakes=[]
 for side in [-1,1]:
  for front in [-1,1]:
   tag=f'{side}_{front}';ji=mo.joint(f'spin_{tag}').id;vi=mo.jnt_dofadr[ji];qi=mo.jnt_qposadr[ji];da.qvel[vi]=-v0/.43
   spins.append((tag,qi,vi));brakes.append((mo.actuator(f'brake_{tag}').id,vi,front))
   if front>0:steers.append(mo.actuator(f'steering_{tag}').id)
 if initial_state is not None:
  da.qpos[:]=initial_state['qpos'];da.qvel[:]=np.array(initial_state['qvel'])*initial_state.get('velocity_scale',1)
 mj.mj_forward(mo,da);carid=mo.body('car').id;tail_local=np.array([0,-2.598,.20]);states=[];contact=None;maxslip=0.;nextsample=0.;prev=da.xpos[carid].copy();dist=0.;contacts={}
 for step in range(round(duration/DT)+1):
  tt=step*DT;rot=da.xmat[carid].reshape(3,3);vel=da.qvel[:3];long=float(np.dot(vel,rot[:,1]));speed=float(np.linalg.norm(vel[:2]))
  ramp=float(smooth((tt-(13/30+brake_shift))/.25));cmd=-0.0+steerpeak*float(smooth((tt-steerstart)/.55))
  for ai in steers:da.ctrl[ai]=cmd
  for ai,vi,front in brakes:
   slip=max(0,(abs(long)-abs(da.qvel[vi])*.43)/max(abs(long),1));maxslip=max(maxslip,slip)
   # Simple brake torque relief above 15% slip, not a claim about OEM ABS.
   relief=np.clip((.24-slip)/.09,0,1)
   torque=2650*ade*brake_factor*.43*(.30 if front>0 else .20)*ramp*relief
   da.ctrl[ai]=-np.tanh(da.qvel[vi]/2)*torque
  # Air and rolling resistance are forces; no velocity or pose is overwritten.
  da.xfrc_applied[carid,:3]=-rot[:,1]*(.5*1.225*.65*long*abs(long)+.010*2650*9.81*np.tanh(long))
  if tt+1e-9>=nextsample:
   rear=da.xpos[carid]+rot@tail_local;rel=rear-CAM;depth=float(rel@FWD);pix=[640+F*float(rel@RIGHT)/depth,F*(-rel[2])/depth]
   states.append(dict(t=tt,position=da.xpos[carid].tolist(),quaternion=da.xquat[carid].tolist(),rear=rear.tolist(),pixel=pix,speed_kmh=speed*3.6,distance_m=dist,steer_rad=cmd,brake_command=ramp,source_frame=344+round(tt*30),wheel_angles=[float(da.qpos[qi]) for _,qi,_ in spins],wheels=[dict(tag=tag,position=da.xpos[mo.body('wheel_'+tag).id].tolist(),quaternion=da.xquat[mo.body('wheel_'+tag).id].tolist()) for tag,qi,vi in spins]))
   states[-1]['source_frame']=source_start_frame+round(tt*30)
   if capture_state:states[-1]['restart_state']=dict(qpos=da.qpos.tolist(),qvel=da.qvel.tolist())
   nextsample+=1/30
  for ci in range(da.ncon):
   co=da.contact[ci];names=[mj.mj_id2name(mo,mj.mjtObj.mjOBJ_GEOM,g) for g in [co.geom1,co.geom2]]
   if 'pole' in names and contact is None:contact=tt
   for obstacle in ['curb','sidewalk','pole','secondary_post']:
    if obstacle in names and obstacle not in contacts:contacts[obstacle]=dict(t=tt,source_time=source_start_frame/30+tt,pair=names,speed_kmh=speed*3.6,position=co.pos.tolist(),distance_m=dist)
  mj.mj_step(mo,da);mj.mj_forward(mo,da);pos=da.xpos[carid];dist+=float(np.linalg.norm(pos[:2]-prev[:2]));prev=pos.copy()
  if not np.all(np.isfinite(da.qpos)):raise RuntimeError('Nonfinite simulation')
 states=states[:round(duration*30)+1]
 return dict(params=list(params),mu=mu,brake_shift=brake_shift,brake_factor=brake_factor,curb_height=curb_height,states=states,pole_contact_s=contact,contacts=contacts,max_wheel_slip=maxslip,engine=mj.__version__)
def residual(params,mu=.9):
 d=run(params,mu=mu,duration=49/30,pole=False);pts=np.array([r['pixel'] for r in d['states']]);target=np.array([[r['x_seed_px'],r['tail_y_px']] for r in obs]);return ((pts-target)/np.array([4,3])).ravel()
def main():
 start=time.time();seed=[38,7,0,0,.06,.35]
 base=run(seed,duration=2,pole=False);print('PROBE',base['states'][0],base['states'][-1],flush=True)
 lo=[30,2,-2,-.08,-.25,.0];hi=[46,11,2,.08,.25,1.2]
 if '--reuse' in sys.argv:
  params=json.loads((R/'physics_results.json').read_text('utf-8'))['baseline_params'];success=True
 else:
  sol=least_squares(residual,seed,bounds=(lo,hi),diff_step=.004,loss='soft_l1',max_nfev=65,verbose=0);params=sol.x.tolist();success=bool(sol.success)
 baseline=run(params,duration=3,pole=True);baseline['label']='基准物理假设';baseline['id']='base'
 sims=[baseline]
 for sid,lab,kw in [('early','提前0.35秒制动',dict(brake_shift=-.35)),('late','晚0.35秒制动',dict(brake_shift=.35)),('wet','较低附着 μ=0.55',dict(mu=.55)),('soft','较弱制动力',dict(brake_factor=.65)),('lowcurb','路缘高10厘米',dict(curb_height=.10)),('highcurb','路缘高22厘米',dict(curb_height=.22))]:
  d=run(params,duration=3,pole=True,**kw);d['id']=sid;d['label']=lab;sims.append(d)
 target=np.array([[r['x_seed_px'],r['tail_y_px']] for r in obs]);pred=np.array([r['pixel'] for r in baseline['states'][:50]]);rmse=np.sqrt(np.mean((pred-target)**2,axis=0))
 out=dict(engine='MuJoCo '+mj.__version__,timestep_s=DT,solver='implicitfast / elliptic contact',vehicle_mass_kg=2650,wheelbase_m=3.11,tire_radius_m=.43,source_time_start_s=344/30,source_light_on_s=357/30,
  baseline_params=params,baseline_pixel_rmse_xy=rmse.tolist(),scenarios=sims,environment=dict(pole_position=POLE.tolist(),road_direction=ROAD_DIR.tolist(),curb_outward=OUTWARD.tolist(),curb_edge=CURB_EDGE.tolist(),curb_height_m=.16,sidewalk_width_m=4,pole_setback_m=.85,geometry_status='Topology informed by user post-incident photo. Heights, setbacks, world alignment and pre-incident intact curb are hypotheses; post-incident damage is not assumed pre-existing.'),
  scope='Rigid vehicle with four rolling wheels, spring-damper suspensions, steering actuators, brake torques and frictional road/pole contact. No prescribed trajectory or post-contact pose. Tire/ABS/suspension/inertia parameters are generic assumptions, not OEM data.',
  fit_success=success,elapsed_s=time.time()-start)
 (R/'physics_results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),'utf-8');(R/'vehicle_simulation.xml').write_text(scene_xml(),'utf-8')
 print(json.dumps({k:v for k,v in out.items() if k!='scenarios'},ensure_ascii=False,indent=2),flush=True)
 for ss in sims:print(ss['id'],ss['pole_contact_s'],ss['states'][49]['speed_kmh'],ss['states'][49]['distance_m'],flush=True)
if __name__=='__main__':main()
