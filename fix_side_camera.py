import bpy,json
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
from pathlib import Path
R=Path(__file__).resolve().parent
(R/'renders/side').mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'神木路口_原图环境与七种物理假设.blend'))
s=bpy.data.scenes['01_基准_真实照片与物理仿真'];bpy.context.window.scene=s
c=bpy.data.objects['CAM_路边固定'];c.location=(60,-3,12);c.rotation_euler=(Vector((-2,-3,1))-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=28
bpy.context.view_layer.update()
states=json.loads((R/'physics_results.json').read_text('utf-8'))['scenarios'][0]['states'];checks=[]
for st in states:
    uv=world_to_camera_view(s,c,Vector(st['position']));checks.append([uv.x,uv.y,uv.z])
assert all(.04<x<.96 and .04<y<.96 and z>0 for x,y,z in checks),checks
(R/'side_camera_validation.json').write_text(json.dumps({'all_91_vehicle_centers_in_frame':True,'normalized_projections':checks},indent=2),'utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(R/'神木路口_原图环境与七种物理假设.blend'))
s.camera=c;s.render.threads_mode='FIXED';s.render.threads=1
for fr in range(1,92):
    s.frame_set(fr);s.render.filepath=str(R/'renders/side'/f'{fr:04}.jpg');bpy.ops.render.render(write_still=True)
print('FIXED SIDE CAMERA',flush=True)
