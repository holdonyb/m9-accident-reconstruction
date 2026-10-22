"""Evidence-driven inserts for the new input audit; no new physical-speed claim."""
import math
from PIL import ImageDraw
def draw(im,d,j,u,c,elapsed=0):
 R=c.R;O=R/'teacher_input_audit';txt,paste,img,panel=c.text,c.paste,c.img,c.panel
 d.rectangle((50,205,1870,975),fill=c.BG)
 if j==0:
  folder=R/'clips/teacher';k=min(180,max(1,int(elapsed*30)+1))
  paste(im,img(str(folder/f'{k:04}.jpg')),(70,220,770,730))
  txt(d,(85,942),'佘雷原片节选 · 00:47—00:53 · '+('正常速度' if elapsed<6 else '结束定格'),23,c.MUT)
  txt(d,(930,260),'先核验两个输入',45,c.FG,True)
  for k,(a,b) in enumerate([('5.5 m','从哪些地面点量出来？'),('8 / 30 s','哪两次画面更新之间？')]):
   y=390+k*245;panel(d,(910,y,1820,y+210));txt(d,(950,y+15),a,67,c.GOLD,True);txt(d,(950,y+125),b,34,c.FG)
 elif j==1:
  cards=[('作者标号 53','author_44.png'),('作者标号 54','author_45.png')]
  for k,(label,file) in enumerate(cards):
   x=75+k*605;panel(d,(x,235,x+570,825));txt(d,(x+23,255),label,37,c.GOLD,True)
   a=img(str(O/file)).crop((0,65,485,470));paste(im,a,(x+10,330,550,460))
  x=1285;panel(d,(x,235,x+570,825));txt(d,(x+23,255),'本地原片 339',37,c.CYAN,True)
  a=img(str(R/'raw_sequence/0339.jpg')).crop((430,120,1080,720));paste(im,a,(x+10,330,550,460))
  txt(d,(90,865),'两张展示画面，都匹配到同一个本地文件帧。',41,c.FG,True)
  txt(d,(90,932),'后续54→339、57→342、61→346；起点的画面与编号需要重新核对。',27,c.MUT)
  phase=(math.sin(u*math.pi*4)+1)/2;d.line((80,817,1840,817),fill=c.CYAN,width=3+round(phase*4))
 elif j==2:
  a=img(str(O/'endpoint_audit.jpg')).crop((40,170,1880,1020));paste(im,a,(60,210,1800,760))
 elif j==3:
  labels=[('3 m','箭头尺寸'),('透视与取点','地面换算'),('5.5 m','得到的距离')]
  for k,(a,b) in enumerate(labels):
   x=90+k*610;y=280;panel(d,(x,y,x+530,y+270));txt(d,(x+35,y+45),a,55,c.GOLD if k!=1 else c.CYAN,True);txt(d,(x+35,y+150),b,35,c.FG)
   if k<2:txt(d,(x+545,y+90),'→',50,c.MUT)
  txt(d,(100,620),'把尺子拿到画面之外，再核验一次',44,c.FG,True)
  for i,s in enumerate(['同一种箭头的头尾与尺寸','独立地标的实际距离','同一车身点的逐帧回投']):txt(d,(110,710+i*75),f'0{i+1}  '+s,36,c.CYAN)
 elif j==4:
  txt(d,(90,225),'先固定作者的 5.5 米，只改变一个帧间隔',38,c.FG,True)
  for k,n in enumerate([7,8,9]):
   x=85+k*615;panel(d,(x,330,x+565,780));col=c.GOLD if n==8 else c.CYAN
   txt(d,(x+35,365),f'{n} 个间隔',40,c.FG,True);txt(d,(x+30,460),f'{5.5/(n/30)*3.6:.2f}',100,col,True);txt(d,(x+40,590),'km/h',33,c.MUT)
   txt(d,(x+35,695),'基准' if n==8 else f'{(8/n-1)*100:+.2f}%',43,col,True)
  txt(d,(95,840),'单项计时扰动，已经超出 ±10%。',44,c.GOLD,True)
  txt(d,(95,925),'这是输入敏感性演示；距离5.5米保持为作者假设。',29,c.MUT)
