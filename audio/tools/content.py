# Source content for kahawa-check/answers.json (docs agent).
# Sources referenced in notes by short key:
SOURCES = {
    "KCS": "Kenya Coffee Sustainability Manual (review led by KALRO Coffee Research Institute with AFA Coffee Directorate and partners), "
           "https://www.globalcoffeeplatform.org/wp-content/uploads/2021/03/KCS-MANUAL-review-03112020.pdf",
    "INFONET": "Infonet-Biovision (Kenya), Coffee (Revised), https://infonet-biovision.org/crops-fruits-vegetables/coffee-revised",
    "CLR_REVIEW": "Coffee Leaf Rust (Hemileia vastatrix) in Kenya - A Review, Agronomy 2021, 11(12):2590, https://www.mdpi.com/2073-4395/11/12/2590",
    "PLANTWISE_BES": "CABI PlantwisePlus Knowledge Bank, Cercospora coffeicola (brown eye spot), https://plantwiseplusknowledgebank.org/doi/full/10.1079/pwkb.20207800275",
    "LUCID_BES": "Pacific Pests, Pathogens and Weeds fact sheet: Coffee brown-eye spot, https://apps.lucidcentral.org/ppp/text/web_full/entities/coffee_browneye_spot_142.htm",
    "PHOMA": "Phoma (Ascochyta) tarda leaf spot: Cultivar Magazine, https://revistacultivar.com/articles/phoma-spot-or-ascochyta-spot-of-coffee ; "
             "Wikipedia, https://en.wikipedia.org/wiki/Ascochyta_tarda",
}

FINAL_EN = "The extension officer makes the final call."
FINAL_SW = "Afisa wa ugani ndiye atakayefanya uamuzi wa mwisho."

C = {}

def add(i, en, sw, kik=None, notes=""):
    C[i] = dict(en=en, sw=sw, kik=kik, notes=notes)

# ---------- single-photo results ----------
add("result_healthy",
    "These leaves look healthy. No sign of rust, leaf miner or leaf spot was seen. This check covers leaves only, not berries.",
    "Majani haya yanaonekana kuwa na afya. Hakuna dalili ya kutu, wadudu wanaochimba ndani ya majani, wala madoa ya ugonjwa. Ukaguzi huu ni wa majani tu, si wa matunda.",
    kik="Mathangũ maya ma kahũa nĩ mega.",
    notes="Not a disease result, so no final-call line; states the leaf-only limit instead. "
          "kik is a short phrase meaning 'These coffee leaves are good' (not 'healthy'); the rest falls back to Swahili.")

add("result_rust",
    "This looks like coffee leaf rust. Rust shows as yellow-orange powder under the leaf. " + FINAL_EN,
    "Hii inaonekana kama ugonjwa wa kutu ya majani ya kahawa. Kutu huonekana kama unga wa manjano au rangi ya chungwa chini ya jani. " + FINAL_SW,
    notes="Symptoms per KCS 8.4.2 (pale yellow spots on the underside turning to yellow/orange powdery masses). 'kutu' = rust.")

add("result_miner",
    "This looks like leaf miner damage. It shows as dry brown patches on the leaf. " + FINAL_EN,
    "Hii inaonekana kama uharibifu wa wadudu wanaochimba ndani ya majani. Huonekana kama sehemu kubwa kavu za rangi ya kahawia kwenye jani. " + FINAL_SW,
    notes="Symptoms per KCS 9.5.8 and INFONET (irregular brown blotches on the upper side of leaves). "
          "Simplification: the protocol photographs the underside; mines are clearest from above.")

add("result_cercospora",
    "This looks like brown eye spot. It shows as round brown spots with a pale centre. " + FINAL_EN,
    "Hii inaonekana kama ugonjwa wa madoa ya kahawia. Huonekana kama madoa ya mviringo ya kahawia, yenye rangi nyeupe katikati. " + FINAL_SW,
    notes="Brown eye spot = Cercospora coffeicola (PLANTWISE_BES, LUCID_BES). KCS lists it as a minor disease in Kenya. "
          "Swahili name is descriptive ('brown spot disease'), not a confirmed standard term.")

