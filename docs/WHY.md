<!--
Generated from docs/templates/WHY.tmpl.md by ml/fill_docs.py (numbers come from results/numbers.json).
Edit the template, not docs/WHY.md.
-->

# Why Majani Relay: the story on one page

## 1. Noor, and what she needs

Noor is the brief's farmer: fictional, but with constraints drawn from real World Bank work. She is 38, farms 2 hectares with coffee on the upper slope, and has been a cooperative member for eleven years. In Annex B (agriculture), her yields have dropped and she cannot say why; the nearest extension officer visits her sub-county "twice a year at best"; a passing middleman names her price. Her own phone is for calls, messages and mobile money; the house has no Wi-Fi, and the phone stays there while she works.

The brief names no country. We chose central Kenya: open Kenyan coffee leaf photos exist, the officer shortage is documented, and cooperatives produce most of the coffee.

**What she needs, in our reading:** a standard check of her trees that reaches the officer in time, explained to her in Swahili during the plot visit, without her own phone. Price is out of scope: the brief asks for one better decision.

## 2. The situation in Kenyan coffee today

- **One officer, thousands of farmers.** One public extension agent per 1,380 farmers; target 1 per 600 by 2029 (Ministry of Agriculture, 2025). A 2026 Ministry draft: one officer "typically serves 1,500–3,000 farmers". Both cover all farmers, not just coffee.
- **Reports arrive late.** Paper reporting has caused "delayed information flows" (same draft). Coffee extension has "collapsed" in places (coffee strategy, 2024).
- **Cooperatives produce 70% of Kenya's coffee** (2021/22): an institution exists to carry a tool.
- **Farmers mostly say they recognise visible rust** (Uganda, 2016; a 2018 project including Kenya); no study we found tests how accurately. Harder: early pale spots, judging how much rust, acting in time.

"Twice a year" is the brief's scenario, not a Kenyan survey.

## 3. The precondition: a farmer registry

Annex B: in many settings the binding constraint is a missing farmer registry, not a missing algorithm. In Ukraine, a working registry unlocked advice, insurance and grants for 150,000 farmers. **In Kenyan coffee this is partly met:**
- KIAMIS, the national registry, lists 8.9 million farmers (news report, September 2026) and is still growing; the Ministry's 2026 draft data policy names real-time checks of farmer contact details as a gap.
- Cooperative member lists, keyed by member (grower) number, reliably reach coffee farmers: a coffee advance fund paid 668,414 farmers through them (news report, June 2026).
- **Left out:** farmers outside cooperatives or never visited; unmapped land, if records are later linked to maps.

So we key records to the existing member number instead of building a registry. The app stores no names, phone numbers or locations, and keeps the member number only as a scrambled code. A KIAMIS link is possible, not built.

## 4. Who we build for and what we built

- **Relay farmer:** trained by the cooperative to check members' plots, on their own smartphone.
- **Extension officer or co-op agronomist:** labels unclear photos, makes the final call, chooses where to go.
- **Co-op manager:** keeps the member list; combines the phones' CSV exports.

Why not Noor's phone: only 27.5% of rural Kenyan women aged 15–49 own a smartphone (Kenya DHS 2022).

What we built (a phone web app):
- **A standard record:** 3 leaves on each of 5 trees, 15 photos per plot, keyed to the member number.
- **The AI step:** a small model names each leaf (healthy, rust, leaf miner, brown eye spot, Phoma) or says **"not sure — the officer will look"**; unclear photos stay out of the rust count.
- **Officer labels teach the model** on the phone, and the update can be shared.
- **Village ranking:** rust shares, adjusted so 2 rust photos out of 3 do not raise an alarm. It ranks rust already seen.
- **Offline:** after one download of about 36 MB (best on cooperative Wi-Fi), the photo check, officer review, model update and ranking work without internet. 4G reaches most people, but over half of Kenya's land had no mobile coverage in a 2021 study.
- **Swahili, fixed wording:** 24 fixed answers, as Swahili text and audio; the app never writes its own sentences.

## 5. The gap, and how Majani Relay aims to close it

The gap we work on is not telling farmers a disease name. It is getting standard field checks to the officer early enough to change where the officer goes.

