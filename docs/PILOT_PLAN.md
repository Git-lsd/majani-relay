<!--
Generated from docs/templates/PILOT_PLAN.tmpl.md by ml/fill_docs.py (numbers come from results/numbers.json).
Edit the template, not docs/PILOT_PLAN.md.
-->

# Pilot plan: 90 days with one Kirinyaga coffee cooperative

**Question the pilot answers:** on Kenyan farms, do relay farmers' plot checks with Majani Relay reach the officer as usable rust counts and a village ranking the officer would act on, and how much officer time does that take? Everything below uses facts from our other documents; items marked *(assumption)* are our proposals, to be agreed with the cooperative. No cooperative has been contacted yet.

## Who

| Role | Who | Time asked *(assumption)* |
|---|---|---|
| Relay farmers | 5, trained by the cooperative, using their own smartphones | About 5 plot visits a week each, about 15 minutes per visit (our estimate; never timed on a farm) |
| Named reviewer | 1 county extension officer or cooperative agronomist / field officer, named before week 1 | One review session a week (queue, spot checks, update, share) |
| Co-op manager | Data controller; combines the relay farmers' CSV exports; names the reviewer | 1 hour a week |
| Our team | ML lead, app lead | Setup, weekly check-in, evaluation |

## Timeline

**Weeks 1–2: setup.**
- **Swahili review:** a Swahili-speaking officer reviews the 24 fixed answers (about 30 minutes; consent and safety lines first, `LANGUAGE.md`, section 5) and the 24 sections of the "What does this mean?" guides (the 4 flagged by machine first, `GUIDES.md`); a Kikuyu speaker reviews the 3 Kikuyu phrases. Only approved strings lose the "not yet checked" tag. A KALRO coffee agronomist checks the Phoma guide, which rests mostly on non-Kenyan sources.
- **Consent and data:** a short data agreement with the cooperative (controller, retention, ODPC registration check, short impact assessment; `RESPONSIBLE_AI.md`, sections 6 and 11). Consent is read aloud at every visit; no photos without it.
- **30-minute training** for relay farmers: photo protocol (3 leaves on each of 5 trees, underside), consent, checklist, export, phone lock, delete after export.
- **Officer onboarding:** the queue, the labels (including "Different problem" and "Skip"), photos the relay farmer sent with "I think it's something else", the three farm-detail taps, the on-phone update and sharing it. The officer relabels 100 random Ecuador and 100 random Ugandan photos so we know how often the dataset labels agree with an officer.
- **App changes before the first visit:** plot and plant fields; a "test set" flag so sealed photos are labelled but never used in an update (not built today); per-farm delete; a PIN each officer sets, in place of the fixed demo officer PIN, and a PIN for the plot-visit records; the "other" setting fixed and written down; keep the "other" answer from wearing down during the on-phone update (`results/RESULTS.md`, section 3.8); add to the plot-records CSV whether the officer's label agreed with the relay farmer's disagreement (today the CSV counts disagreements per plot, and the outcome is visible only on the phone); agree the farm-tap options with the officer (for example, add K7 and "mixed" to variety, and a "within 3 weeks" spray option to match the KALRO-CRI 3-week spray interval). Time the app on the relay farmers' phones (median seconds from photo to answer; first download about 36 MB, done on cooperative Wi-Fi).

**Weeks 3–8: data.**
- Relay farmers run plot visits; about 150 visits and 2,000+ photos over 6 weeks *(assumption: 5 relay farmers × 5 visits a week)*.
- **Sealed Kenyan test:** the first 200 officer-labelled Kenyan photos are kept aside, never used in an update or to choose any setting, and opened once in week 9.
- The officer labels the queue weekly; updates are shared to all 5 phones. Target: 50 labels outside the sealed set by week 5, 200 by week 8.
- Week 4: the ML lead retrains "other" with the officer's "Different problem" photos (1 in 5 kept aside as a test), and re-tunes the update strength, answer threshold and familiarity cutoff on an inner split of the labelled photos.
- Card test: relay farmers label 60 officer-labelled Kenyan photos with the picture card (updated with field pictures), next to the app on the same photos.
- Each week, before seeing the co-op ranking, the officer writes down which villages they plan to visit first.
- Each week the officer notes the free questions relay farmers bring, counted by topic (input for the Majani Relay Assistant, below).

