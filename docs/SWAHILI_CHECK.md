# Swahili check: machine cross-checks before the speaker review

Date: 3 October 2026. A Swahili-speaking extension officer reviews all 24 answers in pilot week 1; until then every line stays tagged "Speaker review: pilot week 1" in the app (`sw_verified: false`). This file records what we checked by machine and which lines we changed.

## Applied on Oct 3

**All 10 revisions are in the app (text and audio). A Swahili-speaking extension officer reviews them with the other 14 lines in pilot week 1.**

- **Text.** The 10 revised Swahili lines (section 4) are in `audio/tools/content.py`, the source, and in `answers.json`. The English lines did not change. `sw_verified` stays `false` for all 24 lines.
- **Audio.** New Swahili clips for the 10 lines. New Kikuyu clip for `result_healthy`, because its Kikuyu clip ends with the rest of the Swahili answer, which changed. Same voices and settings as before (Meta MMS-TTS, then AAC at 32 kbit/s). The sentences that did not change sound exactly as before. The old clips are kept outside the repo.
- **Translation read-back of the shipped lines (NLLB-600M).** 8 of the 10 are now marked `ok` in `answers.json`. 2 stay marked `check`:
  - `action_cercospora`: the officer came back as "land surveyor" and mulch as "nets".
  - `action_phoma`: windbreak trees came back as "windmills" and the officer as "medical examiner".

  We believe these are model errors on words that published sources use (sections 5 and 6). We kept the `check` mark anyway, because the 14 unchanged lines were scored the same way: `check_q6_dry_flowering` is marked `check` for the same mulch error. All 24 lines together: 18 `ok`, 6 `check`. Before the revision it was 14 and 10.
- **Speech-recognition round trip, re-run on the 10 new clips (MMS-1b-all).** Over all 24 Swahili clips, the character error is 3.1% (it was 3.5%) and the word error is 18.2% (it was 17.9%). What the recognizer heard:
  - *Weka alama* (put a mark) as *wakaalama*.
  - *Ugonjwa wa Phoma* as *ugonjwa wa poma*.
  - *usinyunyize* (do not spray) as *usinyinyize*. The *si* that means "do not" is there.
  - *namba yako ya uanachama* (your membership number) as *namba yako ya wanachama* ("the members' number").
- **English updated to match.** In `action_not_sure`, the English now says "Put a mark on this tree" and "Wait for the officer's advice first", the same as the Swahili.
- **Review sheet.** `docs/SWAHILI_REVIEW_SHEET.md` and `.csv` now show the lines that ship, and the list of words we are least sure of uses the new words.

Sections 1 to 9 below record the check itself. Their numbers describe the lines before the revisions, unless a section says otherwise.

## Summary

- We checked 24 answers. **14 KEEP, 10 REVISE.**
- REVISE: `result_healthy`, `result_miner`, `action_cercospora`, `action_phoma`, `action_not_sure`, `plot_all_healthy`, `plot_some_problem`, `check_q1_old_trees`, `disclaimer_final_call`, `consent_photos`.
- The three that matter most:
  - `consent_photos`: one model read the member-number phrase as "social security number", and *kwa njia ya siri* can sound like "secretly".
  - `check_q1_old_trees`: both models read *kukata miti chini* as "cutting down trees".
  - `action_not_sure`: it used a different word for marking a tree. "Do not spray" now has a second sentence after it: "wait for the officer's advice first".
- After the rewrite, both translation models give back the intended meaning for all 10 revised answers. The errors that remain are model mistakes on words that published sources confirm (section 5).
- Safety rules still hold in every line, old and new. No line names a pesticide or a dose. Every disease result ends with "The extension officer makes the final call". Both "do not spray" lines still say "do not spray".

## 1. Who reviews the Swahili

No one on the team speaks Swahili. A Swahili-speaking extension officer reviews all 24 lines in pilot week 1 (about 30 minutes), using the one-page sheet `docs/SWAHILI_REVIEW_SHEET.md` (and `.csv`). Until a speaker signs off, the app shows every Swahili line as unverified.

## 2. The checks we ran

