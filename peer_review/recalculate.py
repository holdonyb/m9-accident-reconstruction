from pathlib import Path
import json, numpy as np
R=Path(__file__).resolve().parent
segments=[{'frames':8,'m':5.5},{'frames':27,'m':14.7},{'frames':23,'m':6.5}]
for x in segments:x.update(seconds=x['frames']/30,kmh=x['m']/(x['frames']/30)*3.6)
T=44.5/29.8;tb=7.5/29.8
grid=[]
for S in [49.7,52.2,54.7]:
 for ag in [.5,.65,.8]:
  a=ag*9.81;v0=(S+.5*a*(T-tb)**2)/T;vf=v0-a*(T-tb)
  grid.append(dict(distance_m=S,a_g=ag,start_kmh=v0*3.6,impact_kmh=vf*3.6,mean_kmh=S/T*3.6))
low=[]
for end_kmh in [20,40,50,60]:
 a=(52.2-end_kmh/3.6*T)/(.5*(T*T-tb*tb))
 low.append(dict(target_impact_kmh=end_kmh,required_constant_deceleration_g=a/9.81,initial_kmh=(end_kmh/3.6+a*(T-tb))*3.6,assumptions='52.2m; first 0.2517s constant speed, then constant braking; no obstacle impulse before endpoint'))
for n in [6,8,10]:print('5.5m /',n,'frames:',5.5/n*30*3.6)
out={'teacher_segments':segments,'teacher_whole':{'distance_m':26.7,'seconds':58/30,'mean_kmh':26.7/(58/30)*3.6},'teacher_after_stopline':{'distance_m':21.2,'seconds':50/30,'mean_kmh':21.2/(50/30)*3.6},'bird_inputs':{'time_s':T,'brake_on_s':tb,'distance_m':[49.7,54.7]},'bird_parameter_grid':grid,'low_impact_conditional_tests':low,'independent_clock_reading':{'source':'assets/source.mp4','clock_seconds':[13,14,15,16],'first_readable_frames':[308,339,368,398],'frame_intervals':[31,29,30],'three_second_average_fps':30,'note':'Zero-based file frames. Read visually from full-resolution clock crops. 3s agreement establishes average playback rate, not CCTV capture fps or every local update time.'}}
out['white_car_clock_reading']={'source':'assets/source.mp4','clock_seconds':[5,6,7,8],'first_readable_frames':[68,107,128,157],'frame_intervals':[39,21,29],'three_second_average_file_frames_per_clock_second':89/3,'note':'Zero-based sequentially decoded frames, confirmed with FFmpeg select=n and PTS. Local update timing is uneven. Frame 67 has mixed old/new clock digits; 68 is the first clear 05. This is timing evidence, not a white-car speed measurement.'}
(R/'recalculation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),'utf-8');print(json.dumps(out,ensure_ascii=False,indent=2))