**Weeks 9–12: evaluation.** Open the sealed Kenyan test and score every target below; replay both village alert rules on the pilot visits against the officer's own village checks; the cooperative, the officer and the team decide: continue, change the design, or stop.

## Measurable targets, with the baseline we have today

Targets are our proposals *(assumption)*, fixed before any Kenyan photo is seen.

| Measure | Baseline today (where measured) | Pilot target, on the sealed Kenyan test unless stated |
|---|---|---|
| Photos answered (not sent to the officer) | Ecuador, cross-validated: 91%. Uganda (photos never used to choose a setting): 7% with no officer labels, 32% after 50, 46% after 100 | Reported at 0, 50 and 200 officer labels, with the app rule and the previous rule side by side; at least 50% after 200 |
| Answers that are correct | Ecuador: 89%. Uganda: 53% with none, 92% after 50, 94% after 100 | At least 85% |
| Rust leaves named rust | Ecuador: 72%. Uganda: 5% with none, 44% after 100 | At least 60% after 200 labels |
| Healthy leaves called a problem | Ecuador: 6%. Uganda: 3.5% with none, 1.6% after 100 | At most 10%. Separately, the learning-loop report (after 50 and 100 officer labels, app rule and previous rule) keeps the limit in `results/RESULTS.md`, section 3.8: under 2% |
| Other problems sent to the officer | Ecuador mite photos: 38% before any officer labels; 13% after 100 healthy and rust labels | At least 38% of the held-out "Different problem" photos, also after the week-4 update |
| Relay farmer disagreements ("I think it's something else") | Not measured | Reported weekly: share of answered photos the relay farmers send to the officer, and how often the officer's label sides with the relay farmer rather than the AI, by class. No target fixed in advance |
| Officer queue time | Not measured | Median at most 14 days from photo to officer label |
| Relay farmer with card vs app (60 Kenyan photos) | Two team members with a card named rust on 5–7 of 30; the app on the same Ecuador photos: 19 of 30 | Both reported; the app names at least as many rust photos, and healthy vs problem is within 5 points of the relay farmers |
| Village ranking vs the officer's own plan | Simulation with synthetic villages: 3.7 real outbreaks among the top 5 (raw shares 3.5); false alarms 1.0, misses 3.0 per 40 villages | The top 5 ranked villages hold at least as many officer-confirmed rust hot spots as the officer's own first 5 planned visits |
| Days from plot visit to the village ranking | Paper reports cause "delayed information flows" (MoALD draft data policy, 2026); not measured locally | Median at most 7 days |

## Officer decision context

The photo check tells the officer what a leaf looks like. Whether a village needs action also depends on things a photo cannot show. Kenyan sources (KALRO-CRI review, Gichuru et al. 2021; Kenya Coffee Sustainability Manual 2020) name four: where the village is in the rainy season, the coffee variety, altitude and temperature, and how dense and well pruned the trees are. They also say spray timing against the KALRO-CRI calendar matters. Studies outside Kenya (Costa Rica, Honduras, Brazil, Hawaii) add fruit load: a heavy crop raises rust. The pilot shows these factors to the officer next to the village rust count. **The AI does not use them.** The photo model is unchanged and sees only the photo. These factors inform the officer's decision; they do not change the result. Every row, with its sources and whether we read the full text, the abstract or only a snippet: [OFFICER_CONTEXT.md](OFFICER_CONTEXT.md).

