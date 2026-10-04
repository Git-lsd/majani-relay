# Result guides ("What does this mean?")

Date: 3 October 2026. Version `g1`. Data file: [`guides.json`](../guides.json).

The Swahili was drafted with an AI model and checked by machine back-translation (section "Swahili check by machine"). A Swahili-speaking extension officer reviews all 24 guide sections in pilot week 1, starting with the 4 flagged sections. Until then every guide has `sw_verified: false`, and the app shows the tag "Speaker review: pilot week 1".

## What the guides are

Each result screen can have a "What does this mean?" button. It opens a short guide for that result. The guide is fixed text: nothing is generated on the phone. There are six guides:

| Guide id | Used for | Title (English / Swahili) |
|---|---|---|
| `healthy` | Healthy | Healthy leaves / *Majani yenye afya* |
| `rust` | Leaf rust | Coffee leaf rust / *Kutu ya majani ya kahawa* |
| `miner` | Leaf miner | Leaf miner / *Wadudu wanaochimba ndani ya majani* |
| `cercospora` | Brown eye spot | Brown eye spot (Cercospora) / *Ugonjwa wa madoa ya kahawia* |
| `phoma` | Phoma leaf spot | Phoma leaf spot / *Ugonjwa wa Phoma* |
| `not_sure` | Not sure, and Different problem (one guide for both) | Not sure, or a different problem / *Sina uhakika, au tatizo jingine* |

Each guide has four parts, always in this order:

1. **What it looks like** (`looks_like`)
2. **Common causes** (`causes`)
3. **What to do now** (`do_now`)
4. **When to call the officer** (`call_officer`)

Part 2 is headed "What keeps trees healthy" in the healthy guide and "Common reasons" in the not-sure guide. Each part is one to three short sentences (45 words or fewer), written to be read aloud, in English and Swahili.

## Rules

- Fixed text only. Nothing is generated on the phone.
- No pesticide product, active ingredient or dose is named anywhere. "What to do now" lists only care and hygiene steps (marking the tree, pruning, removing extra suckers, weeding, feeding as advised, mulching, clearing cut branches, cleaning the pruning tool, windbreak and shade trees). For control it says "ask the officer about approved control".
- "When to call the officer" gives concrete reasons: many trees affected, leaves falling, berries affected, shoot tips dying, or the farmer is not sure.
- Kenyan extension material comes first. Where it is thin (brown eye spot, Phoma), the guide uses other sources, and its notes say so.
- The wording matches the fixed answer list (`answers.json`), for example *afisa wa ugani* (extension officer), *kutu ya majani ya kahawa* (coffee leaf rust), *Weka alama kwenye mti huu* (mark this tree).
- As for the answer list, the app shows the Swahili with the tag "Speaker review: pilot week 1" and offers the "Wording wrong?" button on each guide section.

## Sources

"Read" means we opened the source on 3 Oct 2026. "Snippet" means we saw it only in a search-engine summary.

