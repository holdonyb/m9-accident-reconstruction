"""Bake MuJoCo solver outputs into a photograph-textured, editable Blender scene."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
from bpy_extras.object_utils import world_to_camera_view
R=Path(__file__).resolve().parent;D=json.loads((R/'physics_results.json').read_text('utf-8'));M=json.loads((R/'scene_calibration.json').read_text('utf-8'));P=M['projection'];G=json.loads((R/'assets/geometry.json').read_text('utf-8'))
bpy.ops.wm.open_mainfile(filepath=str(R/'assets/vehicle_source.blend'))
main=bpy.context.scene;bpy.context.window.scene=main
for sc in list(bpy.data.scenes):
 if sc!=main:bpy.data.scenes.remove(sc)
veh=bpy.data.collections['06_主角车辆_动画与形变'];root=bpy.data.objects['CAR_RIG_整车运动'];oldobjects=set(veh.objects)
for ob in list(bpy.data.objects):
 if ob not in oldobjects:bpy.data.objects.remove(ob,do_unlink=True)
for ob in veh.objects:
 ob.animation_data_clear();ob.hide_render=False;ob.hide_set(False)
 if ob.type=='MESH' and ob.data.shape_keys:
  ob.data.shape_keys.animation_data_clear()
  for kb in ob.data.shape_keys.key_blocks[1:]:kb.value=0
for co in list(main.collection.children):
 if co!=veh:main.collection.children.unlink(co)
for mat in bpy.data.materials:
 if mat.animation_data:mat.animation_data_clear()
 if mat.use_nodes and mat.node_tree.animation_data:mat.node_tree.animation_data_clear()
for mar in list(main.timeline_markers):main.timeline_markers.remove(mar)
main.name='01_基准_真实照片与物理仿真';FWD=Vector((*P['forward'],0));RIGHT=Vector((*P['right'],0));OFF=Vector((*P['world_offset'],0));CAM=OFF+Vector((0,0,P['A']+1.21));F=P['F']
env=bpy.data.collections.new('环境_原始卫星底图');main.collection.children.link(env)
photo=bpy.data.collections.new('环境_原视频投影');main.collection.children.link(photo)
metrics=bpy.data.collections.new('测量_卫星图道路方向');main.collection.children.link(metrics)
rig=bpy.data.collections.new('设施_接触位置假设');main.collection.children.link(rig)
def config(s):
 s.render.engine='BLENDER_WORKBENCH';sh=s.display.shading;sh.light='STUDIO';sh.color_type='TEXTURE';sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH';sh.show_specular_highlight=True;sh.show_object_outline=False;sh.background_type='WORLD';s.world.color=(.012,.019,.028);s.view_settings.view_transform='Standard';s.view_settings.exposure=0;s.display.render_aa='16'
 s.render.resolution_x=1600;s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.fps=30;s.render.image_settings.file_format='JPEG';s.render.image_settings.quality=95;s.render.use_sequencer=False;s.frame_start=1;s.frame_end=91
config(main)
def material(n,col):
 m=bpy.data.materials.new(n);m.diffuse_color=(*col,1);return m
def texmat(n,path):
 m=bpy.data.materials.new(n);m.use_nodes=True;nd=m.node_tree.nodes;t=nd.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(path),check_existing=True);t.image.pack();nd.active=t;m.node_tree.links.new(t.outputs['Color'],nd.get('Principled BSDF').inputs['Base Color']);return m
def mesh(n,verts,faces,uvs,ma,co):
 me=bpy.data.meshes.new(n);me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new(n,me);co.objects.link(ob);me.materials.append(ma);layer=me.uv_layers.new()
 for poly in me.polygons:
  for li in poly.loop_indices:layer.data[li].uv=uvs[me.loops[li].vertex_index]
 return ob
def line(n,pts,width,ma,co=metrics):
 cu=bpy.data.curves.new(n,'CURVE');cu.dimensions='3D';cu.bevel_depth=width;cu.bevel_resolution=2;sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
 for pp,xyz in zip(sp.points,pts):pp.co=(*xyz,1)
 ob=bpy.data.objects.new(n,cu);co.objects.link(ob);ob.data.materials.append(ma);return ob
def box(n,loc,dim,ma,co):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);ob=bpy.context.object
 for c in list(ob.users_collection):c.objects.unlink(ob)
 co.objects.link(ob);ob.name=n;ob.dimensions=dim;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);ob.data.materials.append(ma);return ob
def camera(n,loc,target,scene=main,lens=40,ortho=None):
 data=bpy.data.cameras.new(n);ob=bpy.data.objects.new(n,data);scene.collection.objects.link(ob);aim(ob,loc,target);data.lens=lens;data.clip_end=1500
 if ortho:data.type='ORTHO';data.ortho_scale=ortho
 return ob
def aim(ob,loc,target):ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
def exclude(s,name,yes=True):
 lc=s.view_layers[0].layer_collection.children.get(name)
 if lc:lc.exclude=yes
sat=texmat('百度卫星图_原始像素',R/'assets/satellite_full.png');raw=texmat('源视频330帧_道路与背景原图',R/'assets/stable_png/0330.png')
ox,oy=G['origin_px'];scale=G['meters_per_pixel_approx'];W,H=1707,932
# Trim only browser UI, preserving the actual aerial pixels.
pix=[(30,45),(1635,45),(1635,875),(30,875)];verts=[((x-ox)*scale,(oy-y)*scale,.19) for x,y in pix];mesh('卫星实景地面',verts,[(0,1,2,3)],[(x/W,1-y/H) for x,y in pix],sat,env)
# Original-frame projection, densely tessellated; no regenerated lane markings.
def projected(x,y,z=.205):
 depth=F*(CAM.z-z)/y;return tuple(OFF+FWD*depth+RIGHT*((x-640)*depth/F)+Vector((0,0,z)))
xs=list(range(0,1281,40));ys=list(range(165,721,15));verts=[];uvs=[];faces=[]
for y in ys:
 for x in xs:verts.append(projected(x,y));uvs.append((x/1280,1-y/720))
for j in range(len(ys)-1):
 for i in range(len(xs)-1):a=j*len(xs)+i;faces.append((a,a+1,a+1+len(xs),a+len(xs)))
mesh('原视频道路_斑马线车道线湿地反光',verts,faces,uvs,raw,photo)
# Backdrop above the ground junction. The timestamp band is outside this mesh.
depth=F*(CAM.z-.205)/165;pix=[(0,70),(1280,70),(1280,165),(0,165)];verts=[tuple(OFF+FWD*depth+RIGHT*((x-640)*depth/F)+Vector((0,0,CAM.z-y*depth/F))) for x,y in pix]
mesh('原视频背景_树木信号灯远侧设施',verts,[(0,1,2,3)],[(x/1280,1-y/720) for x,y in pix],raw,photo)
gold=material('测量金',(.95,.62,.23));cyan=material('测量青',(.13,.75,.7));steel=material('原片对应立柱_位置假设',(.21,.25,.28))
for n,v in [('杨业大街',(-75,271)),('滨河西路',(433,-197)),('云川大道',(-307,202))]:
 vv=Vector((*v,0)).normalized()*56;line(n+'道路中轴',[(0,0,.35),(vv.x,vv.y,.35)],.13,gold)
a0=math.atan2(271,-75);a1=math.atan2(-197,433);pts=[(17*math.cos(a0+(a1-a0)*i/90),17*math.sin(a0+(a1-a0)*i/90),.37) for i in range(91)]
# Short arc corresponding to the obtuse road interior.
a1=a0-math.radians(G['obtuse_deg']);pts=[(17*math.cos(a0+(a1-a0)*i/90),17*math.sin(a0+(a1-a0)*i/90),.37) for i in range(91)];line('地面夹角_约130度',pts,.16,cyan)
pp=Vector(D['environment']['pole_position'])
box('立柱_固定接触假设',(pp.x,pp.y,3.9),(.36,.36,7.4),steel,rig)
E=D['environment'];RD=Vector(E['road_direction']);OUT=Vector(E['curb_outward']);CE=Vector(E['curb_edge']);road_yaw=math.atan2(RD.y,RD.x)
sp=pp-RD*1.6-OUT*.10;box('细立柱_位置敏感性假设',(sp.x,sp.y,3.2),(.15,.15,6),steel,rig)
site=texmat('现场后拍照片_原始铺砖纹理',R/'site_after_user.png')
curbco=bpy.data.collections.new('路缘人行道_16厘米假设');main.collection.children.link(curbco)
def pavement(co,height):
 curbmat=material(co.name+'_路缘石',(.32,.34,.35))
 for i in range(-25,25):
  cc=CE+RD*(i+.5)+OUT*.12;ob=box('路缘石_连续碰撞边界',(cc.x,cc.y,.2+height/2),(.994,.24,height),curbmat,co);ob.rotation_euler.z=road_yaw
 # The slab is the same collision surface as in MuJoCo. Paver texture comes from the supplied site photo.
 for i in range(-25,25):
  for j in range(4):
   a=CE+RD*i+OUT*(.24+j*.94);b=a+RD;c=b+OUT*.94;d=a+OUT*.94
   vv=[(v.x,v.y,.2+height+.002) for v in [a,b,c,d]]
   mesh('人行道_现场原图纹理',vv,[(0,1,2,3)],[(420/669,1-475/648),(575/669,1-475/648),(575/669,1-630/648),(420/669,1-630/648)],site,co)
pavement(curbco,.16)

# The tail feature is 1.01 m above visual root; MuJoCo chassis origin is .81 m above it.
root.rotation_mode='QUATERNION';high=bpy.data.objects['高位制动灯_源帧357亮起'];wheels=[ob for ob in veh.objects if ob.name.startswith('WHEEL_SPIN_')]
wheel_tags={ob:('-1' if ob.location.x<0 else '1')+'_'+('-1' if ob.location.y<0 else '1') for ob in wheels}
# Wheel spin objects may be local to steering pivots: identify by rest world transforms.
root.location=(0,0,0);root.rotation_quaternion=(1,0,0,0);bpy.context.view_layer.update()
for ob in wheels:
 loc=ob.matrix_world.translation;wheel_tags[ob]=('-1' if loc.x<0 else '1')+'_'+('-1' if loc.y<0 else '1');ob.parent=root;ob.matrix_parent_inverse=Matrix.Identity(4);ob.rotation_mode='QUATERNION'
print('WHEEL TAGS',[(o.name,t) for o,t in wheel_tags.items()],flush=True)
def animate(s,vr,objects,scenario):
 rt=objects[root];rt.rotation_mode='QUATERNION';hm=objects[high].data.materials[0]
 for ob in objects.values():ob.animation_data_clear()
 for st in scenario['states']:
  fr=st['source_frame']-343;q=Quaternion(st['quaternion']);rt.location=Vector(st['position'])-q@Vector((0,0,.81));rt.rotation_quaternion=q;rt.keyframe_insert('location',frame=fr);rt.keyframe_insert('rotation_quaternion',frame=fr);bpy.context.view_layer.update()
  for old,tag in wheel_tags.items():
   wo=objects[old];actual=next(w for w in st['wheels'] if w['tag']==tag);loc=q.inverted()@(Vector(actual['position'])-rt.location);wo.location=loc;wo.rotation_quaternion=q.inverted()@Quaternion(actual['quaternion']);wo.keyframe_insert('location',frame=fr);wo.keyframe_insert('rotation_quaternion',frame=fr)
  on=st['t']>=13/30+scenario['brake_shift'];hm.diffuse_color=(1,.03,.012,1) if on else (.015,.005,.005,1);hm.keyframe_insert('diffuse_color',frame=fr)
 s['scenario_id']=scenario['id'];s['engine']='MuJoCo '+scenario['engine'];s['source_mapping']='source frame = Blender frame +343, 30 fps';s['metric_status']='Conditional camera/scale. Image textures are original evidence; unseen geometry and vehicle dynamics are assumptions.'
 for lab,n in [('起点',344),('原片高位灯亮起',357),('接触前末帧',393)]:s.timeline_markers.new(lab,frame=n-343)
 if scenario['pole_contact_s'] is not None:s.timeline_markers.new('本假设首次接触',frame=round(scenario['pole_contact_s']*30)+1)
for m in [high.data.materials[0]]:
 m.use_nodes=False
animate(main,veh,{o:o for o in veh.objects},D['scenarios'][0])
cctv=camera('CAM_原视频方向',CAM,CAM+FWD,lens=F*36/1280);cctv.data.sensor_width=36;cctv.data.sensor_fit='HORIZONTAL';cctv.data.shift_y=-.28125
follow=camera('CAM_后侧跟拍',(0,0,0),(0,1,0),lens=35)
side=camera('CAM_路边固定',(60,-3,12),(-2,-3,1),lens=28)
top=camera('CAM_俯视全程',(1,1,110),(1,1,0),ortho=87);top.rotation_euler=(0,0,math.pi/2)
curbcam=camera('CAM_路缘与立柱近景',(20,-39,5),(6,-26,1),lens=38)
for st in D['scenarios'][0]['states']:
 fr=st['source_frame']-343;q=Quaternion(st['quaternion']);center=Vector(st['position']);fw=q@Vector((0,1,0));rr=q@Vector((1,0,0));aim(follow,center-fw*10+rr*7+Vector((0,0,4.4)),center)
 follow.keyframe_insert('location',frame=fr);follow.keyframe_insert('rotation_euler',frame=fr)
for sc in [main]:exclude(sc,metrics.name)
main.camera=follow
specs=[dict(id=n,scene=main.name,camera=c.name,start=1,end=91) for n,c in [('cctv',cctv),('follow',follow),('side',side),('top',top),('curb',curbcam)]]
# Separate hypotheses share identical scene geometry and camera, never offset tracks.
for scenario in D['scenarios'][1:]:
 s=main.copy();s.name='假设_'+scenario['label'];exclude(s,veh.name);
 if scenario['curb_height']!=.16:
  exclude(s,curbco.name);cc=bpy.data.collections.new('路缘人行道_'+scenario['id']);s.collection.children.link(cc);pavement(cc,scenario['curb_height'])
 co=bpy.data.collections.new('车辆_'+scenario['id']);s.collection.children.link(co);mapping={}
 for old in veh.objects:
  ob=old.copy();ob.animation_data_clear();co.objects.link(ob);mapping[old]=ob
  if old==high:ob.data=old.data.copy();ma=old.data.materials[0].copy();ma.animation_data_clear();ob.data.materials.clear();ob.data.materials.append(ma)
 for old,ob in mapping.items():
  if old.parent in mapping:ob.parent=mapping[old.parent]
 bpy.context.window.scene=s;animate(s,co,mapping,scenario);s.camera=top
 specs.append(dict(id=scenario['id'],scene=s.name,camera=(curbcam.name if scenario['id'] in ['lowcurb','highcurb'] else top.name),start=1,end=91))
# Satellite-only angle explanation: aerial -> low view, roads remain fixed.
mapsc=main.copy();mapsc.name='地图_原始卫星图与透视';exclude(mapsc,veh.name);exclude(mapsc,photo.name);exclude(mapsc,rig.name);exclude(mapsc,curbco.name);exclude(mapsc,metrics.name,False);mapsc.frame_end=151
mapcam=camera('CAM_卫星到低视角',(0,0,0),(0,1,0),scene=mapsc,lens=28);mapsc.camera=mapcam;angular=[];bpy.context.window.scene=mapsc
for fr in range(1,152):
 u=(fr-1)/150;u=u*u*(3-2*u);a=math.radians(105+25*u);el=math.radians(84-71*u);rr=185;aim(mapcam,(rr*math.cos(el)*math.cos(a),rr*math.cos(el)*math.sin(a),rr*math.sin(el)),(0,0,0));mapcam.keyframe_insert('location',frame=fr);mapcam.keyframe_insert('rotation_euler',frame=fr);bpy.context.view_layer.update()
 vs=[Vector((0,0,.35)),Vector((-75,271,0)).normalized()*56,Vector((433,-197,0)).normalized()*56];coords=[]
 for v in vs:uv=world_to_camera_view(mapsc,mapcam,v);coords.append([uv.x*1600,(1-uv.y)*900])
 aa=Vector(coords[1])-Vector(coords[0]);bb=Vector(coords[2])-Vector(coords[0]);angular.append(dict(frame=fr,points=coords,screen_angle=math.degrees(aa.angle(bb))))
specs.append(dict(id='angle',scene=mapsc.name,camera=mapcam.name,start=1,end=151));(R/'angle_projection.json').write_text(json.dumps(angular),'utf-8')
# 360 degrees, exactly one frozen solver state.
bpy.context.window.scene=main;main.frame_set(50);bpy.context.view_layer.update();orbit=main.copy();orbit.name='冻结_接触前360度';exclude(orbit,veh.name);freeze=bpy.data.collections.new('车辆_冻结真实求解状态');orbit.collection.children.link(freeze);mp={}
for old in veh.objects:
 ob=old.copy();ob.animation_data_clear();freeze.objects.link(ob);mp[old]=ob
for old,ob in mp.items():
 if old.parent in mp:ob.parent=mp[old.parent]
orb=camera('CAM_冻结360度',(0,0,0),(0,1,0),scene=orbit,lens=32);orbit.camera=orb;orbit.frame_end=121;center=Vector(D['scenarios'][0]['states'][49]['position'])
for fr in range(1,122):
 a=math.radians(35+360*(fr-1)/120);aim(orb,center+Vector((11*math.cos(a),11*math.sin(a),5)),center);orb.keyframe_insert('location',frame=fr);orb.keyframe_insert('rotation_euler',frame=fr)
specs.append(dict(id='orbit',scene=orbit.name,camera=orb.name,start=1,end=121))
# Independent baked sample projection check, camera convention shared with solver.
bpy.context.window.scene=main;main.camera=cctv;checks=[]
for st in D['scenarios'][0]['states'][:50]:
 fr=st['source_frame']-343;main.frame_set(fr);bpy.context.view_layer.update();uv=world_to_camera_view(main,cctv,Vector(st['rear']));checks.append(dict(frame=st['source_frame'],solver=st['pixel'],blender=[uv.x*1280,(1-uv.y)*720]))
(R/'projection_physics.json').write_text(json.dumps(checks),'utf-8');(R/'shots_physics.json').write_text(json.dumps(specs,ensure_ascii=False,indent=2),'utf-8')
main.camera=follow;main.frame_set(30)
text=bpy.data.texts.new('必读_原图环境与求解器');text.write('源视频逐帧道路投影 + 百度卫星原图。外观按可见原图，未拍到的背面没有照片证据。车辆采用MuJoCo四轮刚体、弹簧阻尼悬架、转向及制动扭矩，每秒600步；每20步烘焙一帧。没有预设位移轨迹，也没有接触后手工抬车。七组输入假设可切换场景。车辆为M9尺寸的通用模型，轮胎、ABS简化控制与惯量不是原厂数据。相机/米制尺度/立柱位置是条件假设；求解器参数见physics_results.json。画面原始测点与模型误差见配套报告。')
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='SOLID';area.spaces.active.shading.color_type='TEXTURE'
for sc in bpy.data.scenes:sc.use_fake_user=True
bpy.ops.wm.save_as_mainfile(filepath=str(R/'神木路口_原图环境与七种物理假设.blend'))
qa=R/'qa_physics';qa.mkdir(exist_ok=True)
for sp in specs:
 if sp['id'] not in ['cctv','follow','side','top','angle','orbit']:continue
 s=bpy.data.scenes[sp['scene']];bpy.context.window.scene=s;s.camera=bpy.data.objects[sp['camera']];s.frame_set(30 if sp['id'] not in ['angle','orbit'] else 75);s.render.filepath=str(qa/(sp['id']+'.jpg'));bpy.ops.render.render(write_still=True)
print('PHYSICS BLEND READY',flush=True)
