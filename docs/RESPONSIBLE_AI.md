<!--
Generated from docs/templates/RESPONSIBLE_AI.tmpl.md by ml/fill_docs.py (numbers come from results/numbers.json).
Edit the template, not docs/RESPONSIBLE_AI.md.
-->

# Responsible AI, data and safety

The brief makes this a pass/fail criterion. It asks whether the limits are respected, and whether our account of privacy, consent, bias and human oversight is credible. The health annex also asks three questions that apply to any tool on a shared phone: where the data sits, who can read it, and what happens when the phone is lost or shared. This page answers all of them for Majani Relay (earlier name: Kahawa Check).

Facts about the app below were checked against `app.js` (app cache version `kahawa-v18`) and the shipped head (v3-2026-10-03-lab+field+other) on the night of 3–4 October 2026. If the app changes, this page must be checked again. Every limit below ends with its next step: what, who, how we measure it, and when.

## 1. The fail-safe in one paragraph

The tool reads a leaf photo and gives one of five answers (healthy, leaf rust, leaf miner, brown eye spot, Phoma), or **"not sure — the officer will look"**. It sends the photo to the officer in three cases: its best guess is below a confidence line; the photo looks unlike the photos it learned from; or its top answer is "other problem" (a problem outside the five answers, learned from photos of one pest), shown as "looks like a different problem". A photo sent to the officer goes into a queue and stays out of the rust count until the officer labels it. On field photos it did not train on, it answers 91% and is right on 89% of those answers (cross-validated, Ecuador); on the photos it sends to the officer it would have been right only 63% of the time. On farm photos from Uganda, a country it never trained on, it sends 93% to the officer instead of guessing. The relay farmer can also send any answered photo to the officer by tapping "I think it's something else"; that photo stays out of the village counts until the officer decides. Every disease answer ends with "The extension officer makes the final call." The "What does this mean?" guides are fixed text with their sources listed. The tool never names a pesticide or a dose, and it never sends anything by itself.

## 2. Where the data sits, who can read it, and lost or shared phones

### What is stored

