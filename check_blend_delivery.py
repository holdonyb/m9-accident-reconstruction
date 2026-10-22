import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(R/'神木路口_完整成片与仿真.blend'))
s=bpy.data.scenes['影片_完整分析与章节标记'];tl=json.loads((R/'timeline_final.json').read_text('utf-8'))
assert len(bpy.data.scenes)==14
assert s.frame_end==round((tl[-1]['start']+tl[-1]['duration'])*30)
assert len(s.timeline_markers)==len(tl) and len(s.sequence_editor.strips)==2
assert all(x.use_fake_user for x in bpy.data.scenes)
sound=next(x.sound for x in s.sequence_editor.strips if x.type=='SOUND');assert sound.packed_file
movie=next(x for x in s.sequence_editor.strips if x.type=='MOVIE');assert Path(bpy.path.abspath(movie.filepath)).is_file()
result=dict(scene_count=len(bpy.data.scenes),film_frames=s.frame_end,chapter_markers=len(s.timeline_markers),movie_exists=True,narration_packed=True,packed_images=[im.name for im in bpy.data.images if im.packed_file])
(R/'blend_delivery_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps(result,ensure_ascii=False),flush=True)
