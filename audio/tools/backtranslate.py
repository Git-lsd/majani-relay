# Usage (from kahawa-check/audio/tools): ../../../.venv/bin/python backtranslate.py
"""Back-translate every Swahili (swh_Latn) and Kikuyu (kik_Latn) string to English with NLLB-200-distilled-600M.
Sentence by sentence (NLLB sometimes drops sentences in long inputs), greedy-ish beam 4. Writes bt.json."""
import json, re, time, sys
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
sys.path.insert(0, ".")
import content

MODEL = "facebook/nllb-200-distilled-600M"
t0 = time.time()
tok_sw = AutoTokenizer.from_pretrained(MODEL, src_lang="swh_Latn")
tok_kik = AutoTokenizer.from_pretrained(MODEL, src_lang="kik_Latn")
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL).eval()
eng_id = tok_sw.convert_tokens_to_ids("eng_Latn")
print("loaded", round(time.time() - t0), "s", flush=True)

def split(s):
    return [x for x in re.split(r"(?<=[.?!])\s+", s.strip()) if x]

@torch.no_grad()
def tr(sents, tok):
    enc = tok(sents, return_tensors="pt", padding=True)
    out = model.generate(**enc, forced_bos_token_id=eng_id, num_beams=4, max_new_tokens=80)
    return tok.batch_decode(out, skip_special_tokens=True)

res = {}
extra_kik = {  # extra Kikuyu probes, not shipped unless they pass
    "probe_yes_no": "Ĩĩ kana aca?",
    "probe_thanks": "Nĩ wega.",
    "probe_dontknow": "Ndiĩ.", "probe_take1": "Oya mbica ĩngĩ.", "probe_leaves_plain": "Mathangũ maya nĩ mega.", "probe_officer": "Ũria afisa wa ũrimi."
}
for k, v in content.C.items():
    r = {"sw_sents": split(v["sw"])}
    r["sw_bt_sents"] = tr(r["sw_sents"], tok_sw)
    r["sw_bt"] = " ".join(r["sw_bt_sents"])
    if v["kik"]:
        r["kik_bt"] = " ".join(tr(split(v["kik"]), tok_kik))
    res[k] = r
    print(k, "|", r["sw_bt"], "|", r.get("kik_bt", ""), flush=True)
for k, s in extra_kik.items():
    res[k] = {"kik": s, "kik_bt": " ".join(tr([s], tok_kik))}
    print(k, s, "->", res[k]["kik_bt"])
json.dump(res, open("bt.json", "w"), ensure_ascii=False, indent=1)
print("done", round(time.time() - t0), "s")
