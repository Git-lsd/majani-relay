"""External test on East African farm photos: the Uganda coffee-leaf dataset (Soroti University).

Dataset: "A Machine Learning Dataset for Classification of Common Coffee Leaf Diseases in Uganda", Mendeley Data
k36wnd6knb version 1 (doi 10.17632/k36wnd6knb.1), CC BY 4.0. Healthy / coffee leaf rust / Phoma, 256x256 JPEG, with
rotated, flipped and brightness-adjusted copies mixed in (dataset description) and some empty files.

Stages
  --download   curl the files listed by the Mendeley public API into ../data_raw/uganda/ (outside the repo).
  prepare      (cached in ../data_work/uganda_embeddings.npz; rerun with --reprepare)
               1. drop empty, missing, unreadable or checksum-mismatched files;
               2. group augmented copies: similarity = max of (a) 32x32 grey-pixel correlation, best of the 8
                  rotations/flips, (b) 16x16 colour-pixel correlation, best of the 8 rotations/flips, (c) cosine of the
                  standardised backbone embeddings. Images whose near-identical twin (similarity >= 0.95) sits in a
                  different class folder are dropped (label unknown). Average-linkage clusters at similarity 0.85 are
                  the split units; a copy group is a split unit restricted to one class;
               3. embed with the frozen backbone exactly as the phone does (resize shorter side to 256, centre-crop
                  224, ImageNet mean/sd, then the lab-only standardisation that model/backbone.onnx bakes in).
  evaluate     (default) whatever model/head.json + reference.bin are current (5 or 6 classes; a prediction of class
               'other' counts as routed to the officer) and the lab-only model (head_labonly.json); then the officer
               learning loop on Ugandan photos (same on-phone refit as the app: adapt, unit, knn_dist from train_eval).
               Familiarity in the loop is the app's rule: the k nearest of [stored + officer-labelled rows] within
               ood.cutoff, OR (head.json ood.local_nearest_cutoff, results/familiarity_rule.json) the single nearest
               officer-labelled row within ood.local_nearest_cutoff. The previous rule (k nearest only) is reported
               next to it (learning_loop.rule_comparison). Note: that cutoff was chosen on 40% of the Ugandan copy
               clusters (ml/eval_familiarity_rule.py, DEV part); the loop here uses all Ugandan photos, so it includes
               those clusters. results/familiarity_rule.json has the numbers on the other 60% only.

Every copy group counts once (each of its photos has weight 1/size), so repeated copies of one leaf do not inflate
the counts; 'all_images_unweighted' gives the plain per-photo numbers too.

Writes results/uganda_external.json and results/figs/uganda_learning_loop.png.
Run: ../.venv/bin/python ml/eval_uganda.py            (add --download on a fresh machine, --reprepare to regroup)
"""
import os, sys, csv, json, hashlib, argparse, subprocess, time
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from PIL import Image
from scipy.special import softmax
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
ROOT = os.path.dirname(REPO)
RAW = os.path.join(ROOT, 'data_raw', 'uganda')
WORK = os.path.join(ROOT, 'data_work')
RES = os.path.join(REPO, 'results')
FIG = os.path.join(RES, 'figs')
MODEL = os.path.join(REPO, 'model')
EMB_NPZ = os.path.join(WORK, 'uganda_embeddings.npz')
PREP_JSON = os.path.join(WORK, 'uganda_prepare.json')
OUT_JSON = os.path.join(RES, 'uganda_external.json')

DATASET = {'name': 'A Machine Learning Dataset for Classification of Common Coffee Leaf Diseases in Uganda',
           'mendeley_id': 'k36wnd6knb', 'version': 1, 'doi': '10.17632/k36wnd6knb.1',
           'url': 'https://data.mendeley.com/datasets/k36wnd6knb/1', 'license': 'CC BY 4.0',
           'institution': 'Soroti University (Uganda)', 'published': '2025-02-07'}
API = 'https://data.mendeley.com/public-api/datasets/k36wnd6knb'
FOLDER_CLASS = {'Health leaves': 'healthy', 'leaf rust': 'rust', 'phoma': 'phoma'}
UG_CLASSES = ['healthy', 'rust', 'phoma']
CONFLICT_SIM = 0.95       # near-identical images in two class folders: label unknown, dropped
GROUP_SIM = 0.85          # average-linkage cut for copy groups / split units
COARSE_SIM = 0.70         # coarser grouping, for a leakage sensitivity check of the learning loop
KS = [0, 10, 20, 50, 100]
SEEDS = 5


# ----------------------------------------------------------------------------------------------- download
def download():
    os.makedirs(RAW, exist_ok=True)
    meta_p = os.path.join(RAW, 'dataset.json')
    subprocess.run(['curl', '-sS', '-m', '120', '-o', meta_p, API], check=True)  # urllib gets 403; curl works
    folders = json.loads(subprocess.run(['curl', '-sS', '-m', '120', API + '/folders/1'], check=True,
                                        capture_output=True, text=True).stdout)
    fid = {f['id']: FOLDER_CLASS[f['name']] for f in folders if f['name'] in FOLDER_CLASS}
    d = json.load(open(meta_p))
    rows = []
    for f in d['files']:
        cd = f.get('content_details') or {}
        rows.append({'cls': fid.get(f['folder_id'], '?'), 'filename': f['filename'], 'id': f['id'],
                     'size': f['size'], 'sha256': cd.get('sha256_hash', ''), 'url': cd.get('download_url', '')})
    with open(os.path.join(RAW, 'manifest.tsv'), 'w') as fh:
        fh.write('\t'.join(rows[0]) + '\n')
        for r in rows:
            fh.write('\t'.join(str(r[k]) for k in rows[0]) + '\n')

    def get(r):
        p = _path(r)
        if int(r['size']) == 0 or not r['url'] or (os.path.exists(p) and os.path.getsize(p) == int(r['size'])):
            return
        os.makedirs(os.path.dirname(p), exist_ok=True)
        subprocess.run(['curl', '-sSL', '--retry', '4', '-m', '60', '-o', p, r['url']], check=False)
    with ThreadPoolExecutor(24) as ex:
        list(ex.map(get, rows))
    print('downloaded', sum(os.path.exists(_path(r)) for r in rows), 'of', len(rows), 'listed files')


