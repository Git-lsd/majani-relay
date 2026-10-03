# Usage (from kahawa-check/audio/tools): ../../../.venv/bin/python build_answers.py ../..
"""Assemble kahawa-check/answers.json from content.py + bt.json (NLLB back-translations) + my own meaning comparison."""
import json, os, re, sys
sys.path.insert(0, ".")
import content

ROOT = sys.argv[1]
bt = json.load(open("bt.json"))

# My comparison of the NLLB back-translation with the English source.
# "ok"    = the back-translation keeps the meaning (word-sense slips I checked are listed).
# "check" = the back-translation changes a word that matters; a native speaker must confirm the Swahili.
CMP = {
 "result_healthy": ("ok", "'kutu' came back as 'corrosion': same Swahili word as metal rust; NLLB lacks the plant sense."),
 "result_rust": ("ok", "Meaning kept; 'kutu' rendered as 'rash' in sentence two (word-sense slip)."),
 "result_miner": ("check", "'wadudu wachimba majani' came back as 'insects digging for grass' ('majani' = leaves or grass). Ask a reviewer for the usual Kenyan Swahili name for leaf miner."),
 "result_cercospora": ("ok", "Meaning kept. The Swahili disease name is descriptive ('brown spot disease')."),
 "result_phoma": ("ok", "Meaning kept."),
 "result_not_sure": ("ok", "'afisa wa ugani' came back as 'fiction agent' here only; the same phrase back-translates as 'extension officer' in other strings."),
 "retake_photo": ("ok", "'upande wa chini' came back as 'bottom' (= underside)."),
 "action_healthy": ("ok", "'Pogoa' came back as 'cut' (= prune)."),
 "action_rust": ("ok", "Meaning kept; 'kutu' rendered as 'corrosion'."),
 "action_miner": ("check", "'Nyigu' (wasp) came back as 'ants'. I believe 'nyigu' is correct; a reviewer should confirm."),
 "action_cercospora": ("check", "'matandazo' (mulch) came back as 'nets'. Reviewer should confirm the farmer word for mulch."),
 "action_phoma": ("check", "Three slips: 'baridi' -> 'winter', 'miti ya kuzuia upepo' (windbreak trees) -> 'windmills', 'afisa wa ugani' -> 'medical examiner'."),
 "action_not_sure": ("check", "'utepe' (ribbon) came back as 'stick'."),
 "plot_all_healthy": ("ok", "Meaning kept."),
 "plot_some_problem": ("ok", "Meaning kept."),
 "plot_officer_alert": ("ok", "Meaning kept; 'kadhaa' (several) came back as 'some', 'mapema' (soon) as 'in advance'."),
 "check_q1_old_trees": ("check", "Came back as 'cutting down trees to sprout new shoots'. Reviewer should check that 'kukata miti chini' is heard as stumping, not felling."),
 "check_q2_no_fertiliser": ("check", "'mbolea ya samadi' (manure) was lost; came back as 'coffee fertilizer or store fertilizer'."),
 "check_q3_weeding": ("ok", "Meaning kept."),
 "check_q4_berry_spots": ("ok", "'yaliyozama ndani' (sunken) came back as 'deep'."),
 "check_q5_berry_holes": ("check", "'mdudu anayetoboa matunda' (berry-boring insect) came back as 'fruit picking insect'; 'afisa wa ugani' -> 'rumor officer'."),
 "check_q6_dry_flowering": ("check", "'kiangazi' (dry season) came back as 'summer'; 'matandazo' (mulch) as 'grids'."),
 "disclaimer_final_call": ("ok", "Meaning kept."),
 "consent_photos": ("check", "'chama cha ushirika' (cooperative society) came back as 'company'. Consent text should be reviewed by a speaker before any real use."),
}
KIK_CMP = {"result_healthy": "ok", "result_not_sure": "ok", "retake_photo": "ok"}
asr = json.load(open("asr_check.json"))  # MMS-1b-all transcription of the generated audio

out = {}
for k, v in content.C.items():
    status, comment = CMP[k]
    cited = [s for s in content.SOURCES if re.search(r"\b" + s + r"\b", v["notes"])]
    notes = v["notes"]
    notes += " Back-translation check (NLLB-600M, swh->eng, machine only): " + comment
    if v["kik"]:
        notes += (" The kik field = a short Kikuyu phrase ('" + v["kik_phrase"] + "') that replaces the first Swahili sentence, "
                  "followed by the remaining Swahili sentences, so nothing is dropped. "
                  "Kikuyu back-translation (NLLB kik->eng, FLORES chrF++ 42.9, weak evidence): '" + bt[k]["kik_bt"] + "'.")
        if k == "result_not_sure":
            notes += " Machine transcription of the 0.5 s Kikuyu clip failed (heard 'ĩe'); a recorded human clip would be better."
    if cited:
        notes += " Sources: " + " | ".join(f"{s} = {content.SOURCES[s]}" for s in cited)
    out[k] = {
        "en": v["en"],
        "sw": v["sw"],
        "kik": v["kik"],
        "sw_verified": False,
        "kik_verified": False,
        "sw_backtranslation_en": bt[k]["sw_bt"],
        "sw_backtranslation_match": status,
        "kik_phrase": v["kik_phrase"],
        "kik_backtranslation_en": bt[k].get("kik_bt") if v["kik"] else None,
        "kik_backtranslation_match": KIK_CMP.get(k) if v["kik"] else None,
        "kik_partial": bool(v["kik"]),
        "audio_asr_check": {
            "sw_cer": asr[f"sw/{k}"]["cer"], "sw_wer": asr[f"sw/{k}"]["wer"],
            "kik_phrase_cer": asr[f"kik/{k}"]["cer"] if v["kik"] else None,
        },
        "audio": {
            "sw": f"audio/sw/{k}.wav" if os.path.exists(os.path.join(ROOT, "audio", "sw", f"{k}.wav")) else None,
            "kik": f"audio/kik/{k}.wav" if v["kik"] and os.path.exists(os.path.join(ROOT, "audio", "kik", f"{k}.wav")) else None,
        },
        "notes": notes,
    }
with open(os.path.join(ROOT, "answers.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(len(out), "entries;", sum(o["sw_backtranslation_match"] == "check" for o in out.values()), "flagged check")
