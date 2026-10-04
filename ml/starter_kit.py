"""Starter kit: try a better 'learning step' (how the phone uses an officer's few labels) without touching the app.

Run from kahawa-check/:
    ../.venv/bin/python ml/starter_kit.py                 # baseline vs my_method on the DEV part (use this while trying ideas)
    ../.venv/bin/python ml/starter_kit.py --final         # ONE run on the SEALED part, after you have picked your method

What is simulated: a model meeting a NEW REGION's photo style. The base is the LAB-ONLY model (trained on lab photos
only; it has never seen a field photo), and the RoCoLe field photos play the new region. An extension officer labels
k photos from the "not sure" queue; RoCoLe's expert labels (healthy / rust) stand in for the officer. The phone also
holds the other, unlabelled field photos. (The app itself ships a model trained on lab + field photos; when it meets
a new region, e.g. Kenyan farms, the same learning step runs on top of it. This kit uses the lab-only base because
every field photo here is a "new region" photo for it.)

Data (already computed, nothing to download):
  ../data_work/embeddings.npz   E [N,1280]  raw MobileNetV3 embeddings for every row of results/index.csv
  ../data_work/standardisation_labonly.npz  mu, sd  -> Z = (E - mu) / sd  is exactly what model/backbone.onnx outputs
                                (the shipped model uses the same standardisation)
  model/head_labonly.json, model/reference_labonly.bin   the lab-only head, threshold, familiarity cutoff and 1,000
                                stored photos (model/update_demo_50_labonly.json is a 50-label update of this head)

Rules (so the result can be reported):
  * Pick ideas on DEV only. Run --final once, on SEALED, with the method you chose. Every run is logged to
    results/starter_runs.jsonl.
  * The 60 human-baseline photos and the 7 demo samples are never in DEV.
  * To ship a method, it must be expressible on the phone: a head (W, b) + extra stored rows for the familiarity check,
    optionally after a fixed linear transform of Z (that can be folded into W, b and the stored rows). Anything else
    needs a JavaScript change in lib/kahawa-core.js and app.js - talk to the team first.
"""
import os, sys, json, csv, argparse
import numpy as np
from scipy.special import softmax

HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(HERE)
WORK = os.path.join(os.path.dirname(REPO), 'data_work'); RAW = os.path.join(os.path.dirname(REPO), 'data_raw')
sys.path.insert(0, HERE)
from train_eval import adapt, knn_dist, unit, CLASSES, CI  # the exact functions behind the published numbers

KS = [0, 10, 20, 50]          # officer labels
SEEDS = range(5)
DEV_SHARE = 0.30


# ----------------------------------------------------------------------------- data
def load_all():
    rows = list(csv.DictReader(open(os.path.join(REPO, 'results', 'index.csv'))))
    E = np.load(os.path.join(WORK, 'embeddings.npz'))['E']
    st = np.load(os.path.join(WORK, 'standardisation_labonly.npz'))
    Z = ((E - st['mu']) / st['sd']).astype(np.float64)
    head = json.load(open(os.path.join(REPO, 'model', 'head_labonly.json')))  # lab-only base (new-region simulation)
    ref = head['ood']['reference']; n, D = ref['n'], ref['dim']
    raw = open(os.path.join(REPO, 'model', ref['file']), 'rb').read()
    R = np.frombuffer(raw[:n * D], np.int8).reshape(n, D).astype(np.float64) * np.frombuffer(raw[n * D:], '<f4')[:, None]
    base = dict(W=np.array(head['W']), b=np.array(head['b']), T=head['temperature'], thr=head['threshold'],
                cut=head['ood']['cutoff'], k=head['ood']['k'], lam=head['prior_strength'], ref=unit(R))
    return rows, Z, base