| # | Check | What it does | Result |
|---|---|---|---|
| 1 | NLLB-200 600M back-translation | Meta's translation model turns each Swahili sentence back into English. We compared it with our English by hand. Stored in `answers.json` (`sw_backtranslation_en`, `sw_backtranslation_match`). | 14 `ok`, 10 `check` |
| 2 | NLLB-200 1.3B back-translation | A larger model from the same family, with the same settings: Swahili to English, one sentence at a time, beam 4, at most 80 new tokens. | Most meanings came back. Some key words came back wrong, for example "social security number", "The glacier overflows" and "cutting down trees" (section 4). |
| 3 | Blind back-translation by a separate AI agent | The agent saw only the 24 Swahili lines, never our English. For each line it wrote a literal English reading, a naturalness score (1 to 5), the problems it found, and notes on Kenyan usage. | 7 lines scored 3; one scored 5; the rest scored 4. No line read as dangerous advice. |
| 4 | Terminology against published Swahili farming sources | We looked up 23 key terms in Kenyan and Tanzanian Swahili sources (government, extension, farmer TV, dictionaries). Links are in section 6. | 0 wrong, 1 doubtful (*namba yako ya chama cha ushirika*), the rest confirmed or plausible |
| 5 | Speech-recognition round trip | Meta's MMS-1b-all speech recognizer transcribed each Swahili audio clip, and we compared the transcript with the text. Stored in `answers.json` (`audio_asr_check`). | Character error 3.5%, word error 17.9% overall |

What the speech check adds here:
- *kahawia* (brown) was heard as *kahawia*, not *kahawa* (coffee), all 4 times it occurs (3 clips).
- The negative *si* in *usinyunyize* (do not spray) was heard in both clips (*usinyunize*, *kusininize*).
- *Weka utepe* was heard as *wakaotepa*.
- The sentence-initial *Phoma* was heard as *voma*.

## 3. How we decided

- **KEEP**: the meaning came back in the independent checks, and the key words appear in published sources. If a model got a correct, published word wrong, that alone does not make a line REVISE. Examples: NLLB turned *nyigu* (wasp) into "ants" and "small flies", and *kutu* (leaf rust) into "corrosion", because *kutu* is also the word for metal rust.
- **REVISE**: a key word is rare or appears in no source, or the blind reader took a different meaning, or the blind reader scored naturalness below 4.

How we rewrote. Simplifications, stated:
- We changed only the flagged words and kept the rest as it was, so each change can be checked on its own.
- Every new word is a common word or appears in a cited source.
- Each sentence is 20 words or fewer (the longest has 15). The limit is per sentence, not per answer, because the consent answer has six points and cannot fit in 20 words without dropping one. The revised consent answer is 45 words, up from 42.
- We kept *afisa wa ugani* (extension officer) in every revised line, so the app keeps one term in all 17 answers that use it. Kenyan government Swahili uses it. Whether to switch all 17 to *afisa wa kilimo* is a question for a speaker (section 7).
- For marking a tree, we use *Weka alama* (put a mark) in all three action lines. It was already in 2 of the 3, and both models read it correctly. *Utepe* (ribbon) came back as "stick" from one model and was misheard by the speech check.

## 4. Results, line by line

"Model error" means a translation model got wrong a word that sources confirm. "Optional" items are small polish for a speaker to consider. They are not needed.

