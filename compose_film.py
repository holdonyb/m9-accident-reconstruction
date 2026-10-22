"""Editorial compositor: original frames, solver renders, data, captions and Vertex narration."""
from pathlib import Path
from functools import lru_cache
import json,math,re,wave,subprocess,sys,os
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageOps
from speed_panels import draw as draw_speed
from motion_speed import draw as draw_motion
from alternative_panels import draw as draw_alternatives
from section_design import ACTS,act_for,lead_for,draw_section
R=Path(__file__).resolve().parent;CACHE=R/'renders';OUT=R/'edit_cache';OUT.mkdir(exist_ok=True)
D=json.loads((R/'physics_results.json').read_text('utf-8'));SC={s['id']:s for s in D['scenarios']};SCRIPT=json.loads((R/'script.json').read_text('utf-8'));ANGLES=json.loads((R/'angle_projection.json').read_text('utf-8'))
W,H=1920,1080;FPS=30;SPEED=1.10;BG='#08121e';FG='#eef3f4';MUT='#98abb8';CYAN='#58d2c5';GOLD='#ffbd70';RED='#ff746e';RULE='#263847';BLUE='#78adff';PINK='#e8a6d8'
@lru_cache(64)
def font(size,bold=False):return ImageFont.truetype(os.environ.get('M9_FONT_BOLD' if bold else 'M9_FONT_REGULAR','C:/Windows/Fonts/msyhbd.ttc' if bold else 'C:/Windows/Fonts/msyh.ttc'),size)
def txt(im,xy,text,size=30,col=FG,bold=False,anchor=None):ImageDraw.Draw(im).text(xy,str(text),font=font(size,bold),fill=col,anchor=anchor)
def rect(im,box,col,outline=None,radius=0):
 dr=ImageDraw.Draw(im)
 if radius:dr.rounded_rectangle(box,radius=radius,fill=col,outline=outline,width=2)
 else:dr.rectangle(box,fill=col,outline=outline,width=2)
def line(im,pts,col=RULE,width=2):ImageDraw.Draw(im).line(pts,fill=col,width=width,joint='curve')
def pill(im,x,y,t,col=CYAN):
 b=ImageDraw.Draw(im).textbbox((0,0),t,font=font(23));ww=b[2]+28;rect(im,(x,y,x+ww,y+40),'#122735',radius=7);txt(im,(x+14,y+6),t,23,col);return ww
