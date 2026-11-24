import json, torch, torchaudio as ta
from chatterbox.tts import ChatterboxTTS
# (start_time, text, exaggeration, cfg)  -- dramatic beats get a bit more energy
BEATS = [
 (0.4,  "Tonight.", 0.65, 0.35),
 (1.3,  "The Moon disappears.", 0.65, 0.35),
 (3.7,  "Everything goes pitch black.", 0.6, 0.38),
 (6.3,  "The oceans forget how to dance.", 0.55, 0.40),
 (9.2,  "Tides shrink by two thirds.", 0.55, 0.40),
 (11.7, "But here's the scary part.", 0.68, 0.33),
 (14.3, "The Moon was holding Earth steady.", 0.55, 0.40),
 (17.0, "Without it, Earth starts to wobble.", 0.62, 0.36),
 (20.0, "And over millions of years, the seasons go wild.", 0.62, 0.36),
 (23.8, "So tonight, look up.", 0.55, 0.40),
 (25.9, "Say thanks to the Moon.", 0.55, 0.40),
 (28.0, "It does more than you think.", 0.6, 0.38),
]
torch.set_num_threads(4)
model = ChatterboxTTS.from_pretrained(device="cpu")
model.prepare_conditionals("my_voice_ref.wav", exaggeration=0.55)
meta = []
for i, (t, s, ex, cfg) in enumerate(BEATS):
    w = model.generate(s, exaggeration=ex, cfg_weight=cfg, temperature=0.7)
    ta.save(f"beat{i:02d}.wav", w, model.sr)
    meta.append((t, s, w.shape[1] / model.sr)); print(i, s, round(w.shape[1]/model.sr, 2), flush=True)
json.dump(meta, open("beats.json", "w"))
print("GEN DONE")
