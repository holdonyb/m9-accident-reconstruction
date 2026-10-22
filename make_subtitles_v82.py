from pathlib import Path
import sys,json
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P/'peer_review'))
from compose_review import linewrap
def timestamp(t):
 ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
for root in [P/'peer_review',P/'qa_episode']:
 t=json.loads((root/'timeline.json').read_text('utf-8'));out=[];n=0
 for ch in t:
  for p in ch['parts']:
   chunks=linewrap(p['text']);L=sum(map(len,chunks));a=ch['start']+p['start']
   for s in chunks:
    b=a+(p['end']-p['start'])*len(s)/L;n+=1;out.append(f'{n}\n{timestamp(a)} --> {timestamp(b)}\n{s}\n');a=b
 (root/'subtitles.srt').write_text('\n'.join(out),'utf-8');print(root.name,n,'subtitle cues')
