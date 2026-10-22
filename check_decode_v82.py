from pathlib import Path
import cv2,subprocess,io,json
import numpy as np
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parent;R=P/'peer_review';out=R/'canonical_frames';out.mkdir(exist_ok=True)
cv2.setNumThreads(1)
wanted=[68,106,107,108,128,157,308,339,340,346,347,350,357,362,368,398]
cap=cv2.VideoCapture(str(P/'assets/source.mp4'),cv2.CAP_FFMPEG,[cv2.CAP_PROP_N_THREADS,1]);frames={}
for n in range(max(wanted)+1):
 ok,a=cap.read();assert ok
 if n in wanted:
  frames[n]=cv2.cvtColor(a,cv2.COLOR_BGR2RGB);Image.fromarray(frames[n]).save(out/f'{n:04}.png')
cap.release()
rows=[];sheet=Image.new('RGB',(1500,len(wanted)*110));d=ImageDraw.Draw(sheet)
for k,n in enumerate(wanted):
 data=subprocess.check_output(['ffmpeg','-v','error','-threads','1','-i',str(P/'assets/source.mp4'),'-vf',f'select=eq(n\\,{n})','-vsync','0','-frames:v','1','-threads','1','-f','image2pipe','-c:v','png','pipe:1'])
 old=Image.open(io.BytesIO(data)).convert('RGB');a=np.asarray(old)
 row={'frame':n,'ffmpeg_vs_opencv_mae':float(np.abs(a.astype(float)-frames[n]).mean())}
 raw=R/'raw_sequence'/f'{n:04}.jpg'
 if raw.exists():row['raw_jpeg_vs_opencv_mae']=float(np.abs(np.asarray(Image.open(raw)).astype(float)-frames[n]).mean())
 for j,im in enumerate([Image.fromarray(frames[n]),old]):sheet.paste(im.crop((860,0,1280,100)),(100+j*500,k*110))
 d.text((5,k*110+40),str(n));rows.append(row)
sheet.save(out/'decoder_comparison.jpg');(out/'decoder_comparison.json').write_text(json.dumps(rows,indent=2),'utf-8');print(json.dumps(rows))