def _path(r):
    return os.path.join(RAW, 'images', r['cls'], f"{r['id']}__{r['filename']}")


# ----------------------------------------------------------------------------------------------- prepare
def _dihedral_feats(im, s, grey):
    a0 = np.asarray(im.convert('L' if grey else 'RGB').resize((s, s), Image.BILINEAR), np.float32)
    out = []
    for k in range(4):
        for flip in (False, True):
            a = np.rot90(a0, k); a = a[:, ::-1] if flip else a
            v = (a - a.mean((0, 1))).ravel()   # mean removed per channel: brightness shifts do not matter
            out.append(v / (np.linalg.norm(v) + 1e-6))
    return np.stack(out)


def _dihedral_sim(F):
    """max over the 8 rotations/flips of the correlation between two images' pixel vectors."""
    return np.max(np.stack([F[:, 0] @ F[:, t].T for t in range(8)]), 0)


def embed(images):
    """Frozen backbone, same preprocessing as the phone (ml/starter_kit.py embed_images, on in-memory images).
    Returns the RAW embeddings E; Z = (E - mu) / sd with the lab-only standardisation is what backbone.onnx outputs."""
    import torch, timm
    meta = json.load(open(os.path.join(MODEL, 'backbone_meta.json')))
    dev = 'mps' if torch.backends.mps.is_available() else 'cpu'
    m = timm.create_model(meta['backbone'], pretrained=True, num_classes=0).eval().to(dev)
    mean = np.array(meta['mean'], np.float32)[:, None, None]; std = np.array(meta['std'], np.float32)[:, None, None]

    def prep(im):
        w, h = im.size; s = meta['resize_shorter'] / min(w, h)
        im = im.resize((round(w * s), round(h * s)), Image.BILINEAR); w, h = im.size; c = meta['input_size']
        l, t = (w - c) // 2, (h - c) // 2
        a = np.asarray(im.crop((l, t, l + c, t + c)), np.float32).transpose(2, 0, 1) / 255.0
        return (a - mean) / std
    out = []
    for i in range(0, len(images), 64):
        x = torch.from_numpy(np.stack([prep(im) for im in images[i:i + 64]])).to(dev)
        with torch.no_grad():
            out.append(m(x).float().cpu().numpy())
    return np.concatenate(out), meta


def standardisation():
    st = np.load(os.path.join(WORK, 'standardisation_labonly.npz'))
    p2 = os.path.join(WORK, 'standardisation.npz')
    if os.path.exists(p2):
        s2 = np.load(p2)
        assert np.array_equal(s2['mu'], st['mu']) and np.array_equal(s2['sd'], st['sd']), 'standardisation files differ'
    return st['mu'], st['sd']


def unit_(X):
    return X / np.linalg.norm(X, axis=1, keepdims=True)


def prepare():
    man = os.path.join(RAW, 'manifest.tsv')
    if not os.path.exists(man):
        raise SystemExit(f'{man} not found: run with --download first')
    rows = list(csv.DictReader(open(man), delimiter='\t'))
    listed = {c: sum(r['cls'] == c for r in rows) for c in UG_CLASSES}
    dropped = {'empty_file': 0, 'missing': 0, 'checksum_mismatch': 0, 'unreadable': 0}
    keep, images, sizes = [], [], {}
    for r in rows:
        p = _path(r)
        if int(r['size']) == 0:
            dropped['empty_file'] += 1; continue
        if not os.path.exists(p) or os.path.getsize(p) == 0:
            dropped['missing'] += 1; continue
        b = open(p, 'rb').read()
        if r['sha256'] and hashlib.sha256(b).hexdigest() != r['sha256']:
            dropped['checksum_mismatch'] += 1; continue
        try:
            im = Image.open(p); im.load(); im = im.convert('RGB')
        except Exception:
            dropped['unreadable'] += 1; continue
        sizes[f'{im.size[0]}x{im.size[1]}'] = sizes.get(f'{im.size[0]}x{im.size[1]}', 0) + 1
        r = dict(r); r['sha_file'] = hashlib.sha256(b).hexdigest(); keep.append(r); images.append(im)
    print('readable images:', len(keep), 'dropped:', dropped, flush=True)
    t0 = time.time()
    E, meta = embed(images)
    print(f'embedded {len(E)} images in {time.time() - t0:.0f} s', flush=True)
    mu, sd = standardisation()
    Zn = unit_((E - mu) / sd)
    S = np.maximum.reduce([_dihedral_sim(np.stack([_dihedral_feats(im, 32, True) for im in images])),
                           _dihedral_sim(np.stack([_dihedral_feats(im, 16, False) for im in images])),
                           Zn @ Zn.T])
    np.fill_diagonal(S, 1.0)
    cls = np.array([r['cls'] for r in keep])
    n_identical = len(keep) - len({r['sha_file'] for r in keep})
    # label conflicts: a near-identical twin in another class folder
    cross = (S >= CONFLICT_SIM) & (cls[:, None] != cls[None, :])
    conflict = cross.any(1)
    conflict_pairs = {f'{a}-{b}': int(((cls[:, None] == a) & (cls[None, :] == b) & cross).any(1).sum())
                      for a in UG_CLASSES for b in UG_CLASSES if a != b}
    ok = ~conflict
    keep = [r for r, o in zip(keep, ok) if o]; E = E[ok]; S = S[np.ix_(ok, ok)]; cls = cls[ok]
    D = np.clip(1 - S, 0, 2); np.fill_diagonal(D, 0)
    L = linkage(squareform(D, checks=False), method='average')
    unit_fine = fcluster(L, 1 - GROUP_SIM, criterion='distance')
    unit_coarse = fcluster(L, 1 - COARSE_SIM, criterion='distance')
    group = np.array([f'{c}-{u}' for c, u in zip(cls, unit_fine)])
    _, gsz = np.unique(group, return_counts=True)
    stats = {'listed_files': len(rows), 'listed_by_class': listed, 'dropped': dropped,
             'readable': int(len(ok)), 'byte_identical_extra_copies': int(n_identical),
             'dropped_label_conflict': int(conflict.sum()), 'label_conflict_by_folder_pair': conflict_pairs,
             'used': int(ok.sum()), 'used_by_class': {c: int((cls == c).sum()) for c in UG_CLASSES},
             'copy_groups': int(len(gsz)),
             'copy_groups_by_class': {c: int(len(set(group[cls == c]))) for c in UG_CLASSES},
             'group_size': {'singletons': int((gsz == 1).sum()), 'median': float(np.median(gsz)),
                            'p90': float(np.percentile(gsz, 90)), 'max': int(gsz.max()),
                            'counts': {str(s): int(n) for s, n in zip(*np.unique(gsz, return_counts=True))}},
             'split_units': int(len(np.unique(unit_fine))), 'split_units_coarse': int(len(np.unique(unit_coarse))),
             'image_sizes': sizes,
             'grouping': (f'similarity = max(32x32 grey-pixel correlation over 8 rotations/flips, 16x16 colour-pixel '
                          f'correlation over 8 rotations/flips, cosine of standardised embeddings); average-linkage '
                          f'clusters at similarity {GROUP_SIM} = split units; copy group = split unit x class; '
                          f'images with a twin (similarity >= {CONFLICT_SIM}) in another class folder dropped. '
                          f'Coarse units (similarity {COARSE_SIM}) for a sensitivity check.'),
             'preprocessing': f"resize shorter side to {meta['resize_shorter']} (bilinear), centre-crop "
                              f"{meta['input_size']}, ImageNet mean/sd, {meta['backbone']}, lab-only standardisation"}
    # the phone runs model/backbone.onnx (standardisation baked in): check it gives the same embeddings
    stats['onnx_check'] = onnx_check(images, ok, E, mu, sd)
    np.savez_compressed(EMB_NPZ, E=E.astype(np.float32), label=cls, group=group, unit=unit_fine,
                        unit_coarse=unit_coarse, filename=np.array([r['filename'] for r in keep]),
                        file_id=np.array([r['id'] for r in keep]))
    with open(os.path.join(WORK, 'uganda_index.csv'), 'w', newline='') as fh:
        w = csv.writer(fh); w.writerow(['class', 'filename', 'file_id', 'group', 'unit', 'unit_coarse'])
        for r, g, u, uc in zip(keep, group, unit_fine, unit_coarse):
            w.writerow([r['cls'], r['filename'], r['id'], g, u, uc])
    json.dump(stats, open(PREP_JSON, 'w'), indent=1)
    print('prepared:', json.dumps({k: stats[k] for k in ['used', 'copy_groups', 'copy_groups_by_class',
                                                         'dropped_label_conflict']}), flush=True)