**Built today:** three optional taps at the plot visit, labelled "For the officer; the AI does not use this": variety, last spray and fruit load. They are saved with the plot record, shown on the plot card, on each officer queue item and on the Officer screen, and exported in the plot-records CSV. **Not built (pilot design):** the season, rain, altitude and temperature lines below.

**What the officer would see next to the village rust count (one village, last 30 days)**
- **Rust count.** Number of plots with a "leaf rust" result, out of the plots checked. The "not sure" and "different problem" results are listed separately. Photos where the relay farmer tapped "I think it's something else" are also listed separately; they wait for the officer and do not count until the officer decides.
- **Season line** (Kenyan sources). Days since the rains started at this village, next to the KALRO-CRI calendar: first round just before the short rains, repeated 3 weeks later; next round before the long rains. Next to that, the usual rust peak months for the area: West of Rift June–July and October–December; East of Rift May–June and January–March.
- **Rain.** Rainfall and number of rain days in the last 30 days, from CHIRPS (daily satellite rainfall estimates, about 5 km cells) for the village location. The cooperative office downloads it when online. The field app stays offline.
- **Altitude band.** From the village location, looked up at the office. The app records no GPS position today (`RESPONSIBLE_AI.md`, section 3); recording plot positions would need the cooperative's agreement and a change to the consent text, so the pilot starts with the village location.
- **Plot-visit taps (summary).** Share of checked plots by variety, by time since the last spray, and by fruit load.
- **Temperature (optional).** Daily minimum and maximum from NASA POWER. Its cells are about ½° × ⅝°, so one value covers many villages. It is shown as a rough guide only.

**What the pilot records, and how**

| Factor | Recorded in pilot? | How | Evidence |
|---|---|---|---|
| Variety | Yes (in the app now) | Tap: SL28/SL34 / Ruiru 11 / Batian / Other / Don't know | Kenyan: SL28 and SL34 susceptible, Ruiru 11 highly resistant; sources disagree on Batian (resistant or intermediate) |
| Last spray on the coffee | Yes (in the app now) | Tap: Never / Under 1 month / 1–3 months / Over 3 months / Don't know. No product name and no amount are recorded. | Kenyan: KALRO-CRI spray calendar, repeat after 3 weeks |
| Fruit load | Yes (in the app now) | Tap: Low / Medium / High / Don't know, judged by the farmer by eye | **Elsewhere only** (Costa Rica, Honduras, Brazil, Hawaii); no Kenyan study found |
| Rainfall | Yes, at the office | CHIRPS for the village location | Kenyan: rust infects during the rains; peaks after them |
| Altitude | Yes, at the office | From the village location | Kenyan: rust mainly in lower areas, now seen higher up; no Kenyan cut-off found |
| Temperature | Optional | NASA POWER (coarse) | Kenyan: best range 21–25 °C |
| Leaf wetness | No | No sensor. Rain days and humidity are rough stand-ins only. | Kenyan sources disagree on the minimum (3 h vs 24–48 h) |
| Shade, pruning, nutrition | No tap | The officer notes them on a visit | Kenyan evidence on shade is mixed |

**Limits we state up front**
- **No risk score.** The factors are shown side by side, not combined. We found no Kenyan study that says how to weigh them against each other.
- **The village count is a different measure from manual thresholds.** It is the share of *plots checked*, not the share of *leaves* with rust. The Kenyan manual's "severe" level (20% of leaves) and the 5% level used in Brazil cannot be read off it. The 5% level is not Kenyan. Next step: in pilot week 1, the named reviewer and a KALRO-CRI contact say how the plot share should be read against the manual's 20% level (part of the review of [OFFICER_CONTEXT.md](OFFICER_CONTEXT.md)).
- **There is a lag.** Rust seen today started about 3–5 weeks earlier. That estimate comes from studies outside Kenya (France, Brazil) and is not checked for Kenyan highland temperatures. A low count early in the rains does not mean low risk. Next step: the KALRO-CRI contact checks the 3–5 week figure for Kenyan highland temperatures in the same week-1 review.
- **Fruit-load evidence is not Kenyan.** We record fruit load so the pilot can see whether it matters in Kenya.
- **Spray decisions stay with the officer.** They follow the KALRO-CRI programme and the products registered by the Pest Control Products Board. The app never names a product or a dose.
- **No Kenyan officer or KALRO-CRI staff member has reviewed this list yet.** Next step: the named reviewer and a KALRO-CRI contact review [OFFICER_CONTEXT.md](OFFICER_CONTEXT.md) in pilot week 1.

