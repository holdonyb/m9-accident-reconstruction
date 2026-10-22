"""Show the observed stop-line event without inventing a ground contact point."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,numpy as np
R=Path(__file__).resolve().parent;O=R/'teacher_input_audit';rows=json.loads((O/'frame_matches.json').read_text('utf-8'))
row=next(r for r in rows if r['author_label']=='author61');H=np.array(row['candidates'][0]['matrix']);q=np.linalg.inv(H)@np.array([321,305,1]);q=q[:2]/q[2]
line=np.array([[620.,471.],[1086.,509.]])
yline=float(line[0,1]+(q[0]-line[0,0])*(line[1,1]-line[0,1])/(line[1,0]-line[0,0]))
data={'author_second':47,'author_frame_label':61,'best_raw_frame':346,'author_circle_center_px':[321,305],'circle_backprojected_raw_px':q.tolist(),'stop_line_visible_segments_reference_raw_px':line.tolist(),'stop_line_y_at_circle_x':yline,'visible_rear_lower_edges_approx_raw_y':[505,525],'interpretation':'Visible upper tail-lamp trace has crossed the image of the stop line; visible lower rear-body traces remain on the camera side of it. On a locally planar road viewed from above, an elevated rear point projecting on the near side cannot establish that its ground footprint crossed the line. This challenges the named rear-over-stop-line event. Do not substitute a precise wheel-contact coordinate or infer speed from this illustration. Two rear-light and plate images are visible in this phone frame; corresponding exposure times unresolved.'}
data['visible_rear_lower_edges_approx_raw_y']=[495,530]
data['lower_edge_note']='Broad manually inspected band covering visible rear lower traces, not precise contact-point coordinates.'
(O/'endpoint_audit.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),'utf-8')
im=Image.new('RGB',(1920,1080),'#08131d');d=ImageDraw.Draw(im);font=lambda s:ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',s)
d.text((65,35),'灯在画面里越线，车尾就越线了吗？',font=font(53),fill='white')
author=Image.open(O/'author_47.png');author.thumbnail((670,670));im.paste(author,(65,185));d.text((65,125),'原作者：第61帧',font=font(31),fill='#ffcd70')
raw=Image.open(R/'raw_sequence/0346.jpg');crop=(720,360,990,560);patch=raw.crop(crop).resize((1080,800));im.paste(patch,(780,165));sx=4
def point(p):return (780+(p[0]-crop[0])*sx,165+(p[1]-crop[1])*sx)
ends=[]
for x in [725,985]:ends.append(point((x,line[0,1]+(x-line[0,0])*(line[1,1]-line[0,1])/(line[1,0]-line[0,0]))))
d.line(ends,fill='#ffcd70',width=5);d.text((800,710),'停止线：按两侧可见段延伸',font=font(28),fill='#ffcd70')
x,y=point(q);d.ellipse((x-19,y-19,x+19,y+19),outline='#52dfdc',width=5);d.text((800,195),'原片第346帧 · 同一画面',font=font(29),fill='white')
d.text((1410,420),'圈选的是车灯',font=font(29),fill='#52dfdc');d.line([(1400,455),(x+22,y)],fill='#52dfdc',width=3)
d.rectangle((*point((790,495)),*point((918,530))),outline='#ff8d86',width=4)
d.text((800,905),'可见车尾下缘仍在线的近侧',font=font(29),fill='#ff8d86')
d.text((65,915),'这一格还叠着两个车辆位置。',font=font(34),fill='white');d.text((65,975),'先统一取点和曝光，再确定过线时刻。',font=font(31),fill='#aebfcb')
im.save(O/'endpoint_audit.jpg',quality=96);print(json.dumps(data,ensure_ascii=False,indent=2))
