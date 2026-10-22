import bpy,json,time
from pathlib import Path
R=Path(__file__).resolve().parent;out=R/'renders';out.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'神木路口_原图环境与十一种物理假设.blend'))
shots=json.loads((R/'shots_physics.json').read_text('utf-8'))
for sh in shots:
 s=bpy.data.scenes[sh['scene']];bpy.context.window.scene=s;s.camera=bpy.data.objects[sh['camera']];folder=out/sh['id'];folder.mkdir(exist_ok=True)
 for fr in range(sh['start'],sh['end']+1):
  p=folder/f'{fr:04}.jpg'
  if p.exists() and p.stat().st_size>10000:continue
  s.frame_set(fr);s.render.filepath=str(p);bpy.ops.render.render(write_still=True)
 print('SHOT COMPLETE',sh['id'],flush=True)
print('ALL RENDERED',flush=True)
