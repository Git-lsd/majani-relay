# What the evidence says about the need

We checked our problem claim against published evidence on 3 Oct 2026, and changed our pitch because of what we found. This page gives the short answer, then every figure with its source, country, year and link. Longer background on Kenyan coffee, phones and the registry: [PROBLEM_EVIDENCE.md](PROBLEM_EVIDENCE.md).

**Short answer.** Kenyan and East African coffee farmers mostly say they recognise visible leaf rust. The documented gaps are elsewhere: early and mild symptoms, judging how much disease there is, acting in time, and getting field observations to the one officer who serves thousands of farmers. What is missing is **standard plot checks that reach the officer early enough to change where the officer goes and when action starts**. A tool that tells farmers a disease name does not fill that gap. Majani Relay is built for it: it records and routes the relay farmer's checks, and the AI step turns photos into counts. Simplification: the evidence shows the gap is real. It does not show that our tool closes it. That needs a field pilot.

**How to read the "Check" column**
- **Review**: taken from our AI-assisted evidence review on 3 Oct 2026, with the source link recorded; not reopened by us.
- **Read**: we opened the source ourselves on 3 Oct 2026.
- **Snippet**: seen only in a search-engine summary. Open the source before quoting it.

## 1. What farmers can and cannot do

| Finding | Figure | Country, year | Source (URL) | Check |
|---|---|---|---|---|
| Farmers say they know leaf rust | 83.8% of farmers had knowledge of coffee leaf rust | Uganda, 2016 | Luzinda et al. 2016: https://www.ajol.info/index.php/ujas/article/view/141754 | Review |
| Farmers say they recognise coffee berry disease | 99% said they could identify it; 90% said they see it early (90 farmers) | Ethiopia, 2026 | Amente et al. 2026: https://pmc.ncbi.nlm.nih.gov/articles/PMC13440173/ | Review |
| Most smallholders recognise rust; many lack the knowledge to manage it | qualitative (project slide) | Kenya, Uganda, Rwanda, Zimbabwe, India; 2018 | CFC/ICO/CABI seminar slides: https://www.ico.org/documents/cy2017-18/Presentations/seminar-leaf-rust-cabi-e.pdf | Review |
| Farmers knew rust long before the big epidemic | up to 40 years before 2012 | Central America, 2022 case study | BSPP: https://www.bspp.org.uk/wp-content/uploads/2022/11/PP5-Coffee-leaf-rust-rdcd.pdf | Review |
| Losses continue although farmers know the disease | rust cut Arabica income by 49.5%; only 20.8% of farmers sprayed | Uganda, 2016 | Luzinda et al. 2016 (link above) | Review |
| Control often fails | 96% said they had no success controlling berry disease; 1% used fungicide | Ethiopia, 2026 | Amente et al. 2026 (link above) | Review |
| Diseases are known less well than insects | 15% used insecticide against leaf rust and 17% against berry disease (both fungal); 43% had met an extension officer in the past two years (150 farmers, Mt Elgon) | Uganda, 2016 | Liebig et al. 2016: https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0159392 | Review |
| Early rust is easy to miss | early lesions are pale spots before the orange powder appears; infection to spores takes from under 2 weeks to several months | global review, 2017 | Talhinhas et al. 2017: https://pubmed.ncbi.nlm.nih.gov/27885775/ | Review |
| Judging how much rust there is by eye is hard | raters off by up to 38%, and up to 22% with reference diagrams | Brazil, 2011 | Capucho et al. 2011: https://bsppjournals.onlinelibrary.wiley.com/doi/full/10.1111/j.1365-3059.2011.02472.x | Review |
| Unaided severity estimates tend to be too high | review finding | global review, 2021 | Bock et al. 2021: https://link.springer.com/article/10.1007/s40858-021-00439-z | Review |
| Look-alikes get confused in single cases | some farmers call brown eye spot (Cercospora) "anthracnose"; Cercospora goes with low leaf nitrogen and potassium | Hawaii, 2008 | Nelson 2008: https://www3.ctahr.hawaii.edu/oc/freepubs/pdf/PD-41.pdf | Review |
| **Closest tested accuracy is for cassava, not coffee** | naming the condition: farmers 18–31%, extension agents 40–58%, PlantVillage Nuru app 65% on one leaf and 74–88% with six leaves per plant; on mild symptoms the app was right 13–37% of the time | Kenya (Busia) and Tanzania, 2020 | Mrisho et al. 2020: https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2020.590889/full | Review |

