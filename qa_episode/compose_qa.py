"""Anonymous source comments and animated numerical answers in a separate episode."""
from pathlib import Path
import sys,json,math
import numpy as np
from PIL import Image,ImageDraw
Q=Path(__file__).resolve().parent;P=Q.parent;R=P/'peer_review'
sys.path.insert(0,str(R));import compose_review as c
E=json.loads((Q/'evidence.json').read_text('utf-8'))
questions=json.loads((Q/'anonymous_questions.json').read_text('utf-8'))
mapping={'timing':[18],'endpoints':[1,2],'scale':[4,8,10,17],'curve':[22,23],'braking':[13],'brakelight':[11,12],'contact':[14,16,19]}
T=c.text;paste=c.paste;img=c.img;panel=c.panel
BG,FG,MUT,CYAN,GOLD,RED=c.BG,c.FG,c.MUT,c.CYAN,c.GOLD,c.RED
def wrap(d,s,xy,width=1700,size=35,col=FG):
 x,y=xy;line=''
 for char in s:
  if c.font(size).getlength(line+char)>width:T(d,(x,y),line,size,col);y+=size*1.55;line=''
  line+=char
 if line:T(d,(x,y),line,size,col)
 return y+size*1.55
def metric(d,x,y,label,value,col=CYAN,note=''):
 T(d,(x,y),label,29,MUT);T(d,(x,y+48),value,66,col,True)
 if note:T(d,(x,y+145),note,26,MUT)
def render(folder,k):
 files=sorted(folder.glob('*.jpg'));return img(str(files[min(len(files)-1,max(0,k))]))
def quote(im,d,ch,j,u,t):
 ident=ch['id'];ids=mapping.get(ident,[])
 if not ids and ident!='white':return False
 if t>=6.1:return False
 d.rectangle((60,205,1860,982),fill=BG)
 T(d,(100,245),'评论区原话',30,CYAN,True);T(d,(1540,245),'账号已隐去',25,MUT)
 if ident in ['timing','curve','braking','white']:
  shot=img(str(Q/'anonymous_screenshots'/f'{ident}.png'))
  panel(d,(95,320,1825,720));paste(im,shot,(130,355,1650,300))
  T(d,(120,760),'原评论正文截取 · 隐去头像、昵称与账号信息',29,MUT)
 else:
  rows=[questions[i-1] for i in ids[:2]]
  for k,row in enumerate(rows):
   y=325+k*230;panel(d,(95,y,1825,y+205))
   value=row['text'];value=value if len(value)<=115 else value[:112]+'…'
   wrap(d,value,(125,y+30),1640,35)
  T(d,(120,850),'原评论 / 弹幕文字转录 · 保留原意，隐去账号',27,MUT)
 if ident=='endpoints':T(d,(120,910),'第一条来自观众之间的估算讨论，随后检查同类取点问题。',27,GOLD)
 return True
