"""Five narrative acts, with short cinematic section cards."""
from PIL import Image
ACTS=[
 ('看清经过','先看完整过程，再问速度从哪里来。',['title','overview','replay']),
 ('还原路口','把镜头抬高，看清路形与透视。',['map','perspective','environment']),
 ('逐帧测速','从一张原帧，走到曲线上的一个点。',['context','lamp','speed_clock','speed_scale','speed_points','speed_noise','speed_80','claims','speed_fit','speed_sum','model']),
 ('仿真检验','把速度放回这条路，看看车怎样停、怎样碰。',['braking','low_initial','hypotheses','low_impact','contact_results','event']),
 ('回到事故','把运动过程、原片后续和资料放到一起。',['closing','credits'])]
STARTS={a[2][0]:i for i,a in enumerate(ACTS) if i>0}
def act_for(sid):return next((i for i,a in enumerate(ACTS) if sid in a[2]),0)
def lead_for(sid):return 2.1 if sid in STARTS else .18
def draw_section(content,ch,t,g):
 sid=ch['id']
 if sid not in STARTS or t>=2.1:return content
 idx=STARTS[sid];name,detail,_=ACTS[idx]
 im=Image.new('RGB',(1920,1080),'#07121e');txt,line,rect,paste=[g[k] for k in ('txt','line','rect','paste')]
 q=1-(1-min(1,t/.7))**3
 for x in range(0,1920,96):line(im,[(x,0),(x,1080)],'#0e1e2a',1)
 for y in range(0,1080,96):line(im,[(0,y),(1920,y)],'#0e1e2a',1)
 txt(im,(105,96),'影像里的速度 / 神木路口',26,'#8ea8b8')
 txt(im,(110,225),f'PART {idx+1:02}',31,'#58d2c5',True)
 txt(im,(103,315+30*(1-q)),name,104,'#edf3f4',True)
 line(im,[(112,470),(112+770*q,470)],'#ffbd70',5)
 txt(im,(112,520),detail,30,'#a8bac7')
 src=g['render_img']('angle' if idx==1 else 'cctv' if idx==2 else 'curb' if idx==3 else 'orbit',1+int(t*25))
 rect(im,(1044,262,1844,772),'#173142',radius=18);paste(im,src,(1060,280,768,472))
 txt(im,(1062,786),['','路形与相机位置','原帧与投影','同一环境，改变输入','观察与计算'][idx],25,'#8ea8b8')
 for j,(label,_,__) in enumerate(ACTS):
  x=112+j*350;col='#58d2c5' if j==idx else '#5f7788'
  line(im,[(x,894),(x+294,894)],col,4 if j==idx else 2)
  txt(im,(x,923),f'{j+1:02}  {label}',27,col,j==idx)
 if t>1.72:
  u=(t-1.72)/.38;return Image.blend(im,content,u*u*(3-2*u))
 return im