**What the pilot will learn:** whether officers look at the context lines, how often each tap is answered "Don't know", and whether officers decide differently by variety, last spray or fruit load.

## After the pilot: Majani Relay Assistant (roadmap, not built)

A chat assistant for relay farmers that answers only from a vetted library of answers the officer has approved. It never generates free text: it picks an approved answer, or says it does not know and sends the question to the officer. It is not part of this pilot. What the pilot gives it: the free questions relay farmers bring, counted by topic each week (weeks 3–8), and the officer's answers to the most common ones as the library's first entries. Metric for deciding to build it: the share of relay farmers' questions that such a library would have covered.

## Costs and devices

- **Devices:** the relay farmers' own smartphones (the tool assumes they have one). No server, no account, no licence fee; the app is a web page saved on the phone.
- **Data:** one download of about 36 MB per phone, best on cooperative Wi-Fi; officer updates are small files shared by WhatsApp, Bluetooth or memory card.
- **To cost with the cooperative** *(assumption: no figures yet)*: data or airtime for relay farmers, the officer's review time, the training session, one spare Android phone in case a relay farmer's phone fails.

## Risks and stop rules

| Risk | Stop or pause rule |
|---|---|
| Wrong answers on Kenyan photos | If the sealed test gives answers correct below 70% or healthy leaves called a problem above 20%: stop showing AI answers; every photo goes to the officer until a retrained model passes |
| A few "Different problem" labels swing the on-phone update (seen on our demo photos) | Pause sharing an update if, after it, more than 5% of the officer's healthy test photos go to "other" |
| Nobody answers the queue | Queue older than 30 days: pause new visits until the reviewer is back |
| A spray decision based on an app answer | Any report: pause, retrain relay farmers, check the wording with the officer |
| Lost phone or data shared beyond the export | Delete data on the phone, tell the co-op manager; review the data agreement |
| Consent not asked | Records from that visit are deleted |

## What would make us change the design

- **The "not sure" check stays shut on Kenyan photos** (under 20% answered after 200 labels, with the app's nearest-officer-photo check already on): store more officer-labelled Kenyan photos, or re-set that check's cutoff on an inner split of the Kenyan labels (never on the sealed test).
- **The nearest-officer-photo check lets too many healthy leaves through as problems** (healthy leaves called a problem at 2% or more after 100 labels on the sealed test; Uganda: 1.6%): tighten its cutoff, or switch it off and keep the previous rule; the sealed test reports both rules side by side.
- **Relay farmers often disagree and the officer often sides with them** for one class: look at those photos first when retraining, and check the guide and the answer wording for that class.
- **Relay farmers with a card name rust as well as the app:** the value is the standard record and the officer queue; keep those and drop per-photo answers.
- **Phoma or other look-alikes inflate rust counts:** retrain with Kenyan field photos of the look-alikes, and until then report counts as "rust or look-alike".
- **The officer cannot keep up:** lower the spot-check rate, change the review rhythm, or add a second reviewer.
- **15 leaves per plot gives noisy plot estimates:** raise the number of leaves per plot (survey programmes use more; `PRIOR_ART.md`, section 4).
- **The ranking does not match the officer's own checks:** re-set the alert line, or keep the ranked list and drop the alert.