**What this means**
- All the coffee recognition figures are what farmers say about themselves. **No study we found tests how accurately coffee farmers, lead farmers or extension agents name coffee leaf problems**, in any country (searched: Kenya, Ethiopia, Uganda, Tanzania, Rwanda, Central America).
- The cassava figures may not carry over: cassava virus symptoms are subtler than rust that already shows orange powder. We show them only as cassava.
- What the evidence does support: early and mild symptoms are hard for everyone, severity by eye is unreliable, and diseases are known less well than insects.

## 2. The system gap

| Finding | Figure | Country, year | Source (URL) | Check |
|---|---|---|---|---|
| Officers are few, and paper reporting delays information | "one extension officer typically serves 1,500–3,000 farmers, and reliance on paper-based reporting has resulted in delayed information flows" | Kenya, March 2026 (draft) | Ministry of Agriculture (MoALD), Draft Kenya Agricultural Data, Information and Digital Policy: https://kilimo.go.ke/wp-content/uploads/2026/03/Final-DRAFT-KENYA-AGRICULTURAL-DATA-INFORMATION-AND-DIGITAL-3.pdf | Review |
| National ratio | one public extension agent per 1,380 farmers; target 1:600 by 2029; the ratio "has not improved" | Kenya, 2025 and 2023 | Agriculture Extension Manual v1 (2025): https://fsrp.go.ke/sites/default/files/2025-08/Agriculture%20Extension%20Manual%20v1%20final.pdf ; KASEP (2023): https://kilimo.go.ke/wp-content/uploads/2024/10/KENYA-AGRICULTURAL-SECTOR-EXTENSION-POLICY-2023.pdf | Read (see PROBLEM_EVIDENCE row 15) |
| Coffee extension has collapsed in places; coffee data are estimates | coffee-specific extension "reduced and, in some quotas, collapsed"; "Most data for the coffee industry is currently on estimates" | Kenya, 2024 | MoALD, Coffee Development and Marketing Strategy 2024–2029: https://kilimo.go.ke/wp-content/uploads/2024/10/Final-Draft-Coffee-Developemnt-and-Marketing-Strategy-27-Jan-2024-1.pdf | Review |
| Kenya's coffee policy does not blame misidentified disease for falling yields | yield fell from 4 kg to 2 kg per tree; causes listed: low reinvestment, declining soil fertility, ageing farmers, climate change, insufficient extension; specialised coffee extension "inaccessible to coffee growers" | Kenya, 2020 | National Coffee Policy: https://kilimo.go.ke/wp-content/uploads/2024/10/Final-Coffe-policy-July-2020-1-1.pdf | Review |
| No official early warning for crop pests in 2018 | "no official early warning processes"; field surveillance quarterly at most and often skipped; coffee was 12% of plant-clinic queries, second after maize (16%) | Kenya, 2018 | AIR evaluation of Plantwise-Kenya: https://www.plantwise.org/wp-content/uploads/sites/4/2019/03/Air-Pw-K-Final-Report-1.pdf | Review (2018; may have changed) |
| Lab referrals for hard cases are often not completed | 65% of plant doctors meant to send samples to a lab, 30% did, and no result came back in 27% of cases (133 plant doctors) | Kenya, 2016 | CABI study: https://www.cabi.org/cabi-publications/diagnostic-support-to-plantwise-plant-doctors-in-kenya/ ; also cited as Mugambi et al. 2016: https://academicjournals.org/journal/JAERD/article-abstract/8D3262261234 | Review (authors to be confirmed before quoting) |
| Fewer than half of plant-clinic diagnoses could be validated | 44% of plant-clinic diagnoses fully or partly validated (records 2006–2010; all crops seen at the clinics, not coffee only) | Uganda, 2013 | Danielsen et al. 2013: https://eric.ed.gov/?id=EJ996429 | Review |
| A lead-farmer layer exists, and coffee is in it | 3,248 "digitally equipped agripreneurs" in 464 wards and more than 1,200 trained lead farmers | Kenya, Dec 2024 | World Bank NAVCDP progress report (P176758): https://documents1.worldbank.org/curated/en/099120224103511153/pdf/P176758-f935f24c-0040-4764-b17c-f2a25be0aed9.pdf | Review |