**The one decision we help with: which villages the officer visits first.** Instead of waiting for paper reports, the officer would see village rust counts, a ranked list and the queue of unclear photos. The brief's own AI example works alike: Wadhwani AI's cotton tool counts pests in trap photos to decide whether and when to spray.

**We do not claim** that farmers cannot tell when coffee is sick, or that the tool spots rust earlier than people, cuts losses, explains Noor's yield drop (it sees leaves only), diagnoses better than an officer, beats a paper tally sheet, or predicts outbreaks. The gap is real; whether we close it needs a pilot.

## 6. What works in our tests, and what is not yet shown

**Works in our tests** (none yet on Kenyan farm photos):
- **Ecuador field photos it never trained on** (cross-validated; healthy and rust leaves): answers 91%, right on 89% of those; the rest go to the officer.
- **Uganda, a new country:** forced, it would be right on only 43%; it sends 93% to the officer instead.
- **Learns from the officer:** after 100 labels, it answers 46% of Ugandan photos, right on 94% of those (dataset labels stand in for the officer).
- **Careful ranking** (simulated villages): false alarms per 40 villages fall from 3.4 to 1.0; the cost is more misses near the alert line (1.6 → 3.0).

**Not yet shown, with the next step:**
- **Results on Kenyan farm photos** (field results so far come from Ecuador and Uganda; the Kenyan training photos are lab-style close-ups). Next: the first 200 officer-labelled Kenyan pilot photos kept aside as a sealed test, first pilot month.
- **In a new region the officer sees most photos at first** (14% of Ugandan photos answered after 10 labels). Next: measure on the sealed Kenyan test.
- **Look-alikes kept out of the rust count** (today 9% of Ugandan Phoma leaves and 85 of 167 mite photos are answered "rust"). Next: retrain, before the pilot and in pilot week 4.
- **Offline tested on one iPhone in airplane mode** (it opened and checked a sample photo) and in Chrome's offline mode on a computer; not yet on an Android phone, and speed not yet timed. Next: a full visit in airplane mode on a low-cost Android phone, timed, before the pilot.
- **Swahili wording: reviewed by a Swahili-speaking officer in pilot week 1.** It is already cross-checked by machine read-back and against published Swahili farm material.
- **Village ranking tested on simulated villages.** Next: replay on pilot visits against the officer's own village checks.

## 7. Next: the proposed 90-day pilot

- **Who:** one Kirinyaga coffee cooperative, 5 relay farmers, one named officer or co-op agronomist, the co-op manager.
- **Weeks 1–2:** Swahili check, consent and data agreement, training.
- **Weeks 3–8:** about 150 plot visits (our estimate); weekly officer labels, updates shared to all 5 phones. The first 200 officer-labelled Kenyan photos are sealed (never used to update the model or choose a setting) and opened once, in week 9.
- **Measured:** answers correct, rust named, healthy leaves called a problem, queue time, days to the ranking, and whether the top 5 ranked villages hold at least as many officer-confirmed rust hot spots as the officer's own first 5 picks.
- **Stop rule:** below 70% correct on the sealed test, AI answers are switched off; every photo goes to the officer until a retrained model passes.
- **Week 12:** the cooperative, the officer and our team decide: continue, change the design, or stop.

No cooperative has been contacted yet; targets are our proposals.

## The evidence behind this page

Sources, years and links for every figure above, and every limit with its next step:
- [NEED_EVIDENCE.md](NEED_EVIDENCE.md): what farmers can and cannot do, the system gap, and every claim we do not make
- [PROBLEM_EVIDENCE.md](PROBLEM_EVIDENCE.md): Kenyan coffee, officers, phones, signal and the registry
- [PILOT_PLAN.md](PILOT_PLAN.md): the pilot, its targets and stop rules
- [OFFICER_CONTEXT.md](OFFICER_CONTEXT.md): what an officer weighs besides a leaf photo
- [PRIOR_ART.md](PRIOR_ART.md): what exists already, and what we claim
- [RESULTS.md](../results/RESULTS.md): every result, and every limit with its next step (section 3.8)
- [README](../README.md): the app, how to try it, and the full limitations list
