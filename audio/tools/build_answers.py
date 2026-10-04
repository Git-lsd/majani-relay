# Usage (from kahawa-check/audio/tools): ../../../.venv/bin/python build_answers.py ../..
"""Assemble kahawa-check/answers.json from content.py + bt.json (NLLB back-translations) + the team's meaning comparison.
Audio paths point to the AAC files the app plays (audio/<lang>/<id>.m4a); see tts.py for the WAV -> m4a step."""
import json, os, re, sys
sys.path.insert(0, ".")
import content

ROOT = sys.argv[1]
bt = json.load(open("bt.json"))

# The team's comparison of the NLLB back-translation with the English source.
# "ok"    = the back-translation keeps the meaning (word-sense slips we checked are listed).
# "check" = the back-translation changes a word that matters; a native speaker must confirm the Swahili.
CMP = {
 "result_healthy": ("ok", "re-check of the revised line (Oct 3): meaning kept ('pests digging in the leaves'); 'kutu' still came back as 'corrosion', the same Swahili word as metal rust."),
 "result_rust": ("ok", "Meaning kept; 'kutu' rendered as 'rash' in sentence two (word-sense slip)."),
 "result_miner": ("ok", "re-check of the revised line (Oct 3): meaning kept ('insects that dig into the leaves', 'a large dry brownish patch on the leaf')."),
 "result_cercospora": ("ok", "Meaning kept. The Swahili disease name is descriptive ('brown spot disease')."),
 "result_phoma": ("ok", "Meaning kept."),
 "result_not_sure": ("ok", "'afisa wa ugani' came back as 'fiction agent' here only; the same phrase back-translates as 'extension officer' in other strings."),
 "retake_photo": ("ok", "'upande wa chini' came back as 'bottom' (= underside)."),
 "action_healthy": ("ok", "'Pogoa' came back as 'cut' (= prune)."),
 "action_rust": ("ok", "Meaning kept; 'kutu' rendered as 'corrosion'."),
 "action_miner": ("check", "'Nyigu' (wasp) came back as 'ants'. Dictionaries give 'wasp' (docs/SWAHILI_CHECK.md section 6); the speaker review in pilot week 1 checks it."),
 "action_cercospora": ("check", "re-check of the revised line (Oct 3): the soil test and the fertiliser advice now come back as two separate points. Two key words still come back wrong: 'afisa wa ugani' as 'land surveyor' and 'matandazo' (mulch) as 'nets'. Published Kenyan and Tanzanian sources use both words (docs/SWAHILI_CHECK.md section 6), so we kept them; a speaker should confirm."),
 "action_phoma": ("check", "re-check of the revised line (Oct 3): 'Ugonjwa wa Phoma' now comes back as a disease ('Phoma's disease'). Two key words still come back wrong: 'miti ya kuzuia upepo' (windbreak trees) as 'windmills' and 'afisa wa ugani' as 'medical examiner'. Sources confirm both terms (docs/SWAHILI_CHECK.md section 6); a speaker should confirm."),
 "action_not_sure": ("ok", "re-check of the revised line (Oct 3): meaning kept ('Make a mark on this tree', 'Do not spray', 'Wait for the officer's advice first'); 'matokeo' (results) came back as 'effects'."),
 "plot_all_healthy": ("ok", "re-check of the revised line (Oct 3): meaning kept; the line now says the leaves look healthy, not the photos."),
 "plot_some_problem": ("ok", "re-check of the revised line (Oct 3): meaning kept ('there may be a problem'); 'afisa wa ugani' came back as 'expansion officer'."),
 "plot_officer_alert": ("ok", "Meaning kept; 'kadhaa' (several) came back as 'some', 'mapema' (soon) as 'in advance'."),
 "check_q1_old_trees": ("ok", "re-check of the revised line (Oct 3): 'kukata mashina' came back as 'cutting the stems', no longer 'cutting down trees'; 'afisa wa ugani' came back as 'expansion officer'."),
 "check_q2_no_fertiliser": ("check", "'mbolea ya samadi' (manure) was lost; came back as 'coffee fertilizer or store fertilizer'."),
 "check_q3_weeding": ("ok", "Meaning kept."),
 "check_q4_berry_spots": ("ok", "'yaliyozama ndani' (sunken) came back as 'deep'."),
 "check_q5_berry_holes": ("check", "'mdudu anayetoboa matunda' (berry-boring insect) came back as 'fruit picking insect'; 'afisa wa ugani' -> 'rumor officer'."),
 "check_q6_dry_flowering": ("check", "'kiangazi' (dry season) came back as 'summer'; 'matandazo' (mulch) as 'grids'."),
 "disclaimer_final_call": ("ok", "re-check of the revised line (Oct 3): meaning kept ('It gives only a preliminary answer')."),
 "consent_photos": ("ok", "re-check of the revised line (Oct 3): meaning kept; 'namba yako ya uanachama' came back as 'membership number' and 'chama cha ushirika' as 'association'. Consent text should still be reviewed by a speaker before any real use."),
}
KIK_CMP = {"result_healthy": "ok", "result_not_sure": "ok", "retake_photo": "ok"}
# Lines whose Swahili was rewritten on Oct 3 after the machine cross-check (docs/SWAHILI_CHECK.md).
REVISED = {"result_healthy", "result_miner", "action_cercospora", "action_phoma", "action_not_sure", "plot_all_healthy",
           "plot_some_problem", "check_q1_old_trees", "disclaimer_final_call", "consent_photos"}
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
            notes += " Machine transcription did not recognise the 0.5 s Kikuyu clip (heard 'ĩe'); a recorded human clip would be clearer."
    if cited:
        notes += " Sources: " + " | ".join(f"{s} = {content.SOURCES[s]}" for s in cited)
    if k in REVISED:
        notes += " Revised Oct 3 after the machine cross-check; see docs/SWAHILI_CHECK.md."
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
            "sw": f"audio/sw/{k}.m4a" if os.path.exists(os.path.join(ROOT, "audio", "sw", f"{k}.m4a")) else None,
            "kik": f"audio/kik/{k}.m4a" if v["kik"] and os.path.exists(os.path.join(ROOT, "audio", "kik", f"{k}.m4a")) else None,
        },
        "notes": notes,
    }
with open(os.path.join(ROOT, "answers.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(len(out), "entries;", sum(o["sw_backtranslation_match"] == "check" for o in out.values()), "flagged check")