def onnx_check(images, ok, E, mu, sd, n=48):
    try:
        import onnxruntime as ort
    except ImportError:
        return {'skipped': 'onnxruntime not installed'}
    meta = json.load(open(os.path.join(MODEL, 'backbone_meta.json')))
    sess = ort.InferenceSession(os.path.join(MODEL, 'backbone.onnx'), providers=['CPUExecutionProvider'])
    name = sess.get_inputs()[0].name
    idx = np.where(ok)[0][np.linspace(0, ok.sum() - 1, n).astype(int)]
    mean = np.array(meta['mean'], np.float32)[:, None, None]; std = np.array(meta['std'], np.float32)[:, None, None]
    xs = []
    for i in idx:
        im = images[i]; w, h = im.size; s = meta['resize_shorter'] / min(w, h)
        im = im.resize((round(w * s), round(h * s)), Image.BILINEAR); w, h = im.size; c = meta['input_size']
        l, t = (w - c) // 2, (h - c) // 2
        xs.append((np.asarray(im.crop((l, t, l + c, t + c)), np.float32).transpose(2, 0, 1) / 255.0 - mean) / std)
    Zo = np.concatenate([sess.run(None, {name: x[None]})[0] for x in xs])
    pos = np.searchsorted(np.where(ok)[0], idx)
    Zt = (E[pos] - mu) / sd
    return {'n': int(n), 'max_abs_diff_standardised': float(np.abs(Zo - Zt).max()),
            'min_cosine': float((unit_(Zo) * unit_(Zt)).sum(1).min())}


# ----------------------------------------------------------------------------------------------- evaluate
def load_model(head_file):
    h = json.load(open(os.path.join(MODEL, head_file)))
    ref = h['ood']['reference']; n, dim = ref['n'], ref['dim']
    buf = open(os.path.join(MODEL, ref['file']), 'rb').read()
    q = np.frombuffer(buf[:n * dim], np.int8).reshape(n, dim).astype(np.float32)
    sc = np.frombuffer(buf[n * dim:n * dim + 4 * n], '<f4')
    return {'file': head_file, 'version': h['version'], 'classes': list(h['classes']),
            'W': np.array(h['W'], np.float64), 'b': np.array(h['b'], np.float64), 'T': float(h['temperature']),
            'thr': float(h['threshold']), 'cut': float(h['ood']['cutoff']), 'k': int(h['ood']['k']),
            'c1': (float(h['ood']['local_nearest_cutoff']) if h['ood'].get('local_nearest_cutoff') is not None else None),
            'Rn': unit_(q * sc[:, None]).astype(np.float64), 'lam': float(h.get('prior_strength', 0.3))}


def decide(m, Z, Zn, W=None, b=None, R=None, local=None, c1=None):
    """The app's rule: answer only if confident AND familiar AND the class is not 'other'.
    R: stored rows (shipped reference + officer-labelled rows). Familiar = k nearest of R within the cutoff, OR (when
    c1 is given and officer rows exist) the single nearest officer-labelled row (local) within c1."""
    W = m['W'] if W is None else W; b = m['b'] if b is None else b; R = m['Rn'] if R is None else R
    P = softmax((Z @ W.T + b) / m['T'], axis=1)
    pred = P.argmax(1)
    d = knn_dist(Zn, R, m['k'])
    conf = P.max(1) >= m['thr']; fam = d <= m['cut']
    if c1 is not None and local is not None and len(local):
        fam = fam | (knn_dist(Zn, local, 1) <= c1)
    other = np.array([m['classes'][i] == 'other' for i in pred])
    ans = conf & fam & ~other
    return {'pred': pred, 'ans': ans, 'low_conf': ~conf & fam, 'unfamiliar': ~fam, 'other': conf & fam & other,
            'P': P, 'd': d}


