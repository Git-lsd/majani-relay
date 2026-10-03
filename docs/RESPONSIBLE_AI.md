# Responsible AI, data and safety

The brief makes this a pass/fail criterion. It asks whether the limits are respected, and whether our account of privacy, consent, bias and human oversight is credible. The health annex also asks three questions that apply to any tool on a shared phone: where the data sits, who can read it, and what happens when the phone is lost or shared. This page answers all of them for Kahawa Check.

Facts about the app below were checked against `app.js` on 2026-10-03. If the app changes, this page must be checked again.

## 1. The fail-safe in one paragraph

The tool reads a leaf photo and gives one of five answers (healthy, leaf rust, leaf miner, brown eye spot, Phoma), or **"not sure — the officer will look"**. It says "not sure" when its best guess is below a confidence line, or when the photo looks unlike the photos it learned from. A "not sure" photo goes into a queue for the extension officer. Every disease answer ends with "The extension officer makes the final call." The tool never names a pesticide or a dose, and it never sends anything by itself.

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
| Consent | Yes | A flag on the plot record. The visit cannot start without it. |
| Officer labels | Yes | Per reviewed photo. |
| Locally updated model | Yes | The refitted small head, after officer labels. |

### Where it sits

All of this sits in the browser storage (IndexedDB) of the relay farmer's phone, inside the Kahawa Check web app. A few conveniences (chosen language, last village typed) sit in the browser's local storage. There is no server and no account. After the first visit, the app works without internet and makes no network requests with farm data.

Data leaves the phone only when a person exports it:
- **Co-op CSV** (button "Export CSV"): one row per village with counts, shares and the alert flag. No member codes, no photos.
- **Model update file** (button "Share this update with other relay farmers"): the refitted small head, the list of officer labels, and an 8-bit copy of the 1,280-number embedding of each officer-labelled photo (about 1.3 KB per photo). No photos, no villages, no member codes. An embedding is a summary of a leaf photo; it is not designed to be turned back into an image.

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
- What could leak: leaf thumbnails, village names, member codes, and which plots had a possible disease. The last item is the most sensitive. A buyer or neighbour could use "rust on plot X" against a farmer. That is one reason the export holds village totals only.
- Member codes are a weak protection. The hash prefix is public in the code, and member numbers are short, so someone with the phone and time can recover a number by trying all of them. The app says this on screen. In law, this is pseudonymous data, not anonymous data.
- There is no remote wipe (simplification, stated). Mitigation: keep a screen lock; export and then use "Delete all data on this phone" at the end of each round of visits.

### Shared phone

The brief's household shares phones: Noor's daughter's smartphone is used at weekends. A relay farmer's phone may also be used by family members.
- Anyone using the same browser sees the same app data. The app has no PIN of its own (gap, stated).
- Advice in the training of relay farmers: use the phone's own lock, do not lend the phone with the app open, and delete data after export.
- If the daughter's phone is used, delete the data before the phone goes back to school with her.

### Data can also disappear

Browsers may clear website storage. For example, Safari on iPhone may erase the storage of websites not opened for 7 days unless the app was added to the home screen. The app asks the browser to keep its storage (`askPersist`), but browsers do not always agree. So records should be exported regularly. Loss here means lost records, not a privacy leak.

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

- **Everything on the phone:** "Delete all data on this phone" (About tab) removes plot records, photos, officer labels and the local model update, after a confirmation. The app itself stays installed.
- **Clearing the browser's site data** has the same effect.
- **One farmer only:** gap. The app can delete one photo (when a photo is retaken) but has no "delete this farm's records" button yet. Today a farmer's request to delete means deleting all data on that phone after exporting the others' village totals. A per-plot delete button should be added.
- **Exported files** are outside the app. The co-op must delete them by hand.

## 6. Kenya Data Protection Act, 2019

We are not lawyers. This is how we read the Act's relevance. A real deployment should check with counsel and the Office of the Data Protection Commissioner (ODPC).

