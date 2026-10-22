from pathlib import Path
import cv2
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent
cv2.setNumThreads(1)
groups=[range(65,71),range(105,111),range(126,132),range(155,161),range(306,312),range(337,343),range(366,372),range(396,402)]
wanted={n for g in groups for n in g};frames={}
cap=cv2.VideoCapture(str(R.parent/'assets/source.mp4'),cv2.CAP_FFMPEG,[cv2.CAP_PROP_N_THREADS,1])
n=0
while n<=max(wanted):
 ok,a=cap.read()
 assert ok
 if n in wanted:frames[n]=Image.fromarray(cv2.cvtColor(a,cv2.COLOR_BGR2RGB))
 n+=1
cap.release()
sheet=Image.new('RGB',(1800,8*150),'#101923');d=ImageDraw.Draw(sheet);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
for j,g in enumerate(groups):
 for i,n in enumerate(g):
  crop=frames[n].crop((1110,0,1280,95));crop.thumbnail((290,110));sheet.paste(crop,(i*300,j*150));d.text((i*300+5,j*150+115),f'zero-based frame {n}',font=font)
sheet.save(R/'clock_exact_decode.jpg')
