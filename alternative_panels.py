"""Comparison plates share solver time; contact cards use solver event records."""
from pathlib import Path
import json,math
R=Path(__file__).resolve().parent
BASE=json.loads((R/'physics_results.json').read_text('utf-8'))
ALT=json.loads((R/'alternative_results.json').read_text('utf-8'))
SC={x['id']:x for x in BASE['scenarios']+ALT['scenarios']}

def draw(im,ch,t,part,lt,ld,g):
 txt,rect,line,pill,paste,raw,img=[g[k] for k in ('txt','rect','line','pill','paste','raw','img')]
 FG,MUT,CYAN,GOLD,RED=[g[k] for k in ('FG','MUT','CYAN','GOLD','RED')]
 def shot(sid,fr):return img(str(R/'renders'/sid/f'{int(fr):04}.jpg'))
 def st(sid,elapsed):
  ss=SC[sid]['states'];return ss[max(0,min(len(ss)-1,round(elapsed*30)))]
 def value(x,y,label,val,unit,col=GOLD):
  txt(im,(x,y),label,23,MUT);txt(im,(x,y+36),val,48,col,True);txt(im,(x+192,y+55),unit,23,col)
 sid=ch['id']
 if sid=='claims':
  if part==0:
   for x,lab,val,col in [(80,'起始时刻','12.733 s',CYAN),(710,'结束时刻','13.299 s',GOLD),(1340,'地图估计距离','5—7 m',FG)]:
    rect(im,(x,239,x+500,480),'#122735',radius=16);txt(im,(x+30,275),lab,28,MUT);txt(im,(x+30,347),val,58,col,True)
   q=min(1,max(0,lt-1)/1.4);line(im,[(108,530),(108+1660*q,530)],CYAN,4)
   txt(im,(960,602),'5—7 m ÷ 0.566 s × 3.6',62,FG,True,anchor='ma')
   txt(im,(960,709),'31.8—44.5 km/h',73,GOLD,True,anchor='ma')
   txt(im,(960,854),'公开算法：啄泥王 · 新浪公开页面 · 2026-10-21',25,MUT,anchor='ma')
  else:
   for j,n in enumerate([382,394,399]):
    x=64+j*602;paste(im,raw(n),(x,245,580,326));pill(im,x+12,258,f'{n} 帧 / {n/30:.3f} s')
    txt(im,(x+290,610),['进入末段','开始出现异常姿态','运动明显变化'][j],30,FG,True,anchor='ma')
   line(im,[(105,721),(1810,721)],GOLD,4)
   for j,lab in enumerate(['地面端点','同一车辆特征','接触阶段']):
    x=100+j*600;txt(im,(x,771),f'0{j+1}',38,CYAN,True);txt(im,(x+85,777),lab,34,FG,True)
   txt(im,(90,881),'原片逐帧定位 → 区间均速 → 接触时刻的速度',31,GOLD,True)
 elif sid=='low_initial':
  elapsed=min(49/30,max(0,lt-.5)) if part==0 else min(6,max(0,lt-.5))
  n=344+round(min(elapsed,3)*30)
  top=part>0
  for j,(ss,lab,col) in enumerate([('source','原片',FG),('base','基准初速 135',GOLD),('initial60','初速 60',CYAN),('initial80','初速 80','#78adff')]):
   x=64+(j%2)*910;y=210+(j//2)*349;box=(x,y,872,300)
   if ss=='source':a=raw(n)
   elif ss=='base':a=shot('top' if top else 'cctv',1+round(min(3,elapsed)*30))
   else:a=shot(ss+('_top' if top else ''),1+round(min(6 if top else 49/30,elapsed)*30))
   paste(im,a,box);pill(im,x+12,y+12,lab,col)
   if ss!='source':
    s=st(ss,elapsed);txt(im,(x+850,y+267),f'{s["speed_kmh"]:.0f} km/h · {s["distance_m"]:.1f} m',27,col,True,anchor='ra')
   else:pill(im,x+12,y+252,f'{n/30:.3f} s'+(' / 定格' if elapsed>3 else ''))
  if part==0:txt(im,(76,915),f'同步原速回放 / 已经过 {elapsed:.3f} s',26,GOLD,True)
  else:
   txt(im,(76,910),'60：2.77 s / 26.8 m     80：3.57 s / 45.0 m',29,CYAN,True)
   txt(im,(1844,912),'停下阈值：持续低于 0.5 km/h',21,MUT,anchor='ra')
 elif sid=='low_impact':
  # Slow playback is stated. Freeze each independent panel at its own contact.
  local=max(0,lt-.6)/4
  for j,ss in enumerate(['impact40','impact50']):
   x=64+j*1204;s=SC[ss];co=s['contacts']['pole'];elapsed=min(co['t'],local)
   fr=47+round(elapsed*30);paste(im,shot(ss,fr),(x,245,580,326));pill(im,x+12,257,f'主柱接触 {co["speed_kmh"]:.0f} km/h',CYAN if j==0 else GOLD)
   pill(im,x+12,515,'接触定格' if elapsed>=co['t'] else '局部回放 1/4×',GOLD)
   value(x+20,610,'进入速度',f'{s["restart_speed_kmh"]:.1f}','km/h')
   value(x+20,732,'到主柱用时',f'{co["t"]:.3f}','s',CYAN)
   txt(im,(x+20,852),f'先碰路缘：{s["contacts"]["curb"]["speed_kmh"]:.1f} km/h',25,MUT)
  original_n=390+round(min(.3,local)*30)
  paste(im,raw(original_n),(666,245,580,326));pill(im,678,257,f'原片 / {original_n/30:.3f} s')
  txt(im,(956,626),'从同一时刻开始',31,FG,True,anchor='ma')
  txt(im,(956,691),'局部运动对照',27,CYAN,anchor='ma')
  txt(im,(956,758),'原片：相同倍率',25,MUT,anchor='ma')
  txt(im,(956,808),'仿真：各自接触时定格',25,MUT,anchor='ma')
  txt(im,(960,910),'起点：13.000 s 对应位置 / 固定转向，制动释放 / 画面取最近渲染帧',24,FG,anchor='ma')
 elif sid=='contact_results':
  ids=['base','early','late','wet','soft','lowcurb','highcurb']
  cols=[88,645,945,1285,1590]
  for x,lab in zip(cols,['假设','路缘 · 用时','速度','主柱 · 用时','速度']):txt(im,(x,231),lab,26,MUT)
  for j,ss in enumerate(ids):
   s=SC[ss];yy=298+j*79;active=(part==0 and ss=='base') or (part==1 and ss in ('early','late'))
   rect(im,(65,yy-7,1854,yy+65),'#173141' if active else '#10212f',radius=8)
   txt(im,(88,yy+8),s['label'],28,FG,True)
   for x,key in [(645,'curb'),(1285,'pole')]:
    co=s['contacts'].get(key)
    txt(im,(x,yy+8),f'{co["t"]:.3f} s' if co else '未接触',28,CYAN if key=='curb' else GOLD,True)
    txt(im,(x+300,yy+8),f'{co["speed_kmh"]:.1f}' if co else '—',30,FG,True)
  txt(im,(88,888),'用时：从 11.467 s 起算；速度单位：km/h；接触由求解器记录。',25,MUT)
 return im
