"""Reproducible editorial film: measured inputs, source citations, controlled 3D examples."""
from pathlib import Path
from functools import lru_cache
import gc,io,time
import json,math,subprocess,wave,re,sys
import numpy as np,cv2
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;P=R.parent;W,H=1920,1080;FPS=30
BG='#0b121c';FG='#eef4f7';MUT='#9eafbf';CYAN='#80d9cc';GOLD='#f0bd7c';RED='#f48e81'
SCRIPT=json.loads((R/'script.json').read_text('utf-8'));MEAN=json.loads((R/'mean_demo.json').read_text('utf-8'));PHYS=json.loads((P/'physics_results.json').read_text('utf-8'))['scenarios'][0]['states']
cv2.setNumThreads(1)
@lru_cache(6)
def font(n,b=False):return ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc' if b else 'C:/Windows/Fonts/msyh.ttc',n)
def text(d,xy,s,n=36,c=FG,b=False):d.text(xy,str(s),font=font(n,b),fill=c)
@lru_cache(6)
def img(path):return Image.open(path).convert('RGB')
@lru_cache(4)
def source_frame(name,sec):
 saved=R/'reference_stills'/f'{name}_{sec}.jpg'
 if saved.exists():return Image.open(saved).convert('RGB')
 cap=cv2.VideoCapture(str(R/'sources'/f'{name}.mp4'),cv2.CAP_FFMPEG,[cv2.CAP_PROP_N_THREADS,1]);cap.set(cv2.CAP_PROP_POS_MSEC,sec*1000);ok,f=cap.read();cap.release();assert ok;return Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB))
@lru_cache(4)
def raw_frame(n):
 saved=P/'peer_review'/'canonical_frames'/f'{n:04}.png'
 if saved.exists():return Image.open(saved).convert('RGB')
 # Decode from the start: seeking in this phone recording can land one frame early.
 data=subprocess.check_output(['ffmpeg','-v','error','-threads','1','-i',str(P/'assets/source.mp4'),'-vf',f'select=eq(n\\,{n})','-vsync','0','-frames:v','1','-threads','1','-f','image2pipe','-c:v','png','pipe:1'])
 return Image.open(io.BytesIO(data)).convert('RGB')
def paste(im,a,box):
 x,y,w,h=box;ratio=min(w/a.width,h/a.height);a=a.resize((round(a.width*ratio),round(a.height*ratio)),Image.Resampling.LANCZOS);im.paste(a,(int(x+(w-a.width)/2),int(y+(h-a.height)/2)))
def panel(d,box):d.rounded_rectangle(box,20,fill='#101e2c',outline='#25394a',width=2)
def curve(d,box,values,col=CYAN,vmax=160):
 x,y,w,h=box;d.line((x,y,x,y+h,x+w,y+h),fill='#496273',width=2)
 pts=[(x+i/(len(values)-1)*w,y+h-v/vmax*h) for i,v in enumerate(values)];d.line(pts,fill=col,width=5)
def linewrap(s,n=42):
 chunks=[]
 for p in re.findall(r'[^，。；！？]+[，。；！？]?',s):
  if chunks and len(chunks[-1])+len(p)<=n:chunks[-1]+=p
  else:
   while len(p)>n:chunks.append(p[:n]);p=p[n:]
   if p:chunks.append(p)
 return chunks
