"""Bake equations at exact physical timestamps into the photo-textured intersection."""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Quaternion
R=Path(__file__).resolve().parent;P=R.parent
bpy.ops.wm.open_mainfile(filepath=str(P/'神木路口_原图环境与十一种物理假设.blend'))
data=json.loads((R/'author_hypotheses.json').read_text('utf-8'))
base=bpy.data.scenes['01_基准_真实照片与物理仿真'];bpy.context.window.scene=base;base.frame_set(7)
veh=bpy.data.collections['06_主角车辆_动画与形变'];root=bpy.data.objects['CAR_RIG_整车运动']
for case in data['scenarios']:
 sc=base.copy();sc.name='作者条件_'+case['id'];sc.use_fake_user=True;bpy.context.window.scene=sc
 sc.view_layers[0].layer_collection.children[veh.name].exclude=True
 col=bpy.data.collections.new(sc.name+'_车辆');sc.collection.children.link(col);mp={}
 for old in veh.objects:
  ob=old.copy();ob.animation_data_clear();col.objects.link(ob);mp[old]=ob
 for old,ob in mp.items():
  if old.parent in mp:ob.parent=mp[old.parent]
 rt=mp[root];rt.rotation_mode='QUATERNION'
 sc.camera=bpy.data.objects['CAM_原视频方向'];sc.render.resolution_x=960;sc.render.resolution_y=540;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='JPEG';sc.render.image_settings.quality=94;sc.render.use_sequencer=False;sc.frame_start=1;sc.frame_end=51
 sc.render.fps=30000;sc.render.fps_base=30000*case['duration']/50
 sc['duration_seconds']=case['duration'];sc['physical_time_mapping']='t=(frame-1)/50*duration_seconds';sc['equation']=case['model'];sc['geometry_status']=data['geometry']
 for row in case['states']:
  rt.location=row['position'];rt.rotation_quaternion=Quaternion(row['quaternion']);rt.keyframe_insert('location',frame=row['frame']);rt.keyframe_insert('rotation_quaternion',frame=row['frame'])
 folder=R/'renders_author_v3'/case['id'];folder.mkdir(parents=True,exist_ok=True)
 for row in case['states']:
  dest=folder/f"{row['frame']:04}.jpg"
  if dest.exists():continue
  sc.frame_set(row['frame']);sc.render.filepath=str(dest);bpy.ops.render.render(write_still=True)
 print('AUTHOR REPLAY COMPLETE',case['id'],flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(R/'作者条件_六组速度时序对照_v3.blend'))
