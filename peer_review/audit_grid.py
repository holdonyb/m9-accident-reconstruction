"""Audit the displayed grid using independent road-line geometry, not a speed target.

Manual point annotations are saved, and a sensitivity range is computed.
This tests a visible explanatory overlay; it does not recover the author's
unpublished calibration or measure the vehicle's actual speed.
"""
from pathlib import Path
import cv2, numpy as np,json
from PIL import Image,ImageDraw,ImageFont
cv2.setNumThreads(1)
R=Path(__file__).resolve().parent;O=R/'teacher_input_audit'
ref=cv2.imread(str(O/'author_42.png'));raw=cv2.imread(str(R/'raw_sequence/0320.jpg'))
sift=cv2.SIFT_create(nfeatures=4000);mask=np.zeros((720,720),np.uint8);mask[65:470,:485]=255
kr,dr=sift.detectAndCompute(cv2.cvtColor(ref,cv2.COLOR_BGR2GRAY),mask)
ks,ds=sift.detectAndCompute(cv2.cvtColor(raw,cv2.COLOR_BGR2GRAY),None)
pairs=cv2.BFMatcher().knnMatch(ds,dr,k=2);good=[a for a,b in pairs if a.distance<.72*b.distance]
H,valid=cv2.findHomography(np.float32([ks[m.queryIdx].pt for m in good]),np.float32([kr[m.trainIdx].pt for m in good]),cv2.RANSAC,2)
assert valid.sum()>30
def project(p,H):
 a=np.c_[np.asarray(p),np.ones(len(p))]@H.T
 return a[:,:2]/a[:,2,None]
def meet(a,b):
 x=np.cross(np.cross(np.r_[a[0],1],np.r_[a[1],1]),np.cross(np.r_[b[0],1],np.r_[b[1],1]));return x[:2]/x[2]
# Cyan major-line crossings, manual screen coordinates in author 42-second still.
quad=np.float32([[179,229],[378,245],[487,414],[166,388]])
rect=cv2.getPerspectiveTransform(quad,np.float32([[0,0],[1,0],[1,1],[0,1]]))
# The two flanks of the SAME near lane, sampled on continuous paint visible in raw 320.
lanes=np.array([[[551,705],[606,483]],[[931,705],[853,493]]],float)
pl=project(lanes.reshape(-1,2),H).reshape(2,2,2)
gv=meet([quad[0],quad[3]],[quad[1],quad[2]])
gh=meet([quad[0],quad[1]],[quad[3],quad[2]])
rv=meet(pl[0],pl[1]);horizon=np.cross(np.r_[gv,1],np.r_[gh,1]);horizon/=np.linalg.norm(horizon[:2])
res=float(abs(horizon@np.r_[rv,1]))
rng=np.random.default_rng(23);samples=[]
for i in range(5000):
 q=quad+rng.uniform(-2,2,(4,2));lp=lanes+rng.uniform(-4,4,(2,2,2));v=meet(project(lp[0],H),project(lp[1],H));g=meet([q[0],q[3]],[q[1],q[2]]);hh=meet([q[0],q[1]],[q[3],q[2]])
 h=np.cross(np.r_[g,1],np.r_[hh,1]);h/=np.linalg.norm(h[:2]);samples.append(abs(h@np.r_[v,1]))
out=dict(author_second=42,raw_frame=320,registration_inliers=int(valid.sum()),image_registration=H.tolist(),grid_crossings_px=quad.tolist(),road_lane_samples_raw_px=lanes.tolist(),road_lane_samples_author_px=pl.tolist(),grid_forward_vanishing_px=gv.tolist(),grid_transverse_vanishing_px=gh.tolist(),road_lane_vanishing_px=rv.tolist(),grid_horizon_line=horizon.tolist(),road_vanishing_to_grid_horizon_px=res,manual_jitter_sensitivity_p5_p50_p95_px=np.percentile(samples,[5,50,95]).tolist(),scope='Visible overlay consistency test; assumes near lane edges are parallel on a locally planar road. ±2 px grid / ±4 px raw road endpoint jitter is an illustrative annotation sensitivity test, not a statistical confidence interval. Does not identify actual distance or speed; an unpublished different calibration remains untested.')
out['interpretation']='Conditional diagnostic only. Independently verify lane-edge parallelism: taper or widening can also explain a mismatch. Do not present the 72-pixel discrepancy as proven calibration error or as proof of false 5.5 m.'
(O/'grid_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),'utf-8')
# A diagram of measured lines and their intersections, with negative-y room.
im=Image.new('RGB',(1440,1200),'#08131d');d=ImageDraw.Draw(im);font=lambda s:ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',s)
d.text((45,25),'这套方格，能把同一车道拉直吗？',font=font(42),fill='white')
base=Image.fromarray(cv2.cvtColor(ref,cv2.COLOR_BGR2RGB)).crop((0,65,489,470));base=base.resize((880,729));im.paste(base,(40,330));sx=880/489
def screen(p):return (40+p[0]*sx,330+(p[1]-65)*sx)
for line in pl:
 points=project(line,rect)
 for p in line:
  x,y=screen(p);d.ellipse((x-6,y-6,x+6,y+6),fill='#ffce6f')
 end=rv+(line[0]-rv)*((465-rv[1])/(line[0,1]-rv[1]));d.line([screen(rv),screen(end)],fill='#ffce6f',width=4)
for pair in [(quad[0],quad[3]),(quad[1],quad[2])]:d.line([screen(gv),screen(pair[1])],fill='#42dbe6',width=3)
for p,c,label in [(gv,'#42dbe6','方格纵线交点'),(rv,'#ffce6f','车道边线交点')]:
 x,y=screen(p);d.ellipse((x-7,y-7,x+7,y+7),fill=c);d.text((x+15,y-15),label,font=font(23),fill=c)
d.text((960,270),'黄色：原片车道线',font=font(25),fill='#ffce6f');d.text((960,320),'青色：作者方格线',font=font(25),fill='#42dbe6')
lines=['近处同一车道的两条边线','假定在地面上平行。','','它们的交点应落在','网格对应的消失线上。','','本次取点的偏离量：',f'{res:.1f} 像素（作者画幅）','','取点扰动仍有明显差异。','先核验标定，再用它量距离。']
for j,t in enumerate(lines):d.text((960,390+j*39),t,font=font(24),fill='white')
d.text((45,1140),'原视频 42秒；背景配准到本地第320帧。坐标、矩阵和取点扰动计算见 grid_audit.json。',font=font(22),fill='#acbac8')
im.save(O/'grid_audit.jpg',quality=95)
print(json.dumps(out,ensure_ascii=False,indent=2))
