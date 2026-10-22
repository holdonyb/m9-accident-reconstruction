import bpy,json,math
from pathlib import Path
R=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(R/'作者条件_六组速度时序对照_v3.blend'))
data=json.loads((R/'author_hypotheses.json').read_text('utf-8'));checks=[]
for case in data['scenarios']:
 sc=bpy.data.scenes['作者条件_'+case['id']];bpy.context.window.scene=sc
 rigs=[o for o in sc.objects if 'CAR_RIG_整车运动' in o.name and o.visible_get()]
 assert len(rigs)==1,(sc.name,len(rigs));root=rigs[0]
 for row in case['states']:
  sc.frame_set(row['frame']);err=max(abs(a-b) for a,b in zip(root.location,row['position']));assert err<1e-4
 assert sc.frame_end==51
 assert abs(sc['duration_seconds']-case['duration'])<1e-10
 assert len(list((R/'renders_author_v3'/case['id']).glob('*.jpg')))==51
 checks.append({'scene':sc.name,'samples':51,'duration_s':case['duration'],'distance_m':case['states'][-1]['distance_m'],'end_kmh':case['states'][-1]['speed_kmh'],'one_visible_vehicle':True})
external=[i.filepath for i in bpy.data.images if i.source=='FILE' and not i.packed_file]
assert not external,external
(R/'author_v3_validation.json').write_text(json.dumps({'scenes':checks,'packed_images':True,'anchor_frame':346,'scope':'Baked coordinates and timestamps match specified equations. Camera metric scale remains conditional.'},ensure_ascii=False,indent=2),'utf-8')
print('AUTHOR V3 VALIDATED',len(checks),flush=True)
