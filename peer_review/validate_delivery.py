"""Validate the delivered file against its timeline, narration and experiment inputs."""
from pathlib import Path
import json, hashlib, subprocess, wave, math
from PIL import ImageFont
R=Path(__file__).resolve().parent
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def main():
    dest=R/'同一段监控_两种车速_算法逐项复核.mp4'
    meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(dest)]))
    video=next(s for s in meta['streams'] if s['codec_type']=='video')
    audio=next(s for s in meta['streams'] if s['codec_type']=='audio')
    timeline=json.loads((R/'timeline.json').read_text('utf-8'))
    script=json.loads((R/'script.json').read_text('utf-8'))
    expected=sum(c['duration'] for c in timeline)
    assert (video['width'],video['height'])==(1920,1080)
    assert video['avg_frame_rate']=='30/1'
    assert int(video['nb_frames'])==round(expected*30)
    assert abs(float(video['duration'])-expected)<.034
    assert abs(float(audio['duration'])-expected)<.1
    audio_checks=[]
    for chapter in script:
        for j,line in enumerate(chapter['lines']):
            p=R/'audio'/f"{chapter['id']}_{j:02}.wav"
            receipt=json.loads(p.with_suffix('.json').read_text('utf-8'))
            assert receipt['text_sha256']==hashlib.sha256(line.encode()).hexdigest(),p
            assert receipt['audio_sha256']==sha(p),p
            with wave.open(str(p)) as f:
                assert f.getframerate()==24000 and f.getnchannels()==1
                duration=f.getnframes()/f.getframerate()
            audio_checks.append({'file':p.relative_to(R).as_posix(),'sha256':sha(p),'seconds':duration,'voice':receipt['voice']})
    import re
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',35)
    # The compositor splits punctuation phrases to no more than 42 characters.
    for ch in script:
        for line in ch['lines']:
            assert font.getlength('汉'*42)<1860
    means=json.loads((R/'mean_demo.json').read_text('utf-8'))
    for model in means:
        rows=model['states'];a=model['a_ms2'];T=23/30;v0=6.5/T+.5*a*T
        for row in rows:
            t=row['physical_s']
            assert abs(row['distance_m']-(v0*t-.5*a*t*t))<1e-9
            assert abs(row['speed_kmh']-(v0-a*t)*3.6)<1e-9
        assert abs(rows[-1]['distance_m']-6.5)<1e-9
    decode=subprocess.run(['ffmpeg','-v','error','-threads','1','-i',str(dest),'-map','0:v:0','-map','0:a:0','-f','null','-'],capture_output=True,text=True)
    assert decode.returncode==0 and not decode.stderr.strip(),decode.stderr
    result={'file':dest.name,'sha256':sha(dest),'bytes':dest.stat().st_size,'duration_s':float(meta['format']['duration']),'video_duration_s':float(video['duration']),'frames':int(video['nb_frames']),'width':video['width'],'height':video['height'],'fps':video['avg_frame_rate'],'chapters':len(timeline),'audio_segments':audio_checks,'full_decode':'passed','timeline_matches':True,'kinematic_equations':'passed','scope':'Media integrity, text/audio identity and analytic kinematic equations. Does not independently establish accident speed.'}
    (R/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='audio_segments'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