add("result_phoma",
    "This looks like Phoma leaf spot. It shows as dark patches, often on young leaves after cold weather. " + FINAL_EN,
    "Hii inaonekana kama ugonjwa wa Phoma. Huonekana kama madoa meusi, mara nyingi kwenye majani machanga baada ya baridi. " + FINAL_SW,
    notes="Phoma (Ascochyta) tarda; favoured by cold wind at high altitude (PHOMA sources are mostly Brazilian). "
          "KCS lists 'leaf blight and stem die back' as minor in Kenya. 'Phoma' is spelled as in English; TTS may not pronounce it well.")

add("result_not_sure",
    "Not sure. The tool cannot tell from this photo. The photo is saved for the officer to look at.",
    "Sina uhakika. Siwezi kutambua kutoka kwenye picha hii. Picha imehifadhiwa ili afisa wa ugani aiangalie.",
    kik="Ndiĩ.",
    notes="kik phrase means 'I do not know'; the rest of the Swahili text follows it. The abstain lane (fail-safe required by the brief). Shown when confidence is low or the photo looks unlike the training data.")

add("retake_photo",
    "Please take the photo again. Show the underside of one leaf, in daylight. Hold the phone still.",
    "Tafadhali piga picha tena. Onyesha upande wa chini wa jani moja, kwenye mwanga wa mchana. Shika simu bila kutikisa.",
    kik="Oya mbica ĩngĩ.",
    notes="Protocol from SPEC (underside of 3 leaves on 5 trees). kik phrase means 'Take another photo'; the rest falls back to Swahili.")

# ---------- next steps ----------
add("action_healthy",
    "Keep up good care. Prune on time, weed, and feed the trees as advised. Check again at the next visit.",
    "Endelea kutunza vizuri. Pogoa kwa wakati, ondoa magugu, na weka mbolea kama ulivyoshauriwa. Kagua tena katika ziara ijayo.",
    notes="General good practice per KCS modules 4, 6, 7. 'Feed as advised' avoids giving fertiliser types or rates.")

add("action_rust",
    "Mark this tree. Prune so air and light reach the leaves. Ask the extension officer about approved rust control before the rains.",
    "Weka alama kwenye mti huu. Pogoa matawi ili hewa na mwanga vifikie majani. Muulize afisa wa ugani kuhusu njia zilizoidhinishwa za kudhibiti kutu kabla ya mvua.",
    notes="KCS 8.4.2: cultural control by proper and timely pruning; control must start before the rains and follow the CRI programme with "
          "PCPB-registered products. CLR_REVIEW: pruning and shading are key cultural practices. No product, ingredient or dose is named on purpose.")

add("action_miner",
    "Mark this tree. Small wasps kill many leaf miners, so do not spray without advice. Ask the extension officer what to do.",
    "Weka alama kwenye mti huu. Nyigu wadogo huua wadudu wengi wa aina hii, kwa hiyo usinyunyize dawa bila ushauri. Muulize afisa wa ugani hatua za kuchukua.",
    notes="INFONET: parasitic wasps and predatory mites give natural control of leaf miners. KCS 9.5.8: control products are "
          "specific registered types, so the choice is left to the officer. Simplification: 'kill' covers parasitism.")

add("action_cercospora",
    "Brown eye spot is common on weak, underfed trees. Ask the officer about a soil test and feeding. Mulch to keep soil moist.",
    "Ugonjwa wa madoa ya kahawia hutokea sana kwenye miti dhaifu isiyo na mbolea ya kutosha. Muulize afisa wa ugani kuhusu kupima udongo, na kuhusu mbolea inayofaa. Weka matandazo ili udongo ubaki na unyevu.",
    notes="PLANTWISE_BES: nitrogen and potassium shortage and plant stress raise susceptibility; do a soil analysis. "
          "KCS 4.6: soil samples go to CRI; KCS 3.7.1: mulch conserves moisture.")

