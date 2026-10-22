from pathlib import Path
import os,sys
import tts_vertex
os.environ['M9_VERTEX_TRANSPORT']='aiplatform.mtls.googleapis.com'
os.environ['M9_TTS_WORKERS']='1'
tts_vertex.ROOT=Path(__file__).resolve().parent/('qa_episode' if '--qa' in sys.argv else 'peer_review')
tts_vertex.main()
