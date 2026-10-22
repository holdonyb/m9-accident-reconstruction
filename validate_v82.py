from pathlib import Path
import json,hashlib,subprocess,sys,wave
P=Path(__file__).resolve().parent
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
for folder,name in [('peer_review','同一段监控_两种车速_算法逐项复核.mp4'),('qa_episode','Astra答B友问_问界M9神木事故.mp4')]:
 if '--main' in sys.argv and folder!='peer_review':continue
 if '--qa' in sys.argv and folder!='qa_episode':continue
 R=P/folder;dest=R/name;script=json.loads((R/'script.json').read_text('utf-8'));t=json.loads((R/'timeline.json').read_text('utf-8'))
 assert [c['lines'] for c in script]==[c['lines'] for c in t]
 seconds=sum(c['duration'] for c in t)
 meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(dest)]));v=next(s for s in meta['streams'] if s['codec_type']=='video');a=next(s for s in meta['streams'] if s['codec_type']=='audio')
 assert (v['width'],v['height'],v['avg_frame_rate'])==(1920,1080,'30/1')
 assert int(v['nb_frames'])==round(seconds*30),(v['nb_frames'],seconds)
 assert abs(float(a['duration'])-seconds)<.1
 checks=[]
 for c in script:
  cache=R/'edit_revision'/f"{c['id']}.done";dur=next(r['duration'] for r in t if r['id']==c['id']);assert abs(float(cache.read_text())-dur)<.01
  for j,text in enumerate(c['lines']):
   wav=R/'audio'/f"{c['id']}_{j:02}.wav";receipt=json.loads(wav.with_suffix('.json').read_text('utf-8'))
   assert receipt['text_sha256']==hashlib.sha256(text.encode()).hexdigest()
   assert receipt['audio_sha256']==sha(wav)
   assert receipt['voice']=='Charon'
   checks.append({'file':wav.name,'sha256':sha(wav),'text_sha256':receipt['text_sha256']})
 result=subprocess.run(['ffmpeg','-v','error','-threads','1','-i',str(dest),'-map','0:v:0','-map','0:a:0','-f','null','-'],capture_output=True,text=True)
 assert result.returncode==0 and not result.stderr.strip(),result.stderr
 if folder=='qa_episode':
  questions=json.loads((R/'anonymous_questions.json').read_text('utf-8'));assert len(questions)==23
  allowed={'index','text','video','kind','context','topic_ids'};assert all(set(x)<=allowed for x in questions)
  for r in json.loads((R/'anonymous_screenshots/manifest.json').read_text('utf-8')):assert sha(R/'anonymous_screenshots'/r['file'])==r['sha256']
 report={'file':name,'sha256':sha(dest),'bytes':dest.stat().st_size,'duration_s':seconds,'frames':int(v['nb_frames']),'resolution':[1920,1080],'fps':30,'chapters':len(t),'voice':'Vertex Charon','audio_segments':checks,'full_decode':'passed','timeline_and_audio_hashes':'passed','anonymous_questions':23 if folder=='qa_episode' else None,'scope':'Media integrity and identity checks; scientific assumptions documented separately.'}
 (R/'validation_v82.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8');print('VALIDATED',folder,seconds,flush=True)