| Item | Stored? | Form |
|---|---|---|
| Farmer's name | No | The app has no name field. |
| Phone number, GPS location | No | The app does not ask for them or read the location. |
| Cooperative member number | Only as a code | SHA-256 hash of the number with a fixed prefix. The number itself is not saved. |
| Village | Yes | Free text typed by the relay farmer. |
| Leaf photos | Small copy only | A 160-pixel thumbnail plus the model's 1,280-number summary of the photo (the embedding). The full photo is not kept. |
| Model answer, tree and leaf position, date | Yes | Per photo. |
| Checklist answers (yes / no / don't know) | Yes | Per plot visit. |
| Farm details: variety, last spray, fruit load | Optional | Three taps per plot visit, for the officer; "Don't know" is an answer. Last spray records only how long ago, never a product or an amount. The AI does not use them. |
| Relay farmer disagreement | Yes | A flag and a time on the photo when the relay farmer taps "I think it's something else" (removed by "Undo"). |
| Consent | Yes | A flag on the plot record. The visit cannot start without it. |
| Officer labels | Yes | Per reviewed photo: one of the five answers, "Different problem (not in list)" or "Skip (cannot tell)". |
| Locally updated model | Yes | The refitted small head, after officer labels. |
| Wording corrections | Yes | From "Wording wrong?": which sentence, the language, the suggested wording, the person's role (relay farmer, officer, farmer, other) and an optional note. No farm data. |

### Where it sits

All of this sits in the browser storage (IndexedDB) of the relay farmer's phone, inside the Majani Relay web app. A few conveniences (chosen language, last village typed) sit in the browser's local storage. There is no server and no account. After the first visit, the app works without internet and makes no network requests with farm data.

Data leaves the phone only when a person exports it:
- **Co-op CSV** (button "Export CSV"): one row per village with counts, shares and the alert flag. No member codes, no photos.
- **Plot-records CSV** (button "Export plot records (CSV)", on the Officer and Co-op screens): one row per plot visit with village, visit date, counts by class, photos waiting for the officer, photos the relay farmer sent to the officer, the plot card result, the three farm details, the checklist answers and the model version. No member numbers, no member codes, no photos. It is more detailed than the co-op CSV: in a small village, a plot row with its date could still point to one farm. So it is meant for the named officer, not for buyers or wider sharing. **Next step:** the data agreement with the cooperative says who may receive this file (section 11). Who: co-op manager. When: pilot week 1.
- **Wording corrections CSV**: the suggested wordings people saved with "Wording wrong?" (string id, language, shown text, suggestion, the person's role, a note, time and versions). No farm data.
- **Model update file** (button "Share this update with other relay farmers"): the refitted small head, the list of officer labels, and an 8-bit copy of the 1,280-number embedding of each officer-labelled photo (1284 bytes per photo in binary form, `results/numbers.json`). No photos, no villages, no member codes. An embedding is a summary of a leaf photo; it is not designed to be turned back into an image.

How these files travel (Bluetooth, WhatsApp, a memory card) is up to the user. Once a file leaves the app, the app cannot delete it.

### Who can read it

| Person | What they can see |
|---|---|
| The relay farmer (phone owner) | Everything on this phone. |
| The extension officer | Everything, while using the relay farmer's phone during a visit. Otherwise only what is exported to them. |
| The cooperative | Only exported files. |
| The team that built the tool | Nothing. There is no server. |
| Anyone who picks up the unlocked phone | Everything in the app: thumbnails, villages, member codes, answers, labels. |

### Lost phone

- The data stays on the phone. It is protected only by the phone's screen lock.
- What could leak: leaf thumbnails, village names, member codes, farm details (variety, last spray, fruit load), and which plots had a possible disease. The last item is the most sensitive. A buyer or neighbour could use "rust on plot X" against a farmer. That is one reason the co-op export holds village totals only, and the plot-records export goes only to the named officer.
- Member codes are a weak protection. The hash prefix is public in the code, and member numbers are short, so someone with the phone and time can recover a number by trying all of them. The app says this on screen. In law, this is pseudonymous data, not anonymous data.
- There is no remote wipe (simplification, stated). Mitigation: keep a screen lock; export and then use "Delete all data on this phone" at the end of each round of visits. **Next step:** an app PIN and a per-farm delete button (section 11; app lead; both work offline on the pilot phones; before the pilot starts). A remote wipe needs a server and is not planned.

### Shared phone

The brief's household shares phones: Noor's daughter's smartphone is used at weekends. A relay farmer's phone may also be used by family members.
- Anyone using the same browser sees the same app data. The app has no PIN of its own (gap, stated). **Next step:** add an app PIN (section 11; app lead; before the pilot starts).
- Advice in the training of relay farmers: use the phone's own lock, do not lend the phone with the app open, and delete data after export.
- If the daughter's phone is used, delete the data before the phone goes back to school with her.

### Data can also disappear

Browsers may clear website storage. For example, Safari on iPhone may erase the storage of websites not opened for 7 days unless the app was added to the home screen. The app asks the browser to keep its storage (`askPersist`), but browsers do not always agree. So records should be exported regularly. Loss here means lost records, not a privacy leak. **Next step:** relay farmers add the app to the home screen at training and export weekly. Who: the team at the training session; the co-op manager checks exports. Metric: records lost per phone over the pilot. When: pilot weeks 1–12.

## 3. Data minimisation

- No names, phone numbers, ID numbers, faces or locations.
- The member number is kept only as a code, so two visits to the same farm can be linked without writing the number down.
- Photos are shrunk to 160-pixel thumbnails. That is enough for the officer to see the leaf, and too small to be useful for much else.
- The relay farmer is told to photograph leaves only, not people or houses.
- The village field is free text. Training tells the relay farmer to type the village name, never a person's name.

## 4. Consent

Read aloud by the relay farmer before the first photo (`consent_photos` in `answers.json`):

> English: "May I photograph some coffee leaves on your farm? The photos stay on this phone. We keep your co-op number in coded form, not your name. The officer may look at the photos. You can say no, or ask us to delete them later."
>
> Swahili (unverified): "Je, naweza kupiga picha za majani ya kahawa shambani mwako? Picha zitabaki kwenye simu hii. Tunahifadhi namba yako ya chama cha ushirika kwa njia ya siri, si jina lako. Afisa wa ugani anaweza kuziangalia picha hizi. Unaweza kukataa, au kutuomba tuzifute baadaye."

Rules:
- If the farmer says no, no photos are taken. The checklist can still be talked through without the app.
- The visit screen cannot be passed without the consent step.
- Consent covers this visit. It is asked again at the next visit.
- The Swahili text is not yet checked by a native speaker (see `docs/LANGUAGE.md`). Before real use, a speaker must approve it.

## 5. Deletion

- **Everything on the phone:** "Delete all data on this phone" (About tab) removes plot records, photos, officer labels, wording corrections and the local model update, after a confirmation. The app itself stays installed.
- **Clearing the browser's site data** has the same effect.
- **An unfinished visit:** "Discard this visit" (Plot visit tab) deletes that visit's plot record and its photos, after a confirmation.
- **One farmer only:** gap. The app can delete one photo (when a photo is retaken) but has no "delete this farm's records" button yet. Today a farmer's request to delete means deleting all data on that phone after exporting the others' village totals. **Next step:** add a "delete this farm's records" button (section 11). Who: app lead. Metric: works offline on the pilot phones. When: before the pilot starts.
- **Exported files** are outside the app. The co-op must delete them by hand.

## 6. Kenya Data Protection Act, 2019

We are not lawyers. This is how we read the Act's relevance. A real deployment should check with counsel and the Office of the Data Protection Commissioner (ODPC).

- **Is this personal data?** Likely yes. A member code plus village plus plot results can identify a farmer. Hashing makes it pseudonymous, which still counts as personal data.
- **Who is responsible?** In a real deployment, the cooperative (or the county extension service) would be the data controller. The relay farmer collects data on its behalf. The cooperative should check whether it must register with the ODPC under the 2021 registration regulations.
- **Principles (section 25).** Collect only what is needed, for a stated purpose, keep it accurate, keep it no longer than needed, keep it secure. Our design: minimal fields, on-device storage, delete after export.
- **Lawful basis and consent (sections 30 and 32).** We rely on consent. Section 32 puts the burden of proving consent on the controller and lets the person withdraw it at any time. The consent flag on each plot record is the proof in the app. Withdrawal means deletion (section 5 above).
- **Rights (sections 26 and 40).** A farmer can ask to see, correct or delete their data. Today the phone can delete everything ("Delete all data on this phone") or an unfinished visit ("Discard this visit"), but not one saved visit on its own (gap).
- **Impact assessment (section 31).** Required for high-risk processing. Plot-level disease data has commercial risk (a buyer could use it), so we suggest the cooperative run a short impact assessment before a pilot.
- **Transfer abroad.** None. Data stays on the phone.

## 7. Bias and coverage limits

The full list per dataset is in `docs/DATA_CARD.md`. The main limits:

- **Photo style.** The shipped model trains on lab-style photos (JMuBEN and JMuBEN2: cropped close-ups from Kenya; BRACOL: picked leaves on a white background in Brazil) plus 1303 field photos of leaves on the plant (RoCoLe, Ecuador). We added the field photos because a model trained on lab photos alone was right on only 2.5% of field photos while 93% confident (`results/RESULTS.md`, section 3.6). Photos in a style the model has not seen are sent to the officer: on Ugandan farm photos, 93% (section 3.3). So in a new region the tool starts as a structured queue for the officer and becomes a counting tool as the officer labels photos. **Next step:** keep the first 200 officer-labelled Kenyan pilot photos as a sealed test. Who: the team with the extension officer. Metric: photos answered, answers correct, rust named. When: first pilot month.
- **Country and species.** Training: Kenyan and Brazilian arabica (lab-style) and Ecuadorian robusta (field). External test: Ugandan farm photos (species not stated). No photo comes from a Kenyan farm in field conditions. **Next step:** record the coffee species and variety at each pilot visit and report results by species. Who: the extension officer. Metric: answers correct by species. When: from the first pilot visit.
- **Look-alikes in a new country.** In Uganda, 9% of Phoma leaves are answered "rust" (forced, 53% would be), so Phoma can inflate a rust count there. **Next step:** train on half of the Ugandan copy groups (Phoma field photos included) and test on the other half. Who: ML lead. Metric: Phoma leaves answered "rust", rust leaves named rust. When: before the pilot starts.
- **Cameras and light.** BRACOL used five phone models, JMuBEN one digital camera, RoCoLe one smartphone; the Ugandan photos are stored at 256 × 256 px. Shade, glare, wet or dusty leaves and very low light are barely covered. **Next step:** on the first 100 pilot photos, compare answers on full-size photos and the same photos cut to 256 × 256 px, and note light conditions. Who: the team. Metric: photos answered and answers correct. When: pilot week 1.
- **Only five classes, and "other" knows one pest.** Kenya's major coffee diseases (KALRO-led manual) are coffee berry disease, leaf rust, bacterial blight and Fusarium diseases. Only leaf rust is in our list. The "other problem" answer learned one pest (red spider mite, from Ecuador): 38% of mite photos go to the officer (our earlier model without "other": 14%), but 85 of 167 are still answered "rust" (`results/RESULTS.md`, section 3.2). The 38% holds before any officer labels: an on-phone update built from healthy and rust labels only wears "other" down (26% of mite photos sent to the officer after 10 labels, 13% after 100); the fix is scheduled before the pilot (`results/RESULTS.md`, section 3.8). Bacterial blight, Fusarium, nutrient shortage, drought scorch and other pests (antestia, thrips, scales) may be called one of the five. **Next step:** the officer labels every "Different problem" photo in the queue; the ML lead retrains "other" with them and keeps 1 in 5 aside as a test. Metric: share of those test photos sent to the officer (target: at least 38%), and rust leaves named rust within 3 points. When: pilot week 4.
- **No berries, no roots.** Coffee berry disease and coffee berry borer show on berries, not leaves. The non-AI checklist asks about them and refers to the officer. **Next step:** compare checklist "yes" answers on berry spots with the officer's own berry checks. Who: extension officer. Metric: share of officer-confirmed berry problems the checklist flagged. When: pilot weeks 3–8.
- **One answer per photo.** A leaf with two problems gets one answer. Severity is not measured. **Next step:** the officer notes a second problem and a severity level on the photos they label. Who: extension officer. Metric: share of labelled photos with two problems. When: pilot weeks 3–8.
- **Underside protocol.** Rust shows best on the leaf underside. Leaf miner shows best on the upper side. **Next step:** compare leaf miner found by the officer on visited plots with leaf miner answers in the app. Who: extension officer with the ML lead. Metric: leaf miner plots the app missed. When: pilot weeks 9–12.
- **Language.** Swahili and Kikuyu text is unverified. A farmer who speaks neither gets English or Swahili. **Next step:** a Swahili-speaking extension officer reviews all 24 answers and a Kikuyu speaker the 3 Kikuyu phrases (section 11). When: pilot week 1.
- **Who is left out.**
  - Farmers outside cooperatives. Records are keyed to the cooperative member number, and the relay farmer is a cooperative role.
  - Land that is not yet mapped, if records are later linked to plot maps or to KIAMIS. The tool itself uses village and member number, not maps. About 30% of Kenya's coffee land was geo-mapped in July 2025 (32,688 of 109,384 ha; AFA via Business Daily, 29 Jul 2025: https://www.businessdailyafrica.com/bd/economy/kenya-in-2-month-dash-to-comply-with-eu-coffee-import-rules-5136340).
  - Farmers no relay farmer visits; relay farmers without a smartphone; farmers who do not want photos taken.
  - The tool reaches Noor through a person, not through her own basic phone.

### Scope limits

- **Leaf photos only.** The AI looks at leaves. It misses coffee berry disease, which attacks berries and is Kenya's most damaging coffee disease, and bacterial blight of coffee, which is not in its five labels.
- **The checklist, not the AI, covers the rest.** Soil fertility (fertiliser or manure), very old trees, weeds, spots or holes in the berries, and a dry spell at flowering are fixed questions marked "not AI". A "yes" on a berry question tells the relay farmer to tell the officer.
- **It does not explain a yield drop.** Kenya's 2020 coffee policy explains falling yields mainly by soil fertility, ageing trees and farmers, low reinvestment, climate and missing extension, not by misidentified disease. The tool covers one part: leaf problems the officer should look at.
- **It does not predict outbreaks.** The village ranking ranks rust already seen in photos.
- **It does not give spray timing.** It never names a product, dose or date. The officer decides when action starts.

Sources for these points: `docs/NEED_EVIDENCE.md`.

## 8. Human oversight

- **The officer makes the final call.** This sentence is in every disease answer and in the disclaimer. The officer review screen says "You make the final call."
- **The "not sure" lane.** Low confidence or an unfamiliar photo sends the photo to the officer queue. The farmer is told "Do not spray because of this result" (`action_not_sure`).
- **The relay farmer can disagree.** On any answered photo, "I think it's something else" (with a confirm step) sends the photo to the officer with the reason "relay farmer disagrees". It then counts in the village numbers only after the officer labels it; "Skip" keeps it out. The relay farmer can undo it until the plot card is saved or the officer has labelled the photo. The AI answer is never silently kept in the count against the relay farmer's view.
- **Explanations are fixed and sourced.** "What does this mean?" opens one of 6 fixed guides (what it looks like, common causes, what to do now, when to call the officer). Every "not sure", "unfamiliar" and "different problem" result opens the same not-sure guide. Control questions go to the officer ("ask the officer about approved control"); no product or dose is named. Each section has a "Wording wrong?" button. The Swahili was checked by machine only (20 of 24 sections read back correctly; `GUIDES.md`).
- **The learning loop uses only officer labels** (the five answers and "Different problem"). The model's own guesses are never used as labels. "Skip (cannot tell)" photos are not used.
- **Drift is limited.** When the small head is refit on the phone, a penalty pulls it toward the shipped weights (`prior_strength` in `model/head.json`). A few wrong labels cannot move it far. The image backbone is never changed.
- **Shared updates are checked.** An update file only loads on the model version it was made for, and it carries its list of labels, so the receiver can see how many labels it rests on.
- **The village ranking is advice to a person.** It ranks villages for the officer to visit first, from rust already seen in photos; it does not predict outbreaks. It raises no alarm to anyone by itself. The demo villages are labelled "synthetic".
- **Spot check.** A random 1 in 10 of the photos the tool did answer also goes to the officer queue, to catch confident mistakes. The farmer sees a note that the photo was picked.
- **"Different problem (not in list)".** The officer can mark a photo as a problem outside the five answers. With the shipped head, these labels train its "other problem" answer in the on-phone update, and the photos join the familiar-photo set, so similar photos are sent to the officer as "looks like a different problem". Such photos never count as rust. The officer can also choose "Skip (cannot tell)"; skipped photos are not used.

Limits of oversight:
- **A few "Different problem" labels can swing the on-phone update.** In a check on the 7 demo photos, an update built from one "Different problem" label and no healthy label sent the healthy demo photos to the officer as "looks like a different problem"; with one healthy and one rust label added, every demo photo came back as before. This errs toward the officer (more photos queued), not toward a wrong answer. **Next step:** test the on-phone update with 1–20 labels that include "Different problem", and add a rule (a stronger pull toward the shipped model for "other", or a minimum number of healthy and rust labels) if needed. Who: ML lead. Metric: healthy field photos sent to "other" after the update (shipped model: 0.4%). When: before the pilot starts.
- In the brief's scenario the officer visits about twice a year (we found no Kenyan survey of visit frequency). A queued photo may wait months. The relay farmer and farmer may act before then. That is why the "not sure" text tells them not to spray. **Next step:** agree a weekly or monthly review rhythm with the cooperative. Who: co-op manager and reviewer. Metric: median days a queued photo waits. When: pilot week 1, measured to week 12.
- If the officer labels wrongly, the error spreads to every phone that loads the update. The prior penalty limits this; it does not prevent it. **Next step:** the officer relabels 100 random Ecuador and 100 random Ugandan photos so we know how often an officer and the dataset labels agree. Who: extension officer. Metric: share of photos with agreement. When: pilot week 1.

### Who answers the "not sure" queue, and what happens if nobody does

- **Who.** One named person per cooperative: the county extension officer, or the cooperative's own agronomist or field officer. The cooperative names this person before a pilot. Simplification: the app does not record the reviewer's name; naming the person is an agreement, not a feature.
- **How the photos reach them.** Today the queue lives on the relay farmer's phone. The officer reviews it on that phone, in person (for example at the cooperative office or a monthly meeting). Sending queued photos to the officer's own phone is not built.
- **How much work it is.** On field photos like those it trained on (Ecuador, cross-validated), the officer sees 9% of photos plus a 1 in 10 spot check of the answers, plus any photo the relay farmer disagrees with. In a new region the officer starts by seeing almost everything and the load falls as they label: on Ugandan farm photos the officer sees 93% at first; after 50 officer labels the tool answers 32% (92% correct) and after 100, 46% (94% correct), on photos never used to choose a setting (dataset labels stand in for the officer; `results/RESULTS.md`, section 3.3). That uses the app's second familiarity check (a photo close to one officer-labelled photo counts as familiar), which also raises healthy leaves called a problem from 0.7% to 1.6% after 100 labels. **Next step:** report both on the sealed Kenyan pilot test, with the previous rule side by side. Who: ML lead. Metric: photos answered and answers correct after 50 and 100 labels; healthy leaves called a problem under 2%. When: first pilot month.
- **If nobody answers:**
  - the photos stay queued on the phone;
  - the plot card says "Not sure, waiting for the officer";
  - the advice stays "Do not spray because of this result. Wait for the officer's advice first." (`action_not_sure`);
  - the model is not updated, so it keeps saying "not sure" to similar photos;
  - the village ranking counts only answered photos and shows how many are waiting, so with an unanswered queue it rests on very few photos.
- **The risk this leaves.** Kenya's 2024 coffee strategy says coffee-specific extension has "collapsed" in places (https://kilimo.go.ke/wp-content/uploads/2024/10/Final-Draft-Coffee-Developemnt-and-Marketing-Strategy-27-Jan-2024-1.pdf), and a 2016 survey of Kenyan plant doctors found no answer came back for 27% of samples sent to a lab (https://www.cabi.org/cabi-publications/diagnostic-support-to-plantwise-plant-doctors-in-kenya/). A queue with no named reviewer would repeat that. So a cooperative should not start without a named reviewer.

## 9. What the tool never does

- Never names a pesticide product, an active ingredient or a dose. It says "ask the extension officer about approved control".
- Never gives a coffee price or a market tip.
- Never sends a message to a buyer, official, officer or anyone else. Exports happen only when a person presses a button.
- Never writes new text. Every sentence comes from the fixed list in `answers.json` or the fixed guides in `guides.json`. A chat assistant (the "Majani Relay Assistant") is a roadmap item, not built; it would answer only from an officer-approved library and send anything else to the officer.
- Never feeds the farm details (variety, last spray, fruit load) into the AI. They are shown to the officer only.
- Never diagnoses berries, roots or the whole farm.
- Never asks for or stores a name, phone number, ID number or location.

## 10. Failure modes and mitigations

| What can go wrong | Effect | Mitigation in the tool | What remains, and the next step |
|---|---|---|---|
| Confident wrong answer on a field photo | Farmer treats the wrong problem | Training on field photos; familiarity check and confidence line send unlike photos to the officer; officer makes the final call; no spray advice in any answer | Answers are right 89% of the time on Ecuador field photos, not 100%. Next step: sealed Kenyan test, first pilot month |
| Unknown pest or disease | Called one of the five | "Other problem" answer; familiarity check; officer label "Different problem (not in list)"; 1-in-10 spot check; relay farmer's "I think it's something else" | 85 of 167 mite photos still answered "rust"; the demo mite photo is answered "healthy"; updates from healthy and rust labels only wear "other" down (13% of mite photos sent to the officer after 100 labels). Next steps: keep "other" fixed during the on-phone update, before the pilot; retrain "other" on the officer's "Different problem" photos, pilot week 4 |
| Second familiarity check (nearest officer-labelled photo) lets a wrong answer through | A photo close to one labelled photo is answered when it should go to the officer | Cutoff chosen by a rule set in advance and checked on Ecuador, mite and picture-card photos; officer spot check | On Ugandan photos it roughly doubles healthy leaves called a problem (0.7% → 1.6% after 100 labels). Next step: report it on the sealed Kenyan test, first pilot month |
| Relay farmer disagrees often, or wrongly | Correct answers wait for the officer; counts rest on fewer photos | The officer's label decides; disagreements are counted per plot in the plot-records CSV | Next step: report the disagreement rate and how often the officer sides with the relay farmer, weekly in the pilot |
| Look-alike counted as rust (Phoma) | Rust count too high | Familiarity check sends most Ugandan photos to the officer | 9% of Ugandan Phoma leaves answered "rust". Next step: train on Ugandan Phoma field photos, before the pilot |
| A few "Different problem" labels swing the update | Healthy photos queued as "different problem" | Officer can reset to the shipped model; update loads only on its base version | Next step: test updates with 1–20 labels including "other", before the pilot |
| Healthy answer when berries are sick | False comfort | Healthy answers say "leaves only, not berries"; checklist asks about berry spots and holes | Relies on the relay farmer asking the checklist. Next step: compare checklist berry answers with the officer's berry checks, pilot weeks 3–8 |
| Wrong officer label | Spreads to other phones | Prior penalty; version check; label counts in the update file | No second reviewer. Next step: the officer relabels 100 dataset photos to measure agreement, pilot week 1; add a second reviewer if the officer cannot keep up (`PILOT_PLAN.md`) |
| Wrong or unnatural Swahili / Kikuyu | Misunderstood advice | Fixed list; back-translation and audio checks; "not yet checked" tag on screen; 10 strings flagged for review | No native speaker has checked yet. Next step: speaker review, pilot week 1 |
| Lost or shared phone | Plot data seen by others | No names; member number hashed; thumbnails only; delete-all button | Short member numbers can be guessed; no app PIN; no remote wipe. Next step: app PIN and per-farm delete, before the pilot |
| Browser clears storage | Records lost | Persistent-storage request; export | Possible on iPhone if not added to the home screen. Next step: add to home screen at training; weekly export, pilot weeks 1–12 |
| Plot results used against a farmer (price talks) | Livelihood harm | Data stays on the phone; exports are village totals | A person with the phone can still see plot results. Next step: app PIN, before the pilot |
| Village alert: false alarm or miss | Officer goes to the wrong village | Small-sample adjustment; ranked list, not an alarm; officer decides | Fewer false alarms (3.4 → 1.0) but more misses (1.6 → 3.0) than raw shares, in simulation. Next step: replay on pilot data against the officer's own checks, after 3 months |
| Relay farmer over-relies on the tool | Skips the officer | Every result points to the officer; "not sure" is common by design | Depends on training and trust. Next step: any spray decision made on an app answer pauses the pilot and triggers retraining (stop rule in `PILOT_PLAN.md`); the officer asks about this at each weekly review, weeks 3–8 |
| Nobody answers the "not sure" queue | Photos wait; the model never adapts; the ranking rests on few photos | Plot card says "waiting for the officer"; advice stays "do not spray because of this result"; waiting counts shown per village | Needs a named reviewer agreed with the cooperative. Next step: the co-op manager names the reviewer before pilot week 1; median queue waiting time reported |

## 11. Open items before a real pilot

The 90-day pilot plan ([PILOT_PLAN.md](PILOT_PLAN.md)) schedules each of these.

| Item | Who | How we know it is done | When |
|---|---|---|---|
| Native-speaker review of all Swahili and Kikuyu strings, consent first ([LANGUAGE.md](LANGUAGE.md), section 5) | A Swahili-speaking extension officer; a Kikuyu speaker | All 24 strings reviewed; approved strings lose the "not yet checked" tag | Pilot week 1 |
| A "delete this farm" button and an app PIN | App lead | Both work offline on the pilot phones | Before the pilot starts |
| Field photos from Kenyan farms, taken with the relay farmers' phones, labelled by an officer | The team with the extension officer | The first 200 kept as a sealed test, opened once | Weeks 3–9 |
| A data agreement with the cooperative: controller, retention period, ODPC registration check, short impact assessment, and who may receive the plot-records CSV | Co-op manager with the team | Signed agreement | Pilot week 1 |
| A named reviewer for the officer queue, and a review rhythm | Co-op manager | Name agreed; median queue waiting time reported | Before pilot week 1 |
| If the service is ever paid: replace the CC-BY-NC speech audio with recorded human clips or a commercially licensed voice | The team | Audio licence allows paid use | Before any paid use |
