# Usage (from kahawa-check/audio/tools): ../../../.venv/bin/python tts.py ..   (writes ../sw/*.wav, ../kik/*.wav)
"""Synthesize audio for every sw string (facebook/mms-tts-swh) and every non-null kik string (facebook/mms-tts-kik).
Each sentence is synthesized separately and joined with a short silence (the MMS vocab has no punctuation, so
sentence pauses would otherwise be lost). Output: 16-bit PCM mono WAV at the model sampling rate (16 kHz).
Licence of both models: CC-BY-NC-4.0 (non-commercial)."""
import json, os, re, sys, time
import numpy as np
import torch
from scipy.io import wavfile
from transformers import VitsModel, AutoTokenizer
sys.path.insert(0, ".")
import content

OUT = sys.argv[1]
GAP_S = 0.30

def split(s):
    return [x for x in re.split(r"(?<=[.?!])\s+", s.strip()) if x]

def synth(model, tok, text, seed=0):
    sr = model.config.sampling_rate
    gap = np.zeros(int(GAP_S * sr), dtype=np.float32)
    parts = []
    for i, sent in enumerate(split(text)):
        torch.manual_seed(seed + i)  # VITS samples noise; fix the seed so reruns give the same audio
        enc = tok(sent, return_tensors="pt")
        if enc["input_ids"].shape[1] == 0:
            raise ValueError(f"empty tokenization: {sent!r}")
        with torch.no_grad():
            wav = model(**enc).waveform[0].numpy().astype(np.float32)
        parts += [wav, gap]
    y = np.concatenate(parts[:-1])
    y = y / max(1e-6, np.abs(y).max()) * 0.9  # peak-normalise to -0.9 dBFS
    return sr, (y * 32767).astype(np.int16)

log = {}
M = {}
for lang, repo in [("sw", "facebook/mms-tts-swh"), ("kik", "facebook/mms-tts-kik")]:
    M[lang] = (VitsModel.from_pretrained(repo).eval(), AutoTokenizer.from_pretrained(repo))

def dropped(tok, text):
    vocab = set(tok.get_vocab())
    return sorted({c for c in text.lower() if c not in vocab and c not in ".,?!;:"})

def write(lang, k, sr, y, note):
    os.makedirs(os.path.join(OUT, lang), exist_ok=True)
    path = os.path.join(OUT, lang, f"{k}.wav")
    wavfile.write(path, sr, y)
    log[f"{lang}/{k}"] = {"seconds": round(len(y) / sr, 2), "bytes": os.path.getsize(path), "sr": sr, **note}
    print(lang, k, log[f"{lang}/{k}"], flush=True)

for k, v in content.C.items():
    m, t = M["sw"]
    sr, y = synth(m, t, v["sw"])
    write("sw", k, sr, y, {"dropped_chars": dropped(t, v["sw"])})
    if v["kik_phrase"]:
        # Kikuyu phrase in the Kikuyu voice, then the remaining Swahili sentences in the Swahili voice.
        mk, tk = M["kik"]
        sr1, y1 = synth(mk, tk, v["kik_phrase"])
        parts = [y1]
        if v["kik_rest_sw"]:
            sr2, y2 = synth(m, t, v["kik_rest_sw"], seed=1)
            assert sr1 == sr2
            parts += [np.zeros(int(GAP_S * sr1), dtype=np.int16), y2]
        write("kik", k, sr1, np.concatenate(parts), {"dropped_chars": dropped(tk, v["kik_phrase"]), "kik_part_s": round(len(y1) / sr1, 2)})
json.dump(log, open("tts_log.json", "w"), ensure_ascii=False, indent=1)
