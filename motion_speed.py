"""Deterministic motion graphics: actual image samples -> arithmetic -> plotted points."""
import json,math
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent
OBS={o['frame']:o for o in json.loads((R/'assets/observations.json').read_text('utf-8'))}
K=json.loads((R/'scene_calibration.json').read_text('utf-8'))['projection']['K']
ST=json.loads((R/'physics_results.json').read_text('utf-8'))['scenarios'][0]['states']
def ease(t):
 t=max(0,min(1,t));return 1-(1-t)**3
def lerp(a,b,t):return a+(b-a)*t
def point(a,b):
 za=K/OBS[a]['tail_y_px'];zb=K/OBS[b]['tail_y_px'];return za,zb,(zb-za)/((b-a)/30)*3.6
WINDOWS=[(n,n+5) for n in range(344,389,5)]
def draw(im,ch,t,part,lt,ld,g):
 txt,rect,line,pill,paste,raw=[g[n] for n in ['txt','rect','line','pill','paste','raw']]
 FG,MUT,CYAN,GOLD,RED,BG=[g[n] for n in ['FG','MUT','CYAN','GOLD','RED','BG']]
 dr=ImageDraw.Draw(im);sid=ch['id']
 def arrow(a,b,col=CYAN):
  line(im,[a,b],col,3);dx,dy=b[0]-a[0],b[1]-a[1];l=max(1,math.hypot(dx,dy));ux,uy=dx/l,dy/l
  dr.polygon([b,(b[0]-12*ux+6*uy,b[1]-12*uy-6*ux),(b[0]-12*ux-6*uy,b[1]-12*uy+6*ux)],fill=col)
 def card(n,box,active=False,measure=False):
  x,y,w,h=box
  rect(im,(x+9,y+12,x+w+9,y+h+12),'#040b12',radius=10)
  rect(im,(x-4,y-4,x+w+4,y+h+4),GOLD if active else '#273c4e',radius=8)
  paste(im,raw(n),box)
  pill(im,x+8,y+8,f'{n} 帧 · {n/30:.3f} s',GOLD if active else CYAN)
  if measure:
   yy=y+OBS[n]['tail_y_px']/720*h
   line(im,[(x+12,yy),(x+w-12,yy)],GOLD,3)
   # Image points retain the measured vertical coordinate. Horizontal is only an ROI seed.
   xx=x+OBS[n]['x_seed_px']/1280*w
   dr.ellipse((xx-8,yy-8,xx+8,yy+8),outline=CYAN,width=3)
   txt(im,(x+15,y+h-40),f'y = {OBS[n]["tail_y_px"]:.0f} px',26,GOLD,True)
 def plot(box,reveal=1,highlight=None):
  x,y,w,h=box
  def pp(sec,v):return (x+(sec-344/30)/1.633333*w,y+h-(v-60)/130*h)
  for v in [80,100,120,140,160,180]:
   yy=pp(344/30,v)[1];line(im,[(x,yy),(x+w,yy)],'#243746',1);txt(im,(x-16,yy-13),v,22,MUT,anchor='ra')
  for sec in [11.5,12,12.5,13]:
   xx=pp(sec,60)[0];txt(im,(xx,y+h+13),f'{sec:.1f}s',22,MUT,anchor='ma')
  pts=[pp(344/30+s['t'],s['speed_kmh']) for s in ST[:49]]
  line(im,pts[:max(2,round(len(pts)*min(1,reveal)))],GOLD,4)
  for j,(a,b) in enumerate(WINDOWS):
   if j/len(WINDOWS)>reveal:continue
   p=pp((a+b)/60,point(a,b)[2]);dr.ellipse((p[0]-5,p[1]-5,p[0]+5,p[1]+5),fill=CYAN)
  if highlight:
   a,b=highlight;p=pp((a+b)/60,point(a,b)[2]);line(im,[(p[0],y+h),p],CYAN,2);dr.ellipse((p[0]-10,p[1]-10,p[0]+10,p[1]+10),outline=FG,width=3)
  return pp
 if sid=='speed_points':
  # Four sequential visual beats, paced by the corresponding spoken sentence.
  a,b=352,357;za,zb,v=point(a,b)
  if part==0:
   for j,n in enumerate(range(352,358)):
    q=ease((lt-j*.10)/.7);x=64+j*301;y=220+70*(1-q)
    card(n,(x,y,280,158),n in (352,357))
    txt(im,(x+140,395),f'{n-352}/30 秒',23,MUT,anchor='ma')
   q=ease((lt-1)/1.8)
   for n,x in [(352,110),(357,1060)]:
    original_x=64+(n-352)*301
    box=(lerp(original_x,x,q),lerp(220,468,q),lerp(280,750,q),lerp(158,422,q));card(n,box,True,q>.8)
   txt(im,(960,424),'首尾两帧之间：5 个间隔 = 0.1667 s',31,CYAN,True,anchor='ma')
  elif part==1:
   for n,x,z in [(352,70,za),(357,1010,zb)]:
    card(n,(x,225,840,473),True,True)
    yy=OBS[n]['tail_y_px'];u=OBS[n]['x_seed_px']
    crop=raw(n).crop((max(0,int(u)-75),int(yy)-60,min(1280,int(u)+75),int(yy)+35))
    paste(im,crop,(x+520,710,320,203))
    txt(im,(x+10,740),f'{yy:.0f} px',48,GOLD,True)
    txt(im,(x+10,811),f'→ {z:.2f} m',49,CYAN,True)
   txt(im,(960,704),'Z = 17,190.38 ÷ y',29,FG,True,anchor='ma')
  elif part==2:
   q=ease(lt/1.2)
   for x,z,label in [(150,za,'第352帧'),(1090,zb,'第357帧')]:
    rect(im,(x,235,x+680,430),'#142b3d',radius=18);txt(im,(x+32,260),label,26,MUT)
    txt(im,(x+32,315),f'{z:.2f} m',72,CYAN,True)
   arrow((490,430),(lerp(490,830,q),lerp(430,505,q)))
   arrow((1430,430),(lerp(1430,1090,q),lerp(430,505,q)))
   if lt>.4:
    u=ease((lt-.4)/.6);txt(im,(960,530+25*(1-u)),f'{zb:.2f} − {za:.2f} = {zb-za:.2f} m',65,FG,True,anchor='ma')
   if lt>ld*.20:
    u=ease((lt-ld*.20)/.7);txt(im,(960,650+25*(1-u)),f'{zb-za:.2f} ÷ 0.1667 × 3.6',58,GOLD,True,anchor='ma')
   if lt>ld*.44:
    u=ease((lt-ld*.44)/.9);rect(im,(580,746,1340,869),'#193442',radius=16)
    txt(im,(960,750+24*(1-u)),f'≈ {v:.0f} km/h',92,GOLD,True,anchor='ma')
    txt(im,(960,890),'这个点代表五帧间的纵深平均速度',29,MUT,anchor='ma')
  else:
   pp=plot((145,310,1620,460),ease(lt/4),highlight=(352,357))
   dest=pp(354.5/30,v);q=ease(lt/1.8);p=(lerp(960,dest[0],q),lerp(230,dest[1],q))
   rad=15+9*(.5+.5*math.sin(t*3));dr.ellipse((p[0]-rad,p[1]-rad,p[0]+rad,p[1]+rad),outline='#275d62',width=2)
   dr.ellipse((p[0]-11,p[1]-11,p[0]+11,p[1]+11),fill=CYAN);pill(im,p[0]+18,p[1]-20,'129',CYAN)
   txt(im,(160,225),'同样的计算，沿时间轴继续做',38,FG,True)
   txt(im,(160,849),'● 青点：五帧纵深差分',29,CYAN,True)
   txt(im,(1000,849),'━ 金线：连续动力学瞬时速度',29,GOLD,True)
   txt(im,(160,900),'每个青点落在对应时间窗口的中间；短窗波动交给整段画面检验。',25,MUT)
 elif sid=='speed_80':
  if part<2:
   a,b=(384,389) if part==0 else (344,349);za,zb,v=point(a,b)
   for n,x in [(a,70),(b,1010)]:card(n,(x,225,840,473),True,True)
   u=ease(lt/1.3)
   txt(im,(960,723),f'({zb:.2f} − {za:.2f}) ÷ 0.1667 × 3.6',44,FG,True,anchor='ma')
   txt(im,(960,795),f'≈ {v*u:.0f} km/h',83,GOLD,True,anchor='ma')
   pill(im,80,867,'所取时段：'+f'{a/30:.3f} — {b/30:.3f} s',CYAN)
   txt(im,(1840,878),'相同标定 · 相同五帧算法',27,MUT,anchor='ra')
  else:
   za,zb,v=point(352,357);dt=5/30
   txt(im,(100,220),'固定同一个时间窗口：第352—357帧',35,FG,True)
   for j,(vv,dd,col) in enumerate([(80,80/3.6*dt,CYAN),(v,zb-za,GOLD)]):
    y=345+j*230;txt(im,(100,y),f'{vv:.0f} km/h',62,col,True)
    width=dd/6*1040*ease(lt/1.5);rect(im,(550,y+7,550+width,y+76),col,radius=8)
    txt(im,(550+width+25,y+20),f'{dd:.2f} m',40,col,True)
   txt(im,(100,815),'对齐时间  →  对齐特征点  →  对齐定尺依据',43,FG,True)
   txt(im,(100,889),'80 与 129 的距离换算相差约 38%；先比较测量过程，再比较结论。',28,MUT)
 return im

def audit():
 records=[dict(start=a,end=b,seconds=(b-a)/30,z_start=point(a,b)[0],z_end=point(a,b)[1],depth_mean_kmh=point(a,b)[2],plot_time=(a+b)/60) for a,b in WINDOWS+[(352,357)]]
 assert abs(point(384,389)[2]-73.555)<.1
 report={'raw_window_points':records,'80_kmh_distance_over_5_frames':80/3.6*(5/30),'notes':'青点是相同条件标定下的纵深差分，金线为MuJoCo瞬时速度，二者不是同一种测量。74示例位于后段，未获得外部80算法，不能推定其取帧或尺度。'}
 (R/'逐点动画计算.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
if __name__=='__main__':audit()