def summarise(m, dec, y_name, w):
    """Shares of photos (weights w: 1/copy-group size for group-aware numbers, 1 for plain counts)."""
    cls = m['classes']; pred = np.array(cls)[dec['pred']]; ans = dec['ans']
    ws = lambda mask, base: float(w[mask & base].sum() / w[base].sum()) if w[base].sum() > 0 else float('nan')
    allm = np.ones(len(w), bool); right = ans & (pred == y_name)
    hl = y_name == 'healthy'; sick = ~hl
    out = {'n_photos': int(len(w)), 'n_effective': float(w.sum()),
           'answered': ws(ans, allm), 'correct_of_answered': ws(right, ans),
           'correct_of_all': ws(right, allm), 'forced_correct': ws(pred == y_name, allm),
           'rust_named': ws(ans & (pred == 'rust'), y_name == 'rust'),
           'phoma_named': ws(ans & (pred == 'phoma'), y_name == 'phoma'),
           'healthy_flagged': ws(ans & (pred != 'healthy'), hl),
           'sick_called_a_problem': ws(ans & (pred != 'healthy'), sick),
           'healthy_vs_problem_correct_of_answered': ws(ans & ((pred == 'healthy') == hl), ans),
           'not_sure_low_confidence': ws(dec['low_conf'], allm), 'not_sure_unfamiliar': ws(dec['unfamiliar'], allm),
           'routed_as_other_class': ws(dec['other'], allm),
           'mean_confidence': float(np.average(dec['P'].max(1), weights=w))}
    out['by_class'] = {}
    for c in UG_CLASSES:
        mc = y_name == c
        out['by_class'][c] = {'n_photos': int(mc.sum()), 'n_effective': float(w[mc].sum()),
                              'right': ws(right, mc), 'routed_to_officer': ws(~ans, mc),
                              'answered_wrong': ws(ans & (pred != c), mc),
                              'answered_as': {k: ws(ans & (pred == k), mc) for k in cls if ws(ans & (pred == k), mc) > 0},
                              'forced_as': {k: ws(pred == k, mc) for k in cls if ws(pred == k, mc) > 0}}
    return out


def group_weights(group):
    _, inv, cnt = np.unique(group, return_inverse=True, return_counts=True)
    return 1.0 / cnt[inv]


def bootstrap(m, dec, y_name, group, reps=1000, seed=11):
    """95% intervals: resample copy groups with replacement (each group keeps weight 1 per draw)."""
    keys = ['answered', 'correct_of_answered', 'rust_named', 'phoma_named', 'healthy_flagged']
    ug, inv = np.unique(group, return_inverse=True)
    base_w = group_weights(group); rng = np.random.default_rng(seed); res = {k: [] for k in keys}
    for _ in range(reps):
        cnt = np.bincount(rng.integers(0, len(ug), len(ug)), minlength=len(ug))
        w = base_w * cnt[inv]
        s = summarise(m, dec, y_name, w)
        for k in keys:
            res[k].append(s[k])
    return {k: [float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))] for k, v in res.items()}


