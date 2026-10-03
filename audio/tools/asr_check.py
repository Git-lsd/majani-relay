# Usage (from kahawa-check/audio/tools): ../../../.venv/bin/python asr_check.py ..
# Note: asr_check.json here was measured on pure-Kikuyu clips before the Kikuyu clips gained their Swahili tail;
# the Kikuyu phrase audio is the same waveform (same text, same seed). Rerunning now would score the mixed clips.
"""Machine round-trip check of the TTS audio: transcribe each WAV with MMS-1b-all (swh / kik adapter) and
compute character error rate (CER) and word error rate (WER) against the text that was synthesized.
Same model family as the TTS (MMS), so a low error rate means the audio is machine-intelligible,
not that a Kenyan farmer finds it natural."""
import json, re, sys, glob, os
import numpy as np, torch
from scipy.io import wavfile
from transformers import Wav2Vec2ForCTC, AutoProcessor
sys.path.insert(0, ".")
import content

AUDIO = sys.argv[1]

def norm(s):
    s = s.lower()
    s = re.sub(r"[^a-zĩũ' ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def ed(a, b):
    d = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        prev, d[0] = d[0], i
        for j in range(1, len(b) + 1):
            cur = d[j]
            d[j] = min(d[j] + 1, d[j - 1] + 1, prev + (a[i - 1] != b[j - 1]))
            prev = cur
    return d[len(b)]

proc = AutoProcessor.from_pretrained("facebook/mms-1b-all")
model = Wav2Vec2ForCTC.from_pretrained("facebook/mms-1b-all").eval()
ONLY = set(filter(None, os.environ.get("ONLY_IDS", "").split(",")))
LANGS = os.environ.get("LANGS", "sw,kik").split(",")
res = json.load(open("asr_check.json")) if ONLY and os.path.exists("asr_check.json") else {}
for lang, code in [("sw", "swh"), ("kik", "kik")]:
    if lang not in LANGS:
        continue
    proc.tokenizer.set_target_lang(code)
    model.load_adapter(code)
    tot_c = tot_ce = tot_w = tot_we = 0
    for k, v in content.C.items():
        if not v[lang] or (ONLY and k not in ONLY):
            continue
        sr, y = wavfile.read(os.path.join(AUDIO, lang, f"{k}.wav"))
        y = y.astype(np.float32) / 32767
        inp = proc(y, sampling_rate=sr, return_tensors="pt")
        with torch.no_grad():
            ids = model(**inp).logits.argmax(-1)[0]
        hyp = norm(proc.decode(ids))
        ref = norm(v[lang])
        ce, we = ed(ref, hyp), ed(ref.split(), hyp.split())
        tot_c += len(ref); tot_ce += ce; tot_w += len(ref.split()); tot_we += we
        res[f"{lang}/{k}"] = {"ref": ref, "hyp": hyp, "cer": round(ce / len(ref), 3), "wer": round(we / len(ref.split()), 3)}
        print(lang, k, res[f"{lang}/{k}"]["cer"], res[f"{lang}/{k}"]["wer"], "|", hyp, flush=True)
    if ONLY:  # recompute the overall score over all stored clips of this language
        items = [(r["ref"], r["hyp"]) for kk, r in res.items() if kk.startswith(lang + "/") and not kk.endswith("_overall")]
        tot_c = sum(len(a) for a, _ in items); tot_ce = sum(ed(a, b) for a, b in items)
        tot_w = sum(len(a.split()) for a, _ in items); tot_we = sum(ed(a.split(), b.split()) for a, b in items)
    res[f"{lang}/_overall"] = {"cer": round(tot_ce / tot_c, 3), "wer": round(tot_we / tot_w, 3), "n_chars": tot_c, "n_words": tot_w}
    print(lang, "OVERALL", res[f"{lang}/_overall"], flush=True)
json.dump(res, open("asr_check.json", "w"), ensure_ascii=False, indent=1)
