# Language plan

Majani Relay (earlier name: Kahawa Check) speaks in three tiers. English is on the screen. Swahili is the main local language, as text and audio. Kikuyu is the "less-supported" tier: a few short phrases, and Swahili for the rest.

No one on the team speaks Swahili or Kikuyu. So every local-language string is marked **unverified** (`sw_verified: false`, `kik_verified: false` in `answers.json`), and the app shows the tag "Not yet checked by a native speaker" next to it.

All facts below were checked on 2026-10-03.

## 1. The three tiers

| Tier | Language | What the user gets | Who it is for |
|---|---|---|---|
| Screen | English | All buttons, menus and result text | The relay farmer and the extension officer |
| Main local language | Swahili (Kenyan standard) | The fixed list of 24 answers, as text and as audio | The relay farmer, reading or playing the answer aloud to Noor |
| Less-supported language | Kikuyu (Gĩkũyũ) | 3 of the 24 answers start with a short Kikuyu phrase; the rest of each of those answers, and the other 21 answers, are in Swahili | Noor, who speaks Kikuyu at home |

Why these languages:
- Central Kenya's arabica belt (Kirinyaga, Nyeri, Murang'a) is mostly Kikuyu-speaking at home. Swahili is the national language most adults also use. This is the same pattern as Noor in the brief: a home language, plus the national one when she needs it.
- Swahili has good open tools (section 3). Kikuyu has few, which makes it a fair test of how the tool degrades.

How the app picks the text (implemented by the web-app agent in `app.js`):
- Swahili selected: Swahili text, then English if a Swahili text is missing.
- Kikuyu selected: the `kik` field, then Swahili, then English.
- Audio follows the same order: `audio/kik/<id>.m4a`, then `audio/sw/<id>.m4a`.

How the Kikuyu field is built. Simplification, stated: we only wrote Kikuyu phrases we are fairly confident about. Each one replaces the **first** Swahili sentence of an answer. The rest of that answer stays in Swahili. Example for `retake_photo`:

> `kik`: "Oya mbica ĩngĩ. Onyesha upande wa chini wa jani moja, kwenye mwanga wa mchana. Shika simu bila kutikisa."
> (Kikuyu "Take another photo", then the Swahili instructions.)

This way the app needs no extra logic, and no safety sentence is lost when Kikuyu is selected. The Kikuyu audio does the same: the Kikuyu voice says the phrase, then the Swahili voice says the rest. The pure Kikuyu phrase is also stored in `kik_phrase`.

The three Kikuyu phrases:

| Answer id | Kikuyu phrase | Meaning we intend | NLLB back-translation |
|---|---|---|---|
| `result_healthy` | Mathangũ maya ma kahũa nĩ mega. | These coffee leaves are good. | "These coffee leaves are good." |
| `result_not_sure` | Ndiĩ. | I do not know. | "I do not know." |
| `retake_photo` | Oya mbica ĩngĩ. | Take another photo. | "Take another picture." |

We dropped one phrase on purpose: "Mĩtĩ yothe nĩ mĩega" (all the trees are good) for the plot card. It claims more than 15 leaf photos can show.

## 2. Why a fixed list of answers, not generated text

The brief's glossary defines a **fixed list of answers** as everything the tool is allowed to say. It adds that a tool which can say anything cannot be checked for safety.

Our reasons:
- **It can be checked.** 24 answers, each one to three short sentences (14 words or fewer per sentence). A native speaker can review all of them in about 30 minutes.
- **No made-up advice.** The tool never writes new sentences, so it cannot invent a pesticide, a dose or a diagnosis. The guardrails are in the text itself: no product names, no doses, and "The extension officer makes the final call" on every disease result.
- **It works offline and is small.** The audio is made once, before shipping. The phone plays compressed audio files (AAC, about 1.5 MB in total). It does not run a 145 MB speech model or a 2.4 GB translation model.
- **It fits a weak language.** Machine translation into Kikuyu scores far below Swahili (section 3). Generating Kikuyu on the phone would produce text no one on the team can check.

The cost: the tool cannot answer free questions. Anything outside the list goes to the extension officer.

## 3. What open tools exist for each language