| id | verdict | reason | current -> proposed |
|---|---|---|---|
| `result_healthy` | REVISE | *wadudu wachimba majani* (leaf miner) is a coined compound that appears in no source. The blind reader called it a coined term. NLLB-1.3B read it as "insect bites". We changed it to the plain phrase used in `result_miner`. | **Now:** Majani haya yanaonekana kuwa na afya. Hakuna dalili ya kutu, wadudu wachimba majani wala madoa ya ugonjwa. Ukaguzi huu ni wa majani tu, si wa matunda.<br>**Proposed:** Majani haya yanaonekana kuwa na afya. Hakuna dalili ya kutu, wadudu wanaochimba ndani ya majani, wala madoa ya ugonjwa. Ukaguzi huu ni wa majani tu, si wa matunda. |
| `result_rust` | KEEP | The meaning came back in all three readings. *kutu ya majani ya kahawa* matches Tanzanian coffee sources word for word. "Corrosion" is a model error. Optional: *unga wa rangi ya manjano au ya chungwa upande wa chini wa jani*. | no change |
| `result_miner` | REVISE | Naturalness 3. It uses the same coined compound. *madoa ... ya kahawia* (brown spots) repeats the name of brown eye spot, so the two results sound alike. Our first rewrite used *mabaka* (patches). Both models misread it ("calyx", "hairs") and no source uses it, so the second round uses *sehemu kubwa kavu* (large dry areas). | **Now:** Hii inaonekana kama uharibifu wa wadudu wachimba majani. Huonekana kama madoa makubwa ya kahawia yaliyokauka kwenye jani. Afisa wa ugani ndiye atakayefanya uamuzi wa mwisho.<br>**Proposed:** Hii inaonekana kama uharibifu wa wadudu wanaochimba ndani ya majani. Huonekana kama sehemu kubwa kavu za rangi ya kahawia kwenye jani. Afisa wa ugani ndiye atakayefanya uamuzi wa mwisho. |
| `result_cercospora` | KEEP | A Tanzanian extension deck uses *madoa ya kahawia* as the name of brown eye spot. Both models and the blind reader got the meaning. The overlap with leaf miner is fixed in `result_miner`. The speech check heard *kahawia* correctly. Optional: add "(Cercospora)". | no change |
| `result_phoma` | KEEP | All readings were correct. We found no Swahili name for Phoma, and Swahili coffee sources keep the Latin names of other fungi. Optional: *baada ya kipindi cha baridi* (after a cold spell). | no change |
| `result_not_sure` | KEEP | All readings were correct. "Expansion officer" is a model error. Optional: *Siwezi kutambua tatizo kwenye picha hii* (adds "the problem"). | no change |
| `retake_photo` | KEEP | The blind reader got "show the underside of one leaf". Both models said "point to the underside", which is close. Optional: *Geuza jani moja* (turn one leaf over); *bila kuitikisa*. | no change |
| `action_healthy` | KEEP | All readings were correct. Kenyan sources confirm *pogoa* (prune). Optional: *Endelea kutunza kahawa yako vizuri* (adds "your coffee"). | no change |
| `action_rust` | KEEP | The meaning came back in all readings. *zilizoidhinishwa* (approved) is formal, but a Kenyan farmer TV site uses it (*Tumia mbegu zilizoidhinishwa*). "Corrosion" is a model error. Optional: *Pogoa baadhi ya matawi* (prune some branches), so it is not heard as "prune all branches". | no change |
| `action_miner` | KEEP | The meaning came back in all readings. "Ants" and "small flies" for *nyigu* are model errors: dictionaries give "wasp", and a published Swahili leaf-miner page uses *nyigu* in the same sense. "Do not spray" rests on one syllable (*si*), but the speech check heard it, and the next sentence sends the farmer to the officer. Optional: add *Subiri ushauri wa afisa kwanza.* | no change |
| `action_cercospora` | REVISE | All three readers took *kupima udongo na mbolea* as "testing soil and fertiliser". The intent is a soil test plus advice on fertiliser, so we split it. The sentence now starts with *Ugonjwa wa* (the disease), so the name is clear. *matandazo* (mulch) is kept: both Kenyan and Tanzanian sources use it. "Nets", or dropping the word, is a model error. | **Now:** Madoa ya kahawia hutokea sana kwenye miti dhaifu isiyo na mbolea ya kutosha. Muulize afisa wa ugani kuhusu kupima udongo na mbolea. Weka matandazo ili udongo ubaki na unyevu.<br>**Proposed:** Ugonjwa wa madoa ya kahawia hutokea sana kwenye miti dhaifu isiyo na mbolea ya kutosha. Muulize afisa wa ugani kuhusu kupima udongo, na kuhusu mbolea inayofaa. Weka matandazo ili udongo ubaki na unyevu. |
| `action_phoma` | REVISE | A bare foreign word at the start of a sentence is hard to catch. NLLB-1.3B read "The glacier overflows", and the speech check heard *voma*. We added *Ugonjwa wa* (Phoma disease), as `result_phoma` already does. The rest is unchanged. | **Now:** Phoma huzidi wakati wa baridi na upepo mkali katika maeneo ya juu. Miti ya kuzuia upepo na miti ya kivuli inaweza kusaidia. Muulize afisa wa ugani kuhusu njia zilizoidhinishwa za kudhibiti ugonjwa huu.<br>**Proposed:** Ugonjwa wa Phoma huzidi wakati wa baridi na upepo mkali katika maeneo ya juu. Miti ya kuzuia upepo na miti ya kivuli inaweza kusaidia. Muulize afisa wa ugani kuhusu njia zilizoidhinishwa za kudhibiti ugonjwa huu. |
| `action_not_sure` | REVISE | Naturalness 3. *Weka utepe* (put a ribbon) differs from *Weka alama* (put a mark) in the other two action lines. *jibu hili* (this answer) is odd for a result; *matokeo haya* (these results) is the usual phrase. We added *Subiri ushauri wa afisa kwanza* (wait for the officer's advice first), so "do not spray" does not rest on one syllable. | **Now:** Weka utepe kwenye mti huu. Afisa wa ugani ataangalia picha iliyohifadhiwa. Usinyunyize dawa kwa sababu ya jibu hili.<br>**Proposed:** Weka alama kwenye mti huu. Afisa wa ugani ataangalia picha iliyohifadhiwa. Usinyunyize dawa kwa sababu ya matokeo haya. Subiri ushauri wa afisa kwanza. |
| `plot_all_healthy` | REVISE | Naturalness 3. It said the photos are healthy, not the leaves in them. It also lacked *katika* before *kila ziara*. | **Now:** Picha zote za shamba hili zinaonekana kuwa na afya. Endelea kukagua kila ziara. Picha za majani haziwezi kuonyesha matatizo ya matunda.<br>**Proposed:** Majani katika picha zote za shamba hili yanaonekana kuwa na afya. Endelea kukagua katika kila ziara. Picha za majani haziwezi kuonyesha matatizo ya matunda. |
| `plot_some_problem` | REVISE | Naturalness 3. *tatizo linalowezekana* copies "possible problem" word for word, and *linalowezekana* usually means "feasible". The new line uses *huenda kuna tatizo*, which `plot_officer_alert` already uses. | **Now:** Baadhi ya picha zinaonyesha tatizo linalowezekana. Tafadhali mwonyeshe afisa wa ugani kadi hii.<br>**Proposed:** Baadhi ya picha zinaonyesha kwamba huenda kuna tatizo. Tafadhali mwonyeshe afisa wa ugani kadi hii. |
| `plot_officer_alert` | KEEP | The meaning came back. "Office clerk" and "expansion officer" are model errors. Optional: *Afisa ndiye atakayeamua*, the form the other lines use. | no change |
| `check_q1_old_trees` | REVISE | Naturalness 3, and a safety issue: both models read *kukata miti chini* as "cutting down trees". It now says *kukata mashina* (cutting the stems), the wording a Kenya-translated coffee video uses for stumping. *mizee* is used for people; *imezeeka* (has aged) is normal for trees (TaCRI: *mibuni iliyozeeka*). | **Now:** Je, miti mingi ni mizee, yenye matawi mapya machache? Kama ndiyo, muulize afisa wa ugani kuhusu kukata miti chini ili ichipue machipukizi mapya.<br>**Proposed:** Je, miti mingi imezeeka, na ina matawi mapya machache? Kama ndiyo, muulize afisa wa ugani kuhusu kukata mashina ili miti ichipue upya. |
| `check_q2_no_fertiliser` | KEEP | The blind reader got the meaning. The question is negative ("has the coffee gone without...?"), which can confuse yes and no. But the English is negative too, and the app's Yes button is tied to that wording, so do not flip it in Swahili alone. Tanzanian print uses *mbolea ya dukani* as an everyday phrase; optional: *mbolea ya viwandani*. | no change |
| `check_q3_weeding` | KEEP | Naturalness 5. A Kenyan farmer TV site has a very similar sentence (*Magugu/kwekwe huchukua maji na virutubisho...*). | no change |
| `check_q4_berry_spots` | KEEP | The meaning came back. Optional: add "(CBD)", the name Kenyan coffee farmers use, and *matunda hayo* (those berries) after *Mwonyeshe afisa*. | no change |
| `check_q5_berry_holes` | KEEP | The meaning came back. "Rumor officer" and "gardener" are model errors. Tanzanian berry-borer material uses the same verb (*-toboa*). | no change |
| `check_q6_dry_flowering` | KEEP | The blind reader was correct. Sources confirm *kiangazi* and *kuchanua maua*. "Summer", and "layers" or "grids" for mulch, are model errors. | no change |
| `disclaimer_final_call` | REVISE | Naturalness 3. *mtazamo wa kwanza* copies "first look" and sounds like "first opinion". It now says *jibu la awali* (a first answer). | **Now:** Programu hii inaweza kukosea. Inatoa mtazamo wa kwanza tu. Afisa wa ugani ndiye atakayefanya uamuzi wa mwisho.<br>**Proposed:** Programu hii inaweza kukosea. Inatoa jibu la awali tu. Afisa wa ugani ndiye atakayefanya uamuzi wa mwisho. |
| `consent_photos` | REVISE | Naturalness 3, and the highest priority. (1) *namba yako ya chama cha ushirika* can mean the society's own number. NLLB-1.3B read "social security number" and 600M read "company number". It now says *namba yako ya uanachama* (your membership number), the term cooperative registers use. (2) *kwa njia ya siri* can sound like "secretly". It now says *tunaiweka kuwa siri* (we keep it confidential), the form a Kenyan survey consent text uses. (3) "Not your name" is now its own sentence and comes first: *Hatuhifadhi jina lako*. | **Now:** Je, naweza kupiga picha za majani ya kahawa shambani mwako? Picha zitabaki kwenye simu hii. Tunahifadhi namba yako ya chama cha ushirika kwa njia ya siri, si jina lako. Afisa wa ugani anaweza kuziangalia picha hizi. Unaweza kukataa, au kutuomba tuzifute baadaye.<br>**Proposed:** Je, naweza kupiga picha za majani ya kahawa shambani mwako? Picha zitabaki kwenye simu hii. Hatuhifadhi jina lako. Tunahifadhi namba yako ya uanachama katika chama cha ushirika tu, na tunaiweka kuwa siri. Afisa wa ugani anaweza kuziangalia picha hizi. Unaweza kukataa, au kutuomba tuzifute baadaye. |

**Counts: 14 KEEP, 10 REVISE.** Of the 10, 7 were triggered by naturalness below 4. The other 3 were triggered by a rare word (`result_healthy`), a meaning all three readers took differently (`action_cercospora`), and a key word that was lost (`action_phoma`).

## 5. Re-check of the 10 revised answers

We ran both models again on the proposed lines, with the same settings. One line needed a second round: in `result_miner`, *mabaka* was replaced by *sehemu kubwa kavu*. All other first-round versions passed.

| id | NLLB-600M reads | NLLB-1.3B reads | Meaning kept? |
|---|---|---|---|
| `result_healthy` | ...no signs of corrosion, pests digging in the leaves, or patches of disease... | ...no signs of rust, insect bites, or disease spots... | Yes in 600M. 1.3B still says "insect bites" inside this list, but reads the same phrase correctly in `result_miner`. |
| `result_miner` | ...insects that dig into the leaves. ...a large dry brownish patch on the leaf. | ...insects that burrow into the leaves. ...large, dry brown spots on a leaf. | Yes |
| `action_cercospora` | ...about soil measurement, and about suitable fertilizer. Place nets... | ...how the soil is measured and what fertilizers are suitable. Keep the soil moist. | Yes. The fertiliser ambiguity is gone. Mulch is still misread (model error). |
| `action_phoma` | Phoma's disease is more common in the cold and high winds... | Phoma is more common in cold and windy climates in the highlands... | Yes. The "glacier" reading is gone. |
| `action_not_sure` | Make a mark on this tree... Do not spray medication because of these effects. Wait for the officer's advice first. | Same, with "this effect" | Yes |
| `plot_all_healthy` | The leaves in all the pictures of this garden seem healthy... | The leaves in all the pictures of this field look healthy... | Yes |
| `plot_some_problem` | Some pictures suggest that there may be a problem... | Same | Yes |
| `check_q1_old_trees` | ...about cutting the stems so that the trees can bloom again. | ...about pruning the stumps so that the trees can sprout again. | Yes. "Cutting down trees" is gone. |
| `disclaimer_final_call` | ...It gives only a preliminary answer... | Same | Yes |
| `consent_photos` | ...We will not preserve your name. We only keep your membership number in the association, and we keep it confidential... | ...We do not preserve your name. We only keep your membership number in the cooperative, and we keep it confidential... | Yes. "Social security number" is gone. |

What is still off, and why we accept it. These are model errors on words that sources confirm:
- *afisa wa ugani* came back as "surveyor", "medical examiner", "health care provider", "office clerk" or "expansion officer" in some lines, and correctly elsewhere. Near the word "disease", the models lean to medical words.
- *matandazo* (mulch) came back as "nets" or was dropped.
- *kutu* (rust) came back as "corrosion".
- *matokeo* (results) came back as "effects".

## 6. Terminology sources (selected)

| Term | Verdict | Sources |
|---|---|---|
| *kutu ya majani ya kahawa* (coffee leaf rust) | confirmed | [TaCRI annual report 2007](https://www.tacri.or.tz/fileadmin/03_uploads/03_documents/TaCRI.Reports/tacri-Taarifa_ya_Mwaka_2007.pdf); [Tanzanian Coffee Development Strategy, Swahili](https://www.cafeafrica.org/wp-content/uploads/2012/08/tanzanian_coffee_development_strategy_swahili.pdf) |
| *afisa wa ugani* (extension officer) | confirmed | [MyGov, 21 Apr 2026](https://gaa.go.ke/sites/default/files/2026-04/MyGov%20Aprili%2021,%202026.pdf); [MyGov, 23 Sep 2025](https://gaa.go.ke/sites/default/files/2026-01/MyGov%20Septemba%2023,%202025.pdf) (Kenyan government); *afisa wa kilimo* also appears in MyGov |
| *chama cha ushirika* (cooperative) | confirmed | [MyGov, 2 Jun 2026](https://gaa.go.ke/sites/default/files/2026-06/MyGov%20Juni%202,%202026.pdf); [Taifa Leo](https://taifaleo.nation.co.ke/makala/wakulima-wahimizwa-kupanda-miti-zaidi-ya-matunda-kukabili-mabadiliko-ya-tabianchi/) |
| *namba ya uanachama* (membership number) | used in the revision | [UDSM SACCOS rules](https://www.udsm.ac.tz/sites/default/files/2025-02/20200928_123027_UNIT_16_CUSTOM_PAGE_UDSM%20SACCOS%20KANUNI%20ZA%20FEDHA%20wafanyakazi.pdf) |
| *-wekwa kuwa siri* (kept confidential); *kukataa* (refuse) | used in the revision | [Kenyan survey consent text, CNEP 2013 (CSES)](https://cses.org/datacenter/module4/survey/KEN_2013_Untrans_Swahili.pdf) |
| *kukata mashina* (stumping) | used in the revision | [Access Agriculture coffee video, Swahili, Kenya translation](https://www.accessagriculture.org/kwl/mazoea-bora-kukata-na-kupogoa-matawi) |
| *ugonjwa wa madoa ya kahawia* (brown eye spot) | confirmed | [Tanzanian extension deck, coffee pests](https://www.slideshare.net/SikalengoHappy/visumbufu-vya-zao-la-kahawa-presentation-2019) |
| *wadudu wachimba majani* (leaf miner) | not found; replaced | Published name *kidomozi* is Tanzanian only: [Plantix, Swahili](https://plantix.net/sw/library/plant-diseases/600367/coffee-leaf-miner/) |
| *zilizoidhinishwa* (approved) | used on a Kenyan farmer site | [Don't Lose the Plot (Kenya): "Tumia mbegu zilizoidhinishwa"](https://dontlosetheplot.tv/sw/agri-info/crops/viazi/uchaguaji-wa-mbegu/) |
| *matandazo* (mulch), *mbolea ya samadi* (manure), *miti ya kuzuia upepo / ya kivuli* | confirmed | [Vi Agroforestry land-management manual, Swahili](https://www.viagroforestry.org/app/uploads/2019/09/viagroforestry-salm-kiswahili_web.pdf); [Naturland coffee manual, Swahili](https://academy.naturland.org/pluginfile.php/2591/mod_resource/content/10/BROCHURE_Conversion_A5_Swahili.pdf) |
| *magugu ... huchukua maji* (weeds take water) | confirmed | [Don't Lose the Plot crops pages (Kenya)](https://dontlosetheplot.tv/sw/agri-info/crops/) |
| *nyunyiza / nyunyizia dawa* (spray) | confirmed | [Don't Lose the Plot, tomato pests](https://dontlosetheplot.tv/sw/agri-info/crops/nyanya/wadudu-na-magonjwa-ya-nyanya/); [kilimo-bora blog](https://kilimo-bora.blogspot.com/2017/09/yafahamu-magonjwa-makuu-yanayoshambulia.html) |
| *nyigu* (wasp) | dictionary | [bab.la](https://en.bab.la/dictionary/swahili-english/nyigu) |
| *kiangazi* (dry season) | confirmed | [Wiktionary](https://en.wiktionary.org/wiki/kiangazi) |

Sources we could not use: the Plantwise Swahili fact sheets sit behind a bot check, which we did not try to get around. The TUKI dictionary site was offline. We found no Swahili coffee material from KALRO's Coffee Research Institute or the Coffee Directorate. Most published coffee pest names are Tanzanian.

## 7. Questions only a speaker can answer

1. **Officer term.** Is *afisa wa ugani* the usual term in Kirinyaga, Nyeri and Murang'a, or is *afisa wa kilimo* better? If it changes, change all 17 answers together.
2. **"Coded" member number.** The app stores the member number as a code (SHA-256). Short numbers can still be guessed from the code (README). The revised line says the number is kept confidential (*kuwa siri*). Is that fair, or is there a plain word for "coded"?
3. **Marking a tree.** We chose *Weka alama* (put a mark) for all three lines. If the cooperative ties a ribbon or a piece of cloth, the team should pick one word and use it in the English and Swahili of all three action lines (the English now says "Put a mark on this tree" / "Mark this tree").
4. **"Phoma" in the audio.** The speech check heard *poma* and *voma*. Does the voice say it clearly?
5. **Pest names.** Are the Tanzanian names *kidomozi* (leaf miner), *ruhuka* (berry borer) and *chulebuni* (berry disease) known in Central Kenya? We did not use them. Would "CBD" help in `check_q4_berry_spots`?
6. **A content point for the team, not a translation point.** The consent line says the photos stay on this phone and that the officer may look at them. Per the README, the officer reviews them on the phone. Adding *kwenye simu hii* to the officer sentence would remove any doubt.

## 8. Limits of these checks

- All five checks are done by machines.
- The two NLLB models come from the same family and the same training data, so they share blind spots. When they agree, that is weak evidence.
- The blind reader is an AI agent, not a person. It never saw our English, so its reading does not depend on what we meant. It may still share gaps with other language models, especially for everyday Kenyan speech.
- Back-translation cannot catch a wrong word that maps back to the right English word. It does not test tone (too formal, too blunt). It also does not test whether an older farmer whose first language is Kikuyu understands the line.
- The voice and the speech recognizer both come from Meta's MMS. A low error rate shows that a machine can hear the audio. It does not show that a farmer finds it clear.
- **The revised lines are new machine-made Swahili.** They fix the problems we found, but they have had fewer checks than the other 14 lines: no blind read by the separate AI agent. Their audio was made, and passed the speech-recognition round trip, on Oct 3.
- **A speaker review is still the final check: a Swahili-speaking extension officer reviews every line in pilot week 1.**

## 9. What a speaker review would add

- Whether a coffee farmer in Central Kenya would understand each line and find it natural and polite, not bookish.
- The right local terms: the officer term, pest names, CBD.
- A listen to the audio: pronunciation, speed, "Phoma", and the *si* in *usinyunyize*.
- A check of the three Kikuyu phrases.
- A sign-off, so that `sw_verified` can be set to `true` for the approved lines.

Any fluent Kenyan Swahili speaker can do most of this; it does not need someone whose mother tongue is Swahili. A cooperative field officer or extension officer would be best. It takes about 20 to 30 minutes with `docs/SWAHILI_REVIEW_SHEET.md`.

## 10. Until the review

Every line is labelled unverified in the app. All 24 lines live in one editable file (`audio/tools/content.py`, built into `answers.json`), so a correction needs no change to the app's code (section 11). A short, fixed list of lines that a person can review is a safety feature.

## 11. How to apply a change (for the team)

Done on Oct 3 for all 10 revisions. For any later change (for example after a speaker review):
1. Put the new text in `audio/tools/content.py`.
2. Rebuild `answers.json` (`build_answers.py`) and the audio (`tts.py`; `ONLY_IDS=id1,id2` remakes only those lines). Convert each WAV to `.m4a` with `afconvert` (command at the top of `tts.py`) and move the WAVs out of the repo.
3. Rerun `backtranslate.py` and `asr_check.py`.
4. Keep `sw_verified: false` until a speaker approves.
5. Update `docs/SWAHILI_REVIEW_SHEET.md` so the reviewer sees the lines that actually ship.

The proposed text is given in full in section 4. Working files from this check (the proposed lines as JSON, model outputs and scripts) were kept in a temporary folder outside the repo.