add("action_phoma",
    "Phoma is worse in cold, windy weather on high ground. Windbreak and shade trees can help. Ask the extension officer about approved control.",
    "Ugonjwa wa Phoma huzidi wakati wa baridi na upepo mkali katika maeneo ya juu. Miti ya kuzuia upepo na miti ya kivuli inaweza kusaidia. Muulize afisa wa ugani kuhusu njia zilizoidhinishwa za kudhibiti ugonjwa huu.",
    notes="PHOMA sources: cold wind and altitude above about 900 m favour the disease. Windbreak advice is general (KCS recommends windbreaks "
          "for bacterial blight on exposed sides). Weakest-sourced item for Kenya; a CRI agronomist should confirm.")

add("action_not_sure",
    "Put a mark on this tree. The officer will review the saved photo. Do not spray because of this result. Wait for the officer's advice first.",
    "Weka alama kwenye mti huu. Afisa wa ugani ataangalia picha iliyohifadhiwa. Usinyunyize dawa kwa sababu ya matokeo haya. Subiri ushauri wa afisa kwanza.",
    notes="Abstain lane: no action is taken on an uncertain result; the photo waits in the officer queue. "
          "The Swahili says 'put a mark' (not 'ribbon'), as the other two action lines do, and adds "
          "'Wait for the officer's advice first'. The English was updated on Oct 3 to match (mark the tree; wait for the officer's advice).")

# ---------- plot card ----------
add("plot_all_healthy",
    "All photos from this plot look healthy. Keep checking at each visit. Leaf photos cannot show berry problems.",
    "Majani katika picha zote za shamba hili yanaonekana kuwa na afya. Endelea kukagua katika kila ziara. Picha za majani haziwezi kuonyesha matatizo ya matunda.",
    notes="Reminds that coffee berry disease and berry borer are not visible on leaves (see checklist). A Kikuyu phrase ('Mĩtĩ yothe nĩ mĩega', all the trees are good) was dropped: it claims more than the photos show.")

add("plot_some_problem",
    "Some photos show a possible problem. Please show this card to the extension officer.",
    "Baadhi ya picha zinaonyesha kwamba huenda kuna tatizo. Tafadhali mwonyeshe afisa wa ugani kadi hii.",
    notes="Plot card when 1-2 photos on one tree show a disease answer (app rule). The user decides when to share; the app sends nothing by itself.")

add("plot_officer_alert",
    "There may be a problem on several trees in this plot. Please show this card to the extension officer soon. The officer decides what to do.",
    "Huenda kuna tatizo kwenye miti kadhaa katika shamba hili. Tafadhali mwonyeshe afisa wa ugani kadi hii mapema. Afisa ndiye ataamua hatua za kuchukua.",
    notes="Plot card when a disease answer appears on 2 or more trees or in 3 or more photos (app rule in app.js plotVerdict). "
          "It is a prompt to the user, not an automatic message to the officer. The disease may be any of the four, so rust is not named.")

# ---------- non-AI checklist (YES = possible cause) ----------
add("check_q1_old_trees",
    "Are most trees old, with few new branches? If yes, ask the officer about stumping to renew them.",
    "Je, miti mingi imezeeka, na ina matawi mapya machache? Kama ndiyo, muulize afisa wa ugani kuhusu kukata mashina ili miti ichipue upya.",
    notes="Non-AI checklist. KCS 3.8-3.9 and 6.6: rehabilitation by clean stumping or change of cycle renews aging, underproductive trees.")

add("check_q2_no_fertiliser",
    "Has the coffee gone without manure or fertiliser this year? If yes, ask the co-op about a soil test first.",
    "Je, kahawa imekosa mbolea ya samadi au mbolea ya dukani mwaka huu? Kama ndiyo, uliza chama cha ushirika kuhusu kupima udongo kwanza.",
    notes="Non-AI checklist. KCS 4.6: soil analysis every 2-3 years, samples sent to CRI; KCS warns against fertiliser use without soil analysis. "
          "Worded so that YES means a possible cause, like the other questions.")