def layout():
 timeline=[];audio=[];current=0
 for k,ch in enumerate(SCRIPT):
  start=current;parts=[];lead=1.25 if k else 0.45;audio.append(np.zeros(round(lead*24000),np.float32));current+=lead
  for j,s in enumerate(ch['lines']):
   wav=R/'audio'/f"{ch['id']}_{j:02}.wav"
   with wave.open(str(wav)) as f:
    assert f.getframerate()==24000 and f.getnchannels()==1
    a=np.frombuffer(f.readframes(f.getnframes()),np.int16).astype(np.float32)/32768
   duration=len(a)/24000;parts.append({'start':current-start,'end':current-start+duration,'text':s,'index':j});audio.append(a);current+=duration
   audio.append(np.zeros(6000,np.float32));current+=.25
  duration=math.ceil((current-start+.35)*FPS)/FPS;tail=start+duration-current;audio.append(np.zeros(round(tail*24000),np.float32));current=start+duration
  timeline.append({**ch,'start':start,'duration':duration,'parts':parts,'index':k})
 a=np.concatenate(audio);a=np.clip(a,-.97,.97)
 with wave.open(str(R/'narration.wav'),'wb') as f:f.setparams((1,2,24000,0,'NONE','NONE'));f.writeframes((a*32767).astype(np.int16).tobytes())
 (R/'timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2),'utf-8');return timeline
def frame(ch,t):
 im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
 for x in range(0,W,120):d.line((x,0,x,H),fill='#10202b')
 text(d,(76,35),'ASTRA / 观众提问后的四条分析复核',24,MUT);text(d,(1650,35),f"{ch['index']+1:02} / {len(SCRIPT):02}",24,MUT)
 text(d,(76,93),ch['title'],52,FG,True);d.line((76,184,1844,184),fill='#2d4353',width=2)
 ident=ch['id'];part=next((p for p in ch['parts'] if p['start']<=t<p['end']),ch['parts'][-1] if t>=ch['parts'][-1]['start'] else ch['parts'][0]);j=part['index'];u=max(0,min(1,(t-part['start'])/(part['end']-part['start'])))
 if ident=='opening':
  if j==0:
   text(d,(85,230),'接上一期 · 路口重建与十一组仿真',31,CYAN,True)
   paste(im,img(str(P/'B站封面.png')),(80,300,960,540))
   d.line((1070,470,1150,470),fill=CYAN,width=4);d.polygon([(1150,460),(1170,470),(1150,480)],fill=CYAN)
   text(d,(1205,285),'你们接着问',40,MUT)
   for k,(a,b) in enumerate([('七八十？一百多？','为什么初速差这么远'),('撞上时还剩多少？','平均速度怎样推到末速'),('逐帧怎么也有分歧？','先从每一步的输入看起')]):
    y=370+k*175;alpha=min(1,max(0,(u-k*.22)*7));ink=tuple(round(int(BG[i:i+2],16)*(1-alpha)+int(FG[i:i+2],16)*alpha) for i in (1,3,5))
    text(d,(1200,y),a,39,ink,True);text(d,(1200,y+65),b,28,MUT)
   text(d,(90,905),'上一期：BV1p9nC6mE12 · 简介首行可直达',29,MUT)
  else:
   labels=[('01','连续原帧','保留原始时间轴'),('02','卫星底图','对齐地面参照点'),('03','原作者算式','按同样输入复算'),('04','Blender 对照','只改变指定条件')]
   pictures=[raw_frame(339),img(str(P/'assets/satellite_full.png')),source_frame('BV1U9nB6GEwD',51),img(str(R/'renders_context/cctv/0030.jpg'))]
   active=min(3,int(u*4))
   for k,(num,lab,note) in enumerate(labels):
    x=80+k*450;shift=round(20*(1-min(1,max(0,(u-k*.10)*8))))
    panel(d,(x,280+shift,x+410,745+shift));d.rounded_rectangle((x,280+shift,x+410,745+shift),20,outline=CYAN if active==k else '#25394a',width=4 if active==k else 2)
    text(d,(x+25,310+shift),num,38,CYAN,True);paste(im,pictures[k],(x+15,390+shift,380,215));text(d,(x+25,635+shift),lab,35,FG,True);text(d,(x+25,695+shift),note,25,MUT)
   text(d,(100,825),'透视  →  时间  →  标尺  →  减速',57,GOLD,True)
   text(d,(100,915),'把作者的步骤摆出来，再看结果从哪里分开。',32,FG)
  if t<3.6:
   cover=img(str(R/'cover.png')).resize((1920,1080),Image.Resampling.LANCZOS)
   blend=1 if t<2.6 else 1-(t-2.6)
   im=Image.blend(im,cover,max(0,min(1,blend)));d=ImageDraw.Draw(im)
 elif ident=='clock':
  for i,n in enumerate([308,339,368,398]):
   x=80+i*447;panel(d,(x,260,x+425,530));paste(im,raw_frame(n).crop((860,0,1280,100)),(x+10,280,405,130));text(d,(x+25,430),f'文件帧 {n}',38,CYAN,True)
  text(d,(105,600),'31 帧  +  29 帧  +  30 帧',64,FG,True);text(d,(105,725),'3 个监控秒  =  90 个文件帧',64,GOLD,True)
  d.line((100,855,1810,855),fill='#304a5f',width=7);d.ellipse((100+1710*u-9,846,100+1710*u+9,864),fill=CYAN)
  text(d,(100,895),'原片独立读数 · 零基帧号 · 保留文件时间轴',25,MUT)
  focus=min(3,int(u*4));x=80+focus*447;d.rounded_rectangle((x,260,x+425,530),20,outline=CYAN,width=5)
 elif ident=='duplicates':
  if j==0:
   ns=[100,101,102,103,104,107]
   for i,n in enumerate(ns):
    x=80+(i%3)*590;y=245+(i//3)*205
    paste(im,img(str(R/'duplicate_frames'/f'{n:04}.png')).crop((650,155,900,255)),(x,y,565,150));text(d,(x+5,y+150),f'帧 {n}  /  {n/30:.3f} s',29,CYAN)
   text(d,(90,696),'画面有没有更新，和时间有没有经过，是两件事。',44,FG,True)
   for i in range(12):
    x=90+i*145;d.rounded_rectangle((x,785,x+128,854),8,fill=CYAN if i<=int(u*11) else '#24394b');text(d,(x+20,801),f'{i/30:.2f}',25,BG if i<=int(u*11) else MUT)
   text(d,(90,884),'示意：连续文件时间轴；每格 1/30 秒',27,MUT)
   active=min(5,int(u*6));x=80+(active%3)*590;y=245+(active//3)*205;d.rounded_rectangle((x-3,y-3,x+568,y+185),10,outline=GOLD,width=4)
  else:
   for i,n in enumerate([68,107,128,157]):
    x=80+i*447;panel(d,(x,265,x+425,520));paste(im,raw_frame(n).crop((860,0,1280,100)),(x+10,290,405,110));text(d,(x+25,430),f'文件帧 {n}',38,CYAN,True)
   for i,(a,col) in enumerate([(39,GOLD),(21,RED),(29,CYAN)]):
    x=100+i*585;text(d,(x,595),f'{a} 帧',85,col,True);text(d,(x,725),f'{a/30:.3f} 个文件秒',35,MUT)
   text(d,(100,845),'白车经过期间：局部停留与追赶；3 个监控秒对应 89 帧',38,FG,True)
 elif ident=='teacher_math':
  paste(im,source_frame('BV1U9nB6GEwD',51 if j==0 else 35),(80,220,750,700))
  if j==0:
   for k,(s,n,v) in enumerate([(5.5,8,74.25),(14.7,27,58.8),(6.5,23,30.52)]):
    y=280+k*185;text(d,(905,y),f'{s} m ÷ ({n}/30 s)',43,MUT);text(d,(905,y+65),f'{v:g} km/h',64,GOLD,True)
  else:
   text(d,(910,285),'3 m  /  6 m  /  9 m',54,GOLD,True);text(d,(910,400),'减速度异常',55,FG,True)
   for k,s in enumerate(['标尺长度','透视与取点','画面更新节奏']):text(d,(925,520+k*90),'→ '+s,42,CYAN)
   text(d,(910,830),'用独立地标，检验整套标定',34,FG,True)
  text(d,(90,927),'来源：佘雷 · BV1U9nB6GEwD · 00:35 / 00:51',23,MUT)
  if j==0:
   active=min(2,int(u*3));y=280+active*185;d.rounded_rectangle((878,y-15,1825,y+148),15,outline=GOLD,width=3);text(d,(905,220),'作者输入 → 按原条件复算',27,CYAN)
 elif ident=='scale':
  paste(im,img(str(P/'assets/satellite_full.png')).crop((480,180,1190,750)),(80,230,920,690))
  text(d,(1040,270),'第一条：后两段',35,MUT);text(d,(1040,325),'21.2 m',100,GOLD,True)
  text(d,(1040,490),'第二条：地图与车长修正',35,MUT);text(d,(1040,550),'49.7—54.7 m',68,CYAN,True)
  text(d,(1040,735),'对齐起止事件',40,FG,True);text(d,(1040,805),'跟踪同一个车身点',40,FG,True)
  text(d,(90,928),'百度地图底图；右侧为两位作者给定距离，尚未统一端点标定。',23,MUT)
 elif ident=='mean':
  progress=min(1,max(0,((t%10-1)/7 if j==0 else (t-part['start'])/8)));fr=1+round(progress*30)
  for k,a in enumerate([0,4,8]):
   x=70+k*615;st=MEAN[k]['states'][fr-1];end=MEAN[k]['states'][-1]['speed_kmh']
   text(d,(x+10,225),['匀速','减速度 4 m/s²','减速度 8 m/s²'][k],35,[GOLD,CYAN,RED][k],True)
   paste(im,img(str(R/'renders_mean'/str(a)/f'{fr:04}.jpg')),(x,285,595,335))
   text(d,(x+20,640),f"{st['speed_kmh']:.1f}",80,[GOLD,CYAN,RED][k],True);text(d,(x+250,682),'km/h',29,MUT)
   vals=[q['speed_kmh'] for q in MEAN[k]['states']];curve(d,(x+30,755,520,130),vals,[GOLD,CYAN,RED][k],45)
   px=x+30+520*progress;py=885-st['speed_kmh']/45*130;d.ellipse((px-7,py-7,px+7,py+7),fill=FG)
   text(d,(x+30,895),f'终点 {end:.2f} km/h',28,FG)
  text(d,(80,946),f'运动学控制实验 · 同为 6.5 m / 0.767 s · 当前仿真时刻 {progress*23/30:.3f} s · 慢放',23,MUT)
 elif ident=='bird':
  if j==0:
   paste(im,source_frame('BV1SQn66HEjf',206),(80,240,1100,620));text(d,(1220,320),'时钟校准',48,CYAN,True);text(d,(1220,450),'同一点的位移',48,CYAN,True);text(d,(1220,580),'均速与末速分开',44,CYAN,True);text(d,(90,910),'来源：铂金小鸟 · BV1SQn66HEjf · 03:26',24,MUT)
  elif j==1:
   for k,(lab,val) in enumerate([('路程','49.7—54.7 m'),('总时间','1.493 s'),('制动起点','0.252 s'),('减速度','0.5—0.8 g')]):text(d,(100,275+k*140),lab,32,MUT);text(d,(100,320+k*140),val,48,FG,True)
   text(d,(830,275),'按原作者条件复算',38,MUT);text(d,(830,365),'初速 128.9—146.5',65,GOLD,True);text(d,(830,490),'末速 99.3—119.1',65,CYAN,True);text(d,(1610,580),'km/h',32,MUT)
   vals=[137.692 if z<=.251678 else 137.692-(z-.251678)*.65*9.81*3.6 for z in np.linspace(0,1.493289,90)];curve(d,(870,670,850,210),vals, CYAN,160);text(d,(870,895),'曲线示例：52.2 m / 0.65 g',25,MUT)
  else:
   curve(d,(140,310,1550,440),[150]*100,GOLD,170);curve(d,(140,310,1550,440),list(np.linspace(150,100,100)),CYAN,170)
   text(d,(170,215),'初速 150',48,FG,True);text(d,(1040,230),'全程匀速 150',48,GOLD,True);text(d,(1040,660),'150 → 100；均速 125',42,CYAN,True);text(d,(130,850),'示例：恒减速时，初速高于全程平均速度',37,FG)
 elif ident=='views':
  fr=1+int((t%6)/6*49);state=PHYS[fr-1]
  if j==0:
   for k,(shot,lab) in enumerate([('cctv','机位 A · 向远处行驶'),('side','机位 B · 从路旁观察')]):
    x=75+k*900;text(d,(x,240),lab,38,CYAN,True);paste(im,img(str(R/'renders_context'/shot/f'{fr:04}.jpg')),(x,310,875,492));d.rectangle((x,310,x+875,802),outline='#37576c',width=2)
   text(d,(100,845),'同一条运动轨迹 · 同一时刻 · 两台相机',43,FG,True);text(d,(100,915),f'源时间 {state["source_frame"]/30:.3f} s / 同步慢放 · 第三条：折腾旳老猫 BV1Q6n16NECy',25,MUT)
  else:
   text(d,(95,230),'路面坐标：每段距离相等',38,CYAN,True);text(d,(1060,230),'透视画面：远处被压缩',38,GOLD,True)
   d.rounded_rectangle((100,370,925,670),14,fill='#223343');d.line((115,520,910,520),fill=FG,width=3)
   for k in range(6):
    x=140+k*145;d.line((x,385,x,655),fill='#7d9baa',width=2);text(d,(x-30,690),f'{k*10} m',27,MUT)
   q=(t-part['start'])%6/6;x=140+q*725;d.rounded_rectangle((x-42,478,x+42,560),10,fill=CYAN)
   d.polygon([(1070,780),(1810,780),(1500,340),(1380,340)],fill='#223343');d.line((1440,780,1440,340),fill=FG,width=3)
   # Pinhole illustration: equal world-distance increments have decreasing image gaps.
   for k in range(6):
    f=1/(1+k*.8);y=300+480*f;half=370*f;d.line((1440-half,y,1440+half,y),fill='#7d9baa',width=2)
   f=1/(1+q*4);y=300+480*f;cw=85*f;d.rounded_rectangle((1440-cw,y-45*f,1440+cw,y+45*f),5,fill=GOLD)
   text(d,(95,830),'相同的地面位移',43,FG,True);text(d,(1060,830),'不同的像素位移',43,FG,True)
   text(d,(95,925),'投影原理示意 · 等间距刻度用于说明透视，不代表事故路口测量值',26,MUT)
 elif ident=='pole':
  paste(im,source_frame('BV1kTnz6YENQ',8),(80,230,740,690));text(d,(860,255),'从设施痕迹，补全接触几何',48,CYAN,True)
  for k,s in enumerate(['哪一根构件','接触位置与高度','基座与截面','擦碰、正碰与后续运动']):text(d,(890,380+k*120),f'0{k+1}  '+s,42,FG)
  text(d,(85,928),'来源：zyzhuyin001 · BV1kTnz6YENQ · 00:08',23,MUT)
 elif ident=='closing':
  if j==0:
   for k,(a,b) in enumerate([('01  佘雷','核对三米标尺与减速估计'),('02  铂金小鸟','核对地图端点与制动条件'),('03 / 04','对齐机位、碰撞方向与接触条件')]):
    y=260+k*200;panel(d,(80,y,1840,y+165));text(d,(110,y+35),a,40,CYAN,True);text(d,(560,y+42),b,43,FG)
   text(d,(100,895),'原画面时间位置 · 复算代码 · 参数表 · Blender 工程',34,GOLD)
  else:
   text(d,(110,280),'把每一步，留给别人复算。',82,FG,True);text(d,(110,440),'工程下载链接在简介',48,CYAN)
   for k,s in enumerate(['点赞','投币','收藏']):
    x=110+k*570;panel(d,(x,610,x+500,805));text(d,(x+150,665),s,64,GOLD,True)
   text(d,(110,910),'Vertex AI / Charon 男声 · Gemini 4 Argon 梳理文案 · 按原帧复核',27,MUT)
 import revision_panels
 revision_panels.draw(im,d,ch,t,part,j,u,sys.modules[__name__])
 # Captions follow phrases rather than exposing entire paragraphs at once.
 if part['start']<=t<part['end']:
  chunks=linewrap(part['text']);length=sum(len(z) for z in chunks);pos=u*length;acc=0;caption=chunks[-1]
  for z in chunks:
   acc+=len(z)
   if pos<acc:caption=z;break
  d.rectangle((0,982,1920,1080),fill='#070d14');bbox=d.textbbox((0,0),caption,font=font(35));text(d,((W-bbox[2])/2,1000),caption,35,FG)
 d.rectangle((0,1073,W*t/ch['duration'],1080),fill=CYAN)
 if ch['index'] and t<1.25:
  fade=min(1,(1.25-t)/.35);overlay=Image.new('RGB',(W,H),BG);dd=ImageDraw.Draw(overlay)
  text(dd,(100,240),'顺着证据，往下看',30,MUT);text(dd,(100,340),f"{ch['index']+1:02}",140,CYAN,True);text(dd,(100,560),ch['title'],57,FG,True)
  dd.line((100,720,100+1720*min(1,t/.9),720),fill=CYAN,width=4)
  text(dd,(100,790),'透视   /   时间   /   标尺   /   减速',31,MUT);im=Image.blend(im,overlay,max(0,fade))
 return im
def main():
 timeline=layout();out=R/'edit_revision';out.mkdir(exist_ok=True)
 if '--preview' in sys.argv:
  qa=R/'qa';qa.mkdir(exist_ok=True)
  for ch in timeline:
   for p in ch['parts']:
    frame(ch,(p['start']+p['end'])/2).save(qa/f"{ch['id']}_{p['index']}.jpg")
  print('PREVIEW READY',sum(c['duration'] for c in timeline));return
 for ch in timeline:
  dest=out/(ch['id']+'.mp4')
  if dest.exists() and dest.with_suffix('.done').exists():continue
  img.cache_clear();source_frame.cache_clear();raw_frame.cache_clear();gc.collect()
  cmd=['ffmpeg','-y','-hide_banner','-loglevel','error','-filter_threads','1','-thread_queue_size','1','-f','image2pipe','-c:v','mjpeg','-threads','1','-framerate','30','-i','pipe:0','-an','-c:v','libx264','-threads','1','-preset','veryfast','-tune','zerolatency','-crf','19','-pix_fmt','yuv420p',str(dest)]
  proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
  temp_jpeg=out/(ch['id']+'_frame.tmp.jpg')
  try:
   for n in range(round(ch['duration']*FPS)):
    for attempt in range(12):
     im=None
     try:
      im=frame(ch,n/FPS)
      im.save(temp_jpeg,format='JPEG',quality=93,subsampling=0)
      break
     except MemoryError:
      if im is not None:im.close()
      img.cache_clear();source_frame.cache_clear();raw_frame.cache_clear();font.cache_clear();gc.collect()
      print('ALLOCATION RETRY',ch['id'],n,attempt,flush=True)
      if attempt==11:raise
      time.sleep(2)
     finally:
      if im is not None:im.close()
    with temp_jpeg.open('rb') as buffer:
     for block in iter(lambda:buffer.read(65536),b''):proc.stdin.write(block)
    if n%5==0:gc.collect()
    if n%300==0:print('RENDER',ch['id'],n,flush=True)
  finally:proc.stdin.close()
  if proc.wait():raise RuntimeError('Encode failed '+ch['id'])
  temp_jpeg.unlink(missing_ok=True)
  dest.with_suffix('.done').write_text(str(ch['duration']));print('CHAPTER READY',ch['id'],flush=True)
 listing=out/'concat.txt';listing.write_text(''.join("file '"+c['id']+".mp4'\n" for c in timeline),'utf-8')
 final=R/globals().get('FINAL_NAME','同一段监控_两种车速_算法逐项复核.mp4')
 subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-f','concat','-safe','0','-i',str(listing),'-i',str(R/'narration.wav'),'-map','0:v:0','-map','1:a:0','-c:v','copy','-af','loudnorm=I=-16:TP=-1.5:LRA=11','-c:a','aac','-b:a','192k','-movflags','+faststart',str(final)],check=True)
 print('FINAL READY',final,flush=True)
if __name__=='__main__':main()
