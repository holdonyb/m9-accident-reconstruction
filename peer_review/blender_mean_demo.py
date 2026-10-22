"""Controlled kinematic identifiability demo, not an accident dynamics fit."""
import bpy,math,json
from pathlib import Path
from mathutils import Vector,Quaternion
R=Path(__file__).resolve().parent;P=R.parent
bpy.ops.wm.open_mainfile(filepath=str(P/'神木路口_原图环境与十一种物理假设.blend'))
base=bpy.data.scenes['01_基准_真实照片与物理仿真'];bpy.context.window.scene=base;base.frame_set(20)
veh=bpy.data.collections['06_主角车辆_动画与形变'];root=bpy.data.objects['CAR_RIG_整车运动']
q=root.rotation_quaternion.copy();start=root.location.copy();fw=q@Vector((0,1,0));right=q@Vector((1,0,0));T=23/30;S=6.5
spec=[]
for idx,a in enumerate([0,4,8]):
 sc=base.copy();sc.name=f'方法演示_同距离同时间_减速度{a}';sc.use_fake_user=True;bpy.context.window.scene=sc
 sc.view_layers[0].layer_collection.children[veh.name].exclude=True
 coll=bpy.data.collections.new(f'独立车辆_示例{a}');sc.collection.children.link(coll);mp={}
 for old in veh.objects:
  ob=old.copy();ob.animation_data_clear();coll.objects.link(ob);mp[old]=ob
 for old,ob in mp.items():
  if old.parent in mp:ob.parent=mp[old.parent]
 rt=mp[root];rt.rotation_mode='QUATERNION';rt.rotation_quaternion=q
 data=bpy.data.cameras.new(f'方法演示相机{a}');cam=bpy.data.objects.new(data.name,data);sc.collection.objects.link(cam)
 center=start+fw*(S/2)+Vector((0,0,1));cam.location=center+right*13-fw*6+Vector((0,0,10));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();data.lens=32;data.clip_end=1500;sc.camera=cam
 sc.render.resolution_x=1280;sc.render.resolution_y=720;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='JPEG';sc.render.image_settings.quality=93;sc.render.use_sequencer=False;sc.render.fps=30;sc.frame_start=1;sc.frame_end=31
 v0=S/T+.5*a*T;rows=[]
 for fr in range(1,32):
  t=(fr-1)/30*T;s=v0*t-.5*a*t*t;rt.location=start+fw*s;rt.keyframe_insert('location',frame=fr)
  rows.append({'frame':fr,'physical_s':t,'distance_m':s,'speed_kmh':(v0-a*t)*3.6})
 sc['purpose']='Kinematic example: same 6.5m and 23/30s, different final speeds. Not fitted crash simulation.'
 spec.append({'scene':sc.name,'a_ms2':a,'states':rows})
 folder=R/'renders_mean'/str(a);folder.mkdir(parents=True,exist_ok=True)
 for fr in range(1,32):
  dest=folder/f'{fr:04}.jpg'
  if dest.exists():continue
  sc.frame_set(fr);sc.render.filepath=str(dest);bpy.ops.render.render(write_still=True)
 print('DEMO COMPLETE',a,flush=True)
(R/'mean_demo.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2),'utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(R/'同时间同距离_三种末速_方法演示.blend'))
