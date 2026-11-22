import subprocess, sys, wave, tempfile, os
txt, out = sys.argv[1], sys.argv[2]
model = os.environ["PIPER_MODEL"]
lines = [l.strip() for l in open(txt).read().split("\n") if l.strip()]
tmp = tempfile.mkdtemp()
frames, params = [], None
for i, l in enumerate(lines):
    p = f"{tmp}/{i}.wav"
    subprocess.run([sys.executable, "-m", "piper", "-m", model, "--length-scale", "1.08",
                    "--sentence-silence", "0.28", "-f", p], input=l.encode(), check=True, capture_output=True)
    w = wave.open(p); params = w.getparams(); frames.append(w.readframes(w.getnframes())); w.close()
sil = b"\x00\x00" * int(params.framerate * 1.0)
o = wave.open(out, "wb"); o.setparams(params)
o.writeframes(sil.join(frames)); o.close()