- **Is this personal data?** Likely yes. A member code plus village plus plot results can identify a farmer. Hashing makes it pseudonymous, which still counts as personal data.
- **Who is responsible?** In a real deployment, the cooperative (or the county extension service) would be the data controller. The relay farmer collects data on its behalf. The cooperative should check whether it must register with the ODPC under the 2021 registration regulations.
- **Principles (section 25).** Collect only what is needed, for a stated purpose, keep it accurate, keep it no longer than needed, keep it secure. Our design: minimal fields, on-device storage, delete after export.
- **Lawful basis and consent (sections 30 and 32).** We rely on consent. Section 32 puts the burden of proving consent on the controller and lets the person withdraw it at any time. The consent flag on each plot record is the proof in the app. Withdrawal means deletion (section 5 above).
- **Rights (sections 26 and 40).** A farmer can ask to see, correct or delete their data. Today only "delete all" exists on the phone (gap).
- **Impact assessment (section 31).** Required for high-risk processing. Plot-level disease data has commercial risk (a buyer could use it), so we suggest the cooperative run a short impact assessment before a pilot.
- **Transfer abroad.** None. Data stays on the phone.

## 7. Bias and coverage limits

The full list per dataset is in `docs/DATA_CARD.md`. The main limits:

- **Lab photos, not field photos.** JMuBEN and JMuBEN2 are cropped close-ups of leaves, with many rotated or flipped copies. BRACOL leaves were photographed on a white background. On the sealed field test (RoCoLe, photos of leaves on the plant), the lab-trained model was almost always wrong while reporting high confidence (`results/RESULTS.md`, finding 1). The familiarity check catches this, so out of the box the tool says "not sure" to nearly all field photos (finding 2). In early use it works mostly as a structured queue for the officer, not as a diagnosis tool.
- **Country and species.** Training: Kenyan and Brazilian arabica. Field test: Ecuadorian robusta. No photo in any split comes from a Kenyan farm in field conditions. Rust looks similar on both species, but this is a stand-in.
- **Cameras and light.** BRACOL used five phone models. JMuBEN used one digital camera. Shade, glare, wet or dusty leaves and very low light are not covered.
- **Only five classes.** Kenya's major coffee diseases (KALRO-led manual) are coffee berry disease, leaf rust, bacterial blight and Fusarium diseases. Only leaf rust is in our list. Bacterial blight, Fusarium, nutrient shortage, drought scorch and other pests (antestia, thrips, scales, red spider mite) are not. Such photos should come out as "not sure", but may be called one of the five. After local adaptation, the tool flagged unknown-pest photos as "not sure" much less often (`results/RESULTS.md`, finding 6).
- **No berries, no roots.** Coffee berry disease and coffee berry borer show on berries, not leaves. The non-AI checklist asks about them and refers to the officer.
- **One answer per photo.** A leaf with two problems gets one answer. Severity is not measured.
- **Underside protocol.** Rust shows best on the leaf underside. Leaf miner shows best on the upper side.
- **Language.** Swahili and Kikuyu text is unverified. A farmer who speaks neither gets English or Swahili.
- **Who is left out.** Farmers no relay farmer visits; relay farmers without a smartphone; farmers who do not want photos taken. The tool reaches Noor through a person, not through her own basic phone.

## 8. Human oversight

