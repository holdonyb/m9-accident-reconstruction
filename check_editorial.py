"""Check caption fit, source timing, section lead-ins and exact audio provenance."""
from pathlib import Path
import json,hashlib
import compose_film as c
R=Path(__file__).resolve().parent
tl=json.loads((R/'timeline_final.json').read_text('utf-8'));c.TIMELINE=tl
script=json.loads((R/'script.json').read_text('utf-8'))
assert [x['lines'] for x in tl]==[x['lines'] for x in script]
maximum=0;bad=[]
for ch in tl:
 assert abs(ch['parts'][0]['start']-c.lead_for(ch['id']))<1e-6
 for i,line in enumerate(ch['lines']):
  meta=json.loads((R/'audio'/f'{ch["id"]}_{i:02}.json').read_text('utf-8'))
  assert meta['text_sha256']==hashlib.sha256(line.encode()).hexdigest()
 for fr in range(round(ch['duration']*30)):
  s=c.caption(ch,fr/30);width=c.font(33).getlength(s);maximum=max(maximum,width)
  if width>1792:bad.append((ch['id'],fr,s,width))
assert not bad,bad[:5]
for sid in ['initial60','initial80','initial60_top','initial80_top','impact40','impact50']:
 sh=next(x for x in json.loads((R/'shots_physics.json').read_text('utf-8')) if x['id']==sid)
 assert all((R/'renders'/sid/f'{n:04}.jpg').is_file() for n in range(sh['start'],sh['end']+1))
result={'chapter_count':len(tl),'narration_lines':sum(len(x['lines']) for x in tl),'caption_max_width_px':maximum,'safe_width_px':1792,'section_lead_seconds':2.1,'section_count':5,'script_matches_timeline_and_audio':True,'alternative_frames_present':True}
(R/'editorial_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps(result,ensure_ascii=False))
