# Starter kit: improve the on-phone learning step

**Goal.** When the extension officer labels a few "not sure" field photos, the phone refits a small head and adds the labelled photos to its stored set. Make that step get more out of the same labels: more photos answered, more answers right, rust named more often, fewer healthy leaves flagged, and still "not sure" on a pest it was never taught.

**Status.** The submitted app uses the learning step described in the README. This kit is for improving it after the challenge.

## Setup (one time)

1. Clone the code into a new folder, for example `~/kahawa`:
   ```bash
   mkdir -p ~/kahawa && cd ~/kahawa && git clone https://github.com/git-lsd/majani-relay.git kahawa-check
   ```
   The repo is now `majani-relay` (earlier `kahawa-check`); cloning into a folder called `kahawa-check` keeps the paths below working.
2. Make a Python environment next to it:
   ```bash
   cd ~/kahawa && python3 -m venv .venv && .venv/bin/pip install -r kahawa-check/ml/requirements.txt
   ```
3. Build the precomputed files: download the raw datasets into `~/kahawa/data_raw/` (links in [DATA_CARD.md](DATA_CARD.md)), then, from `~/kahawa/kahawa-check`, run `../.venv/bin/python ml/prepare_embed.py` (writes `../data_work/embeddings.npz`) and `../.venv/bin/python ml/train_eval.py` (writes `../data_work/standardisation_labonly.npz` and rebuilds the published results).
4. Run it from `~/kahawa/kahawa-check` with `../.venv/bin/python ml/starter_kit.py`.

The precomputed files hold image descriptions only (MobileNetV3, for all ~10,000 images). `embed_images()` (real image augmentation) also needs the raw photos in `../data_raw/`. Work on a branch and open a pull request when a method is ready.

## Run it

From the folder that holds `kahawa-check` and `.venv`:
```bash
cd kahawa-check && ../.venv/bin/python ml/starter_kit.py
```

It takes about 4 seconds. It prints two tables: `baseline` (what the app does today) and `my_method` (your function, which starts as a copy of the baseline). Edit `my_method()` in [`ml/starter_kit.py`](../ml/starter_kit.py) and rerun.

Current baseline on the dev part, starting from the lab-only model with the Ecuador field photos treated as a new region (so it starts near 0% answered; the shipped model's results are in the README). 5 random splits; copied by script from the latest run in `results/starter_runs.jsonl`, 2026-10-03 23:58, using the app's familiarity rule including the nearest-officer-photo check:

| Officer labels | Answered | Right (of answered) | Rust named (of rust photos) | Healthy flagged | Mite still "not sure" |
|---|---|---|---|---|---|
| 0 | 0.2% | – | 0% | 0.3% | 100% |
| 10 | 83% | 73% | 54% | 25% | 37% |
| 20 | 89% | 80% | 56% | 14% | 25% |
| 50 | 93% | 84% | 62% | 8% | 20% |

## What you get

- `Z`: standardised MobileNetV3 embeddings (1,280 numbers per photo) for every image, exactly what the phone's model outputs. No GPU needed.
- `my_method(base, Z_lab, y_lab, Z_unlab)` returns `predict(Z) -> (P, d)`: class probabilities and the familiarity distance. A photo is answered only if `P.max() >= base['thr']` and it is familiar: `d <= base['cut']`, or (the app's second check) its nearest officer-labelled photo is within `base['c1']` (return that distance as an optional third output).
- `Z_unlab`: the other field photos on the phone, unlabelled. Using them is realistic: they are the "not sure" queue.
- `embed_images(paths, augment=...)`: real image augmentations through the frozen backbone (about a minute per 1,000 images on a laptop GPU).

## Data and rules

- Field photos: RoCoLe (Ecuador, robusta, leaves on the plant), healthy and rust, with expert labels standing in for the officer. Mite photos are the "never taught" test.
- **Dev part** (30% of field photos, half the mite photos): use it for every idea. **Sealed part** (the rest, including the 60 human-baseline photos): run `--final` once, when you have chosen. Every run is appended to `results/starter_runs.jsonl`.
- To ship a method, it must fit the phone: a head (`W`, `b`) plus extra stored rows, optionally after a fixed linear transform of the embedding (that can be folded into `W`, `b` and the rows). Anything else needs JavaScript changes in `lib/kahawa-core.js`, followed by a rerun of every published number with the scripts in the README's Run it section.

## Ideas (your judgment beats this list)

1. **Use the unlabelled field photos.** Align field and lab feature statistics (mean/variance shift, CORAL) before the head and the familiarity check; or pseudo-label confident field photos.
2. **Augment the officer's few labels.** Flips, crops and colour changes through `embed_images()`.
3. **A different head for few labels.** Prototype / nearest-class-mean, or kNN on the stored rows, or a different pull strength toward the shipped head.
4. **Keep "not sure" on new pests.** The mite rate drops from 100% to 20% after 50 labels (table above); a rule that compares a photo with the labelled field photos of each class (not just "is it familiar?") may hold it up.
