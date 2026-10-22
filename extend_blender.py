"""Add solver-derived low-speed/contact experiments without changing existing scenes."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
R=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(R/'神木路口_原图环境与七种物理假设.blend'))
main=bpy.data.scenes['01_基准_真实照片与物理仿真'];bpy.context.window.scene=main;main.frame_set(1);bpy.context.view_layer.update()
veh=bpy.data.collections['06_主角车辆_动画与形变'];root=bpy.data.objects['CAR_RIG_整车运动'];high=bpy.data.objects['高位制动灯_源帧357亮起']
wheel_tags={}
for ob in veh.objects:
 if ob.name.startswith('WHEEL_SPIN_'):
  loc=root.matrix_world.inverted()@ob.matrix_world.translation;wheel_tags[ob]=('-1' if loc.x<0 else '1')+'_'+('-1' if loc.y<0 else '1')
assert set(wheel_tags.values())=={'-1_-1','-1_1','1_-1','1_1'}
alt=json.loads((R/'alternative_results.json').read_text('utf-8'))
specs=json.loads((R/'shots_physics.json').read_text('utf-8'));specs=[x for x in specs if not x['id'].startswith(('initial','impact'))]
checks=[]
for scenario in alt['scenarios']:
 sid=scenario['id'];s=main.copy();s.name='速度试验_'+scenario['label'];s.use_fake_user=True
 s.view_layers[0].layer_collection.children[veh.name].exclude=True
 co=bpy.data.collections.new('车辆试验_'+sid);s.collection.children.link(co);mp={}
 for old in veh.objects:
  ob=old.copy();ob.animation_data_clear();co.objects.link(ob);mp[old]=ob
  if old==high:
   ob.data=old.data.copy();ma=old.data.materials[0].copy();ma.animation_data_clear();ob.data.materials.clear();ob.data.materials.append(ma)
 for old,ob in mp.items():
  if old.parent in mp:ob.parent=mp[old.parent]
 rt=mp[root];rt.rotation_mode='QUATERNION';hm=mp[high].data.materials[0];hm.use_nodes=False
 bpy.context.window.scene=s
 for st in scenario['states']:
  fr=st['source_frame']-343;q=Quaternion(st['quaternion']);rt.location=Vector(st['position'])-q@Vector((0,0,.81));rt.rotation_quaternion=q
  rt.keyframe_insert('location',frame=fr);rt.keyframe_insert('rotation_quaternion',frame=fr)
  for old,tag in wheel_tags.items():
   ob=mp[old];w=next(w for w in st['wheels'] if w['tag']==tag);ob.parent=rt;ob.matrix_parent_inverse=Matrix.Identity(4);ob.rotation_mode='QUATERNION'
   ob.location=q.inverted()@(Vector(w['position'])-rt.location);ob.rotation_quaternion=q.inverted()@Quaternion(w['quaternion']);ob.keyframe_insert('location',frame=fr);ob.keyframe_insert('rotation_quaternion',frame=fr)
  hm.diffuse_color=(1,.03,.012,1) if scenario['brake_factor']>0 and st['t']>=13/30 else (.015,.005,.005,1);hm.keyframe_insert('diffuse_color',frame=fr)
 s.frame_start=scenario['states'][0]['source_frame']-343;s.frame_end=scenario['states'][-1]['source_frame']-343;s['experiment']=scenario['experiment'];s['scenario_id']=sid
 s.camera=bpy.data.objects['CAM_俯视全程']
 for marker in list(s.timeline_markers):s.timeline_markers.remove(marker)
 for ob,c in scenario['contacts'].items():s.timeline_markers.new(f'{ob} {c["speed_kmh"]:.1f} km/h',frame=round(c['source_time']*30)-343)
 if sid.startswith('initial'):
  specs.append(dict(id=sid,scene=s.name,camera='CAM_原视频方向',start=1,end=50))
  specs.append(dict(id=sid+'_top',scene=s.name,camera='CAM_俯视全程',start=1,end=181))
 else:specs.append(dict(id=sid,scene=s.name,camera='CAM_路缘与立柱近景',start=s.frame_start,end=s.frame_end))
 for st in scenario['states'][::15]:
  fr=st['source_frame']-343;s.frame_set(fr);bpy.context.view_layer.update();expected=Vector(st['position'])-Quaternion(st['quaternion'])@Vector((0,0,.81));checks.append((rt.location-expected).length)
 assert max(checks)<1e-5
 s.frame_set(s.frame_start)
for s in bpy.data.scenes:s.use_fake_user=True
bpy.context.window.scene=main;main.frame_set(30)
(R/'shots_physics.json').write_text(json.dumps(specs,ensure_ascii=False,indent=2),'utf-8')
(R/'alternatives_blender_validation.json').write_text(json.dumps(dict(scenes=len(bpy.data.scenes),new_scenarios=4,max_baked_position_error_m=max(checks),sample_count=len(checks)),indent=2),'utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(R/'神木路口_原图环境与十一种物理假设.blend'))
print('EXTENDED BLEND READY',len(bpy.data.scenes),flush=True)
