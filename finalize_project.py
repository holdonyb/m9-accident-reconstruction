"""Add the finished film and chapter markers to the portable 3D project."""
import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(R/'神木路口_原图环境与十一种物理假设.blend'))
active=bpy.context.scene
bpy.context.preferences.system.memory_cache_limit=64
tl=json.loads((R/'timeline_final.json').read_text('utf-8'))
film=bpy.data.scenes.new('影片_完整分析与章节标记');film.use_fake_user=True
film.render.resolution_x=1920;film.render.resolution_y=1080;film.render.resolution_percentage=100
film.render.fps=30;film.render.threads_mode='FIXED';film.render.threads=1
film.frame_start=1;film.frame_end=round((tl[-1]['start']+tl[-1]['duration'])*30)
seq=film.sequence_editor_create();movie=R/'问界M9_路口重建与逐帧测速_B站发布版.mp4'
st=seq.strips.new_movie('神木路口：速度、刹车与碰撞',str(movie),channel=1,frame_start=1);st.filepath='//'+movie.name
for ch in tl:film.timeline_markers.new(ch['title'],frame=round(ch['start']*30)+1)
voice=seq.strips.new_sound('Vertex Gemini 3.8 · Charon男声',str(R/'narration_final.wav'),channel=2,frame_start=1);voice.sound.pack();film.render.use_sequencer=True
film['editing']=f'{len(tl)} chapter markers. Graphics and captions: compose_film.py. Narration: script.json. Vehicle dynamics: physics.py. Thirteen editable 3D scenes.'
bpy.context.window.scene=active
bpy.ops.wm.save_as_mainfile(filepath=str(R/'神木路口_完整成片与仿真.blend'))
print('FINAL PROJECT',len(bpy.data.scenes),'scenes',len(seq.strips),'strips',film.frame_end,'frames',flush=True)