- **The officer makes the final call.** This sentence is in every disease answer and in the disclaimer. The officer review screen says "You make the final call."
- **The "not sure" lane.** Low confidence or an unfamiliar photo sends the photo to the officer queue. The farmer is told "Do not spray because of this result" (`action_not_sure`).
- **The learning loop uses only officer labels** for the five classes. The model's own guesses are never used as labels.
- **Drift is limited.** When the small head is refit on the phone, a penalty pulls it toward the shipped weights (`prior_strength` in `model/head.json`). A few wrong labels cannot move it far. The image backbone is never changed.
- **Shared updates are checked.** An update file only loads on the model version it was made for, and it carries its list of labels, so the receiver can see how many labels it rests on.
- **The co-op early warning is advice to a person.** It ranks villages for the officer to visit first. It raises no alarm to anyone by itself. The demo villages are labelled "synthetic".
- **Spot check.** A random 1 in 10 of the photos the tool did answer also goes to the officer queue, to catch confident mistakes. The farmer sees a note that the photo was picked.
- **"Different problem (not in list)".** The officer can mark a photo as a problem outside the five classes. These photos are not used to refit the model and are not added to the familiar-photo set, so the tool keeps saying "not sure" to similar photos. The officer can also choose "Skip (cannot tell)"; skipped photos are not used either.

Limits of oversight:
- The officer visits about twice a year. A "not sure" photo may wait months. The relay farmer and farmer may act before then. That is why the "not sure" text tells them not to spray.
- If the officer labels wrongly, the error spreads to every phone that loads the update. The prior penalty limits this; it does not prevent it.

## 9. What the tool never does

- Never names a pesticide product, an active ingredient or a dose. It says "ask the extension officer about approved control".
- Never gives a coffee price or a market tip.
- Never sends a message to a buyer, official, officer or anyone else. Exports happen only when a person presses a button.
- Never writes new text. Every sentence comes from the fixed list in `answers.json`.
- Never diagnoses berries, roots or the whole farm.
- Never asks for or stores a name, phone number, ID number or location.

## 10. Failure modes and mitigations

| What can go wrong | Effect | Mitigation in the tool | What remains |
|---|---|---|---|
| Confident wrong answer on a field photo | Farmer treats the wrong problem | Familiarity check and confidence line send unlike photos to "not sure"; officer makes the final call; no spray advice in any answer | After adaptation, some unknown problems get one of the five answers |
| Unknown pest or disease | Called one of the five | Familiarity check; "not sure" lane; officer label "Different problem (not in list)"; 1-in-10 spot check | Weaker after local labels (finding 6); the spot check sees only 1 in 10 answers |
| Healthy answer when berries are sick | False comfort | Healthy answers say "leaves only, not berries"; checklist asks about berry spots and holes | Relies on the relay farmer asking the checklist |
| Wrong officer label | Spreads to other phones | Prior penalty; version check; label counts in the update file | No second reviewer |
| Wrong or unnatural Swahili / Kikuyu | Misunderstood advice | Fixed list; back-translation and audio checks; "not yet checked" tag on screen; 10 strings flagged for review | No native speaker has checked yet |
| Lost or shared phone | Plot data seen by others | No names; member number hashed; thumbnails only; delete-all button | Short member numbers can be guessed; no app PIN; no remote wipe |
| Browser clears storage | Records lost | Persistent-storage request; export | Possible on iPhone if not added to the home screen |
| Plot results used against a farmer (price talks) | Livelihood harm | Data stays on the phone; exports are village totals | A person with the phone can still see plot results |
| Early-warning false alarm or miss | Officer goes to the wrong village | Small-sample adjustment; ranked list, not an alarm; officer decides | Fewer false alarms but more misses than raw shares (finding 4) |
| Relay farmer over-relies on the tool | Skips the officer | Every result points to the officer; "not sure" is common by design | Depends on training and trust |

## 11. Open items before a real pilot

1. Native-speaker review of all Swahili and Kikuyu strings, consent first (`docs/LANGUAGE.md`, section 5).
2. A "delete this farm" button and an app PIN.
3. Field photos from Kenyan farms, taken with the relay farmers' own phones, labelled by an officer, to measure accuracy where it will be used.
4. A data agreement with the cooperative: who is controller, retention period, ODPC registration check, short impact assessment.
5. If the service is ever paid: replace the CC-BY-NC speech audio with recorded human clips or a commercially licensed voice.
