# Data card

This page lists every dataset Kahawa Check learns from or is tested on: where it comes from, its licence, its size, what we use it for, and **what it does not cover**. Counts after our cleaning come from `results/` by the main session.

All four image datasets are open under **CC BY 4.0**: they may be shared and changed with credit. None of them was collected by us.

## Summary

| Dataset | Country, species | Photo type | Licence | Raw download | Role in Kahawa Check | Used after cleaning |
|---|---|---|---|---|---|---|
| JMuBEN | Kenya (Kirinyaga), arabica | Cropped close-ups of lesions, many augmented copies | CC BY 4.0 | 3 zip files, 549 MB; 22,591 images | Train (rust, Cercospora, Phoma) | 1,500 sampled per class (rust, Cercospora, Phoma); about 1,280 per class train, 220 held out |
| JMuBEN2 | Kenya (Kirinyaga), arabica | Same | CC BY 4.0 | 2 zip files, 1.29 GB; 35,964 images | Train (healthy, leaf miner) | 1,500 sampled per class (healthy, miner); 1,282 / 1,253 train, 218 / 247 held out |
| BRACOL | Brazil (Espírito Santo), arabica | Whole picked leaves on a white background, five phone models | CC BY 4.0 | 1 zip file, 165 MB; 1,747 leaf images | Half train, half calibrate | 1,342 usable of 1,747 (the Mendeley archive itself is damaged: our copy matches its published checksum) |
| RoCoLe | Ecuador (Manabí), robusta | Leaves on the plant, one smartphone, real field light and backgrounds | CC BY 4.0 | DatasetNinja mirror, 711 MB tar; 1,560 images | Sealed field test (healthy vs rust); red spider mite = out-of-scope test | 1,385 healthy/rust (787 / 598), 167 red spider mite (8 photos with mixed labels dropped) |
| `samples/` | From RoCoLe | Same as RoCoLe | CC BY 4.0 | 7 JPEGs, about 0.6 MB | Demo photos in the app | 7 |

Raw sizes are the file sizes we downloaded. Image counts are those stated by the dataset authors.

## 1. JMuBEN (Kenya, arabica: rust, Cercospora, Phoma)

- **Source:** https://data.mendeley.com/datasets/t2r6rszp5c/1 (DOI 10.17632/t2r6rszp5c.1)
- **Citation:** Jepkoech J., Kenduiywo B., Mugo D., Chebet E. (2021). *JMuBEN*. Mendeley Data, V1. Paper: Jepkoech J., Mugo D. M., Kenduiywo B. K., Too E. C. (2021). Arabica coffee leaf images dataset for coffee leaf disease detection and classification. *Data in Brief* 36, 107142. https://doi.org/10.1016/j.dib.2021.107142
- **Institutions:** University of Embu, Jomo Kenyatta University of Agriculture and Technology, Chuka University.
- **Licence:** CC BY 4.0.
- **Raw size:** three zip files, 549 MB in total (Cercospora 252 MB, leaf rust 69 MB, Phoma 227 MB). The paper lists 7,682 Cercospora, 8,337 rust and 6,572 Phoma images (22,591).
- **Conditions:** Mutira coffee plantation, Kirinyaga County, Kenya. The paper says "real-world conditions", one digital camera, labelled with the help of a plant pathologist. The images were cropped to the diseased area and resized. Smaller classes were enlarged with augmented copies (rotations and flips) of the same photos.
- **Role:** training data for the classes rust, Cercospora (brown eye spot) and Phoma. The main session sampled up to 1,500 photos per class. Used for training: rust 1,279, Cercospora 1,286, Phoma 1,275 (another 214–225 per class held out; these overlap with training through augmented copies, so they are not used as a headline) per class.
- **What it does not cover:**
  - Whole leaves on the tree, as a relay farmer would photograph them. The crops show the lesion, not the leaf, the branch or the background.
  - Independent photos: many images are rotated or flipped copies of each other. A random train/test split puts copies of the same leaf on both sides, so accuracy measured inside JMuBEN is too optimistic. We do not use it as a headline number.
  - More than one camera, or phone cameras.
  - Healthy leaves and leaf miner (those are in JMuBEN2).
  - Coffee variety and season: not stated per image.
  - Coffee berry disease, bacterial blight, Fusarium, nutrient shortage, berries.

## 2. JMuBEN2 (Kenya, arabica: healthy, leaf miner)

