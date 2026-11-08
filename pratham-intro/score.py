"""Procedural score: tuned marimba-like notes, felt pulse, foley, pad. Reads events.json (same table that drives the picture)."""
import json, numpy as np, wave
SR = 48000
d = json.load(open('events.json')); DUR = d['dur']; ev = d['ev']
N = int(SR * (DUR + 0.5)); L = np.zeros(N); R = np.zeros(N)
rng = np.random.default_rng(7)
def add(buf_l, buf_r, x, t, gain=1.0, pan=0.0):
    i = int(t * SR); n = min(len(x), N - i)
    if n <= 0: return
    gl = gain * np.cos((pan + 1) * np.pi / 4); gr = gain * np.sin((pan + 1) * np.pi / 4)
    buf_l[i:i+n] += x[:n] * gl; buf_r[i:i+n] += x[:n] * gr
def tt(dur): return np.arange(int(dur * SR)) / SR
def hz(m): return 440 * 2 ** ((m - 69) / 12)
def marimba(m, dur=1.4):
    t = tt(dur); f = hz(m)
    x = np.sin(2*np.pi*f*t)*np.exp(-t*3.2) + 0.35*np.sin(2*np.pi*f*4*t)*np.exp(-t*14) + 0.12*np.sin(2*np.pi*f*9.2*t)*np.exp(-t*30)
    a = np.minimum(1, t*600); return x * a
def noise_filt(dur, lo, hi):
    n = rng.standard_normal(int(dur*SR)); F = np.fft.rfft(n); fr = np.fft.rfftfreq(len(n), 1/SR)
    F *= ((fr > lo) & (fr < hi)); return np.fft.irfft(F, len(n))
def whoosh(dur, up=True):
    t = tt(dur); x = noise_filt(dur, 400, 7000); env = np.sin(np.pi * np.clip(t/dur, 0, 1)) ** 2
    return x * env / np.max(np.abs(x) + 1e-9) * 0.6
def key(): t = tt(0.05); return (rng.standard_normal(len(t)) * np.exp(-t*140) * 0.5 + np.sin(2*np.pi*2200*t) * np.exp(-t*200) * 0.3)
def digit(n): t = tt(0.04); return np.sin(2*np.pi*(1400+n*90)*t) * np.exp(-t*110) * 0.35
def pulse(): t = tt(0.4); return np.sin(2*np.pi*(55 + 40*np.exp(-t*30))*t) * np.exp(-t*7)
def crt(): t = tt(0.55); f = 1800*np.exp(-t*7)+60; ph = 2*np.pi*np.cumsum(f)/SR; return np.sin(ph)*np.exp(-t*5)*0.45 + noise_filt(0.55, 2000, 9000)*np.exp(-t*20)*0.2
def shimmer(): 
    t = tt(1.2); x = sum(np.sin(2*np.pi*hz(m)*t)*np.exp(-t*2.5)*(0.5/(k+1)) for k, m in enumerate([84, 88, 91, 96, 100])); return x*np.minimum(1, t*30)*0.35
def chord(big):
    dur = 3.0 if big else 1.8; x = 0
    for k, m in enumerate([60, 64, 67, 71, 74] if big else [64, 67, 72]): x = x + marimba(m + (12 if (k % 2 == 0 and big) else 0), dur) * (0.5 / (1 + 0.1*k))
    t = tt(dur); pad = sum(np.sin(2*np.pi*hz(m)*t) for m in (48, 55, 60, 64)) * 0.08 * np.minimum(1, t*4) * np.exp(-t*(0.9 if big else 2))
    return x*0.6 + pad
for e in ev:
    ty = e['type']; t = e['t']
    if ty == 'key': add(L, R, key(), t, 0.5, rng.uniform(-0.15, 0.15))
    elif ty == 'note': add(L, R, marimba(e['n']), t, 0.55, 0.0); add(L, R, marimba(e['n']-12, 1.0), t, 0.2)
    elif ty == 'digit': add(L, R, digit(e['n']), t, 0.5, rng.uniform(-0.5, 0.5))
    elif ty == 'lock': add(L, R, marimba(84, 0.5), t, 0.12, 0.2)
    elif ty == 'whoosh': add(L, R, whoosh(0.6), t - 0.05, 0.5)
    elif ty == 'whoosh_s': add(L, R, whoosh(0.5), t, 0.35, rng.uniform(-0.6, 0.6))
    elif ty == 'crt': add(L, R, crt(), t, 0.5)
    elif ty == 'pulse': add(L, R, pulse(), t, 0.5)
    elif ty == 'shimmer': add(L, R, shimmer(), t, 0.5)
    elif ty == 'chord': add(L, R, chord(bool(e.get('big'))), t, 0.55)
# quiet pad bed under everything, swells into the end card
t = tt(DUR + 0.5); bed = sum(np.sin(2*np.pi*hz(m)*t + k) for k, m in enumerate([36, 43, 48])) * 0.05
env = np.clip(t/1.5, 0, 1) * (0.5 + 0.5*np.clip((t-8.5)/1.0, 0, 1))
L += bed * env; R += bed * env
# fade tail, normalise to about -14 LUFS-ish peak headroom
fade = np.clip((DUR + 0.5 - t) / 0.6, 0, 1); L *= fade; R *= fade
pk = max(np.abs(L).max(), np.abs(R).max()); g = 0.85 / pk
out = (np.stack([L, R], 1) * g * 32767).astype('<i2')
with wave.open('score.wav', 'wb') as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(out.tobytes())
print('score.wav ok, peak scale', round(g, 2))