**What this means.** Each officer serves many farmers, coffee-specific extension has shrunk in places, field information arrives late on paper, and many hard cases sent for checking get no answer. The brief names the same problem: extension services constrained by "staff shortages, manual data collection, and delayed alerts". We found no coffee-specific officer-to-farmer ratio for Kenya; the figures above are for all farmers.

## 3. The Central America lesson

| Finding | Figure | Country, year | Source (URL) | Check |
|---|---|---|---|---|
| The 2012–13 rust epidemic was very costly | rust hit 55% of 593,037 ha; losses over 19% of the crop (3.5 million 60-kg bags), USD 499 million; 373,584 jobs lost | Central America, 2013 | PROMECAFE/IICA: http://promecafe.net/documents/Publicaciones/coffee%20rust%20in%20central%20america.pdf | Review |
| Its causes were many, not just late detection | the report calls the causes "multifactorial": low prices, little fertiliser or spraying, old susceptible trees, weather | Central America, 2013 | same | Review |
| Field monitoring had stopped | after the 1990s cuts, "field monitoring and data analysis all but ceased" | Central America, 2013 | same | Review |
| Timing matters | preventive fungicide "as soon as 5% of leaves become infected" (a Central American / Brazilian rule, not Kenya's); production fell 16% in 2012–13 and 10% more in 2013–14 | Colombia and Central America, 2015 | Avelino et al. 2015: https://d-nb.info/1198124938/34 | Review |
| Hotspots came first | "unusually high levels of coffee rust were detected in 2011-12, one year before the great epidemic, in specific localities" | Guatemala, El Salvador; published 2015 | same | Review |
| The response: routine plot surveillance plus alerts | Colombia inspects more than 4,500 plots four times a year, which "alerts field technicians"; SATCAFE lets users upload incidence from a smartphone; PROCAGICA (EUR 16.5 million) built a regional early warning network | Colombia and Central America, 2013–2021 | Avelino et al. 2015 (above); IICA: https://www.iica.int/en/press/news/iica-and-eu-launch-program-address-effects-coffee-leaf-rust-central-america-and-dominican | Review |
| Spraying by monitoring uses less fungicide than a fixed calendar | fungicide volume down 71.3% and rust-control cost down 21% | Brazil (Conilon coffee), 2020 | Belan et al. 2020: https://link.springer.com/article/10.1007/s10658-019-01917-6 | Review |
| Rust was worst where advice was thinnest | worst where farmers had no training, few technical visits and low incomes | Nicaragua, 2020 | Villarreyna et al. 2020: https://research.wur.nl/en/publications/economic-constraints-as-drivers-of-coffee-rust-epidemics-in-nicar/ | Review |

**What this means.** After the crisis, the coffee sector answered with a design similar to ours: standard plot checks, pooled by phone, that alert technicians (in our app, each phone keeps its records offline and the cooperative combines the phones' exports). But the losses had many causes, and **no study we found shows that phone-based surveillance reduced rust losses**.

## 4. The brief's own AI example works the same way

The brief's agriculture annex cites Wadhwani AI's cotton tool: a farmer photographs a pheromone trap, and the model counts the pests and advises "whether and when to spray" (India; KDD 2020 paper: https://dl.acm.org/doi/pdf/10.1145/3394486.3403363 ; product page: https://aiopportunity.wadhwaniai.org/main-page-dev-lib/cottonace). Its value comes from counting to decide timing, not from naming a pest. The product page claims "70% crop loss prevented" with no year or place given, so we do not use that figure.

## 5. Registry fit

| Finding | Figure | Country, year | Source (URL) | Check |
|---|---|---|---|---|
| Cooperatives already hold the farmers | over 800,000 smallholders; about 550 cooperatives market over 80% of coffee | Kenya, 2024 | MoALD Coffee Strategy (link above); USDA FAS GAIN KE2024-0003: https://apps.fas.usda.gov/newgainapi/api/Report/DownloadReportByFileName?fileName=Coffee+Annual_Nairobi_Kenya_KE2024-0003.pdf | Read (PROBLEM_EVIDENCE rows 4, 6) |
| The national registry exists; real-time checks of contact details are a stated gap | KIAMIS: 7.2 million farmers and "lack of realtime farmer contact validation" in the March 2026 draft policy; 8.9 million registered by 30 Sep 2026 per Kenya News Agency | Kenya, 2026 | draft policy (link in section 2); KNA: https://www.kenyanews.go.ke/cs-kagwe-unveils-digital-farming-push/ | Review; Secondary |
| One cooperative mapped its members' plots | Toroton Farmers Cooperative Society (southern Nandi) mapped 1,621 coffee plots in six weeks | Kenya, July 2026 | FAO: https://www.fao.org/transparent-supply-chains/detail/detail/from-one-cooperative-to-a-county--how-kenyan-coffee-farmers-are-taking-ownership-of-their-geodata-with-open-foris-ground-and-whisp/en | Read (page dated 31 Jul 2026) |
| Most coffee land was not yet mapped | about 30% of coffee land geo-mapped: 32,688 of 109,384 ha, in 16 of 33 counties | Kenya, July 2025 (AFA figure) | Business Daily, 29 Jul 2025: https://www.businessdailyafrica.com/bd/economy/kenya-in-2-month-dash-to-comply-with-eu-coffee-import-rules-5136340 | Read (article dated 29 Jul 2025; the share may be higher now) |

**What this means.** We do not build a registry. Each plot record is keyed to the cooperative member number that already exists, and could later be linked to KIAMIS. Farmers outside cooperatives are left out. The tool itself uses village and member number, not maps; any later link to plot maps would leave out land that is not yet mapped.

## 6. Claims we do not make

- That farmers cannot tell when their coffee is sick.
- Any accuracy figure for farmers or officers naming coffee leaf problems. None exists. The cassava figures appear only as cassava, labelled as not coffee.
- That the tool detects rust earlier than people do, or before symptoms show.
- That it reduces losses, raises yield or saves money. No study shows that phone surveillance cut rust losses.
- That the 2012–13 Central American losses (USD 499 million) came from late detection. The source calls the causes "multifactorial".
- That it explains Noor's yield drop. It sees leaves only: it misses coffee berry disease (berries) and bacterial blight (not in its labels). The checklist, not the AI, covers soil fertility, old trees, berry problems and dry spells.
- That it diagnoses better than extension officers, or replaces them.
- That the village ranking predicts outbreaks. It ranks rust that has already been seen.
- That 5% of leaves infected is Kenya's spray rule. That threshold comes from Central America and Brazil. Kenya's rust spraying follows a calendar starting mid-October (Kenya rust review, 2021; seen only in a search summary).
- That Kenya has no early-warning system today. That finding is from a 2018 evaluation.
- That the tool builds or fixes a farmer registry, or that it reaches Noor directly. Its user is the relay farmer, and the decision it serves is the officer's.
- That the AI beats a paper tally sheet or a plain digital form. We have not shown that yet.
- That 1,500–3,000 farmers per officer is a coffee-specific ratio. It is for all farmers.
- The cotton tool's "70% crop loss prevented". No year or place is given.

## 7. Not found or not checked

- Any test of how accurately coffee farmers name leaf problems (searched six countries or regions).
- When East African farmers first notice rust.
- A coffee-specific officer-to-farmer ratio for Kenya.
- The share of Kenyan coffee farmers who get advice on pests and diseases.
- Kenya's spray calendar and chemical-cost figures (chemical control up to 30% of production cost, Alwora and Gichuru 2014): seen only in search summaries: https://www.researchgate.net/publication/270494688_Advances_in_the_Management_of_Coffee_Berry_Disease_and_Coffee_Leaf_Rust_in_Kenya
- How far bacterial blight of coffee has spread in Kenya (one summary named Murang'a, Nyeri and Kiambu; not confirmed): https://infonet-biovision.org/PlantHealth/MinorPests/bacterial-blight-coffee
- Results of the cotton tool in the field, with year and place.