- **Source:** https://data.mendeley.com/datasets/tgv3zb82nd/1 (DOI 10.17632/tgv3zb82nd.1)
- **Citation:** Jepkoech J., Mugo D., Kenduiywo B., Chebet E. (2021). *JMuBEN2*. Mendeley Data, V1. Same paper as JMuBEN.
- **Licence:** CC BY 4.0.
- **Raw size:** two zip files, 1.29 GB in total (healthy 567 MB, miner 725 MB). The paper lists 18,985 healthy and 16,979 miner images (35,964).
- **Conditions:** same plantation, camera and processing as JMuBEN: cropped, resized, with augmented copies.
- **Role:** training data for healthy and leaf miner (up to 1,500 sampled per class). Used for training: healthy 1,282, leaf miner 1,253 (218 / 247 held out) per class.
- **What it does not cover:** the same gaps as JMuBEN. In addition, "healthy" here means healthy-looking crops from one plantation; it does not show the range of healthy leaves under other light, dust, water drops or old age.

## 3. BRACOL (Brazil, arabica: healthy, miner, rust, Phoma, Cercospora)

- **Source:** https://data.mendeley.com/datasets/yy2k5y8mxg/1 (DOI 10.17632/yy2k5y8mxg.1)
- **Citation:** Krohling R. A., Esgario G. J. M., Ventura J. A. (2019). *BRACOL – A Brazilian Arabica Coffee Leaf images dataset to identification and quantification of coffee diseases and pests*. Mendeley Data, V1. Paper: Esgario J. G. M., Krohling R. A., Ventura J. A. (2020). Deep learning for classification and severity estimation of coffee leaf biotic stress. *Computers and Electronics in Agriculture* 169, 105162 (arXiv:1907.11561).
- **Institution:** Universidade Federal do Espírito Santo.
- **Licence:** CC BY 4.0.
- **Raw size:** one zip file, 165 MB (164,516,964 bytes). 1,747 whole-leaf images, plus 2,147 cropped symptom images that we do not use.
- **Conditions:** leaves picked in Santa Maria de Marechal Floriano, a mountain area of Espírito Santo state, Brazil, at different times of the year. Photographed from the underside, on a white background, under partly controlled light, with five phones (ASUS Zenfone 2, Xiaomi Redmi 5A, Xiaomi S2, Galaxy S8, iPhone 6S). Each leaf is labelled with its main problem and a severity band (healthy below 0.1% of leaf area, up to "very high" above 15%), with help from an expert. Its "phoma" column (brown leaf spot) is mapped to our Phoma class.
- **Known problem with the source file:** the BRACOL zip on Mendeley does not open fully (no central directory), and our copy matches the checksum Mendeley publishes, so the archive itself is damaged. We recovered 1,401 of the 1,747 leaf images plus the label file; 1,342 of them carry one of our five labels (59 have label code 5, not one of our classes, and are excluded).
- **Role:** half of the recovered photos are used for training; the other half calibrate the model (temperature, confidence line, familiarity cutoff). Training: 670 (healthy 71, miner 126, rust 232, Phoma 173, Cercospora 68). Calibration: 672 (healthy 71, miner 127, rust 233, Phoma 173, Cercospora 68).
- **What it does not cover:**
  - Leaves on the tree. Every leaf was picked and laid on a white background, which makes the leaf easy to see.
  - Kenya, or East African varieties and climate.
  - Mixed problems as separate labels: a leaf with two problems carries only its main one.
  - Berries, coffee berry disease, bacterial blight, Fusarium.
  - Calibration on field photos: the confidence line and familiarity cutoff are set on these lab-style photos, not on field photos.

## 4. RoCoLe (Ecuador, robusta: healthy, rust, red spider mite) — sealed field test

- **Source:** https://data.mendeley.com/datasets/c5yvn32dzg/2 (DOI 10.17632/c5yvn32dzg.2). We downloaded the DatasetNinja mirror (https://datasetninja.com/rocole, Supervisely format), which carries the same CC BY 4.0 licence.
- **Citation:** Parraga-Alava J., Cusme K., Loor A., Santander E. (2019). RoCoLe: A robusta coffee leaf images dataset for evaluation of machine learning based methods in plant diseases recognition. *Data in Brief* 25, 104414. https://doi.org/10.1016/j.dib.2019.104414
- **Institutions:** Escuela Superior Politécnica Agropecuaria de Manabí (Ecuador), Universidad de Santiago de Chile.
- **Licence:** CC BY 4.0.
- **Raw size:** 711 MB tar file (DatasetNinja mirror); 1,560 images with leaf outlines and labels.
- **Conditions:** leaves on the plant in one robusta field in Manabí, Ecuador. One smartphone camera (5 megapixels), 20 to 30 cm away, no zoom, on cloudy, sunny and windy days, with other plants and weeds behind. Four images per plant from 390 plants, upper and lower sides of the leaf. Labels: healthy, red spider mite, rust levels 1 to 4 (by leaf area with spots).
- **Role:**
  - **Sealed field test:** healthy vs rust (rust levels 1 to 4 counted as rust). It was not used for training or for setting any threshold before the test. Used: 787 healthy, 598 rust.
  - **Out-of-scope test:** red spider mite photos, a pest the model was never taught. The right answer is "not sure". Used: 167.
  - **Learning-loop simulation:** labelled RoCoLe photos stand in for officer labels, to show how the model adapts. The labels come from the dataset authors, not from an extension officer.
