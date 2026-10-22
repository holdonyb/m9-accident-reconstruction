"""Vertex Gemini 3.8 narration. Credentials stay in gcloud and process memory."""
import base64, concurrent.futures, hashlib, json, os, subprocess, time, wave
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parent
MODEL='gemini-3.8-flash-tts'
GCLOUD=r'E:\Program Files\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd'
def gcloud(*args):
    p=subprocess.run([GCLOUD,*args],capture_output=True,text=True,timeout=60)
    if p.returncode: raise RuntimeError('gcloud authentication/configuration failed')
    return p.stdout.strip()

def main():
    project=os.environ.get('GOOGLE_CLOUD_PROJECT') or gcloud('config','get-value','project')
    if not project or project=='(unset)': raise RuntimeError('Google Cloud project unset')
    token=gcloud('auth','print-access-token')
    target=ROOT/'audio';target.mkdir(exist_ok=True)
    scenes=json.loads((ROOT/'script.json').read_text('utf-8'))
    jobs=[(s['id'],i,t) for s in scenes for i,t in enumerate(s['lines'])]
    api_host=os.environ.get('M9_VERTEX_API_HOST','aiplatform.googleapis.com')
    location=os.environ.get('M9_VERTEX_LOCATION','global')
    url=f'https://{api_host}/v1/projects/{project}/locations/{location}/publishers/google/models/{MODEL}:generateContent'
    def generate(job):
        scene,i,transcript=job
        out=target/f'{scene}_{i:02}.wav';meta=out.with_suffix('.json')
        digest=hashlib.sha256(transcript.encode()).hexdigest()
        if out.exists() and meta.exists() and json.loads(meta.read_text())['text_sha256']==digest:
            return str(out.name)+' cached'
        body={'contents':[{'role':'user','parts':[{'text':transcript,'speechMetadata':{'style':'Speak Mandarin Chinese with clear standard pronunciation. A warm resonant male baritone narrator, intimate and compelling, like a high-end automotive documentary. Natural conversational Mandarin, grounded, not an announcer, never robotic. Crisp consonants, relaxed rich low register, varied rhythm, around 4.8 Chinese characters per second. Brief natural pauses at punctuation. Emphasize numerical comparisons. No theatrical excitement, no background music.'}}]}], 'generationConfig':{'responseModalities':['AUDIO'],'speechConfig':{'voiceConfig':{'voice':'Charon'}}}}
        for attempt in range(6):
            payload=target/f'{scene}_{i:02}.request.json'
            payload.write_text(json.dumps(body,ensure_ascii=False),encoding='utf-8')
            # TLS stays verified for the original host. Only transport resolution
            # uses another official Google API hostname because local proxy DNS
            # to the global hostname is intermittently failing.
            config='header = "Authorization: Bearer '+token+'"\nheader = "Content-Type: application/json"\n'
            transport=['us-central1-aiplatform.googleapis.com','aiplatform.mtls.googleapis.com','us-east1-aiplatform.googleapis.com'][attempt%3]
            cmd=['curl.exe','-sS','--connect-timeout','12','--max-time','150','--config','-','--connect-to',f'aiplatform.googleapis.com:443:{transport}:443','--data-binary','@'+str(payload),url]
            response=subprocess.run(cmd,input=config.encode(),capture_output=True,timeout=160)
            if response.returncode:
                if attempt<5:time.sleep(2);continue
                raise RuntimeError('Vertex network request failed: '+response.stderr.decode(errors='replace')[:160])
            data=json.loads(response.stdout)
            code=data.get('error',{}).get('code',200)
            if code in (429,500,502,503) and attempt<5:
                time.sleep(3+attempt*5);continue
            if code!=200:
                err=data.get('error',{})
                raise RuntimeError(f'{code}: {err.get("message","")[:450]}')
            parts=data.get('candidates',[{}])[0].get('content',{}).get('parts',[])
            audio=next((p['inlineData'] for p in parts if 'inlineData' in p),None)
            if audio is None:raise RuntimeError('No audio returned')
            raw=base64.b64decode(audio['data'])
            if raw[:4]==b'RIFF':out.write_bytes(raw)
            elif 'L16' in audio.get('mimeType','') or 'pcm' in audio.get('mimeType',''):
                with wave.open(str(out),'wb') as w:w.setparams((1,2,24000,0,'NONE','NONE'));w.writeframes(raw)
            else:raise RuntimeError('Unsupported audio type '+audio.get('mimeType',''))
            with wave.open(str(out)) as w: duration=w.getnframes()/w.getframerate()
            meta.write_text(json.dumps({'model_requested':MODEL,'model_returned':data.get('modelVersion'),'provider':'Vertex AI','voice':'Charon','text_sha256':digest,'seconds':duration,'mime':audio.get('mimeType'),'audio_sha256':hashlib.sha256(out.read_bytes()).hexdigest()},indent=2),encoding='utf-8')
            return f'{out.name}: {duration:.2f}s'
    # Probe first, then bounded concurrency for independent sentences.
    print(generate(jobs[0]),flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for result in pool.map(generate,jobs[1:]):print(result,flush=True)

if __name__=='__main__':main()

