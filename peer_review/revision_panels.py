"""Timed evidence panels: source excerpts, measured map, perspective, conditional replays."""
import json,math
from functools import lru_cache
@lru_cache(None)
def datafile(path):return json.loads(path.read_text(encoding='utf-8'))
import numpy as np
from PIL import Image,ImageDraw
def draw(im,d,ch,t,part,j,u,c):
 R,P=c.R,c.P;txt,paste,img,panel=c.text,c.paste,c.img,c.panel
 CYAN,GOLD,FG,MUT,RED=c.CYAN,c.GOLD,c.FG,c.MUT,c.RED
 ident=ch['id'];elapsed=max(0,t-part['start'])
 if ident=='teacher_math' and ch.get('input_audit'):
  from input_audit_panels import draw as draw_input_audit
  draw_input_audit(im,d,j,u,c,elapsed)
  return
 def clear():d.rectangle((50,205,1870,975),fill=c.BG)
 def clip(name,x,y,w,h,seconds=6):
  folder=R/'clips'/name;n=len(list(folder.glob('*.jpg')));k=min(n,max(1,int(min(elapsed,seconds)*30)+1))
  paste(im,img(str(folder/f'{k:04}.jpg')),(x,y,w,h))
  txt(d,(x,y+h+12),'原片节选 · 正常速度' if elapsed<seconds else '原片定格',23,MUT)
 if ident=='opening':
  clear()
  input_revision=any(x.get('input_audit') for x in c.SCRIPT)
  cards=[('佘雷','先查过线时刻与标尺' if input_revision else '均速被写成初速','5.5米需要接回原始画面' if input_revision else '三米标尺还需要独立验证',GOLD),('铂金小鸟','链条更完整','端点与制动条件仍影响结果',CYAN),('其他事故 / 现场','提供线索','观感和车损无法单独定速',FG)]
  if j==0:
   for k,(who,a,b,col) in enumerate(cards):
    y=235+k*215;panel(d,(80,y,1840,y+180));txt(d,(110,y+25),who,34,MUT);txt(d,(480,y+22),a,53,col,True);txt(d,(480,y+105),b,32,FG)
    if u>=k*.28:d.line((82,y+5,82,y+175),fill=col,width=8)
   txt(d,(95,915),'先给判断，再把每一步展开。',32,GOLD)
  else:
   paste(im,img(str(P/'B站封面.png')),(85,250,910,512));txt(d,(1060,260),'观众带来的四条分析',39,CYAN,True)
   for k,s in enumerate(['原片与作者输入','卫星图与时间轴','Blender 条件重放','把结论留给复算']):txt(d,(1070,370+k*125),f'0{k+1}  '+s,41,FG)
   txt(d,(100,860),'上一期：BV1p9nC6mE12',30,MUT)
  if t<2.0:
   cover=Image.new('RGB',(1920,1080),c.BG);paste(cover,img(str(R/'cover_4x3.png')),(0,0,1920,1080));im.paste(Image.blend(im,cover,1 if t<1.25 else (2-t)/.75))
 elif ident=='scale':
  clear();a=img(str(R/'map_candidate_measurement.png'));crop=(500,190,1100,640);a=a.crop(crop)
  x,y,w,h=80,230,1080,810;paste(im,a,(x,y,w,650));ratio=min(w/a.width,650/a.height);ox=x+(w-a.width*ratio)/2;oy=y+(650-a.height*ratio)/2
  def p(px,py):return (ox+(px-500)*ratio,oy+(py-190)*ratio)
  A=p(837,334);B=p(902,496);q=21.2/56;E=(A[0]+(B[0]-A[0])*q,A[1]+(B[1]-A[1])*q)
  # Independent length overlay on the native measurement, not asserted author endpoint registration.
  if j==0:
   f=min(1,u*2);end=(A[0]+(E[0]-A[0])*f,A[1]+(E[1]-A[1])*f);d.line((A,end),fill=CYAN,width=10);d.ellipse((E[0]-9,E[1]-9,E[0]+9,E[1]+9),fill=CYAN)
   txt(d,(E[0]-210,E[1]-15),'21.2 m',39,CYAN,True)
  else:
   txt(d,(1180,700),'作者新增 P2 · 约 58 m',29,CYAN,True);clip('bird_map',1180,390,650,280)
  txt(d,(1190,245),'卫星图候选基线',32,MUT);txt(d,(1190,300),'56 m',86,GOLD,True)
  if j==0:
   txt(d,(1190,480),'14.7 + 6.5',49,FG,True);txt(d,(1190,555),'= 21.2 m',65,CYAN,True)
   txt(d,(1190,700),'同一起点，终点在哪里？',30,FG)
  txt(d,(90,905),'候选端点：入口附近 → 对侧路缘附近；需与原帧过点事件逐一匹配。',26,MUT)
  txt(d,(90,945),'百度地图 · 原生测距截图与像素端点随工程保存',22,MUT)
 elif ident=='marking':
  clear();paste(im,c.raw_frame(339),(70,235,790,445));txt(d,(85,705),'先认箭头的同一形状与头尾',35,CYAN,True)
  page=img(str(R/'standards/shenmu_arrow_page65.png'));paste(im,page.crop((970,50,1870,170)),(920,280,900,190))
  txt(d,(940,500),'公开工程文件：300 cm',47,GOLD,True)
  txt(d,(940,590),'神木市青少年宫北侧道路',31,FG)
  txt(d,(940,650),'用于说明当地存在三米箭头设计',28,MUT)
  txt(d,(940,710),'事故路口尺寸：仍需独立地标核定',28,MUT)
  txt(d,(85,870),'形状识别  →  设计条件  →  地面尺度验证',45,FG,True)
  txt(d,(85,940),'来源：陕西省政府采购网 · 市政道路改造工程公开设计文件，PDF 第65页',23,MUT)
 elif ident=='perspective':
  clear();n=round(1+150*min(1,max(0,(elapsed-2)/10)));row=datafile(P/'angle_projection.json')[n-1]
  paste(im,img(str(P/'renders/angle'/f'{n:04}.jpg')),(70,215,1410,730))
  pts=[(70+(1410-1600*(730/900))/2+p[0]*(730/900),215+p[1]*(730/900)) for p in row['points']]
  d.line((pts[1],pts[0],pts[2]),fill=GOLD,width=7)
  for px,py in pts:d.ellipse((px-7,py-7,px+7,py+7),fill=FG)
  txt(d,(1480,285),'地面夹角',31,MUT);txt(d,(1480,350),'≈130°',65,CYAN,True)
  txt(d,(1480,520),'屏幕投影角',29,MUT);txt(d,(1480,585),f"{row['screen_angle']:.1f}°",65,GOLD,True)
  txt(d,(1480,770),'两条地面线固定',26,FG);txt(d,(1480,820),'只移动相机',26,FG)
  txt(d,(80,945),'同一组地面方向的视角演示 · 地面角度为卫星图描线近似值',23,MUT)
 elif ident in ('author_teacher','author_bird'):
  clear();data=datafile(R/'author_hypotheses.json');cases=data['scenarios'][:3] if ident=='author_teacher' else data['scenarios'][3:]
  T=cases[0]['duration'];physical=min(T,elapsed%(T+2.5));progress=physical/T;k=round(progress*50)
  positions=[(75,245),(1000,245),(75,600),(1000,600)]
  raw=data['source_frame_anchor']+round(physical*30);rf=R/'raw_sequence'/f'{raw:04}.jpg';x,y=positions[0]
  paste(im,img(str(rf)),(x,y,570,320));txt(d,(x+590,y+20),'原视频',31,FG,True);txt(d,(x+590,y+90),f'帧 {raw}',30,CYAN);txt(d,(x+590,y+150),f'+{physical:.3f} s',28,MUT)
  for idx,case in enumerate(cases):
   x,y=positions[idx+1];st=case['states'][k];paste(im,img(str(R/'renders_author_v3'/case['id']/f'{k+1:04}.jpg')),(x,y,570,320));col=[GOLD,CYAN,RED][idx]
   txt(d,(x+590,y+5),case['label'],30,col,True);txt(d,(x+590,y+70),f"{st['speed_kmh']:.1f}",56,col,True);txt(d,(x+590,y+140),'km/h',24,MUT);txt(d,(x+590,y+195),f"{st['distance_m']:.1f} m",35,FG)
   txt(d,(x+590,y+255),'终点定格' if physical==T else '按物理时间播放',22,MUT)
  txt(d,(75,210),f'正常速度重放 → 终点停留   /   经过 {physical:.3f} s',26,CYAN,True)
  txt(d,(75,947),'共同起点：原帧346较远灯带影像；相机和米尺为条件标定。两次叠影的曝光时刻仍有歧义。',23,MUT)
 # Source excerpts occupy their own evidence area, retaining visible author credit.
 elif ident=='teacher_math' and j==0:clip('teacher',80,220,750,660)
 elif ident=='teacher_math' and j==1:
  clear();txt(d,(90,245),'5.5 m ÷ (8/30 s) × 3.6',51,FG,True);txt(d,(90,335),'74.25 km/h',92,GOLD,True);txt(d,(95,465),'八帧区间的平均速度',45,GOLD,True)
  vals=np.linspace(78.01704,70.48296,90);c.curve(d,(920,300,850,390),vals,CYAN,90)
  txt(d,(920,220),'恒减速 0.8 g 的示例',34,MUT);txt(d,(930,720),'起点 78.02 → 终点 70.48',42,CYAN,True)
  txt(d,(95,650),'持续减速时：',41,FG);txt(d,(95,730),'起点速度 > 区间均速',47,CYAN,True)
  txt(d,(95,870),'明确混淆：把 S/T 的区间均速直接标成入画瞬时速度。',39,FG,True)
  txt(d,(95,940),'这个错误本身不足以否定“末速20多”；末速还需检验距离和制动模型。',24,MUT)
 elif ident=='bird' and j==0:clip('bird',80,240,1100,620)
 elif ident=='views' and j==0 and elapsed<5.6:
  clear();clip('views',85,235,1120,630,5);txt(d,(1280,300),'原片：其他事故对比',32,CYAN,True);txt(d,(1280,435),'随后保持轨迹',32,FG);txt(d,(1280,495),'只切换相机',32,FG);txt(d,(85,930),'折腾旳老猫 · BV1Q6n16NECy · 00:21—00:26',24,MUT)
 elif ident=='pole':clip('pole',80,230,740,640)
