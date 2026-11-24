import json, sys, torch, torchaudio as ta
from chatterbox.tts import ChatterboxTTS
BEATS = [
 (0.4, "What if the Moon just vanished?"),
 (3.3, "Would you even notice?"),
 (6.85, "Poof!"),
 (7.8, "Just like that."),
 (10.6, "Without it, tides shrink by two thirds."),
 (16.2, "And the Earth starts to wobble."),
 (18.9, "Seasons get weird."),
 (21.9, "Nights get darker."),
 (23.9, "And the owls are very confused."),
 (27.4, "Thank you, Moon."),
 (28.8, "Keep looking up."),
]
torch.set_num_threads(4)
model = ChatterboxTTS.from_pretrained(device="cpu")
model.prepare_conditionals("my_voice_ref.wav", exaggeration=0.55)
meta = []
for i, (t, s) in enumerate(BEATS):
    w = model.generate(s, exaggeration=0.55, cfg_weight=0.40, temperature=0.7)
    ta.save(f"beat{i:02d}.wav", w, model.sr)
    meta.append((t, s, w.shape[1] / model.sr)); print(i, s, round(w.shape[1]/model.sr, 2), flush=True)
json.dump(meta, open("beats.json", "w"))
print("GEN DONE")