def learning_loop(m, Z, Zn, y_name, group, units, ks=KS, seeds=SEEDS, seed0=2000, rule='app'):
    """Officer labels k Ugandan photos (one photo per copy group, random order) from a pool of split units; the head
    is refit on the phone (pulled toward the starting head, strength = prior_strength) and the labelled photos join the
    familiarity reference; scored on the other half of the split units (each copy group counts once)."""
    ci = {c: i for i, c in enumerate(m['classes'])}
    y = np.array([ci[c] for c in y_name])
    keys = ['answered', 'correct_of_answered', 'forced_correct', 'rust_named', 'phoma_named', 'healthy_flagged',
            'sick_called_a_problem', 'not_sure_unfamiliar', 'not_sure_low_confidence']
    runs = {k: {key: [] for key in keys} for k in ks}
    by_class = {k: {c: {'right': [], 'routed_to_officer': []} for c in UG_CLASSES} for k in ks}
    n_pool, n_test = [], []
    for s in range(seeds):
        r = np.random.default_rng(seed0 + s)
        uu = r.permutation(np.unique(units)); pool_u = set(uu[:len(uu) // 2].tolist())
        in_pool = np.array([u in pool_u for u in units]); test = np.where(~in_pool)[0]
        pool = []
        for g in r.permutation(np.unique(group[in_pool])):   # one photo per copy group, random order
            pool.append(r.choice(np.where(in_pool & (group == g))[0]))
        pool = np.array(pool); n_pool.append(len(pool)); n_test.append(len(test))
        wt = group_weights(group[test])
        for k in ks:
            pick = pool[:k]
            Wa, ba = adapt(Z[pick], y[pick], m['W'], m['b'], m['T'], m['lam']) if k else (m['W'], m['b'])
            R = unit(np.vstack([m['Rn'], Zn[pick]])) if k else m['Rn']   # labelled photos join the stored photos
            if rule == 'app':        # the app: k nearest of all stored rows, OR the nearest officer-labelled row
                dec = decide(m, Z[test], Zn[test], Wa, ba, R, local=Zn[pick] if k else None, c1=m['c1'])
            else:                    # 'previous': k nearest of all stored rows only (the app before the second check)
                dec = decide(m, Z[test], Zn[test], Wa, ba, R)
            sm = summarise(m, dec, y_name[test], wt)
            for key in keys:
                runs[k][key].append(sm[key])
            for c in UG_CLASSES:
                for key in ('right', 'routed_to_officer'):
                    by_class[k][c][key].append(sm['by_class'][c][key])
    mean = lambda v: float(np.nanmean(v)) if not np.all(np.isnan(v)) else None
    return {'ks': ks, 'seeds': seeds, 'prior_strength': m['lam'], 'familiarity_rule': rule,
            'local_nearest_cutoff': m['c1'] if rule == 'app' else None,
            'pool_copy_groups_mean': float(np.mean(n_pool)), 'test_photos_mean': float(np.mean(n_test)),
            'mean': {key: [mean(runs[k][key]) for k in ks] for key in keys},
            'sd': {key: [float(np.nanstd(runs[k][key])) for k in ks] for key in keys},
            'by_class_mean': {c: {key: [mean(by_class[k][c][key]) for k in ks] for key in ('right', 'routed_to_officer')}
                              for c in UG_CLASSES}}


def pct(x, d=0):
    return 'n/a' if x is None or (isinstance(x, float) and np.isnan(x)) else f'{100 * x:.{d}f}%'


def figure(res):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    S1, S2, S3 = '#2a78d6', '#eb6834', '#1baf7a'
    SURF, INK, INK2, GRID = '#fcfcfb', '#0b0b0b', '#52514e', '#e4e3df'
    plt.rcParams.update({'figure.facecolor': SURF, 'axes.facecolor': SURF, 'savefig.facecolor': SURF,
                         'axes.edgecolor': GRID, 'axes.labelcolor': INK2, 'xtick.color': INK2, 'ytick.color': INK2,
                         'text.color': INK, 'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': 0.8, 'lines.linewidth': 2})
    LS = res['learning_loop']['shipped_base']; LL = res['learning_loop']['lab_only_base']
    OP = res['learning_loop']['rule_comparison']['previous_rule_extended']
    mk = dict(marker='o', markersize=6, markeredgecolor=SURF, markeredgewidth=2)
    xmax = 100

    def curve(ax, L_, key, col, name=None, ls='-', dy=8, at=None, ha='right', dx=-4):
        pts = [(k, v) for k, v in zip(L_['ks'], L_['mean'][key]) if v is not None and k <= xmax]
        sds = [s_ for k, v, s_ in zip(L_['ks'], L_['mean'][key], L_['sd'][key]) if v is not None and k <= xmax]
        xs = [p[0] for p in pts]; ys = np.array([100 * p[1] for p in pts]); sd = 100 * np.array(sds)
        ax.fill_between(xs, ys - sd, ys + sd, color=col, alpha=0.10, linewidth=0)
        ax.plot(xs, ys, color=col, linestyle=ls, **mk)
        if name:
            i = len(xs) - 1 if at is None else xs.index(at)
            ax.annotate(name if at is not None else f'{name}: {ys[i]:.0f}%', (xs[i], ys[i]), xytext=(dx, dy),
                        textcoords='offset points', ha=ha, fontsize=9.5, color=INK)
        return dict(zip(xs, ys))

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
    ax = axes[0]
    curve(ax, LS, 'answered', S1, 'Shipped model, app rule', dy=12)
    curve(ax, OP, 'answered', S1, 'Previous rule (10 nearest only)', ls='--', dy=-14)
    curve(ax, LL, 'answered', S2, 'Lab-only model, app rule', dy=-22)
    ax.set_title('Photos the tool answers (the rest go to the officer)', loc='left', fontsize=11)
    ax.set_ylabel('Ugandan photos answered (%)')
    ax = axes[1]
    curve(ax, LS, 'forced_correct', S3, 'Right if forced to answer', at=50, dy=-24, ha='left', dx=-30)
    curve(ax, LS, 'correct_of_answered', S1, 'Correct, of the photos it answers', at=50, dy=12, ha='right', dx=-8)
    ax.set_title('Shipped model: the head learns Ugandan photos', loc='left', fontsize=11)
    ax.set_ylabel('% of Ugandan test photos')
    ax = axes[2]
    a_r = curve(ax, LS, 'rust_named', S1, 'Rust named rust', dy=8)
    a_p = curve(ax, LS, 'phoma_named', S3, 'Phoma named Phoma', dy=-14)
    curve(ax, OP, 'rust_named', S1, ls='--'); curve(ax, OP, 'phoma_named', S3, ls='--')
    a_h = curve(ax, LS, 'healthy_flagged', S2)
    ax.text(0.02, 0.98, f'App rule at 100 labels: rust named {a_r[100]:.0f}%, Phoma named {a_p[100]:.0f}%,\n'
            f'healthy called a problem {a_h[100]:.0f}% (dashed: previous rule)',
            transform=ax.transAxes, va='top', ha='left', fontsize=9, color=INK2)
    ax.set_title('Per class, of all photos of that class', loc='left', fontsize=11)
    ax.set_ylabel('% of photos of that class')
    for ax in axes:
        ax.set_ylim(0, 105); ax.set_xlim(-5, xmax + 8); ax.set_xticks([0, 10, 20, 50, 100])
        ax.set_xlabel('Ugandan photos labelled by the officer')
    d = res['data']
    fig.suptitle(f"External test: {d['used']:,} coffee-leaf photos from farms in Uganda ({d['copy_groups']:,} distinct "
                 f"leaves after grouping copies), never trained on.\nWith officer labels the head learns and the 'not "
                 f"sure' check opens. Mean of {LS['seeds']} random label orders (band: spread). Each copy group counts "
                 f"once.\nDashed: the previous familiarity rule (10 nearest stored photos only). All Ugandan photos, including "
                 f"the 40% of copy clusters used to choose the app rule's second cutoff.", x=0.01, ha='left',
                 fontsize=11.5)
    fig.tight_layout()
    os.makedirs(FIG, exist_ok=True)
    fig.savefig(os.path.join(FIG, 'uganda_learning_loop.png'), dpi=200); plt.close(fig)


def evaluate():
    d = np.load(EMB_NPZ, allow_pickle=False)
    E, y_name, group, unit_f, unit_c = d['E'], d['label'], d['group'], d['unit'], d['unit_coarse']
    stats = json.load(open(PREP_JSON))
    mu, sd = standardisation()
    Z = ((E - mu) / sd).astype(np.float64); Zn = unit(Z)
    w = group_weights(group)
    res = {'what': 'External test of Kahawa Check on coffee-leaf photos from farms in Uganda (never trained on), and '
                   'the officer learning loop on those photos (the new-region test).',
           'generated_by': 'ml/eval_uganda.py', 'dataset': DATASET, 'data': stats, 'models': {}}
    for tag, hf in [('shipped', 'head.json'), ('lab_only', 'head_labonly.json')]:
        m = load_model(hf)
        missing = [c for c in UG_CLASSES if c not in m['classes']]
        assert not missing, f'{hf} lacks classes {missing}'
        dec = decide(m, Z, Zn)
        res['models'][tag] = {'head_file': hf, 'version': m['version'], 'classes': m['classes'],
                              'n_classes': len(m['classes']), 'threshold': m['thr'], 'cutoff': m['cut'],
                              'local_nearest_cutoff': m['c1'],
                              'temperature': m['T'], 'reference_n': int(len(m['Rn'])),
                              'group_aware': summarise(m, dec, y_name, w),
                              'all_images_unweighted': summarise(m, dec, y_name, np.ones(len(w))),
                              'ci95_group_bootstrap': bootstrap(m, dec, y_name, group)}
        print(tag, m['version'], 'answered', pct(res['models'][tag]['group_aware']['answered']),
              'correct of answered', pct(res['models'][tag]['group_aware']['correct_of_answered']),
              'forced', pct(res['models'][tag]['group_aware']['forced_correct']), flush=True)
    ms = load_model('head.json'); ml_ = load_model('head_labonly.json')
    t0 = time.time()
    res['learning_loop'] = {
        'setup': (f'Split units (clusters of copies) are split 50/50 into pool and test at random, {SEEDS} seeds. The '
                  f'officer labels k photos from the pool, one photo per copy group, in random order; the head is refit '
                  f'on the phone (adapt from ml/train_eval.py: cross-entropy + prior_strength/2 x squared distance to '
                  f'the starting head) and the labelled photos join the familiarity reference. Familiarity is the '
                  f"app's rule: 10 nearest stored rows within the cutoff, OR the nearest officer-labelled photo within "
                  f"ood.local_nearest_cutoff ({ms['c1']}). Threshold, cutoffs and temperature stay as shipped. Test "
                  f'photos: the other half; each copy group counts once. Labels are the dataset authors\' folder '
                  f'labels, standing in for the officer. ood.local_nearest_cutoff was chosen on 40% of the Ugandan copy '
                  f'clusters (results/familiarity_rule.json), which are included here; that file has the numbers on '
                  f'the other 60% only.'),
        'shipped_base': learning_loop(ms, Z, Zn, y_name, group, unit_f),
        'lab_only_base': learning_loop(ml_, Z, Zn, y_name, group, unit_f)}
    sens = learning_loop(ms, Z, Zn, y_name, group, unit_c, ks=[0, 50, 100])
    res['learning_loop']['sensitivity_coarse_split_units'] = {
        'what': f'shipped base, split units clustered more coarsely (similarity {COARSE_SIM}), so near-copies that the '
                f'main grouping missed cannot sit on both sides of the split', **sens}
    ks_ext = KS + [200]
    res['learning_loop']['rule_comparison'] = {
        'what': ('The app rule (10 nearest stored rows OR the nearest officer-labelled photo within '
                 'ood.local_nearest_cutoff) next to the previous rule (10 nearest stored rows only), same refit, '
                 'seeds and label orders, up to 200 labels.'),
        'app_rule_extended': learning_loop(ms, Z, Zn, y_name, group, unit_f, ks=ks_ext),
        'previous_rule_extended': learning_loop(ms, Z, Zn, y_name, group, unit_f, ks=ks_ext, rule='previous'),
        'previous_rule_coarse_grouping': learning_loop(ms, Z, Zn, y_name, group, unit_c, ks=[0, 50, 100], rule='previous')}
    # how far Ugandan photos sit from what the phone stores, and from each other
    d_ship = knn_dist(Zn, ms['Rn'], ms['k'])
    S = Zn @ Zn.T; S[unit_f[:, None] == unit_f[None, :]] = -9
    d_ug = 1 - (-np.sort(-S, 1)[:, :ms['k']]).mean(1); del S
    res['familiarity_distances'] = {
        'cutoff': ms['cut'], 'to_shipped_reference_median': float(np.median(d_ship)),
        'to_shipped_reference_share_within_cutoff': float(np.average(d_ship <= ms['cut'], weights=w)),
        'to_all_other_ugandan_photos_median': float(np.median(d_ug)),
        'to_all_other_ugandan_photos_share_within_cutoff': float(np.average(d_ug <= ms['cut'], weights=w)),
        'note': ('distance = 1 - mean of the 10 largest cosine similarities; "all other Ugandan photos" leaves out '
                 'the photo\'s own split unit. If every other Ugandan photo were stored, this share would be familiar.')}
    print(f'learning loops {time.time() - t0:.0f} s', flush=True)
    # context: the same loop on the Ecuador field photos (lab-only base, from results/metrics.json)
    try:
        EL = json.load(open(os.path.join(RES, 'metrics.json')))['lab_only_new_region_simulation']['learning_loop']
        res['context_ecuador_loop'] = {'source': 'results/metrics.json lab_only_new_region_simulation.learning_loop',
                                       'ks': EL['ks'], 'answered': EL['curves']['prior_adapt']['coverage'],
                                       'correct_of_answered': EL['curves']['prior_adapt']['acc_answered']}
    except Exception as e:  # metrics.json missing or reshaped: leave the context out
        res['context_ecuador_loop'] = {'missing': str(e)}
    sh = res['models']['shipped']['group_aware']; LS = res['learning_loop']['shipped_base']
    i50 = LS['ks'].index(50)
    res['summary'] = {
        'shipped_version': res['models']['shipped']['version'],
        'shipped_answered': sh['answered'], 'shipped_correct_of_answered': sh['correct_of_answered'],
        'shipped_forced_correct': sh['forced_correct'], 'shipped_rust_named': sh['rust_named'],
        'shipped_phoma_named': sh['phoma_named'], 'shipped_healthy_flagged': sh['healthy_flagged'],
        'shipped_sick_called_a_problem': sh['sick_called_a_problem'],
        'loop_k50_answered': LS['mean']['answered'][i50], 'loop_k50_correct_of_answered': LS['mean']['correct_of_answered'][i50],
        'loop_k50_forced_correct': LS['mean']['forced_correct'][i50],
        'loop_k50_rust_named': LS['mean']['rust_named'][i50], 'loop_k50_phoma_named': LS['mean']['phoma_named'][i50],
        'loop_k50_healthy_flagged': LS['mean']['healthy_flagged'][i50]}
    res['suggested_numbers'] = suggested_numbers(res)
    res['plain_summary'] = plain_summary(res)
    res['limits_and_next_steps'] = limits(res)
    json.dump(res, open(OUT_JSON, 'w'), indent=1, default=float)
    figure(res)
    print('\n'.join(res['plain_summary']))
    print(json.dumps(res['suggested_numbers'], indent=1))


def _at(L, key, k):
    return L['mean'][key][L['ks'].index(k)]


def suggested_numbers(res):
    """Ready-made strings for numbers.json (the integration step decides which to adopt)."""
    d = res['data']; sh = res['models']['shipped']['group_aware']; lo = res['models']['lab_only']['group_aware']
    LS = res['learning_loop']['shipped_base']; LL = res['learning_loop']['lab_only_base']
    RC = res['learning_loop']['rule_comparison']; FD = res['familiarity_distances']
    out = {'UG_N_PHOTOS': f"{d['used']:,}", 'UG_N_GROUPS': f"{d['copy_groups']:,}",
           'UG_N_LISTED': f"{d['listed_files']:,}", 'UG_N_EMPTY': str(d['dropped']['empty_file']),
           'UG_N_CONFLICT': str(d['dropped_label_conflict']), 'UG_N_IDENTICAL': f"{d['byte_identical_extra_copies']:,}",
           'UG_SHIP_VERSION': res['models']['shipped']['version'],
           'UG_SHIP_ANSWERED': pct(sh['answered']), 'UG_SHIP_NOT_SURE': pct(1 - sh['answered']),
           'UG_SHIP_ACC_ANSWERED': pct(sh['correct_of_answered']),
           'UG_SHIP_FORCED': pct(sh['forced_correct']), 'UG_SHIP_RUST_NAMED': pct(sh['rust_named']),
           'UG_SHIP_PHOMA_NAMED': pct(sh['phoma_named']), 'UG_SHIP_HEALTHY_FLAGGED': pct(sh['healthy_flagged']),
           'UG_SHIP_SICK_PROBLEM': pct(sh['sick_called_a_problem']),
           'UG_SHIP_NOT_SURE_UNFAMILIAR': pct(sh['not_sure_unfamiliar']),
           'UG_SHIP_FORCED_RUST_AS_RUST': pct(sh['by_class']['rust']['forced_as'].get('rust', 0.0)),
           'UG_SHIP_FORCED_PHOMA_AS_PHOMA': pct(sh['by_class']['phoma']['forced_as'].get('phoma', 0.0)),
           'UG_SHIP_FORCED_HEALTHY_AS_HEALTHY': pct(sh['by_class']['healthy']['forced_as'].get('healthy', 0.0)),
           'UG_LABONLY_ANSWERED': pct(lo['answered']), 'UG_LABONLY_ACC_ANSWERED': pct(lo['correct_of_answered']),
           'UG_LABONLY_FORCED': pct(lo['forced_correct']),
           'UG_FAMILIAR_IF_ALL_UG_STORED': pct(FD['to_all_other_ugandan_photos_share_within_cutoff'])}
    for k in (10, 20, 50, 100):
        out[f'UG_LOOP{k}_ANSWERED'] = pct(_at(LS, 'answered', k))
        out[f'UG_LOOP{k}_ACC_ANSWERED'] = pct(_at(LS, 'correct_of_answered', k))
        out[f'UG_LOOP{k}_FORCED'] = pct(_at(LS, 'forced_correct', k))
        out[f'UG_LOOP{k}_RUST_NAMED'] = pct(_at(LS, 'rust_named', k))
        out[f'UG_LOOP{k}_PHOMA_NAMED'] = pct(_at(LS, 'phoma_named', k))
        out[f'UG_LOOP{k}_HEALTHY_FLAGGED'] = pct(_at(LS, 'healthy_flagged', k))
        out[f'UG_LABONLY_LOOP{k}_ANSWERED'] = pct(_at(LL, 'answered', k))
        out[f'UG_LABONLY_LOOP{k}_ACC_ANSWERED'] = pct(_at(LL, 'correct_of_answered', k))
    EC = res.get('context_ecuador_loop', {})
    if 'ks' in EC and 50 in EC['ks']:
        out['EC_LOOP50_ANSWERED'] = pct(EC['answered'][EC['ks'].index(50)])
    for k in (50, 100, 200):
        out[f'UG_APPRULE_LOOP{k}_ANSWERED'] = pct(_at(RC['app_rule_extended'], 'answered', k))
    for k in (10, 20, 50, 100, 200):
        PR = RC['previous_rule_extended']
        out[f'UG_PREVRULE_LOOP{k}_ANSWERED'] = pct(_at(PR, 'answered', k))
        out[f'UG_PREVRULE_LOOP{k}_ACC_ANSWERED'] = pct(_at(PR, 'correct_of_answered', k))
        out[f'UG_PREVRULE_LOOP{k}_RUST_NAMED'] = pct(_at(PR, 'rust_named', k))
        out[f'UG_PREVRULE_LOOP{k}_PHOMA_NAMED'] = pct(_at(PR, 'phoma_named', k))
        out[f'UG_PREVRULE_LOOP{k}_HEALTHY_FLAGGED'] = pct(_at(PR, 'healthy_flagged', k))
    for k in (50, 100):
        PC = RC['previous_rule_coarse_grouping']
        out[f'UG_PREVRULE_COARSE_LOOP{k}_ANSWERED'] = pct(_at(PC, 'answered', k))
        out[f'UG_PREVRULE_COARSE_LOOP{k}_ACC_ANSWERED'] = pct(_at(PC, 'correct_of_answered', k))
    return out


def plain_summary(res):
    """Strengths first, then each limit with what we do about it. Every number comes from this run."""
    n = suggested_numbers(res); d = res['data']
    return [
        f"Test set: {n['UG_N_PHOTOS']} coffee-leaf photos from farms in Uganda (healthy, rust, Phoma; "
        f"{n['UG_N_GROUPS']} distinct leaves after grouping copies), never used for training; one setting of the "
        f"app's familiarity rule (ood.local_nearest_cutoff) was chosen on 40% of the copy clusters "
        f"(results/familiarity_rule.json), which this loop includes.",
        f"The 'not sure' check protects the count in a new country: if forced to answer, the shipped model "
        f"({n['UG_SHIP_VERSION']}) is right on only {n['UG_SHIP_FORCED']} of Ugandan photos; the app instead sends "
        f"{n['UG_SHIP_NOT_SURE']} of them to the officer and calls only {n['UG_SHIP_HEALTHY_FLAGGED']} of healthy "
        f"leaves a problem.",
        f"With officer labels the tool learns the new country: after 50 labels it answers {n['UG_LOOP50_ANSWERED']} of "
        f"photos, {n['UG_LOOP50_ACC_ANSWERED']} correctly; after 100, {n['UG_LOOP100_ANSWERED']} "
        f"({n['UG_LOOP100_ACC_ANSWERED']} correct). Right if forced goes from {n['UG_SHIP_FORCED']} to "
        f"{n['UG_LOOP50_FORCED']} after 50 labels.",
        f"Why it opens: a photo also counts as familiar when its nearest officer-labelled photo is close. With the "
        f"previous rule (10 nearest stored photos only) the tool answered only {n['UG_PREVRULE_LOOP50_ANSWERED']} "
        f"after 50 labels and {n['UG_PREVRULE_LOOP100_ANSWERED']} after 100.",
        f"Limit: Phoma is the look-alike. After 100 labels the tool names rust on {n['UG_LOOP100_RUST_NAMED']} of "
        f"rust leaves and Phoma on {n['UG_LOOP100_PHOMA_NAMED']} of Phoma leaves; healthy leaves called a problem: "
        f"{n['UG_LOOP100_HEALTHY_FLAGGED']}.",
        f"Data checks: {n['UG_N_EMPTY']} empty files dropped, {n['UG_N_IDENTICAL']} byte-identical extra copies "
        f"grouped, {n['UG_N_CONFLICT']} photos dropped because a near-identical copy sits in another class folder "
        f"({_conflict_pairs(d)}). Photos are 256 x 256 close-ups of leaves on the plant."]


def _conflict_pairs(d):
    pairs = sorted({tuple(sorted(k.split('-'))) for k, v in d['label_conflict_by_folder_pair'].items() if v})
    return ', '.join(a + ' vs ' + b for a, b in pairs) or 'none'


def limits(res):
    d = res['data']; n = suggested_numbers(res)
    return [
        {'limit': f"The 'not sure' check opens only with officer labels: with none, the app answers "
                  f"{n['UG_SHIP_ANSWERED']} of Ugandan photos; after 50 labels {n['UG_LOOP50_ANSWERED']}, after 100 "
                  f"{n['UG_LOOP100_ANSWERED']}, so the officer still sees most photos early on. The setting that "
                  f"opens it (ood.local_nearest_cutoff) was chosen on 40% of these copy clusters.",
         'next_step': "Report answered and correct of answered on the first 200 officer-labelled Kenyan pilot photos "
                      "(sealed); who: ML lead; metric: answered and correct of answered after 50 and 100 labels; when: "
                      "first pilot month."},
        {'limit': 'Uganda, not Kenya: photos come from farms in Uganda (Soroti University team), not from Kenyan farms.',
         'next_step': 'Keep the first 200 officer-labelled Kenyan pilot photos aside as a Kenyan test set; who: the '
                      'team with the co-op extension officer; metric: share answered and correct of answered; when: '
                      'first pilot month.'},
        {'limit': 'Coffee species not stated in the dataset description (Uganda grows both robusta and arabica).',
         'next_step': 'Record species per plot with pilot photos and report results by species; who: the officer at '
                      'each plot visit; metric: correct of answered by species; when: from the first pilot visit.'},
        {'limit': 'Photo style: close-ups of single leaves on the plant, outdoors in daylight, stored at 256 x 256 '
                  'pixels (checked by eye on about 70 photos; a few show soil behind the leaf, so some may be fallen '
                  'or held leaves). The phone sees full-resolution photos framed by a relay farmer.',
         'next_step': 'On the first 100 pilot photos, compare share answered on full photos vs the same photos cut '
                      'to 256 px; who: the team; metric: share answered and correct of answered; when: pilot week 1.'},
        {'limit': f"Copies: the dataset mixes rotated, flipped, brightness-adjusted and byte-identical copies "
                  f"({n['UG_N_IDENTICAL']} byte-identical extra files). We group copies by image similarity "
                  f"({n['UG_N_GROUPS']} copy groups from {n['UG_N_PHOTOS']} photos); copies that were also cropped "
                  f"or strongly brightened can escape the grouping, so a few near-copies may sit on both sides of the "
                  f"learning-loop split. The coarser-grouping runs show how much this matters.",
         'next_step': 'Ask the dataset authors for the original (before augmentation) file list; who: the team by '
                      'email; metric: rerun with exact groups and compare; when: after the challenge.'},
        {'limit': f"Labels: folder labels from the dataset authors stand in for the officer. {n['UG_N_CONFLICT']} "
                  f"photos had a near-identical copy in another class folder ({_conflict_pairs(d)}) "
                  f"and were dropped; some photos in the Phoma folder show rust-like orange spots, so some label noise "
                  f"likely remains.",
         'next_step': 'Have the extension officer relabel a random 100 Ugandan photos and report agreement with the '
                      'folder labels; who: co-op officer; metric: share of agreement; when: pilot week 1.'},
        {'limit': 'Learning-step strength (prior_strength), answer threshold and familiarity cutoff are the shipped '
                  'values; none was tuned on Ugandan photos.',
         'next_step': 'Re-tune them on the first pilot labels (inner split of the labelled pool only); who: ML lead; '
                      'metric: correct of answered at 50 labels; when: after the first 50 pilot labels.'}]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--download', action='store_true')
    ap.add_argument('--reprepare', action='store_true')
    a = ap.parse_args()
    if a.download:
        download()
    if a.reprepare or not (os.path.exists(EMB_NPZ) and os.path.exists(PREP_JSON)):
        prepare()
    evaluate()


sys.path.insert(0, HERE)
from train_eval import adapt, unit, knn_dist  # noqa: E402  (same on-phone refit and familiarity check as the app)

if __name__ == '__main__':
    main()
