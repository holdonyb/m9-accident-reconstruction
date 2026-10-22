import bpy,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent
p=R/'同时间同距离_三种末速_方法演示.blend'
bpy.ops.wm.open_mainfile(filepath=str(p))
rows=[]
for a in [0,4,8]:
    sc=bpy.data.scenes[f'方法演示_同距离同时间_减速度{a}']
    bpy.context.window.scene=sc
    coll=bpy.data.collections[f'独立车辆_示例{a}']
    root=next(o for o in coll.objects if o.name.startswith('CAR_RIG_整车运动'))
    sc.frame_set(1);start=root.location.copy()
    sc.frame_set(31);end=root.location.copy()
    distance=(end-start).length
    assert abs(distance-6.5)<1e-4,(a,distance)
    assert sc.camera is not None
    assert len(root.animation_data.action.fcurves) if hasattr(root.animation_data.action,'fcurves') else root.animation_data is not None
    rows.append({'scene':sc.name,'distance_m':distance,'frame_start':1,'frame_end':31,'objects':len(coll.objects),'camera':sc.camera.name})
external=[]
for im in bpy.data.images:
    if im.source=='FILE' and not im.packed_file:
        path=Path(bpy.path.abspath(im.filepath))
        external.append({'image':im.name,'exists':path.exists()})
result={'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'scenes_checked':rows,'unpacked_image_references':external,'reopen':'passed'}
(R/'blend_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf-8')
print('BLEND VALIDATION',json.dumps(result,ensure_ascii=False))
