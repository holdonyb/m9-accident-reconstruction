"""Match visible author stills to continuously decoded original frames via background registration."""
from pathlib import Path
import cv2,numpy as np,json
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;O=R/'teacher_input_audit';cv2.setNumThreads(1)
sift=cv2.SIFT_create(nfeatures=2500);matcher=cv2.BFMatcher();results=[]
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',22)
for sec,roi,label in [(44,(305,320,480,470),'author53'),(45,(300,310,480,470),'author54'),(46,(260,260,440,425),'author57'),(47,(240,230,395,365),'author61'),(59,(210,185,330,300),'author69'),(62,(160,115,270,210),'author88'),(67,(105,100,200,180),'author102'),(72,(105,90,185,160),'author111')]:
 ref=cv2.imread(str(O/f'author_{sec}.png'));gray=cv2.cvtColor(ref,cv2.COLOR_BGR2GRAY);mask=np.zeros(gray.shape,np.uint8);mask[65:470,:480]=255;x1,y1,x2,y2=roi;mask[y1:y2,x1:x2]=0
 kr,dr=sift.detectAndCompute(gray,mask);scores=[]
 for n in range(320,405):
  raw=cv2.imread(str(R/'raw_sequence'/f'{n:04}.jpg'));g=cv2.cvtColor(raw,cv2.COLOR_BGR2GRAY);ks,ds=sift.detectAndCompute(g,None)
  pairs=matcher.knnMatch(ds,dr,k=2);good=[a for a,b in pairs if a.distance<.72*b.distance]
  if len(good)<8:continue
  H,inlier=cv2.findHomography(np.float32([ks[m.queryIdx].pt for m in good]),np.float32([kr[m.trainIdx].pt for m in good]),cv2.RANSAC,3)
  if H is None:continue
  warped=cv2.warpPerspective(raw,H,(720,720));a=cv2.cvtColor(warped,cv2.COLOR_BGR2GRAY)[y1:y2,x1:x2].astype(float);b=gray[y1:y2,x1:x2].astype(float)
  # Compare gradient structure after background-only registration; author overlay is masked.
  color=ref[y1:y2,x1:x2];keep=~((color[:,:,0]>color[:,:,2]*1.3)&(color[:,:,0]>90))
  aa=cv2.GaussianBlur(a,(5,5),0);bb=cv2.GaussianBlur(b,(5,5),0);aa=(aa-aa[keep].mean())/(aa[keep].std()+1);bb=(bb-bb[keep].mean())/(bb[keep].std()+1);score=float(np.mean((aa[keep]-bb[keep])**2))
  scores.append(dict(frame=n,score=score,inliers=int(inlier.sum()),matrix=H.tolist()))
 scores.sort(key=lambda x:x['score']);results.append(dict(author_label=label,source_video_second=sec,roi=roi,candidates=scores[:8],method='background SIFT homography; normalized grayscale ROI difference; visually verify'))
 sheet=Image.new('RGB',(1440,1000),'#111');d=ImageDraw.Draw(sheet)
 refpatch=Image.fromarray(cv2.cvtColor(ref[y1:y2,x1:x2],cv2.COLOR_BGR2RGB));refpatch=refpatch.resize((360,310));sheet.paste(refpatch,(0,35));d.text((10,5),f'{label} author still',font=font,fill='white')
 for k,row in enumerate(scores[:7]):
  raw=cv2.imread(str(R/'raw_sequence'/f"{row['frame']:04}.jpg"));w=cv2.warpPerspective(raw,np.array(row['matrix']),(720,720));patch=Image.fromarray(cv2.cvtColor(w[y1:y2,x1:x2],cv2.COLOR_BGR2RGB)).resize((360,310));idx=k+1;x=idx%4*360;y=idx//4*350;sheet.paste(patch,(x,y+35));d.text((x+10,y+5),f"raw {row['frame']} score {row['score']:.3f}",font=font,fill='white')
 sheet.save(O/f'{label}_matches.jpg',quality=95)
 print(label,[(r['frame'],round(r['score'],3),r['inliers']) for r in scores[:8]],flush=True)
(O/'frame_matches.json').write_text(json.dumps(results,indent=2),'utf-8')
