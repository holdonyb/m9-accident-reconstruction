"""Validate and package only the final, reproducible delivery."""
from pathlib import Path
import json,hashlib,subprocess,zipfile,wave,sys,os
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent
MOVIE=R/'问界M9_路口重建与逐帧测速_B站发布版.mp4'
def run(*args):return subprocess.run(args,capture_output=True,text=True,encoding='utf-8',check=True).stdout
def validate():
    tl=json.loads((R/'timeline_final.json').read_text('utf-8'))
    duration=tl[-1]['start']+tl[-1]['duration'];frames=round(duration*30)
    probe=json.loads(run('ffprobe','-v','error','-show_streams','-show_format','-of','json',str(MOVIE)))
    (R/'video_probe_final.json').write_text(json.dumps(probe,ensure_ascii=False,indent=2),'utf-8')
    v=next(s for s in probe['streams'] if s['codec_type']=='video');a=next(s for s in probe['streams'] if s['codec_type']=='audio')
    assert (v['width'],v['height'],v['r_frame_rate'],int(v['nb_frames']))==(1920,1080,'30/1',frames)
    assert abs(float(probe['format']['duration'])-duration)<.04
    assert a['codec_name']=='aac'
    p=subprocess.run(['ffmpeg','-v','error','-xerror','-threads','1','-i',str(MOVIE),'-filter_threads','1','-threads','1','-f','null','-'],capture_output=True)
    (R/'decode_final.log').write_bytes(p.stderr);assert p.returncode==0 and not p.stderr,p.stderr[-500:]
    audio=[]
    for ch in tl:
        for i,line in enumerate(ch['lines']):
            name=f'{ch["id"]}_{i:02}';meta=json.loads((R/'audio'/f'{name}.json').read_text())
            assert meta['text_sha256']==hashlib.sha256(line.encode()).hexdigest()
            assert meta['audio_sha256']==hashlib.sha256((R/'audio'/f'{name}.wav').read_bytes()).hexdigest()
            audio.append(meta)
    with wave.open(str(R/'narration_final.wav')) as w:
        samples=np.frombuffer(w.readframes(w.getnframes()),'<i2').astype(float)/32768
        wavduration=w.getnframes()/w.getframerate()
    assert abs(wavduration-duration)<.01 and np.max(np.abs(samples))<1
    out=R/'qa_encoded';out.mkdir(exist_ok=True)
    for i,ch in enumerate(tl):
        t=ch['start']+min(ch['duration']*.55,8)
        run('ffmpeg','-v','error','-y','-threads','1','-ss',str(t),'-i',str(MOVIE),'-frames:v','1','-threads','1',str(out/f'{i:02}_{ch["id"]}.jpg'))
    sheet=Image.new('RGB',(1440,270*((len(tl)+2)//3)),'#09121c');dr=ImageDraw.Draw(sheet);ft=ImageFont.truetype(os.environ.get('M9_FONT_REGULAR','C:/Windows/Fonts/msyh.ttc'),20)
    for i,p in enumerate(sorted(out.glob('*.jpg'))):
        x=(i%3)*480;y=(i//3)*270;sheet.paste(Image.open(p).resize((480,240)),(x,y));dr.text((x+8,y+241),p.stem,font=ft,fill='white')
    sheet.save(R/'完整影片验收总览.jpg',quality=93)
    report=dict(duration_s=duration,frames=frames,resolution=[1920,1080],fps=30,full_decode_passed=True,audio_segments=len(audio),voice='Vertex AI Gemini 3.8 / Charon',wav_peak=float(np.max(np.abs(samples))),wav_duration=wavduration,video_sha256=hashlib.sha256(MOVIE.read_bytes()).hexdigest(),chapters=len(tl))
    if (R/'edit_cache/resume_prefix.mp4').exists():
        import compose_film as composition
        composition.TIMELINE=tl
        prefix=json.loads(run('ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=nb_frames','-of','json',str(R/'edit_cache/resume_prefix.mp4')))
        split=int(prefix['streams'][0]['nb_frames']);errs=[]
        for frame in [split-1,split,split+1]:
            sec=frame/30;ch=next(c for c in tl if round(c['start']*30)<=frame<round((c['start']+c['duration'])*30))
            expected=np.asarray(composition.chapter_frame(ch,(frame-round(ch['start']*30))/30)).astype(np.float32)
            path=R/'qa_encoded'/f'seam_{frame}.png'
            run('ffmpeg','-v','error','-y','-threads','1','-ss',str(sec),'-i',str(MOVIE),'-frames:v','1','-threads','1',str(path))
            decoded=np.asarray(Image.open(path).convert('RGB')).astype(np.float32)
            error=float(np.mean(np.abs(expected-decoded)));assert error<6,error;errs.append(dict(frame=frame,mean_pixel_error=error))
        report['resume_seam_verified']=errs
    (R/'validation_final.json').write_text(json.dumps(report,indent=2),'utf-8')
    print(json.dumps(report,indent=2))
def package():
    names=['问界M9_路口重建与逐帧测速_B站发布版.mp4','神木路口_原图环境与十一种物理假设.blend','神木路口_完整成片与仿真.blend','site_after_user.png','physics.py','build_physics_blender.py','render_physics.py','compose_film.py','tts_vertex.py','finalize_project.py','check_delivery.py','check_blend_delivery.py','scene_calibration.json','physics_results.json','vehicle_simulation.xml','physics_validation.json','blender_validation.json','blend_delivery_validation.json','video_probe_final.json','validation_final.json','script.json','timeline_final.json','shots_physics.json','angle_projection.json','projection_physics.json','requirements.txt','README.md','PROJECT_STATUS.md','逐帧仿真数据.csv','五帧区间比较.csv','完整讲解.srt','narration_final.wav','sources.json','完整影片验收总览.jpg']
    names+=['side_camera_validation.json','fix_side_camera.py','speed_panels.py','calculate_speed_workings.py','速度推导计算.json','速度推导逐帧表.csv','测速推导说明.md']
    names+=['motion_speed.py','alternative_panels.py','section_design.py','alternative_speeds.py','alternative_results.json','contact_ledger.json','extend_blender.py','alternatives_blender_validation.json','逐点动画计算.json','争议算法核对.md','REPRODUCE_PROMPT.md','reproduce.py','完整口播_Argon审稿后.md','argon_review_receipt.json','argon_transitions_receipt.json','argon_review_application.json','B站封面.png']
    names.remove('PROJECT_STATUS.md')
    names+=['check_editorial.py','editorial_validation.json']
    files=[R/n for n in names]+list((R/'assets').rglob('*'))+list((R/'calibration_audit').glob('*'))
    for ch in json.loads((R/'script.json').read_text('utf-8')):
        for i in range(len(ch['lines'])):
            files.extend([R/'audio'/f'{ch["id"]}_{i:02}{ext}' for ext in ['.wav','.json']])
    target=R/'问界M9_Blender与MuJoCo完整工程.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=4) as z:
        for p in files:
            if p.is_file():z.write(p,p.relative_to(R))
            elif not p.exists():raise FileNotFoundError(p)
    with zipfile.ZipFile(target) as z:assert z.testzip() is None;count=len(z.namelist())
    print('ZIP VERIFIED',count,'files',target.stat().st_size,'bytes',target)
if __name__=='__main__':
    {'validate':validate,'package':package}[sys.argv[1]]()
