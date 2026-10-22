"""Five explanatory panels using the actual observations and saved solver states."""
import json,math
from pathlib import Path
import numpy as np
from PIL import ImageDraw
R=Path(__file__).resolve().parent
P=json.loads((R/'scene_calibration.json').read_text('utf-8'))['projection']
OBS=json.loads((R/'assets/observations.json').read_text('utf-8'))
O={o['frame']:o for o in OBS}
D=json.loads((R/'physics_results.json').read_text('utf-8'));S=D['scenarios'][0]['states'];K=P['K']
def draw(im,ch,t,part,lt,g):
 txt,rect,line,pill,paste,raw=[g[n] for n in ['txt','rect','line','pill','paste','raw']]
 FG,MUT,CYAN,GOLD,RED,BG=[g[n] for n in ['FG','MUT','CYAN','GOLD','RED','BG']]
 sid=ch['id']
 if sid=='speed_clock':
  for x,n in [(64,344),(1016,393)]:
   paste(im,raw(n),(x,218,840,472));pill(im,x+16,232,f'第 {n} 帧 / {n/30:.3f} s',CYAN)
  txt(im,(960,419),'→',62,GOLD,True,anchor='ma')
  for j in range(50):
   x=100+j*(1720/49);line(im,[(x,733),(x,754)],CYAN if j<=min(49,int(lt*10)) else MUT,2)
  txt(im,(100,781),'50 张画面，49 个帧间隔',33,FG,True)
  txt(im,(1850,776),'(393 − 344) ÷ 30 = 1.633 s',40,GOLD,True,anchor='ra')
  txt(im,(100,866),'隔 5 帧 = 5 ÷ 30 = 0.1667 s',30,CYAN,True)
  txt(im,(1020,866),'重复画面仍计入经过的时间',27,MUT)
 elif sid=='speed_scale':
  if part<2:
   n=352 if lt<4.0 else 357;y=O[n]['tail_y_px'];z=K/y
   paste(im,raw(n),(64,231,1080,607));yy=231+y/720*607
   line(im,[(76,yy),(1130,yy)],GOLD,4);pill(im,86,yy+12,f'y = {y:.0f} px',GOLD)
   pill(im,84,249,f'同一车尾特征 / 第 {n} 帧',CYAN)
   txt(im,(1210,228),'透视反算示例',32,FG,True)
   txt(im,(1210,291),'Z = K ÷ (y − y0)',37,GOLD,True)
   txt(im,(1210,363),'K = 17,190.38 m·px',26,MUT)
   txt(im,(1210,406),'本片条件标定：y0 = 0',25,MUT)
   txt(im,(1210,493),'369 px → 46.59 m',36,CYAN,True)
   txt(im,(1210,558),'327 px → 52.57 m',36,CYAN,True)
   txt(im,(1210,675),'纵深差 ≈ 5.98 m',38,GOLD,True)
   txt(im,(1210,748),'纵深是相机前方距离',25,MUT)
   txt(im,(1210,791),'转弯行程还须考虑横向位移',23,MUT)
   txt(im,(82,878),'同一特征高度的近似反算；相机、特征高度和米制尺度共同决定结果。',25,MUT)
  elif part==2:
   crop=raw(344).crop((710,350,1010,530));paste(im,crop,(70,245,1050,630))
   # Candidate roof points used by the inherited conditional calibration.
   for px,py,label in [(856,411,'车顶前边界候选'),(869,442,'车顶后边界候选')]:
    xx=70+(px-710)*3.5;yy=245+630/2-180*3.5/2+(py-350)*3.5
    ImageDraw.Draw(im).ellipse((xx-10,yy-10,xx+10,yy+10),fill=GOLD)
    line(im,[(xx,yy),(xx+130,yy)],GOLD,4);pill(im,xx+140,yy-20,label,GOLD)
   pill(im,85,262,'第 344 帧 / 候选边界',CYAN)
   txt(im,(1190,240),'米尺来自哪里',37,FG,True)
   txt(im,(1190,311),'假设间距 L = 2.70 m',34,GOLD,True)
   txt(im,(1190,380),'用第 344 / 350 / 355 帧',25,MUT)
   txt(im,(1190,430),'车顶边界估计相机尺度',27,FG)
   txt(im,(1190,501),'再换算到车尾特征',27,FG)
   txt(im,(1190,565),'K ≈ 17,190.38 m·px',32,CYAN,True)
   txt(im,(1190,660),'间距、边界身份、相对位置',25,MUT)
   txt(im,(1190,706),'都是这一步的输入假设',27,GOLD,True)
   txt(im,(85,888),'从车顶换算到尾灯高度；完整换算过程和原始点表随工程附上。',25,MUT)
  else:
   for j,(a,b,c) in enumerate([('地图上量距离','保留比例尺和测距端点',CYAN),('与原片对同一点','道路角点、标线、立柱',GOLD),('恢复车辆地面位置','逐帧位置差 → 行程',CYAN)]):
    x=80+j*612;rect(im,(x,245,x+560,480),'#102534',radius=15);txt(im,(x+27,277),f'0{j+1}',30,c,True);txt(im,(x+27,336),a,34,FG,True);txt(im,(x+27,413),b,25,MUT)
    if j<2:txt(im,(x+574,350),'→',30,GOLD,True)
   txt(im,(100,548),'候选边界偏移 6 px，米尺约变 −21% / +34%',42,GOLD,True)
   txt(im,(100,625),'对齐卫星图与原片地标，可以进一步校准尺度。',29,FG)
   for j,(a,b) in enumerate([('米尺 ×0.79','换算速度 ×0.79'),('米尺 ×1.00','换算速度 ×1.00'),('米尺 ×1.34','换算速度 ×1.34')]):
    x=110+j*600;txt(im,(x,729),a,32,CYAN,True);txt(im,(x,790),b,32,FG,True)
   txt(im,(100,883),'保持像素观测与时间相同，查看几何尺度变化带来的换算差异。',24,MUT)
 elif sid=='speed_noise':
  for j,n in enumerate([352,357,362]):
   x=64+j*602;paste(im,raw(n),(x,226,580,326));pill(im,x+12,238,f'第 {n} 帧 / y={O[n]["tail_y_px"]:.0f} px',CYAN)
   txt(im,(x+290,575),f'Z ≈ {K/O[n]["tail_y_px"]:.2f} m',34,FG,True,anchor='ma')
  for j,(a,b) in enumerate([(352,357),(357,362)]):
   ds=K/O[b]['tail_y_px']-K/O[a]['tail_y_px'];x=102+j*930
   txt(im,(x,665),f'{ds:.2f} m ÷ 0.1667 s × 3.6',34,MUT)
   txt(im,(x,724),f'≈ {ds*21.6:.0f} km/h',61,GOLD,True)
  if part==0:txt(im,(100,864),'短窗差分会放大取点误差；结合整段观测判断运动趋势。',29,FG)
  else:
   rect(im,(80,832,1840,925),'#162b37',radius=10)
   txt(im,(100,847),'327 px 处：单个端点偏 2 px，距离约偏 0.32 m',29,CYAN,True)
   txt(im,(100,888),'0.32 m ÷ 0.1667 s × 3.6 ≈ 7 km/h；两个端点、重影和姿态变化都会影响结果。',23,MUT)
 elif sid=='speed_fit':
  x0,y0,w,h=120,255,1080,470
  def point(fr,y):return (x0+(fr-344)/49*w,y0+(500-y)/330*h)
  for y in [200,300,400,500]:
   yy=point(344,y)[1];line(im,[(x0,yy),(x0+w,yy)],'#263847',2);txt(im,(x0-18,yy-14),str(y),23,MUT,anchor='ra')
  txt(im,(x0,y0-46),'尾灯下缘 / 像素 y（越往远处，y 越小）',25,MUT)
  count=max(2,min(50,int(lt*8)+2));pts=[point(st['source_frame'],st['pixel'][1]) for st in S[:count]];line(im,pts,GOLD,4)
  for o in OBS[:count]:
   x,y=point(o['frame'],o['tail_y_px']);ImageDraw.Draw(im).ellipse((x-4,y-4,x+4,y+4),fill=CYAN)
  for n in [344,357,369,381,393]:
   x=point(n,500)[0];txt(im,(x,y0+h+16),str(n),23,MUT,anchor='ma')
  txt(im,(1300,255),'图像特征',30,CYAN,True);txt(im,(1300,307),'连续模型预测',30,GOLD,True)
  txt(im,(1300,405),'共同调整',29,MUT)
  for j,a in enumerate(['初速度','制动强度与建立过程','转向与初始位姿']):txt(im,(1300,458+j*55),a,28,FG,True)
  txt(im,(1300,676),'投回原镜头，比较偏差',26,CYAN,True)
  rect(im,(82,825,1840,926),'#102534',radius=10)
  txt(im,(105,842),'纵向：逐帧亮度特征；横向：锚点插值',29,FG,True)
  txt(im,(105,889),'初速搜索：108—165.6 km/h；基准结果约135 km/h；采用本片保存的条件尺度。',23,MUT)
 elif sid=='speed_sum':
  if part<2:
   a,b=(357,362) if part==0 else (344,393);ds=S[b-344]['distance_m']-S[a-344]['distance_m'];dt=(b-a)/30;v=ds/dt*3.6
   txt(im,(95,236),f'第 {a} → {b} 帧',38,FG,True);pill(im,1390,238,'拟合后的模型行程',CYAN)
   for j,(lab,value,col) in enumerate([('累计路程之差',f'{ds:.2f} m',CYAN),('时间间隔',f'{dt:.4f} s',FG),('单位换算','× 3.6',GOLD)]):
    x=96+j*600;rect(im,(x,327,x+550,570),'#102534',radius=12);txt(im,(x+30,355),lab,28,MUT);txt(im,(x+30,420),value,66,col,True)
   txt(im,(960,650),f'{ds:.2f} ÷ {dt:.4f} × 3.6 ≈ {v:.0f} km/h',65,GOLD,True,anchor='ma')
   txt(im,(960,776),'区间平均速度 = 这段路程 ÷ 这段时间',39,FG,True,anchor='ma')
   txt(im,(960,872),'区间均速看整段行程；接触速度读取该时刻的运动状态。',25,MUT,anchor='ma')
  else:
   steps=[('01','数对时间','帧间隔 ÷ 帧率'),('02','确定米尺','相机、地标与尺度'),('03','整段拟合','位置、制动与转向'),('04','再算速度','局部与全段分别计算')]
   for j,(n,a,b) in enumerate(steps):
    x=65+j*462;rect(im,(x,300,x+435,565),'#102534',radius=13);txt(im,(x+25,327),n,34,CYAN,True);txt(im,(x+25,392),a,36,FG,True);txt(im,(x+25,479),b,24,MUT)
   txt(im,(100,653),'约 135 km/h 初速  /  约 126 km/h 全段均速',51,GOLD,True)
   txt(im,(100,758),'这组标定下的重建结果',40,FG,True)
   txt(im,(100,852),'地图保留测距端点，图像保留特征坐标，模型保留逐时刻的运动状态。',28,MUT)
 return im
