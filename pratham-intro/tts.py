import sys, json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
M='/tmp/claude-0/-home-user-video-gen/6d4a016a-85a4-5831-a276-85e929e0b110/scratchpad/kmodel/'
k=Kokoro(M+'kokoro-v1.0.onnx',M+'voices-v1.0.bin')
voice=sys.argv[1]; speed=float(sys.argv[2])
lines=json.load(open('lines.json')); dur={}
for l in lines:
    a,sr=k.create(l['text'],voice=voice,speed=speed,lang='en-us')
    a=np.trim_zeros(a,'fb') if False else a
    # trim silence
    idx=np.where(np.abs(a)>0.01)[0]; a=a[idx[0]:idx[-1]+1]
    sf.write(f"voice/{l['id']}.wav",a,sr); dur[l['id']]=len(a)/sr; print(l['id'],round(dur[l['id']],2))
json.dump(dur,open('voice/dur.json','w'))