add("check_q3_weeding",
    "Are there many weeds under the coffee? If yes, weed before feeding the trees. Weeds take water and food.",
    "Je, kuna magugu mengi chini ya kahawa? Kama ndiyo, ondoa magugu kabla ya kuweka mbolea. Magugu huchukua maji na chakula cha mimea.",
    notes="Non-AI checklist. KCS 7.4: weed before fertiliser is applied, so weeds do not take it up.")

add("check_q4_berry_spots",
    "Do green berries have dark, sunken spots? This may be coffee berry disease. Show the extension officer soon.",
    "Je, matunda mabichi yana madoa meusi yaliyozama ndani? Huenda ni ugonjwa wa matunda ya kahawa. Mwonyeshe afisa wa ugani mapema.",
    notes="Non-AI checklist; referral only. KCS 8.4.1: CBD shows as small dark sunken lesions on green berries and can cause total crop loss. "
          "The leaf model cannot see this.")

add("check_q5_berry_holes",
    "Do berries have a small round hole near the tip? This may be berry borer. Collect fallen berries and tell the officer.",
    "Je, matunda yana tundu dogo la mviringo karibu na ncha? Huenda ni mdudu anayetoboa matunda. Okota matunda yaliyoanguka na umwambie afisa wa ugani.",
    notes="Non-AI checklist. KCS 9.5.2 and INFONET: one or two small round holes near the tip of berries; collect infested fallen berries "
          "(field hygiene). The leaf model cannot see this.")

add("check_q6_dry_flowering",
    "Was there a long dry spell during flowering? That can mean fewer berries. Mulch helps keep the soil moist.",
    "Je, kulikuwa na kiangazi kirefu wakati wa kuchanua maua? Hilo linaweza kusababisha matunda machache. Matandazo husaidia udongo kubaki na unyevu.",
    notes="Non-AI checklist. KCS 5.5: critical water periods include flower buds formed with no rain and early fruit (pinhead) stage; "
          "KCS 3.7.1: mulch conserves moisture. Simplification: weather is asked, not measured.")

# ---------- safety and consent ----------
add("disclaimer_final_call",
    "This tool can be wrong. It gives a first look only. " + FINAL_EN,
    "Programu hii inaweza kukosea. Inatoa jibu la awali tu. " + FINAL_SW,
    notes="Shown on every result screen and plot card.")

add("consent_photos",
    "May I photograph some coffee leaves on your farm? The photos stay on this phone. "
    "We keep your co-op number in coded form, not your name. The officer may look at the photos. "
    "You can say no, or ask us to delete them later.",
    "Je, naweza kupiga picha za majani ya kahawa shambani mwako? Picha zitabaki kwenye simu hii. "
    "Hatuhifadhi jina lako. Tunahifadhi namba yako ya uanachama katika chama cha ushirika tu, na tunaiweka kuwa siri. "
    "Afisa wa ugani anaweza kuziangalia picha hizi. "
    "Unaweza kukataa, au kutuomba tuzifute baadaye.",
    notes="Read aloud by the relay farmer before the first photo. 'Coded form' = SHA-256 hash of the member number "
          "(pseudonymous, not anonymous). The Swahili says 'We do not keep your name. We keep only your membership number "
          "in the cooperative, and we keep it confidential' ('tunaiweka kuwa siri'); it has no separate word for 'coded'.")


# Kikuyu tier: a short phrase replaces the FIRST Swahili sentence; the remaining Swahili sentences follow it,
# so nothing is dropped when the app shows the kik field without any extra logic.
import re as _re
def _split(t):
    return [x for x in _re.split(r"(?<=[.?!])\s+", t.strip()) if x]
for _k, _v in C.items():
    if _v["kik"]:
        _v["kik_phrase"] = _v["kik"]
        _v["kik_rest_sw"] = " ".join(_split(_v["sw"])[1:])
        _v["kik"] = (_v["kik_phrase"] + " " + _v["kik_rest_sw"]).strip()
    else:
        _v["kik_phrase"] = None
        _v["kik_rest_sw"] = None