def frame(ch,t):
 im=Image.new('RGB',(1920,1080),BG);d=ImageDraw.Draw(im)
 for x in range(0,1920,120):d.line((x,0,x,1080),fill='#10202b')
 T(d,(75,35),'ASTRA / 答B友问',25,CYAN,True);T(d,(1420,35),'问界M9神木事故',25,MUT)
 T(d,(75,96),ch['title'],50,FG,True);d.line((75,185,1845,185),fill='#355363',width=2)
 part=next((p for p in ch['parts'] if p['start']<=t<p['end']),ch['parts'][-1] if t>=ch['parts'][-1]['start'] else ch['parts'][0]);j=part['index'];elapsed=max(0,t-part['start']);u=max(0,min(1,elapsed/(part['end']-part['start'])))
 ident=ch['id']
 if ident=='opening':
  if t<2.2:paste(im,img(str(Q/'cover.png')),(0,0,1920,1080))
  else:
   cards=[('01','80刹停45米','先检查仿真条件',GOLD),('02','逐帧与标尺','把问题接回原画面',CYAN),('03','路缘与立柱','拆开每一次接触',FG)]
   for k,(n,a,b,col) in enumerate(cards):
    y=240+k*225;panel(d,(85,y,1835,y+185));T(d,(115,y+35),n,65,col,True);T(d,(300,y+25),a,55,col,True);T(d,(300,y+110),b,32,MUT)
 elif ident=='timing':
  for k,n in enumerate([68,107,128,157]):
   x=85+k*447;panel(d,(x,250,x+420,540));paste(im,c.raw_frame(n).crop((860,0,1280,105)),(x+10,270,400,145));T(d,(x+20,455),f'原帧 {n}',36,CYAN,True)
  for k,n in enumerate([39,21,29]):metric(d,110+k*590,610,f'相邻监控秒 · 区间{k+1}',f'{n} 个文件帧',[GOLD,RED,CYAN][k])
  T(d,(110,855),'取位置：挑清楚的影像    计时间：保留原始时间戳',38,FG,True)
  d.line((100,935,1820,935),fill='#2c4556',width=8);xx=100+1720*((t%6)/6);d.ellipse((xx-9,926,xx+9,944),fill=CYAN)
 elif ident=='endpoints':
  paste(im,img(str(R/'map_candidate_measurement.png')).crop((500,190,1100,640)),(70,235,950,680))
  paste(im,img(str(R/'teacher_input_audit/endpoint_audit.jpg')),(1050,250,800,450))
  T(d,(1060,735),'时间起点 ↔ 距离起点',43,CYAN,True);T(d,(1060,815),'车头 / 车尾：统一同一点',37,GOLD,True)
  T(d,(95,935),'地图候选线与原帧选点并排检查；斜穿路口需另画路径。',28,MUT)
 elif ident=='scale':
  n=1+round(((t%10)/10)*150);paste(im,img(str(P/'renders/angle'/f'{n:04}.jpg')),(60,215,1270,710))
  metric(d,1390,260,'候选尺度敏感性','−21%',GOLD,'像素边界扰动实验')
  metric(d,1390,510,'另一侧偏差','+34%',RED,'原模型条件，非现场误差上限')
  T(d,(130,875),'地面点定相机 → 保留独立点验证 → 再换算米数',38,FG,True)
  T(d,(130,940),'模型刻度不是测量证据；高度、畸变、坡度应分别检查。',26,MUT)
 elif ident=='curve':
  rows=E['curve']['states'];xy=np.array([r['xy'] for r in rows]);a=xy.min(axis=0);b=xy.max(axis=0);scale=min(650/(b[0]-a[0]),560/(b[1]-a[1]));span=(b-a)*scale;xy=(xy-a)*scale+[110+(650-span[0])/2,290]
  d.line([tuple(v) for v in xy],fill='#2c4556',width=10);d.line((tuple(xy[0]),tuple(xy[-1])),fill=GOLD,width=3)
  k=max(2,round(len(xy)*u));d.line([tuple(v) for v in xy[:k]],fill=CYAN,width=7);x,y=xy[k-1];d.ellipse((x-12,y-12,x+12,y+12),fill=FG)
  metric(d,950,275,'模型质心 · 逐点累加','56.978 m',CYAN)
  metric(d,950,510,'同一组端点 · 直线','56.856 m',GOLD)
  T(d,(950,750),'相差 0.122 m',48,FG,True);T(d,(95,930),'帧344—393的模型轨迹；真实路程仍需独立尺度与逐帧对应。',28,MUT)
 elif ident=='braking':
  k=min(107,int((t%6)*30));paste(im,render(P/'renders/initial80_top',k),(65,240,1120,630))
  metric(d,1230,250,'同减速度 · 立即制动','27.3 m',CYAN)
  metric(d,1230,510,'保留原模型控制','45.0 m',GOLD)
  T(d,(100,840),'0.433 s 后开始制动  +  0.25 s 建立过程  +  转向与轮胎控制',33,FG,True)
  T(d,(100,935),'27.3 m按评论42.6 m百零距离推算；45.0 m为条件仿真累计路程。',27,MUT)
 elif ident=='brakelight':
  if j==0:
   frames=[350,357,362];labels=['观察灯光','核对后续位移','估计制动过程']
   for k,n in enumerate(frames):
    x=75+k*615;paste(im,img(str(R/'raw_sequence'/f'{n:04}.jpg')),(x,270,590,332));T(d,(x+10,645),labels[k],38,CYAN,True);T(d,(x+10,720),f'原帧 {n}',30,MUT)
   T(d,(100,865),'灯光时刻只是线索，制动力还要看位移变化。',44,FG,True)
  else:
   a=E['energy_example']['a_ms2'];ds=np.linspace(0,40,80);vs=np.sqrt((139/3.6)**2-2*a*ds)*3.6
   c.curve(d,(140,360,1540,400),list(vs),CYAN,150)
   k=min(79,round(u*79));x=140+k/79*1540;y=760-vs[k]/150*400;d.ellipse((x-10,y-10,x+10,y+10),fill=GOLD)
   T(d,(130,240),'v² = v0² − 2as',66,FG,True);T(d,(1120,250),'139 → 99.7 km/h',54,GOLD,True)
   T(d,(140,810),'0 m',30,MUT);T(d,(1590,810),'40 m',30,MUT)
   T(d,(130,920),'按观众问题做恒减速算例 · a≈9.056 m/s² · 用于检验推理',30,MUT)
 elif ident=='contact':
  k=1+int((t%5)/5*49);paste(im,render(P/'renders/curb',k),(65,235,1130,635))
  metric(d,1240,275,'模型 · 路缘接触前','112.0',GOLD,'km/h · 经过1.592秒')
  metric(d,1240,550,'模型 · 主柱接触前','100.4',CYAN,'km/h · 经过1.643秒')
  T(d,(100,900),'接触先后、速度、变形吸能，需要分别记录。',40,FG,True)
  T(d,(100,950),'数值属于公开基准假设；柱子刚体设置不提供真实材料变形证据。',25,MUT)
 elif ident=='white':
  paste(im,img(str(P/'white_car_analysis/satellite_measurements_55m_5m.png')),(70,230,1240,700))
  metric(d,1380,270,'卫星图候选线','55 m',GOLD)
  metric(d,1380,500,'两侧斑马线','约5 m',CYAN)
  T(d,(1350,760),'同一点',39,FG,True);T(d,(1350,820),'两个过线时刻',34,FG,True)
  T(d,(100,945),'早期约45 km/h已撤回；地图端点与过点时间需要可靠对应。',28,MUT)
 elif ident=='closing':
  T(d,(100,270),'每个数字，都能追到原画面。',70,FG,True);T(d,(100,410),'原帧 / 匿名问题 / 计算代码 / Blender工程',39,CYAN)
  T(d,(100,500),'GitHub链接在简介与置顶评论',35,MUT)
  for k,label in enumerate(['点赞','投币','收藏']):
   x=100+k*580;panel(d,(x,650,x+510,840));T(d,(x+150,705),label,62,GOLD,True)
  T(d,(100,930),'欢迎带着具体帧号、地标与计算步骤来复核。',32,FG)
 quote(im,d,ch,j,u,t)
 if part['start']<=t<part['end']:
  chunks=c.linewrap(part['text']);pos=u*sum(len(z) for z in chunks);acc=0;caption=chunks[-1]
  for z in chunks:
   acc+=len(z)
   if pos<acc:caption=z;break
  d.rectangle((0,982,1920,1080),fill='#070d14');T(d,((1920-c.font(35).getlength(caption))/2,1000),caption,35,FG)
 d.rectangle((0,1073,1920*t/ch['duration'],1080),fill=CYAN)
 if ch['index'] and t<1.25:
  overlay=Image.new('RGB',(1920,1080),BG);dd=ImageDraw.Draw(overlay);T(dd,(100,260),'ASTRA / 答B友问',30,MUT);T(dd,(100,360),f"{ch['index']:02}",130,CYAN,True);T(dd,(100,570),ch['title'],52,FG,True);dd.line((100,740,100+1720*min(1,t/.9),740),fill=CYAN,width=4);im=Image.blend(im,overlay,min(1,(1.25-t)/.35))
 return im
def setup():
 c.R=Q;c.SCRIPT=json.loads((Q/'script.json').read_text('utf-8'));c.frame=frame;c.FINAL_NAME='Astra答B友问_问界M9神木事故.mp4'
if __name__=='__main__':setup();c.main()