| Resource | Swahili | Kikuyu |
|---|---|---|
| Mozilla Common Voice (scripted speech) | 417 validated hours of 1,138 recorded; 1,530 speakers | 0 hours. The locale `ki` exists but is not open for recording yet. |
| FLEURS speech benchmark (Google) | Yes (`sw_ke`) | No. FLEURS has three Kenyan configs: `sw_ke`, `luo_ke`, `kam_ke`. |
| Whisper (OpenAI) | Supported. Zero-shot FLEURS word error rate: large-v2 39.3%, small 73.7% (Whisper paper, Table 13). | Not in Whisper's language list. |
| MMS speech recognition (Meta, `mms-1b-all`, 1B parameters) | Yes (`swh` adapter) | Yes (`kik` adapter) |
| MMS text-to-speech (Meta) | Yes, `facebook/mms-tts-swh` (145 MB) | Yes, `facebook/mms-tts-kik` (145 MB) |
| NLLB-200 language code | `swh_Latn` | `kik_Latn` |
| FLORES-200 chrF++, NLLB-600M distilled (English to X / X to English) | 58.0 / 60.7. English to Swahili ranks 15th of 201 directions. | 34.9 / 42.9. English to Kikuyu ranks 146th of 201. |
| FLORES-200 chrF++, NLLB-1.3B distilled | 58.8 / 63.5 | 36.2 / 45.6 |
| Other open data | MASSIVE `sw-KE` (intents), WAXAL Swahili TTS, ALFFA ASR corpus, Masakhane sets (MasakhaNER 2.0, MAFAND-MT), InkubaLM-0.4B | African Next Voices Kikuyu: 754 hours (183 scripted, 571 unscripted), CC BY 4.0, on Hugging Face (`Anv-ke`). It covers five dialects, including Ki-Ndia and Gĩ-Gichugu (Kirinyaga), Ki-Mathira (Nyeri) and Ki-Murang'a. WAXAL also has a Kikuyu TTS subset (`data/TTS/kik`); we did not check its licence. |

For reference, the median FLORES chrF++ for NLLB-600M over all 201 directions is 44.4 (English to X) and 55.2 (X to English). Swahili is well above the median. Kikuyu is well below it.

Licences of the models we used: NLLB-200, MMS TTS and MMS-1b-all are all **CC-BY-NC 4.0** (non-commercial). Only the audio files made with MMS TTS ship in the app. NLLB and MMS-1b-all were used on a laptop for checking only.

What CC-BY-NC means for us: the shipped Swahili and Kikuyu audio comes from a non-commercial model. That is fine for a hackathon and a non-commercial pilot. A paid or commercial service would need the 24 clips re-recorded by a person (section 7) or a TTS model with a commercial licence.

Sources: Common Voice live stats API (`commonvoice.mozilla.org/api/v1/stats/languages`); Hugging Face repos `google/fleurs`, `facebook/mms-1b-all`, `facebook/mms-tts-swh`, `facebook/mms-tts-kik`, `facebook/nllb-200-distilled-600M`, `google/WaxalNLP`, `Anv-ke`; Meta's NLLB `metrics.csv` files (`dl.fbaipublicfiles.com/large_objects/nllb/models/nllb_200_dense_distill_600m/metrics.csv` and `..._1b/metrics.csv`); Whisper paper (arXiv 2212.04356) and tokenizer language list; AfriVoices-KE (arXiv 2604.08448).

## 4. How we checked the text without a speaker

Every check below is done by a machine or by us. None of them replaces a native speaker. That is why every string stays marked unverified.

1. **Source wording.** The advice comes from Kenyan extension material: the Kenya Coffee Sustainability Manual (review led by KALRO Coffee Research Institute), Infonet-Biovision, and the CABI Plantwise fact sheet for brown eye spot. Each answer cites its source in its `notes` field in `answers.json`.
2. **Back-translation.** We translated every Swahili sentence back to English with NLLB-200-distilled-600M (`swh_Latn` to `eng_Latn`, beam 4, one sentence at a time). We then compared it with our English by hand and set `sw_backtranslation_match`:
   - `ok` (14 of 24): the meaning came back. Some word slips are expected and listed in `notes`. For example, *kutu* (leaf rust) often comes back as "corrosion", because it is the same word as metal rust.
   - `check` (10 of 24): a word that matters came back wrong. Examples: *nyigu* (wasp) came back as "ants"; *matandazo* (mulch) as "nets"; *utepe* (ribbon) as "stick"; *chama cha ushirika* (cooperative society) as "company". We believe our Swahili is right in most of these cases, but only a speaker can confirm it.
   - Kikuyu: we back-translated the three Kikuyu phrases (`kik_Latn` to `eng_Latn`). All three came back with the intended meaning. NLLB's Kikuyu-to-English score is low (chrF++ 42.9), so this is weak evidence.