def splits(rows):
    """DEV / SEALED split of the RoCoLe field photos (healthy + rust), and of the out-of-scope mite photos."""
    name = lambda r: os.path.basename(r['path'])
    keep_out = {s['original_file'] for s in json.load(open(os.path.join(REPO, 'samples', 'manifest.json')))['samples']}
    kp = os.path.join(REPO, 'baseline', 'key.json')
    hb = set()
    if os.path.exists(kp):
        key = json.load(open(kp))
        hb = {v['original_file'] for v in key.get('photos', {}).values() if v.get('original_file')}
        assert len(hb) == key['meta']['n'], 'could not read the 60 human-baseline photos from baseline/key.json'
    field = [i for i, r in enumerate(rows) if r['source'] == 'RoCoLe' and r['label'] in ('healthy', 'rust') and name(r) not in keep_out]
    mite = [i for i, r in enumerate(rows) if r['source'] == 'RoCoLe' and r['label'] == 'mite']
    rng = np.random.default_rng(424242)
    free = [i for i in field if name(rows[i]) not in hb]
    rng.shuffle(free)
    nd = int(DEV_SHARE * len(field))
    dev, sealed = np.array(free[:nd]), np.array(free[nd:] + [i for i in field if name(rows[i]) in hb])
    m = np.array(mite); rng.shuffle(m)
    return dict(dev=dev, sealed=sealed, mite_dev=m[:len(m) // 2], mite_sealed=m[len(m) // 2:])


# ----------------------------------------------------------------------------- methods
def baseline_method(base, Z_lab, y_lab, Z_unlab):
    """What the app does today: refit the head pulled toward the base head; labelled photos join the stored set."""
    W, b = adapt(Z_lab, y_lab, base['W'], base['b'], base['T'], base['lam']) if len(y_lab) else (base['W'], base['b'])
    ref = np.vstack([base['ref'], unit(Z_lab)]) if len(y_lab) else base['ref']

    def predict(Z):
        P = softmax((Z @ W.T + b) / base['T'], axis=1)
        d = knn_dist(unit(Z), ref, base['k'])
        return P, d
    return predict


def my_method(base, Z_lab, y_lab, Z_unlab):
    """YOUR IDEA GOES HERE. Same inputs and output as baseline_method.
      base     : dict with W [5,1280], b [5], T, thr, cut, k, lam, ref (stored rows, L2-normalised)
      Z_lab    : [k,1280] officer-labelled field photos (standardised embeddings); y_lab: class indices (0 healthy, 1 rust)
      Z_unlab  : [m,1280] other field photos on the phone, no labels (e.g. for feature alignment or pseudo-labels)
    Return predict(Z) -> (P [N,5] class probabilities, d [N] familiarity distance; d > base['cut'] means 'not sure').
    Ideas: augment Z_lab (use embed_images() below for real image augmentations), align field vs lab feature
    statistics with Z_unlab (mean/variance, CORAL), pseudo-label confident Z_unlab, prototype/kNN head, a different
    pull strength, a separate 'unfamiliar' rule. Start by copying baseline_method."""
    return baseline_method(base, Z_lab, y_lab, Z_unlab)


# ----------------------------------------------------------------------------- evaluation
def evaluate(method, Z, y, idx, mite_idx, base, seeds=SEEDS, ks=KS):
    out = {}
    for k in ks:
        acc = {m: [] for m in ['answered', 'acc_answered', 'hvp_answered', 'rust_named', 'healthy_flagged', 'mite_not_sure']}
        for s in seeds:
            r = np.random.default_rng(1000 + s); perm = r.permutation(idx)
            pool, test = perm[:len(perm) // 2], perm[len(perm) // 2:]
            lab, unl = pool[:k], pool[k:]
            predict = method(base, Z[lab], y[lab], Z[unl])
            P, d = predict(Z[test]); pr = P.argmax(1); yt = y[test]
            ans = (P.max(1) >= base['thr']) & (d <= base['cut'])
            acc['answered'].append(ans.mean())
            acc['acc_answered'].append((pr[ans] == yt[ans]).mean() if ans.any() else np.nan)
            acc['hvp_answered'].append(((pr[ans] == 0) == (yt[ans] == 0)).mean() if ans.any() else np.nan)
            rust = yt == CI['rust']; hl = yt == CI['healthy']
            acc['rust_named'].append(((pr == CI['rust']) & ans & rust).sum() / max(1, rust.sum()))
            acc['healthy_flagged'].append(((pr != CI['healthy']) & ans & hl).sum() / max(1, hl.sum()))
            Pm, dm = predict(Z[mite_idx])
            acc['mite_not_sure'].append(1 - ((Pm.max(1) >= base['thr']) & (dm <= base['cut'])).mean())
        out[k] = {m: float(np.nanmean(v)) for m, v in acc.items()}
    return out


def show(name, res):
    print(f'\n{name}')
    print(f"{'labels':>6} {'answered':>9} {'right(ans)':>11} {'sick?(ans)':>11} {'rust named':>11} {'healthy flagged':>16} {'mite not sure':>14}")
    for k, v in res.items():
        f = lambda x: '   -' if np.isnan(x) else f'{100 * x:5.1f}%'
        print(f"{k:>6} {f(v['answered']):>9} {f(v['acc_answered']):>11} {f(v['hvp_answered']):>11} {f(v['rust_named']):>11} "
              f"{f(v['healthy_flagged']):>16} {f(v['mite_not_sure']):>14}")


# ----------------------------------------------------------------------------- optional: real image augmentation
def embed_images(paths, augment=None, batch=64):
    """Embed images (paths relative to ../data_raw, as in results/index.csv) with the frozen backbone, standardised
    exactly like the phone. augment: optional function PIL.Image -> PIL.Image applied before the standard resize/crop.
    About a minute per 1,000 images on the Mac GPU."""
    import torch, timm
    from PIL import Image
    meta = json.load(open(os.path.join(REPO, 'model', 'backbone_meta.json')))
    st = np.load(os.path.join(WORK, 'standardisation_labonly.npz'))
    dev = 'mps' if torch.backends.mps.is_available() else 'cpu'
    m = timm.create_model(meta['backbone'], pretrained=True, num_classes=0).eval().to(dev)
    mean = np.array(meta['mean'], np.float32)[:, None, None]; std = np.array(meta['std'], np.float32)[:, None, None]

    def prep(p):
        im = Image.open(os.path.join(RAW, p)).convert('RGB')
        if augment: im = augment(im)
        w, h = im.size; s = meta['resize_shorter'] / min(w, h)
        im = im.resize((round(w * s), round(h * s)), Image.BILINEAR); w, h = im.size; c = meta['input_size']
        l, t = (w - c) // 2, (h - c) // 2
        a = np.asarray(im.crop((l, t, l + c, t + c)), np.float32).transpose(2, 0, 1) / 255.0
        return (a - mean) / std
    out = []
    for i in range(0, len(paths), batch):
        x = torch.from_numpy(np.stack([prep(p) for p in paths[i:i + batch]])).to(dev)
        with torch.no_grad():
            out.append(m(x).float().cpu().numpy())
    return (np.concatenate(out) - st['mu']) / st['sd']


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--final', action='store_true'); a = ap.parse_args()
    rows, Z, base = load_all()
    y = np.array([CI.get(r['label'], -1) for r in rows])
    S = splits(rows)
    part, mpart = ('sealed', 'mite_sealed') if a.final else ('dev', 'mite_dev')
    if a.final:
        print('FINAL RUN on the SEALED part. Do this once, after choosing your method on DEV.')
    print(f'{part}: {len(S[part])} field photos (half are the pool the officer labels from, half are scored), '
          f'{len(S[mpart])} mite photos; {len(list(SEEDS))} random splits.')
    rb = evaluate(baseline_method, Z, y, S[part], S[mpart], base); show('baseline (the app\'s learning step, lab-only base)', rb)
    rm = evaluate(my_method, Z, y, S[part], S[mpart], base); show('my_method', rm)
    import datetime
    with open(os.path.join(REPO, 'results', 'starter_runs.jsonl'), 'a') as f:
        f.write(json.dumps({'when': datetime.datetime.now().isoformat(timespec='seconds'), 'part': part,
                            'baseline': rb, 'my_method': rm}) + '\n')