@lru_cache(8)
def img(path):return Image.open(path).convert('RGB')
def paste(im,source,box,fit=False):
 x,y,w,h=map(int,box);a=source if isinstance(source,Image.Image) else img(str(source))
 if fit:a=ImageOps.fit(a,(w,h),method=Image.Resampling.BICUBIC)
 else:a=ImageOps.contain(a,(w,h),method=Image.Resampling.BICUBIC)
 im.paste(a,(x+(w-a.width)//2,y+(h-a.height)//2))
def render_img(sid,fr):
 p=CACHE/sid/f'{max(1,min(151 if sid=="angle" else 121 if sid=="orbit" else 91,int(fr))):04}.jpg'
 if not p.exists():
  q=R/'qa_physics'/f'{sid}.jpg'
  if q.exists():return img(str(q))
  return img(str(R/'qa_physics/top.jpg'))
 return img(str(p))
def raw(n):return img(str(R/'assets/stable_png'/f'{max(330,min(450,int(n))):04}.png'))
def state(n,sid='base'):return SC[sid]['states'][max(0,min(90,int(n)-344))]
def playback(t,start=344,end=434,lead=.30,hold=.8,rate=1):
 play=(end-start)/30/rate;cy=lead+play+hold;u=t%cy;f=start+int(max(0,min(play,u-lead))*30*rate+1e-7);return f,('1× 正常速度' if rate==1 else f'逐帧 {rate:g}×') if lead<=u<lead+play else '定格'
def source_label(im,x,y,t):pill(im,x,y,t,MUT)
def metrics(im,n,y=823):
 st=state(n);rect(im,(64,y,1856,y+100),'#101f2c',radius=12)
 vals=[('原片时间',f'{n/30:06.3f} s',FG),('仿真速度',f'{st["speed_kmh"]:.0f} km/h',GOLD),('累计路程',f'{st["distance_m"]:.1f} m',CYAN),('制动输入','施加中' if st['brake_command']>0 else '尚未施加',RED if st['brake_command']>0 else MUT)]
 for j,(a,b,c) in enumerate(vals):xx=90+j*447;txt(im,(xx,y+12),a,22,MUT);txt(im,(xx,y+41),b,34,c,True)
def pair(im,n,right='cctv',badge='1× 正常速度',bottom=True):
 for x,label,a in [(64,'原片 · 仅稳像',raw(n)),(984,'物理仿真 · '+{'cctv':'监控方向','follow':'后侧跟拍','side':'路边固定','top':'全程俯视','curb':'路缘近景'}.get(right,right),render_img(right,n-343))]:
  rect(im,(x,204,x+872,694),'#111f2a');paste(im,a,(x,204,872,490));pill(im,x+14,218,label)
 pill(im,64,724,badge,GOLD);txt(im,(984,732),'相同时间 · 同一组输入',25,MUT)
 if bottom:metrics(im,n)
def titlebase(ch,idx):
 yy=np.linspace(0,1,H)[:,None,None];top=np.array([7,16,27])[None,None,:];bot=np.array([13,28,42])[None,None,:];arr=np.repeat((top*(1-yy)+bot*yy).astype('uint8'),W,axis=1);im=Image.fromarray(arr)
 act=act_for(ch['id']);txt(im,(64,34),f'{act+1:02} / 05  {ACTS[act][0]}   ·   神木路口',23,MUT);txt(im,(1856,34),f'{idx+1:02} / {len(SCRIPT):02}',23,MUT,anchor='ra')
 txt(im,(64,78),ch['title'],47,FG,True);txt(im,(66,143),ch['tag'],23,CYAN);line(im,[(64,184),(1856,184)],RULE)
 return im
@lru_cache(2)
def cached_base(sid):
 idx=next(i for i,ch in enumerate(SCRIPT) if ch['id']==sid)
 return titlebase(SCRIPT[idx],idx)
def audio_timeline():
 timeline=[];full=[];clock=0;rate=24000
 for ch in SCRIPT:
  start=clock;parts=[];lead=lead_for(ch['id']);full.append(np.zeros(round(lead*rate),np.float32));clock+=lead
  for i,words in enumerate(ch['lines']):
   src=R/'audio'/f'{ch["id"]}_{i:02}.wav';dst=OUT/f'{ch["id"]}_{i:02}_tempo.wav'
   subprocess.run(['ffmpeg','-v','error','-y','-i',str(src),'-af',f'atempo={SPEED}','-ar','24000','-ac','1',str(dst)],check=True)
   with wave.open(str(dst)) as w:a=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(np.float32)/32768
   dur=len(a)/rate;parts.append(dict(start=clock-start,end=clock-start+dur,text=words));full.append(a);clock+=dur;full.append(np.zeros(round(.16*rate),np.float32));clock+=.16
  # quantize each chapter to whole video frames
  target=math.ceil(max(clock+.45,start+10.5 if ch['id']=='replay' else clock+.45)*30)/30;full.append(np.zeros(round((target-clock)*rate),np.float32));clock=target
  timeline.append(dict(**ch,start=start,duration=clock-start,parts=parts))
 a=np.concatenate(full);t=np.arange(len(a))/rate
 # Original minimal ambient bed, no borrowed music or fake impact sounds.
 env=np.minimum(1,t/2)*np.minimum(1,(t[-1]-t)/2)
 bed=(np.sin(2*np.pi*65.406*t)+.35*np.sin(2*np.pi*98*t)+.2*np.sin(2*np.pi*130.81*t))*.0025*(.7+.3*np.sin(2*np.pi*.08*t))*env
 a=np.clip(a+bed,-.98,.98)
 with wave.open(str(OUT/'mix_raw.wav'),'wb') as w:w.setparams((1,2,rate,0,'NONE','NONE'));w.writeframes((a*32767).astype('<i2').tobytes())
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(OUT/'mix_raw.wav'),'-af','loudnorm=I=-16:TP=-1.5:LRA=7','-ar','48000',str(R/'narration_final.wav')],check=True)
 (R/'timeline_final.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2),'utf-8');return timeline

def caption(ch,t):
 for p in ch['parts']:
  if p['start']<=t<=p['end']:
   chunks=re.findall(r'[^，。；！？]+[，。；！？]?',p['text']);groups=[];buf=''
   for c in chunks:
    if len(buf)+len(c)>32 and buf:groups.append(buf);buf=c
    else:buf+=c
   if buf:groups.append(buf)
   total=sum(len(c) for c in groups);u=(t-p['start'])/(p['end']-p['start'])*total
   for c in groups:
    if u<=len(c):return c
    u-=len(c)
 return ''
def whichpart(ch,t):
 for i,p in enumerate(ch['parts']):
  if t<p['end']+.22:return i,max(0,t-p['start']),p['end']-p['start']
 return len(ch['parts'])-1,t-ch['parts'][-1]['start'],ch['parts'][-1]['end']-ch['parts'][-1]['start']
def top_path(im,box,sid,n,col):
 x,y,w,h=box;pts=[]
 # The top camera is a fixed orthographic camera, rotated 90 degrees.
 for st in SC[sid]['states'][:max(1,n-343)]:
  wx,wy=st['position'][:2];px=.5+(wy-1)/87;py=.5+(wx-1)/(87*9/16);pts.append((x+px*w,y+py*h))
 if len(pts)>1:line(im,pts,col,3)
 if pts:xx,yy=pts[-1];ImageDraw.Draw(im).ellipse((xx-5,yy-5,xx+5,yy+5),fill=col)
def chapter_frame(ch,t):
 sid=ch['id'];im=cached_base(sid).copy();part,lt,ld=whichpart(ch,t)
 if sid=='credits':
  paste(im,render_img('orbit',min(121,1+int(t*25))),(70,225,1000,562))
  for j,(a,b) in enumerate([('建模与镜头','Blender'),('车辆运动与接触','MuJoCo'),('男声讲解','Gemini TTS · Charon'),('工程与逐帧计算','GitHub · 简介内下载')]):
   yy=250+j*155;txt(im,(1180,yy),a,25,MUT);txt(im,(1180,yy+48),b,39,GOLD if j==3 else FG,True)
  txt(im,(88,850),'换一组参数，再看结果。',43,CYAN,True)
 elif sid in ('claims','low_initial','low_impact','contact_results'):
  im=draw_alternatives(im,ch,t,part,lt,ld,globals())
 elif sid in ('speed_points','speed_80'):
  im=draw_motion(im,ch,t,part,lt,ld,globals())
 elif sid.startswith('speed_'):
  im=draw_speed(im,ch,t,part,lt,globals())
 elif sid=='opening':
  n,mode=playback(t);pair(im,n,'cctv' if part==0 else 'follow',mode);pill(im,1480,724,'条件仿真',GOLD)
 elif sid=='title':
  shot=img(str(R/'assets/original_0350.jpg'));z=1.025+.045*min(1,t/ch['duration']);cw=int(1280/z);chh=int(720/z);xx=(1280-cw)//2;yy=(720-chh)//2
  im=shot.crop((xx,yy,xx+cw,yy+chh)).resize((1920,1080),Image.Resampling.BICUBIC)
  shade=np.zeros((1080,1920,4),dtype=np.uint8);shade[:,:,:3]=[3,11,20];shade[:,:,3]=np.linspace(238,110,1920,dtype=np.uint8)[None,:];im=Image.alpha_composite(im.convert('RGBA'),Image.fromarray(shade)).convert('RGB')
  txt(im,(110,112),'事故影像分析  /  问界 M9',27,CYAN);line(im,[(110,205),(110+int(310*min(1,t/1.3)),205)],GOLD,5)
  txt(im,(105,255),'看着没那么快？',94,FG,True);txt(im,(110,402),'把路口还原，再算一次',66,GOLD,True)
  txt(im,(113,550),'陕西 · 榆林 · 神木',29,GOLD);txt(im,(113,601),'云川大道 × 滨河西路',34,FG)
  txt(im,(114,766),'逐帧测速  /  Blender 建模  /  MuJoCo 仿真',29,MUT);txt(im,(1800,865),'题图：原片定格',21,MUT,anchor='ra')
 elif sid=='overview':
  n=min(540,330+int(max(0,t-.5)*30));paste(im,R/'assets'/f'original_{n:04}.jpg',(64,210,1280,720));pill(im,84,229,'原片 1× · 事故过程' if n<540 else '原片定格',GOLD)
  txt(im,(1400,240),'先看发生顺序',32,FG,True)
  events=[('驶向路口','11.47 s',344),('高位灯亮','11.90 s',357),('抬起、偏转','13.13–13.20 s',394),('后续出现火光','原片后续画面',450)]
  line(im,[(1414,337),(1414,781)],RULE,4)
  for j,(a,b,k) in enumerate(events):
   yy=340+j*145;col=GOLD if n>=k else MUT;ImageDraw.Draw(im).ellipse((1405,yy-3,1423,yy+15),fill=col);txt(im,(1450,yy-8),a,31,col,True);txt(im,(1450,yy+45),b,24,MUT)
  txt(im,(1400,871),f'原片时间 {n/30:.3f} s',26,CYAN,True)
 elif sid=='context':
  cards=[(64,'厂方披露的路口车速','139.1','km/h',GOLD),(674,'这段重建的平均速度','≈126','km/h',CYAN),(1284,'撞击前后的瞬时速度','随阶段变化','',FG)]
  for x,lab,val,unit,col in cards:
   rect(im,(x,265,x+572,725),'#10212f',radius=14);txt(im,(x+28,299),lab,27,MUT);txt(im,(x+28,386),val,77 if unit else 49,col,True);txt(im,(x+30,489),unit,29,col)
  txt(im,(92,575),'厂方说明：处于人驾状态',27,FG);txt(im,(92,632),'所述路段限速：50 km/h',26,MUT)
  txt(im,(702,575),'11.467—13.100 s',29,FG);txt(im,(702,632),'约57 m ÷ 1.633 s × 3.6',25,MUT)
  txt(im,(1312,575),'碰路缘 → 碰立柱',29,FG);txt(im,(1312,632),'不能拿同一个数代替',27,MUT)
  txt(im,(80,802),'三个数值的时间、位置和定义不同，不能直接混用。',35,FG,True)
  txt(im,(80,874),'厂方信息：问界用户服务 2026-10-21 说明；新京报转引。',24,MUT)
 elif sid=='braking':
  if part==0:
   n=min(392,357+int(max(0,lt-.5)*30));paste(im,render_img('follow',n-343),(64,218,1170,658));pill(im,85,235,'制动输入后 · 原图场景物理仿真')
   txt(im,(1320,258),'仍在减速',38,CYAN,True);txt(im,(1320,334),'134 → 112',61,GOLD,True);txt(im,(1320,420),'km/h  /  亮灯至碰缘前',25,MUT)
   txt(im,(1320,540),'仍要前进',34,FG,True);txt(im,(1320,608),'约 40 m',62,CYAN,True);txt(im,(1320,715),'用时约 1.16 s',30,FG);txt(im,(1320,828),'灯亮 ≠ 立刻停下',31,GOLD,True)
  else:
   txt(im,(100,236),'同一亮灯时速度：约 134 km/h',35,FG,True);txt(im,(100,294),'直线制动参照：8 m/s²，制动力建立 0.25 s',26,MUT)
   xx,ww=105,1480
   for j in range(6):
    px=xx+j/5*ww;line(im,[(px,373),(px,752)],RULE,1);txt(im,(px,779),f'{j*20} m',25,MUT,anchor='ma')
   scale=min(1,max(0,lt)/2);rect(im,(xx,421,xx+ww*.9183*scale,506),GOLD,radius=7);txt(im,(xx,370),'持续直线制动至停车',28,GOLD,True);txt(im,(xx+ww*.9183+25,439),'≈92 m',44,GOLD,True)
   rect(im,(xx,623,xx+ww*.40*scale,708),CYAN,radius=7);txt(im,(xx,571),'重建中：亮灯到路缘',28,CYAN,True);txt(im,(xx+ww*.40+25,640),'≈40 m',44,CYAN,True)
   txt(im,(110,860),'这是给定速度与制动参数的距离比较，不能代替现场定尺。',26,MUT)
 elif sid=='closing':
  if False:
   n,mode=playback(lt);paste(im,raw(n),(64,216,1136,639));pill(im,84,234,'回到原片 · '+mode,GOLD)
   for j,(a,b,col) in enumerate([('看着慢','透视压缩了画面位移',CYAN),('灯已经亮','车速不会瞬间归零',GOLD),('路口是钝角','沿路仍需改变约50°方向',FG)]):
    yy=245+j*205;txt(im,(1290,yy),a,35,col,True);txt(im,(1290,yy+63),b,28,MUT)
  elif False:
   n=min(420,380+int(max(0,lt)*30/4));paste(im,render_img('curb',n-343),(64,210,1280,720));pill(im,85,230,'基准假设的接触机制 · 逐帧1/4×',GOLD)
   for j,a in enumerate(['较高速度接近','车轮碰到路缘','再与立柱接触','产生抬起与偏转']):
    yy=260+j*148;txt(im,(1410,yy),f'{j+1:02}',26,CYAN,True);txt(im,(1410,yy+40),a,30,FG,True)
  else:
   image_path=R/'assets/aftermath_27s.jpg';paste(im,image_path,(64,210,1180,664));pill(im,84,230,'后续原片 · 27.0 s 定格',GOLD)
   txt(im,(1320,254),'画面呈现事件先后',32,FG,True);txt(im,(1320,350),'厂方初步解释',27,MUT);txt(im,(1320,408),'机舱撞击后',29,FG);txt(im,(1320,462),'线路短路、油液泄漏',29,FG)
   txt(im,(1320,598),'起火机理与责任',31,GOLD,True);txt(im,(1320,656),'还需车辆数据和现场调查',26,MUT);txt(im,(1320,812),'来源：问界用户服务说明',21,MUT);txt(im,(1320,850),'新京报转引 · 2026-10-21',21,MUT)
 elif sid=='environment':
  if part==0:
   paste(im,raw(330),(64,235,1050,591));paste(im,R/'site_after_user.png',(1190,210,640,620));pill(im,82,248,'原视频：路面、标线、反光');pill(im,1210,224,'现场照片');txt(im,(80,860),'可见纹理直接取自原图',35,FG,True);txt(im,(1190,860),'路缘 / 人行道 / 立柱',30,GOLD,True)
  else:
   n,mode=playback(lt);paste(im,render_img('follow',n-343),(64,205,1250,703));paste(im,R/'site_after_user.png',(1375,220,450,435));pill(im,90,225,'原图投影 + 实体接触面');txt(im,(1375,715),'纹理负责外观',30,CYAN,True);txt(im,(1375,764),'几何参与碰撞',30,GOLD,True);txt(im,(1375,828),'遮挡背面为简化几何',22,MUT)
 elif sid=='map':
  crop=(300,60,1500,860);panel=(64,220,1050,700);sat=img(str(R/'assets/satellite_full.png')).crop(crop);paste(im,sat,panel)
  def mp(p):return (64+(p[0]-300)*.875,220+(p[1]-60)*.875)
  for aa,bb,col,name in ([((805,347),(896,563),CYAN,'A—B 约56 m'),((718,245),(846,208),GOLD,'C—D 约32 m')] if part==0 else []):
   a,b=mp(aa),mp(bb);line(im,[a,b],col,5)
   for p in [a,b]:ImageDraw.Draw(im).ellipse((p[0]-7,p[1]-7,p[0]+7,p[1]+7),fill=BG,outline=col,width=3)
   txt(im,(b[0]+12,b[1]),name,25,col,True)
  if part==1:
   center=np.array(mp((864.440593,477.586136)));ends=[np.array(mp((789.440593,206.586136))),np.array(mp((1297.440593,674.586136)))];progress=min(1,lt/1.3)
   for end in ends:
    line(im,[tuple(center),tuple(center+(end-center)*progress)],BG,13);line(im,[tuple(center),tuple(center+(end-center)*progress)],GOLD,7)
   dr=ImageDraw.Draw(im);cx,cy=center;dr.arc((cx-100,cy-100,cx+100,cy+100),-105.47,-105.47+129.93*progress,fill=CYAN,width=6)
   pill(im,cx+112,cy-65,'130°',CYAN);pill(im,390,268,'杨业大街',GOLD);pill(im,815,719,'滨河西路',GOLD);pill(im,98,389,'云川大道',MUT)
  # Both rulers use the same satellite scale, 0.238095 m per original pixel.
  for yy in [211,927]:
   xx=100;step=10/(10/42)*.875;line(im,[(xx,yy),(xx+step*8,yy)],FG,2)
   for j in range(9):line(im,[(xx+j*step,yy-6),(xx+j*step,yy+6)],FG,2)
   txt(im,(xx+step*8+12,yy-12),'80 m',20,FG)
  txt(im,(1200,246),'地面夹角',29,MUT);txt(im,(1190,292),'≈130°',92,GOLD,True);txt(im,(1200,425),'沿路转向约 50°',33,FG,True)
  txt(im,(1200,528),'56 m',55,CYAN,True);txt(im,(1200,598),'图上 A—B 测距',26,MUT);txt(im,(1200,676),'32 m',55,GOLD,True);txt(im,(1200,746),'图上 C—D 测距',26,MUT);txt(im,(1200,852),'百度地图卫星图 · 截图比例尺换算',21,MUT);txt(im,(1200,886),'测距端点不等于车辆起止点',22,MUT)
 elif sid=='lamp':
  for j,n in enumerate([356,357,358]):
   x=64+j*602;paste(im,raw(n),(x,244,580,326));pill(im,x+14,258,f'{n/30:.3f} s  /  第 {n} 帧',GOLD if j==1 else MUT)
   # Unsharpened, nearest-neighbour enlargement of the same original pixels.
   crop=raw(n).crop((730,255,840,360)).resize((352,336),Image.Resampling.NEAREST);paste(im,crop,(x+110,583,352,336));txt(im,(x+290,205),['上沿未亮','首次清楚亮起','持续亮着'][j],30,RED if j else MUT,True,anchor='ma')
   yy=583+(296-255)*3.2;line(im,[(x+96,yy),(x+105,yy)],GOLD,4)
  if part==1:rect(im,(514,856,1406,922),'#102936',radius=8);txt(im,(960,873),'首次亮灯 → 异常姿态：约 1.23–1.30 s',31,CYAN,True,anchor='ma')
 elif sid=='model':
  # Continuous speed from actual solver states, ending before curb contact.
  x0,y0,cw,chh=110,265,1080,455
  for v in [100,110,120,130,140]:
   yy=y0+chh-(v-95)/50*chh;line(im,[(x0,yy),(x0+cw,yy)],RULE);txt(im,(x0-18,yy-14),str(v),22,MUT,anchor='ra')
  txt(im,(x0,y0-45),'km/h',24,MUT)
  for sec in [0,.4,.8,1.2,1.6]:
   xx=x0+sec/1.633*cw;line(im,[(xx,y0),(xx,y0+chh)],'#192c3b');txt(im,(xx,y0+chh+15),f'{11.4667+sec:.2f}',21,MUT,anchor='ma')
  states=SC['base']['states'][:48];pts=[(x0+s['t']/1.633*cw,y0+chh-(s['speed_kmh']-95)/50*chh) for s in states];upto=max(2,min(len(pts),int(lt/4.5*len(pts))));line(im,pts[:upto],GOLD,5)
  bx=x0+(13/30)/1.633*cw;line(im,[(bx,y0-5),(bx,y0+chh)],RED,3);txt(im,(bx+12,y0+15),'11.900 s 高位灯亮',25,RED,True)
  txt(im,(1300,225),'同一组物理假设',27,MUT);txt(im,(1300,280),'135 → 112',65,GOLD,True);txt(im,(1300,368),'初速 → 碰路缘前 / km/h',25,MUT)
  txt(im,(1300,470),'≈57 m',60,CYAN,True);txt(im,(1300,548),'÷ 1.633 s × 3.6',31,FG);txt(im,(1300,620),'≈126 km/h',51,GOLD,True);txt(im,(1300,694),'这段时间的平均速度',25,MUT)
  rect(im,(85,808,1835,922),'#102331',radius=12);txt(im,(115,829),'连续输入 → 轮胎受力 → 连续运动',33,FG,True);txt(im,(115,879),'数值依赖相机与米制尺度；用于比较复现，不是独立实测车速。',23,MUT)
  cursor=min(47,max(0,int((t/max(.1,ch['duration']-.6))*48)));st=states[cursor];px,py=pts[cursor]
  line(im,[(px,y0),(px,y0+chh)],CYAN,2);ImageDraw.Draw(im).ellipse((px-9,py-9,px+9,py+9),fill=GOLD)
  rect(im,(1280,430,1835,758),'#102331',radius=12)
  txt(im,(1310,457),f'第 {344+cursor} 帧 / {(344+cursor)/30:.3f} s',29,CYAN,True)
  txt(im,(1310,526),f'{st["speed_kmh"]:.2f} km/h',56,GOLD,True)
  txt(im,(1310,610),'求解器水平速度 × 3.6',27,FG)
  txt(im,(1310,674),'每 1/600 秒更新一次运动',25,MUT)
  if part==0:
   rect(im,(85,808,1835,922),'#102331',radius=12)
   for j,(aa,bb) in enumerate([(352,357),(357,362),(387,392)]):
    sa,sb=state(aa),state(bb);ds=sb['distance_m']-sa['distance_m'];xx=112+j*578
    txt(im,(xx,820),f'第 {aa} → {bb} 帧 · 0.167 s',24,MUT)
    txt(im,(xx,864),f'{ds:.2f} m  /  均速 {ds*21.6:.0f} km/h',32,CYAN,True)
 elif sid=='replay':
  view=['cctv','side','top'][min(2,int(t/(ch['duration']/3)))];n,mode=playback(t%(ch['duration']/3));pair(im,n,view,mode);pill(im,1480,724,'共用同一组状态',CYAN)
 elif sid=='perspective':
  if part==0:
   a=raw(330);paste(im,a,(64,235,1056,594));K=2632.7*(7.7394-.205)
   for z1,z2,col in [(40,50,GOLD),(80,90,CYAN)]:
    yy1=235+K/z1/720*594;yy2=235+K/z2/720*594
    line(im,[(150,yy1),(1030,yy1)],col,3);line(im,[(150,yy2),(1030,yy2)],col,3);line(im,[(1050,yy1),(1050,yy2)],col,4);txt(im,(1070,(yy1+yy2)/2),'10 m',23,col,True,anchor='lm')
   txt(im,(1250,260),'同样走 10 米',43,FG,True);txt(im,(1250,370),'近处：约 99 像素',33,GOLD,True);txt(im,(1250,449),'远处：约 28 像素',33,CYAN,True);txt(im,(1250,565),'路程相同',32,FG);txt(im,(1250,615),'屏幕位移却差很多',32,FG);txt(im,(1250,776),'按同一投影模型演示',23,MUT)
  else:
   fr=max(1,min(151,1+round(max(0,lt-1)*30)));paste(im,render_img('angle',fr),(64,210,1280,720));ang=ANGLES[fr-1]['screen_angle'];txt(im,(1390,285),'地面夹角',29,MUT);txt(im,(1390,338),'130°',77,GOLD,True);txt(im,(1390,485),'画面投影',29,MUT);txt(im,(1390,538),f'{ang:.0f}°',77,CYAN,True);txt(im,(1390,720),'镜头降低',28,FG);txt(im,(1390,764),'道路没有改变',28,FG)
   pp=[(64+p[0]*.8,210+p[1]*.8) for p in ANGLES[fr-1]['points']]
   for endpoint in pp[1:]:line(im,[pp[0],endpoint],BG,11);line(im,[pp[0],endpoint],GOLD,5)
   for px,py in pp:ImageDraw.Draw(im).ellipse((px-6,py-6,px+6,py+6),fill=CYAN)
 elif sid=='hypotheses':
  n,mode=playback(lt);ids=['base','early','late','wet'] if part==0 else ['base','early','late','soft'];cols=[FG,BLUE,GOLD,PINK]
  for j,ss in enumerate(ids):
   co=SC[ss]['contacts'].get('pole') or SC[ss]['contacts'].get('curb');stop=344+round(co['t']*30);nn=min(n,stop);frozen=n>=stop
   x=64+(j%2)*664;y=210+(j//2)*365;box=(x,y,640,360);paste(im,render_img('top' if ss=='base' else ss,nn-343),box);top_path(im,box,ss,nn,cols[j]);pill(im,x+12,y+12,SC[ss]['label'],cols[j]);st=state(nn,ss)
   speed=co['speed_kmh'] if frozen else st['speed_kmh'];event='主柱' if SC[ss]['contacts'].get('pole') else '路缘'
   txt(im,(x+622,y+318),f'{event} {co["t"]:.3f}s / {speed:.0f} km/h' if frozen else f'{speed:.0f} km/h',25,cols[j],True,anchor='ra')
   if frozen:pill(im,x+12,y+265,'接触定格',GOLD)
  txt(im,(1430,240),mode,28,GOLD,True);txt(im,(1430,302),f'{n/30:.3f} s',43,FG,True);txt(im,(1430,405),'各组接触后定格',29,MUT)
  for j,ss in enumerate(ids):
   co=SC[ss]['contacts'].get('curb');txt(im,(1430,465+j*87),SC[ss]['label'],24,cols[j]);txt(im,(1430,500+j*87),f'{co["source_time"]:.3f} s' if co else '区间内未接触',30,FG,True)
 elif sid=='event':
  if part==0:
   n=min(420,380+int(max(0,lt-.3)*30/8));pair(im,n,'curb','逐帧 1/8×',bottom=False)
   events=[('原片高位灯亮',11.9,RED),('模型前轮碰路缘',SC['base']['contacts']['curb']['source_time'],GOLD),('模型接触立柱',SC['base']['contacts']['pole']['source_time'],CYAN)]
   for j,(a,b,c) in enumerate(events):xx=88+j*590;txt(im,(xx,825),a,26,c,True);txt(im,(xx,870),f'{b:.3f} s',37,FG,True)
  elif part==1:
   n=min(424,382+int(max(0,lt-.3)*30/4))
   for j,ss in enumerate(['lowcurb','base','highcurb']):
    x=64+j*602;paste(im,render_img('curb' if ss=='base' else ss,n-343),(x,278,580,326));pill(im,x+15,292,f'路缘 {SC[ss]["curb_height"]*100:.0f} cm',[BLUE,CYAN,GOLD][j]);st=state(n,ss);txt(im,(x+290,652),f'{n/30:.3f} s',35,FG,True,anchor='ma');txt(im,(x+290,710),f'车身参考点高 {st["position"][2]:.2f} m',26,MUT,anchor='ma')
   pill(im,64,822,'相同初速、制动和转向 · 仅改变路缘高度',GOLD);txt(im,(64,883),'抬起和偏转由接触求解产生',33,FG,True)
  else:
   fr=max(1,min(121,1+int(lt*30)));paste(im,render_img('orbit',fr),(64,210,1250,703));pill(im,88,228,'同一求解状态 · 360°冻结',CYAN);paste(im,raw(393),(1375,225,450,253));txt(im,(1375,550),'刚体接触仿真',30,GOLD,True);txt(im,(1375,615),'检验接触顺序',28,FG);txt(im,(1375,660),'比较姿态变化',28,FG);txt(im,(1375,763),'车体压溃与断裂',26,MUT);txt(im,(1375,805),'需要更详细的材料模型',26,MUT)
 # consistent progress rail and compact captions
 line(im,[(64,956),(1856,956)],RULE,4);globalt=ch['start']+t;total=TIMELINE[-1]['start']+TIMELINE[-1]['duration'];line(im,[(64,956),(64+1792*globalt/total,956)],CYAN,4)
 for cc in TIMELINE:xx=64+1792*cc['start']/total;line(im,[(xx,949),(xx,963)],MUT,1)
 cap=caption(ch,t)
 if cap:txt(im,(960,986),cap,33,FG,False,anchor='ma')
 txt(im,(1856,1041),'原始影像参照 · 条件物理仿真',19,MUT,anchor='ra')
 if sid=='credits' and t>ch['duration']-.7:im=Image.blend(im,Image.new('RGB',(W,H),'black'),min(1,(t-ch['duration']+.7)/.7))
 return draw_section(im,ch,t,globals())

def srt_time(t):
 ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
def main():
 global TIMELINE
 if '--reuse-audio' in sys.argv and (R/'timeline_final.json').exists():TIMELINE=json.loads((R/'timeline_final.json').read_text('utf-8'))
 else:TIMELINE=audio_timeline()
 srt=[];ii=1
 for ch in TIMELINE:
  for p in ch['parts']:srt.append(f'{ii}\n{srt_time(ch["start"]+p["start"])} --> {srt_time(ch["start"]+p["end"])}\n{p["text"]}\n');ii+=1
 (R/'完整讲解.srt').write_text('\n'.join(srt),'utf-8');qa=R/'qa_final';qa.mkdir(exist_ok=True)
 for ch in TIMELINE:
  for j,p in enumerate(ch['parts']):chapter_frame(ch,p['start']+(p['end']-p['start'])*.55).save(qa/f'{ch["id"]}_{j}.jpg',quality=94)
 if '--preview' in sys.argv:print('PREVIEW READY',sum(c['duration'] for c in TIMELINE),flush=True);return
 # Require all requested solver renders before claiming a complete film.
 for sh in json.loads((R/'shots_physics.json').read_text('utf-8')):
  assert all((CACHE/sh['id']/f'{fr:04}.jpg').exists() for fr in range(sh['start'],sh['end']+1)),sh['id']
 target=R/'问界M9_路口重建与逐帧测速_B站发布版.mp4';log=open(R/'encode.log','w');start_frame=0;prefix=None
 if '--resume-partial' in sys.argv:
  probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=nb_frames','-of','json',str(target)]))
  start_frame=int(probe['streams'][0]['nb_frames']);assert 0<start_frame<round(sum(c['duration'] for c in TIMELINE)*30)
  prefix=OUT/'resume_prefix.mp4';assert not prefix.exists(),'Preserve existing resume prefix'
  target.replace(prefix);encoded=OUT/'resume_suffix.mp4';print('RESUME FROM FRAME',start_frame,flush=True)
 else:encoded=target
 cmd=['ffmpeg','-y','-v','warning','-threads','1','-filter_threads','1','-thread_queue_size','2','-f','rawvideo','-pixel_format','rgb24','-video_size','1920x1080','-framerate','30','-i','-']
 encoder=os.environ.get('M9_VIDEO_ENCODER','h264_nvenc')
 cmd+=['-c:v',encoder]+(['-preset','p5','-tune','hq','-rc','vbr','-cq','21','-b:v','0'] if encoder=='h264_nvenc' else ['-preset','medium','-crf','20'])+['-pix_fmt','yuv420p']
 cmd+=['-an']
 cmd+=['-movflags','+faststart',str(encoded)]
 proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log)
 for ch in TIMELINE:
  for fr in range(max(0,start_frame-round(ch['start']*30)),round(ch['duration']*30)):
   frame=chapter_frame(ch,fr/30)
   for row in range(0,1080,120):proc.stdin.write(frame.crop((0,row,1920,row+120)).tobytes())
  print('COMPOSED',ch['id'],flush=True)
 proc.stdin.close();rc=proc.wait();log.close();assert rc==0,rc
 if prefix is None:
  muxed=OUT/'final_mux.mp4'
  subprocess.run(['ffmpeg','-v','error','-y','-threads','1','-i',str(target),'-i',str(R/'narration_final.wav'),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart',str(muxed)],check=True)
  muxed.replace(target)
 if prefix is not None:
  concat=OUT/'resume_concat.txt';concat.write_text("file '"+prefix.as_posix()+"'\nduration "+str(start_frame/30)+"\nfile '"+encoded.as_posix()+"'\n",'utf-8')
  subprocess.run(['ffmpeg','-v','error','-y','-threads','1','-f','concat','-safe','0','-i',str(concat),'-i',str(R/'narration_final.wav'),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart',str(target)],check=True)
 print('FILM READY',target,flush=True)
if __name__=='__main__':main()