- **What it does not cover:**
  - Arabica. RoCoLe is robusta. Leaf rust looks similar on both, but leaf shape, size and colour differ. It is a stand-in for Kenyan field photos, not a Kenyan test.
  - Kenya, or the relay farmers' phones.
  - Leaf miner, Cercospora and Phoma: only healthy and rust can be scored. The other three classes have no field test.
  - Independent farms: all photos come from one field, and each plant gives four photos. Photos of the same plant are alike, so the learning-loop gain is likely larger here than it would be across many farms.
  - Berries, coffee berry disease.

## 5. Demo samples (`samples/`)

- Seven RoCoLe images copied into the app for demonstration: three healthy, one each of rust levels 1, 2 and 3, and one red spider mite. Each file's source, licence and dataset label are in `samples/manifest.json`.
- They are part of the sealed field test set, so a demo with them is not a new test.
- The app marks results from these photos as sample photos, and the officer review screen shows the dataset label next to them.

## 6. Other data the tool depends on

- **ImageNet (pretraining of the image backbone).** The backbone is timm `mobilenetv3_large_100.ra_in1k`, with weights released under Apache-2.0. Those weights were trained on ImageNet-1k, whose own terms limit the images to non-commercial research. We use the weights as released and do not redistribute ImageNet images. ImageNet has very few coffee leaves; the backbone is generic.
- **Synthetic data, labelled as such.** The co-op early-warning screen has a button that adds six demo villages, each marked "(synthetic)". The village simulation in `results/RESULTS.md` (finding 4) also uses synthetic villages; only the classifier error rates in it are measured.
- **Language models (not training data).** NLLB-200, MMS TTS and MMS speech recognition were used to make and check the Swahili and Kikuyu audio. They are described with their licences in `docs/LANGUAGE.md`.
- **Advice text.** The fixed answers are written from Kenyan extension material, mainly the Kenya Coffee Sustainability Manual (review led by KALRO Coffee Research Institute). Sources are cited per answer in `answers.json`.

## 7. What the data as a whole does not cover

This is the list that matters most for how far the results can be trusted.

1. **No photo from a Kenyan farm taken the way the tool will be used.** The Kenyan photos (JMuBEN, JMuBEN2) are cropped close-ups; the field photos (RoCoLe) are from Ecuador and robusta. The first real test would need officer-labelled photos from relay farmers' phones in Kirinyaga, Nyeri or Murang'a.
2. **Lab-to-field gap, measured.** On the sealed field test the lab-trained model was almost always wrong while reporting high confidence; the familiarity check turns those cases into "not sure" (`results/RESULTS.md`, findings 1 and 2).
3. **Only five leaf classes.** Kenya's two most costly coffee diseases are coffee berry disease and leaf rust (KALRO-led manual). Coffee berry disease shows on berries and is not in any dataset here. Bacterial blight, Fusarium, nutrient shortage, drought scorch, antestia, thrips, scales and berry borer are not covered either. The non-AI checklist asks about the berry problems and refers them to the officer.
4. **No berries, roots, whole trees or whole plots.**
5. **Few cameras.** One digital camera (JMuBEN, JMuBEN2), five phones (BRACOL), one phone (RoCoLe). The relay farmers' own phones are not represented.
6. **Little variation in light and leaf state.** Wet leaves, dust, deep shade, glare and very young or very old leaves are rare or absent.
7. **Severity and early stages.** The model gives one label per photo. It does not measure how much of the leaf is affected, and very early lesions may not be visible at phone resolution.
8. **One answer per leaf.** Leaves with two problems at once are labelled by their main problem only.
9. **Season and variety.** None of the datasets records coffee variety (for example SL28, Ruiru 11, Batian) or season per image.
