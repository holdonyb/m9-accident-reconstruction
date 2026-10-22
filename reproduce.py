"""Rebuild from saved inputs. Default is a non-mutating preflight."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,sys
R=Path(__file__).resolve().parent
def main():
 p=argparse.ArgumentParser();p.add_argument('--run',action='store_true');p.add_argument('--blender',default=os.environ.get('BLENDER_EXE') or shutil.which('blender') or 'C:/Program Files/Blender Foundation/Blender 5.1/blender.exe');args=p.parse_args()
 for name in ['ffmpeg','ffprobe']:
  if not shutil.which(name):raise SystemExit('Missing executable: '+name)
 if not Path(args.blender).is_file():raise SystemExit('Set --blender to Blender executable')
 for name in ['numpy','scipy','PIL','mujoco']:__import__(name)
 if not Path(os.environ.get('M9_FONT_REGULAR','C:/Windows/Fonts/msyh.ttc')).exists():raise SystemExit('Set M9_FONT_REGULAR and M9_FONT_BOLD to available Chinese font files')
 for name in ['assets/source.mp4','assets/vehicle_source.blend','scene_calibration.json','physics_results.json','script.json']:
  if not (R/name).is_file():raise SystemExit('Missing input: '+name)
 stale=[]
 for c in json.loads((R/'script.json').read_text('utf-8')):
  for i,words in enumerate(c['lines']):
   name=f'{c["id"]}_{i:02}';wav=R/'audio'/f'{name}.wav';meta=wav.with_suffix('.json')
   if not wav.exists() or not meta.exists():stale.append(name);continue
   data=json.loads(meta.read_text('utf-8'))
   if data['text_sha256']!=hashlib.sha256(words.encode()).hexdigest() or data['audio_sha256']!=hashlib.sha256(wav.read_bytes()).hexdigest():stale.append(name)
 if stale:raise SystemExit('Narration pending review/regeneration: '+', '.join(stale))
 print('INPUT PREFLIGHT PASSED',flush=True)
 if not args.run:return
 def call(*cmd):subprocess.run(cmd,cwd=R,check=True)
 call(sys.executable,'physics.py','--reuse')
 call(sys.executable,'alternative_speeds.py')
 call(sys.executable,'calculate_speed_workings.py')
 call(args.blender,'-b','--python','build_physics_blender.py')
 call(args.blender,'-b','--python','fix_side_camera.py')
 call(args.blender,'-b','--python','extend_blender.py')
 call(args.blender,'-b','-t','2','--python','render_physics.py')
 call(sys.executable,'compose_film.py')
 call(sys.executable,'check_editorial.py')
 call(sys.executable,'check_delivery.py','validate')
 call(args.blender,'-b','--python','finalize_project.py')
 call(args.blender,'-b','--python','check_blend_delivery.py')
 print('REBUILD AND DELIVERY VALIDATION PASSED',flush=True)
if __name__=='__main__':main()
