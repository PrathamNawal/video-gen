"""Synthesise a soft ambient score (no samples, nothing to license): slow Am - F - C - G pads with a faint high shimmer."""
import json, numpy as np, wave, sys
dur = json.load(open(sys.argv[1] + "/audio/timing.json"))["total_duration"] + 1.0
sr = 44100; n = int(sr * dur); t = np.arange(n) / sr
rng = np.random.default_rng(3)
def note(f): return 440 * 2 ** ((f - 69) / 12)
chords = [(57, 60, 64, 69), (53, 57, 60, 65), (48, 55, 60, 64), (55, 59, 62, 67)]   # Am F C G
seg = dur / 8.0
out = np.zeros(n)
for ci in range(8):
    ch = chords[ci % 4]
    t0, t1 = ci * seg, (ci + 1) * seg + 2.5
    i0, i1 = int(t0 * sr), min(n, int(t1 * sr))
    tt = t[i0:i1] - t0
    env = np.clip(tt / 2.8, 0, 1) ** 2 * np.clip((t1 - t[i0:i1]) / 2.5, 0, 1) ** 2
    for k, m in enumerate(ch):
        f = note(m - (12 if k == 0 else 0))
        for det in (-0.0035, 0.0, 0.0035):
            ff = f * (1 + det)
            v = np.sin(2 * np.pi * ff * tt) + 0.35 * np.sin(2 * np.pi * 2 * ff * tt) + 0.12 * np.sin(2 * np.pi * 3 * ff * tt)
            out[i0:i1] += v * env * (0.05 if k else 0.08) * (1 + 0.15 * np.sin(2 * np.pi * (0.11 + 0.02 * k) * tt))
# faint shimmer: sparse high notes
for i in range(26):
    tt0 = 3 + i * (dur - 8) / 26 + rng.uniform(-0.4, 0.4)
    m = [81, 84, 88, 91, 93][int(rng.integers(0, 5))]
    i0 = int(tt0 * sr); L = int(2.6 * sr)
    if i0 + L > n: continue
    x = np.arange(L) / sr
    out[i0:i0 + L] += np.sin(2 * np.pi * note(m) * x) * np.exp(-x * 1.7) * 0.018
# soft low-pass by moving average, gentle fade in/out, stereo with slight delay
k = 24; out = np.convolve(out, np.ones(k) / k, mode="same")
out *= np.clip(t / 3, 0, 1) * np.clip((dur - t) / 4, 0, 1)
out /= np.max(np.abs(out)) / 0.6
L = out; R = np.roll(out, int(0.011 * sr))
st = np.stack([L, R], 1)
pcm = (st * 32767).astype("<i2")
with wave.open(sys.argv[1] + "/audio/score.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())
print("score.wav", round(dur, 1), "s")