| Id | Source | Year | Country | Check |
|---|---|---|---|---|
| `KCS` | [Kenya Coffee Sustainability Manual (review led by KALRO Coffee Research Institute with AFA Coffee Directorate and partners); sections 3.3, 3.7.1, 4.3, 4.6, 6.2, 6.4, 7.4, 8.1-8.4, 8.5.2, 9.4, 9.5.2, 9.5.8](https://www.globalcoffeeplatform.org/wp-content/uploads/2021/03/KCS-MANUAL-review-03112020.pdf) | 2020 (date in the file name; posted March 2021) | Kenya | Read (full text of the PDF) |
| `INFONET` | [Infonet-Biovision, Coffee (Revised): leaf rust, leafmining caterpillars, bacterial blight of coffee](https://infonet-biovision.org/crops-fruits-vegetables/coffee-revised) | 2019 (page says updated 8 July 2019) | Kenya | Read (page opened 3 Oct 2026) |
| `LUCID_BES` | [Pacific Pests, Pathogens and Weeds fact sheet: Coffee brown-eye spot (142)](https://apps.lucidcentral.org/ppp/text/web_full/entities/coffee_browneye_spot_142.htm) | 2019 | Pacific Islands (not Kenya) | Read (page opened 3 Oct 2026) |
| `PLANTWISE_BES` | [CABI PlantwisePlus Knowledge Bank: Cercospora coffeicola; brown eye spot, berry blotch (seen only in a search summary; the page is behind a bot check)](https://plantwiseplusknowledgebank.org/doi/full/10.1079/pwkb.20207800275) | not confirmed | not confirmed | Snippet (page behind a bot check; not opened) |
| `CULTIVAR_PHOMA` | [Pereira and Reis, Phoma spot or Ascochyta spot of coffee, Cultivar magazine](https://revistacultivar.com/articles/phoma-spot-or-ascochyta-spot-of-coffee) | 2024 | Brazil | Read (page opened 3 Oct 2026) |
| `WIKI_ASCOCHYTA` | [Wikipedia: Ascochyta tarda (Phoma tarda), coffee leaf spot and dieback; names Kenya among affected countries](https://en.wikipedia.org/wiki/Ascochyta_tarda) | undated page (read 3 Oct 2026) | global (names Ethiopia, Kenya, Cameroon) | Read (page opened 3 Oct 2026) |
| `WCR_VARIETIES` | [World Coffee Research, Arabica Coffee Varieties catalogue: Batian ('Intermediate resistance' to leaf rust) and Ruiru 11 ('Highly resistant'); also https://varieties.worldcoffeeresearch.org/varieties/ruiru-11](https://varieties.worldcoffeeresearch.org/varieties/batian) | undated pages (read 3 Oct 2026) | global (pages on Kenyan varieties) | Read (both pages opened 3 Oct 2026) |
| `APP` | [Majani Relay photo protocol and fixed answers (answers.json: retake_photo, action_not_sure)](../answers.json) | 2026 | Kenya (this project) | Our own app text |

How well each guide is sourced for Kenya:

- **Healthy, leaf rust, leaf miner, not sure:** Kenyan sources (Kenya Coffee Sustainability Manual, Infonet-Biovision). The rust variety line also uses the World Coffee Research variety catalogue.
- **Brown eye spot:** the Kenyan manual lists it only as a minor disease. Symptoms and causes come from a Pacific fact sheet.
- **Phoma:** the least Kenya-specific. Symptoms and weather come from Brazilian and general sources. The hygiene and windbreak steps come from Kenyan advice for bacterial blight of coffee, a major disease that looks similar, so the steps fit both. A KALRO coffee agronomist should confirm this guide.

## Simplifications

- **Rust, "about one leaf in five".** This is the Kenyan manual's definition of a severe rust infection (20% of leaves). The manual uses it in its spray programme. Here it is only a reason to call the officer.
- **Rust varieties.** The manual says Batian and Ruiru 11 resist rust and SL28 and SL34 get it easily. World Coffee Research rates Ruiru 11 "highly resistant" and Batian "intermediate", and warns that resistance can change. So the guide says Batian and Ruiru 11 "resist it better, but can still get it". We did not check field data on resistance in Kenya today.
- **Rust and shade.** The rust guide does not advise more shade: at the same crop load, shade can raise rust (Avelino et al. 2004, *Plant Pathology*; seen only in a search summary). A later review (Avelino et al. 2015, *Food Security*, Colombia and Central America; read) says shade has many effects on rust, some opposing, and the balance is hard to establish.
- **Leaf miner.** "Small wasps that feed on them" covers wasps that lay eggs inside the caterpillars.
- **Healthy.** "Green and even in colour" is a plain description, not a sourced definition.
- **Not sure.** The look-alikes it names (bacterial blight, insects, sun scorch, shortage of plant food) are examples, not a full list.

## Swahili check by machine

Every Swahili text was translated back into English with Meta's NLLB-200 (distilled, 600M), the same model and settings as the answer list: one sentence at a time, beam 4. We compared each read-back with our English by hand. A section is `ok` when the meaning and the key words come back, and `check` when a key word comes back wrong.

- **First round:** 10 of 24 sections were `ok`. We revised the Swahili once in the other 14.
- **After one revision:** **20 `ok`, 4 `check`.** Each section in `guides.json` has the read-back (`sw_backtranslation_en`) and the mark (`sw_backtranslation_match`).
- **After the quality check:** three sections were changed again (see the next section) and read back again. The count stays 20 `ok`, 4 `check`.

The four sections still marked `check`:

| Section | Swahili word | Should mean | Model read |
|---|---|---|---|
| `miner.looks_like` | *kiwavi* | caterpillar | "squirrel" |
| `miner.do_now` | *nyigu* | wasp | "ants" (same error as `action_miner` in the answer list) |
| `miner.call_officer` | *nondo* | moth | "ants" |
| `cercospora.do_now` | *matandazo* | mulch | "netting" (same error as `action_cercospora`) |

We think these are model errors. Dictionaries give caterpillar for *kiwavi* and moth for *nondo* (bab.la; seen in search summaries). The same model read *viwavi* as "larvae" and *nondo* as "moths" in the leaf-miner causes. *Nyigu* and *matandazo* are discussed in [SWAHILI_CHECK.md](SWAHILI_CHECK.md) (section 6). A speaker should still confirm all four.

Other words the model read loosely, but with the meaning kept: *kutu* (rust) as "rash" or "corrosion", *afisa wa ugani* (extension officer) as "expansion officer", *machipukizi ya ziada* (extra suckers) as "extra buds", *unga* (powder) as "flour", *takriban* (about) as "at least". The titles and headings were also read back. Only the rust title came back wrong (*Kutu ya majani ya kahawa* as "Coarseness of coffee leaves"), though the same words came back as "coffee leaf rust" inside a sentence.

Limits: the check is machine-only. It cannot catch a wrong word that maps back to the right English word, and it does not test tone or whether a farmer in Kirinyaga, Nyeri or Murang'a finds the line natural. **A speaker review is still the final check: a Swahili-speaking extension officer reviews every section in pilot week 1.**

## Quality check (3 October 2026)

A second review pass checked the file for safety and fit with the answer list. It changed three sections. Each change was read back again by machine, with the same settings.

| Section | Change | Why | Mark |
|---|---|---|---|
| `rust.causes` | "Batian and Ruiru 11 resist it" became "resist it better, but can still get it" | World Coffee Research rates Batian only "intermediate" for leaf rust. A farmer with Batian should not dismiss a rust result. | `ok` |
| `cercospora.do_now` | Added "and approved control" to the question for the officer. To stay within 45 Swahili words, *mbolea inayofaa* became *mbolea*, and *vizuri* (well) was dropped from the pruning sentence. | The rust and Phoma guides already send control questions to the officer; brown eye spot did not. | `check` (*matandazo* still reads back as "netting") |
| `healthy.causes` | Sentence 3 now reuses the answer-list line *Picha za majani haziwezi kuonyesha matatizo ya matunda* ("Leaf photos cannot show berry problems") | The old *Hauwezi kuona matatizo ya matunda* read back as "You can't see the problems of fruit", because *hauwezi* can also mean "you cannot". | `ok` |

It also corrected one note: the Phoma windbreak advice comes from Infonet-Biovision and the Brazilian article, not from the Kenyan manual. No product, active ingredient or dose was found in any text, read-back or note.

## All guide text

For a reviewer. The data file is the source; this table is generated from it.

### Healthy leaves (`healthy`)

| Part | English | Swahili | Machine read-back | Mark |
|---|---|---|---|---|
| What it looks like | Healthy coffee leaves are green and even in colour. The underside is clean: no yellow-orange powder, no spots, and no dry brown patches. | Majani ya kahawa yenye afya ni ya kijani, na rangi yake ni sawa kote. Upande wa chini ni safi: hakuna unga wa manjano au wa rangi ya chungwa, hakuna madoa, na hakuna sehemu kavu za kahawia. | Healthy coffee leaves are green, and the color is the same everywhere. The bottom is clean: no yellow or tan flour, no stains, and no dry brown patches. | `ok` |
| What keeps trees healthy | Trees stay healthy with good care: pruning on time, weeding, and feeding as advised. This check sees leaves only. Leaf photos cannot show berry problems. | Miti hubaki na afya ikitunzwa vizuri: kupogoa kwa wakati, kuondoa magugu, na kuweka mbolea kama ulivyoshauriwa. Ukaguzi huu unaangalia majani ya kahawa tu. Picha za majani haziwezi kuonyesha matatizo ya matunda. | Trees remain healthy if properly cared for: timely pruning, weeding, and keeping fertilizer as instructed. This review looks only at coffee leaves. Pictures of the leaves cannot reveal the problems of the fruit. | `ok` |
| What to do now | Keep up good care. Prune and remove extra suckers on time, and weed before you feed the trees. Check the leaves again at the next visit. | Endelea kutunza vizuri. Pogoa na uondoe machipukizi ya ziada kwa wakati, na uondoe magugu kabla ya kuweka mbolea. Kagua majani tena katika ziara ijayo. | Keep taking good care of them. Cut and remove the extra buds in time, and remove the weeds before fertilizing. Review the leaves again on the next visit. | `ok` |
| When to call the officer | Call the officer if berries have dark sunken spots or a small hole, if many leaves turn yellow or fall, or if branches dry from the tip. | Mjulishe afisa wa ugani ikiwa matunda yana madoa meusi yaliyozama ndani au tundu dogo, ikiwa majani mengi yanageuka manjano au kuanguka, au ikiwa matawi yanakauka kuanzia ncha. | Notify the extension officer if the fruit has deep black spots or a small hole, if many of the leaves turn yellow or fall, or if the branches dry from the tip. | `ok` |

### Coffee leaf rust (`rust`)

| Part | English | Swahili | Machine read-back | Mark |
|---|---|---|---|---|
| What it looks like | Rust starts as small pale yellow spots on the underside of the leaf. The spots turn into yellow-orange powder. Badly hit leaves fall early. | Kutu huanza kama madoa madogo ya manjano hafifu upande wa chini wa jani. Baadaye unga wa manjano au wa rangi ya chungwa hutokea kwenye madoa hayo. Majani yaliyoathirika sana huanguka mapema. | The rash begins as tiny yellow spots on the underside of the leaf. Later on, yellow or tan flour appears on the stains. The severely damaged leaves fall early. | `ok` |
| Common causes | Coffee leaf rust is a disease spread by wind and rain. It spreads fast in warm, wet weather. The varieties SL28 and SL34 get it easily; Batian and Ruiru 11 resist it better, but can still get it. | Kutu ya majani ya kahawa ni ugonjwa unaoenezwa na upepo na mvua. Huenea haraka wakati wa joto na mvua. Aina za kahawa SL28 na SL34 hushambuliwa kwa urahisi; Batian na Ruiru 11 zinastahimili ugonjwa huu zaidi, lakini bado zinaweza kushambuliwa. | Coffee leaf rust is a disease spread by wind and rain. It spreads rapidly in the heat and rain. The SL28 and SL34 varieties are easily attacked; Batian and Ruiru 11 are more resistant to the disease, but they can still be attacked. | `ok` |
| What to do now | Mark the tree. Prune so air and light get into the tree, and remove extra suckers. Ask the officer about approved rust control before the next rains. | Weka alama kwenye mti huu. Pogoa matawi ili hewa na mwanga viingie ndani ya mti, na uondoe machipukizi ya ziada. Muulize afisa wa ugani kuhusu njia zilizoidhinishwa za kudhibiti kutu kabla ya mvua zijazo. | Make a mark on this tree. Cut off the branches so that the air and light enter the tree, and remove the extra buds. Ask an expansion officer about approved methods for controlling corrosion before the coming rains. | `ok` |
| When to call the officer | Call the officer soon if rust is on several trees, if many leaves are falling, or if about one leaf in five has rust. Also call if you are not sure. | Mjulishe afisa wa ugani bila kuchelewa ikiwa kutu iko kwenye miti kadhaa, ikiwa majani mengi yanaanguka, au ikiwa takriban jani moja kati ya kila majani matano lina kutu. Mjulishe pia ikiwa huna uhakika. | Notify the extension officer immediately if there is corrosion on several trees, if many leaves are falling, or if at least one out of every five leaves is corrosive. Also, let him know if you are unsure. | `ok` |

### Leaf miner (`miner`)

| Part | English | Swahili | Machine read-back | Mark |
|---|---|---|---|---|
| What it looks like | Leaf miner shows as dry brown patches on the top side of the leaf. A small white caterpillar may be inside a patch. Badly hit leaves fall early. | Uharibifu wa wadudu hawa huonekana kama sehemu kavu za kahawia upande wa juu wa jani. Ndani ya sehemu hiyo kunaweza kuwa na kiwavi mdogo mweupe. Majani yaliyoathirika sana huanguka mapema. | The destruction of these insects appears as dry brown patches on the upper part of the leaf. Inside may be a small white squirrel. The severely damaged leaves fall early. | `check` |
| Common causes | Tiny white moths lay eggs on the leaf. The young caterpillars eat the leaf from inside. They increase fast after sprays that kill the small wasps that feed on them. | Nondo wadogo weupe hutaga mayai kwenye jani. Viwavi wao hula jani kutoka ndani. Wadudu hawa huongezeka sana baada ya kunyunyizia dawa zinazoua nyigu wadogo wanaowala. | Small white moths lay eggs on the leaf. Their larvae feed on leaves from the inside. These insects multiply exponentially after being sprayed with pesticides that kill small insects that eat them. | `ok` |
| What to do now | Mark the tree, and do not spray without advice, so the helpful wasps survive. Keep the trees pruned, weeded and fed. Ask the officer what to do. | Weka alama kwenye mti huu, na usinyunyize dawa bila ushauri, ili nyigu, wadudu wenye manufaa, waendelee kuishi. Endelea kupogoa, kuondoa magugu na kuweka mbolea. Muulize afisa wa ugani hatua za kuchukua. | Make a mark on this tree, and do not spray the medicine without advice, so that the ants, the beneficial insects, can survive. Keep cutting, removing weeds, and keeping fertilizer. Ask the extension officer what steps to take. | `check` |
| When to call the officer | Call the officer if these insects are on many trees, or if leaves are falling. The officer can shake a tree and count the flying white moths to decide if control is needed. | Mjulishe afisa wa ugani ikiwa wadudu hawa wako kwenye miti mingi, au ikiwa majani yanaanguka. Afisa anaweza kuutikisa mti na kuhesabu nondo weupe wanaoruka, ili kuamua kama udhibiti unahitajika. | Notify the extension officer if these insects are on many trees, or if leaves are falling. An officer can shake a tree and count flying white ants, to determine if control is needed. | `check` |

### Brown eye spot (Cercospora) (`cercospora`)

| Part | English | Swahili | Machine read-back | Mark |
|---|---|---|---|---|
| What it looks like | Brown eye spot shows as round brown spots with a pale grey or white centre and often a yellow ring. These spots can also show on the berries. | Ugonjwa wa madoa ya kahawia huonekana kama madoa ya mviringo ya kahawia, yenye rangi ya kijivu au nyeupe katikati, na mara nyingi yenye duara la manjano. Madoa haya yanaweza pia kuonekana kwenye matunda. | Brown spots appear as round brown spots, with a gray or white center, and often a yellow circle. These stains can also be seen on fruits. | `ok` |
| Common causes | It is a disease spread by wind and rain splash. It is worst on weak trees: trees that are underfed, short of water, or in strong sun without enough shade. | Ni ugonjwa unaoenezwa na upepo na matone ya mvua. Huzidi kwenye miti dhaifu: miti isiyo na mbolea ya kutosha, inayokosa maji, au iliyo kwenye jua kali bila kivuli cha kutosha. | It is a disease spread by wind and raindrops. It grows on weak trees: trees that do not have enough fertilizer, lack water, or are exposed to the hot sun without sufficient shade. | `ok` |
| What to do now | Mark the tree, and ask the officer about a soil test, feeding and approved control. Cover the soil with mulch to keep it moist, but keep the mulch off the stem. Prune for air flow, and clear away the cut branches. | Weka alama kwenye mti huu, na umuulize afisa wa ugani kuhusu kupima udongo, mbolea, na njia zilizoidhinishwa za kudhibiti. Funika udongo kwa matandazo ili ubaki na unyevu, lakini matandazo yasiguse shina la mti. Pogoa matawi ili hewa ipite ndani ya mti, na uondoe matawi yaliyokatwa. | Make a mark on this tree, and ask the expansion officer about soil measurements, fertilizers, and approved control methods. Cover the soil with netting to keep it moist, but keep the netting from touching the trunk of the tree. Cut the branches to allow air to pass through the tree, and remove the cut branches. | `check` |
| When to call the officer | Call the officer if the spots are on many trees, if leaves are falling, or if berries have spots too. Spots on berries need the officer to check them. | Mjulishe afisa wa ugani ikiwa madoa yako kwenye miti mingi, ikiwa majani yanaanguka, au ikiwa matunda nayo yana madoa. Madoa kwenye matunda yanahitaji kukaguliwa na afisa. | Notify the extension officer if there are spots on many trees, if leaves fall off, or if the fruit also has spots. The stains on the fruit need to be examined by an official. | `ok` |

### Phoma leaf spot (`phoma`)

| Part | English | Swahili | Machine read-back | Mark |
|---|---|---|---|---|
| What it looks like | Phoma shows as black or dark brown spots on young leaves near the shoot tips. The leaves may curl and crack. Young shoots can dry from the tip. | Ugonjwa wa Phoma huonekana kama madoa meusi au ya kahawia kwenye majani machanga karibu na ncha za matawi. Majani yanaweza kujikunja na kupasuka. Matawi machanga yanaweza kukauka kuanzia ncha. | Phoma's disease appears as black or brown spots on young leaves near the tip of the branches. The leaves can twist and crack. Young branches can wither from the tip. | `ok` |
| Common causes | It is a disease of cold, wet, windy weather on high ground. Wind, hail and cold damage young leaves, and the disease gets in through the wounds. | Ni ugonjwa wa hali ya baridi, unyevunyevu na upepo mkali katika maeneo ya juu. Upepo, mvua ya mawe na baridi huumiza majani machanga, na ugonjwa huingia kupitia majeraha hayo. | It is a disease of cold, humidity, and high-altitude winds. Wind, hail, and cold damage young leaves, and disease enters through these wounds. | `ok` |
| What to do now | Mark the tree. Cut off dead shoot tips, and clean the pruning tool before the next tree. Planting windbreak and shade trees on the windy side can help; ask the officer about approved control. | Weka alama kwenye mti huu. Kata ncha za matawi zilizokauka, na usafishe kifaa cha kupogoa kabla ya kuhamia mti mwingine. Kupanda miti ya kukinga upepo na miti ya kivuli upande wa upepo kunaweza kusaidia; muulize afisa wa ugani kuhusu njia zilizoidhinishwa za kudhibiti ugonjwa huu. | Make a mark on this tree. Cut the dried ends of the branches, and clean the cutting tool before moving to another tree. Planting windshields and shade trees on the windward side may help; ask an extension officer about approved methods of controlling the disease. | `ok` |
| When to call the officer | Call the officer soon. Bacterial blight of coffee looks similar and is a major disease in Kenya. Call at once if shoot tips die on many trees, or if flowers or young berries turn black. | Mjulishe afisa wa ugani bila kuchelewa. Ugonjwa wa bakteria wa kahawa unafanana na huu, na ni ugonjwa mkubwa nchini Kenya. Mjulishe mara moja ikiwa ncha za matawi zinakauka kwenye miti mingi, au ikiwa maua au matunda machanga yanageuka meusi. | Notify the extension officer without delay. The bacterial disease of coffee is similar to this, and it is a major disease in Kenya. Immediately let him know if the tips of the branches wither on many trees, or if the young flowers or fruits turn black. | `ok` |

### Not sure, or a different problem (`not_sure`)

| Part | English | Swahili | Machine read-back | Mark |
|---|---|---|---|---|
| What it looks like | The tool could not match this photo to one of its answers. The photo may be unclear, or the leaf may have a problem the tool does not know. | Programu haikuweza kulinganisha picha hii na mojawapo ya majibu yake. Huenda picha haiko wazi, au jani lina tatizo ambalo programu hailijui. | The program could not compare this picture to one of its responses. The image may not be clear, or the leaf may have a problem that the program was unaware of. | `ok` |
| Common reasons | Often the photo is blurred, too dark, or shows the top of the leaf. Other problems also look different: bacterial blight, insects, sun scorch, or a shortage of plant food. | Mara nyingi picha haiko wazi, ina giza sana, au inaonyesha upande wa juu wa jani. Matatizo mengine pia huonekana tofauti: ugonjwa wa bakteria, wadudu, kuungua kwa jua, au upungufu wa chakula cha mimea. | Often the image is not clear, too dark, or shows the top of the leaf. Other problems also appear differently: bacterial infections, insects, sunburn, or malnutrition. | `ok` |
| What to do now | Take the photo again: the underside of one leaf, in daylight, phone held still. Mark the tree. Do not spray because of this result; the officer will look at the saved photo. | Piga picha tena: upande wa chini wa jani moja, kwenye mwanga wa mchana, ukishika simu bila kutikisa. Weka alama kwenye mti huu. Usinyunyize dawa kwa sababu ya matokeo haya; afisa wa ugani ataangalia picha iliyohifadhiwa. | Picture again: at the bottom of one leaf, in broad daylight, holding the phone without shaking. Make a mark on this tree. Do not spray the drug because of these results; the extension officer will look at the saved image. | `ok` |
| When to call the officer | Call the officer if many trees look sick, if leaves fall fast, or if branches dry from the tip. Also call if berries have dark sunken spots: it may be coffee berry disease. | Mjulishe afisa wa ugani ikiwa miti mingi inaonekana kuwa na ugonjwa, ikiwa majani yanaanguka kwa haraka, au ikiwa matawi yanakauka kuanzia ncha. Mjulishe pia ikiwa matunda yana madoa meusi yaliyozama ndani: huenda ni ugonjwa wa matunda ya kahawa. | Inform the extension officer if many trees appear to be infected, if the leaves fall quickly, or if the branches dry from the tip. Also let him know if the fruit has deep black spots: it may be a disease of the coffee fruit. | `ok` |

## Changing a guide

1. Edit the text in `guides.json`. Keep `en` and `sw` saying the same thing, and keep within three sentences and 45 words.
2. Do not add a product name, ingredient or dose.
3. Keep `sw_verified: false` until a Kenyan Swahili speaker approves the line. A cooperative field officer or extension officer would be best.
4. Re-run the back-translation for the changed lines and update `sw_backtranslation_en` and `sw_backtranslation_match`.