3. **Audio round trip.** We transcribed every generated audio file with MMS-1b-all speech recognition and compared the transcript with the text:
   - Swahili, 24 clips: character error rate 3.5%, word error rate 17.9% overall. Per clip, character error rate ranges from 1.2% to 8.0%. Most errors are single letters inside a word (for example *ugani* heard as *udani*).
   - Kikuyu phrases: "Mathangũ maya ma kahũa nĩ mega" 13% character error rate; "Oya mbica ĩngĩ" 7%; the one-word clip "Ndiĩ" (0.5 seconds) failed (heard as "ĩe").
   - Limit: the recogniser and the voice are both from Meta's MMS project. A low error rate shows a machine can understand the audio. It does not show that a farmer finds it natural.
4. **Benchmarks.** We report the published scores in section 3 instead of claiming quality ourselves.
5. **Labelled unverified.** Every string carries `sw_verified: false` and `kik_verified: false` until a speaker signs off. The app shows this to the user.

6. **Second round (Oct 3 evening).** A second machine translation model (NLLB-1.3B), a blind back-translation by a separate AI agent that never saw our English, and a check of key terms against published Swahili agricultural sources. 10 phrases were rewritten in simpler, better-attested Swahili and their audio regenerated; after the rewrite, 18 of 24 come back "ok" and 6 "check" (mostly model errors on attested words such as *matandazo*, mulch). Details: [SWAHILI_CHECK.md](SWAHILI_CHECK.md). Review sheet for a speaker: [SWAHILI_REVIEW_SHEET.md](SWAHILI_REVIEW_SHEET.md).
7. **Corrections from the field.** Every spoken answer in the app has a "Wording wrong?" button. The relay farmer (who reads the English beside the Swahili) or the officer types a better phrasing. Reports stay on the phone, travel with the officer's update file or a CSV export, and do not change the app's text until someone reviews them.

What these checks can miss. A wrong word that NLLB maps back to the "right" English word passes the back-translation check. The register (too formal, too blunt) is not tested at all. The pronunciation of the technical name "Phoma" was not checked by ear.

## 5. What a 30-minute native-speaker review would check

Ask a Swahili speaker with farm vocabulary, ideally a cooperative staff member or extension officer in Kirinyaga, Nyeri or Murang'a. For Kikuyu, ask someone from the same area.

Give them a sheet with these columns: answer id | English | Swahili | back-translation | flag | correct / fix / unnatural / offensive | suggested wording | reviewer initials and date.

Order of work (most important first):
1. **Safety lines (10 minutes).** `result_not_sure`, `action_not_sure`, `disclaimer_final_call`, `consent_photos`, and the final-call sentence used in the four disease results. Is it clear that the tool can be wrong, that a person decides, and that the farmer can say no?
2. **The 10 answers flagged `check` (10 minutes).** Confirm or replace these words: *wadudu wachimba majani* (leaf miner), *nyigu* (wasp), *matandazo* (mulch), *miti ya kuzuia upepo* (windbreak trees), *utepe* (ribbon), *kukata miti chini ili ichipue machipukizi mapya* (stumping, not felling), *mbolea ya samadi* (manure), *mdudu anayetoboa matunda* (berry borer), *kiangazi* (dry spell), *chama cha ushirika* (cooperative).
3. **Farmer words (5 minutes).** What do farmers actually call leaf rust, brown eye spot, Phoma and coffee berry disease? Is *afisa wa ugani* the usual term, or *afisa wa kilimo*? Is the first-person "Sina uhakika" (I am not sure) acceptable from an app?
4. **Listen (3 minutes).** Play five Swahili clips and the three Kikuyu clips. Is the voice understandable? Is "Phoma" said in a usable way?
5. **Kikuyu (2 minutes).** Are the three phrases correct and polite? Which other answers should get a Kikuyu phrase first? (Our suggestion: the final-call sentence and the consent question.)

After review: update the text in `answers.json`, set `sw_verified` or `kik_verified` to `true` only for the strings the reviewer approved, write the reviewer's initials and date in `notes`, and regenerate the audio (`audio/tools/tts.py`).

Where to find reviewers: the cooperative itself; KALRO Coffee Research Institute (Ruiru); the University of Embu team that published the JMuBEN photos; the Masakhane community.

## 6. How the tool fares in Kikuyu

What still works in Kikuyu: the whole photo check (it does not depend on language), the screen in English, and every answer in Swahili text and audio. Three answers start with a short Kikuyu phrase in a Kikuyu voice.

What is missing, and why:
- **Most answers are not in Kikuyu.** We only wrote phrases we were fairly confident about. Machine translation is too weak to fill the gap: NLLB scores chrF++ 34.9 from English to Kikuyu, against 58.0 for Swahili.
- **No Kikuyu speech input.** The tool has no voice input in any language, so nothing is lost here. If voice yes/no answers were added later, MMS has a Kikuyu recognition adapter, and the African Next Voices Kikuyu set (754 hours, CC BY 4.0, including Kirinyaga dialects) could be used to test or fine-tune it. We have not done this.
- **Short Kikuyu audio is fragile.** The one-word clip "Ndiĩ" was not recognised by the machine round trip. Short words from a TTS model are often clipped.

The fallback is the design, not a failure: when a Kikuyu text is missing, the app shows Swahili with a "Swahili fallback" tag. A Kikuyu speaker can add phrases later by editing `answers.json` and running `audio/tools/tts.py`. No code change is needed.

## 7. A language with no speech model: recorded human clips

Some languages have no TTS model at all. Example: Kiembu and Kimeru, spoken in the Embu and Meru coffee areas on the eastern side of Mt Kenya. We found no `facebook/mms-tts-ebu` or `facebook/mms-tts-mer` checkpoint on Hugging Face, and neither language has an NLLB code.

For such a language the plan is:
1. A speaker translates the 24 answers. Someone else back-translates them aloud to check.
2. The same speaker, or another local voice, records each answer on a phone. That is about 5 minutes of speech.
3. The clips are saved as `audio/<code>/<id>.m4a` (AAC, 32 kbps, mono; converted from 16 kHz WAV with macOS `afconvert`). The text goes in a new field in `answers.json`.
4. The app plays them the same way it plays the Swahili clips. Adding the language to the app's menu and fallback chain is a small change in `app.js`.

Conditions: the speaker gives written consent, is credited, and agrees to a licence for the recordings (for example CC BY 4.0). With their agreement, the recordings can also be given to Mozilla Common Voice, which accepts new languages.

Human clips are better than TTS in two ways: the voice is local, and there is no non-commercial licence limit. The cost is that every text change needs a new recording.

## 8. Audio files

| Folder | Files | Format | Length | Total size |
|---|---|---|---|---|
| `audio/sw/` | 24 (one per answer) | AAC (`.m4a`), 32 kbps, mono, converted from 16 kHz WAV | 7.5 to 24 seconds each | about 1.45 MB |
| `audio/kik/` | 3 | Same | 9 to 13 seconds each (Kikuyu phrase 0.5 to 3.2 seconds, then Swahili) | about 0.14 MB |

How they were made: each sentence was synthesized separately and joined with a 0.3-second pause, because the MMS vocabulary has no punctuation and would otherwise run sentences together. The random seed is fixed, so rerunning gives the same audio. Each file is peak-normalised.

Size note: the WAV files (about 11 MB) were converted to AAC with macOS `afconvert`, which cut the size about sevenfold.

Scripts and logs to rebuild everything are in `audio/tools/`:
- `content.py`: English, Swahili and Kikuyu texts with notes and sources.
- `backtranslate.py`: NLLB back-translation, writes `bt.json`.
- `tts.py`: MMS TTS, writes the WAV files and `tts_log.json`.
- `asr_check.py`: MMS-1b-all round trip, writes `asr_check.json`.
- `build_answers.py`: assembles `answers.json`.
