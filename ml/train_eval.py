"""Train the small head, calibrate it, and evaluate it on sealed field photos.

Also runs the two experiments that make the entry more than a leaf classifier:
  (1) learning loop: how much do a few officer-labelled local photos help (random vs uncertain-first)?
  (2) co-op early warning: raw village shares vs empirical-Bayes shrunk shares (simulation that uses
      the error rates measured on the field test; labelled synthetic).
Writes results/*.json and model/head.json, and re-exports model/backbone.onnx with the embedding
standardisation baked in (so the web app and this script use identical numbers).
Run: ../.venv/bin/python ml/train_eval.py
"""
import os, json, csv
import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import softmax, logsumexp
from scipy.stats import beta as beta_dist
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
WORK = os.path.join(os.path.dirname(REPO), 'data_work')
RES = os.path.join(REPO, 'results')
CLASSES = ['healthy', 'rust', 'miner', 'cercospora', 'phoma']
CI = {c: i for i, c in enumerate(CLASSES)}
TARGET_ACC = 0.90      # threshold chosen so answered accuracy on calibration photos >= 90%
OOD_PCT = 97.5         # centroid-distance cutoff = 97.5th percentile on calibration photos
RNG = np.random.default_rng(0)


def load():
    rows = list(csv.DictReader(open(os.path.join(RES, 'index.csv'))))
    E = np.load(os.path.join(WORK, 'embeddings.npz'))['E']
    assert len(rows) == len(E)
    return rows, E


def split_masks(rows):
    n = len(rows)
    src = np.array([r['source'] for r in rows]); lab = np.array([r['label'] for r in rows])
    grp = np.array([r['group'] for r in rows])
    train = np.zeros(n, bool); val = np.zeros(n, bool); calib = np.zeros(n, bool)
    jm = np.isin(src, ['JMuBEN', 'JMuBEN2'])
    ug = np.unique(grp[jm]); RNG.shuffle(ug)
    vg = set(ug[:int(0.15 * len(ug))])
    val[jm] = [g in vg for g in grp[jm]]; train[jm] = ~val[jm]
    br = np.where(src == 'BRACOL')[0]
    for c in CLASSES:  # BRACOL: half to training, half to calibration, stratified
        idx = br[lab[br] == c].copy(); RNG.shuffle(idx)
        h = len(idx) // 2
        train[idx[:h]] = True; calib[idx[h:]] = True
    field = (src == 'RoCoLe') & np.isin(lab, ['healthy', 'rust'])
    mite = (src == 'RoCoLe') & (lab == 'mite')
    return dict(train=train, val=val, calib=calib, field=field, mite=mite), src, lab


def fit_head(Z, y, C):
    clf = LogisticRegression(C=C, max_iter=3000, class_weight='balanced')
    clf.fit(Z, y)
    W = np.zeros((len(CLASSES), Z.shape[1])); b = np.zeros(len(CLASSES))
    W[clf.classes_] = clf.coef_; b[clf.classes_] = clf.intercept_
    return W, b


def logits(Z, W, b):
    return Z @ W.T + b


def nll(L, y, T=1.0):
    return float(np.mean(logsumexp(L / T, axis=1) - (L / T)[np.arange(len(y)), y]))


def ece(P, y, bins=10):
    conf = P.max(1); pred = P.argmax(1); acc = (pred == y)
    e = 0.0
    for lo in np.linspace(0, 1, bins, endpoint=False):
        m = (conf > lo) & (conf <= lo + 1 / bins)
        if m.any():
            e += m.mean() * abs(acc[m].mean() - conf[m].mean())
    return float(e)


def centroid_dist(Z, cents):
    Zn = Z / np.linalg.norm(Z, axis=1, keepdims=True)
    Cn = cents / np.linalg.norm(cents, axis=1, keepdims=True)
    return 1 - (Zn @ Cn.T).max(1)


def decide(P, d, thr, cut):
    """answered = confident and in-distribution; otherwise 'not sure'."""
    return (P.max(1) >= thr) & (d <= cut)


def risk_coverage(P, y):
    conf = P.max(1); order = np.argsort(-conf); corr = (P.argmax(1) == y)[order]
    cov = np.arange(1, len(y) + 1) / len(y); acc = np.cumsum(corr) / np.arange(1, len(y) + 1)
    idx = np.unique(np.linspace(0, len(y) - 1, 40).astype(int))
    return {'coverage': cov[idx].round(4).tolist(), 'accuracy': acc[idx].round(4).tolist(),
            'aurc': float(np.mean(1 - acc))}


def adapt(Z, y, W0, b0, T, lam, steps=200):
    """Officer-label learning loop: min mean CE((WZ+b)/T) + lam/2 (||W-W0||^2 + ||b-b0||^2)."""
    if len(y) == 0:
        return W0.copy(), b0.copy()
    Zt = torch.tensor(Z, dtype=torch.float64); yt = torch.tensor(y)
    W0 = np.ascontiguousarray(W0, np.float64); b0 = np.ascontiguousarray(b0, np.float64); Z = np.ascontiguousarray(Z)
    W = torch.tensor(W0, requires_grad=True); b = torch.tensor(b0, requires_grad=True)
    W0t = torch.tensor(W0); b0t = torch.tensor(b0)
    opt = torch.optim.LBFGS([W, b], max_iter=steps, line_search_fn='strong_wolfe')

    def closure():
        opt.zero_grad()
        L = (Zt @ W.T + b) / T
        loss = torch.nn.functional.cross_entropy(L, yt) + lam / 2 * (((W - W0t) ** 2).sum() + ((b - b0t) ** 2).sum())
        loss.backward()
        return loss
    opt.step(closure)
    return W.detach().numpy(), b.detach().numpy()


REF_PER_CLASS = 200   # stored reference photos per class for the familiarity check (1,000 total)
KNN = 10


def quantise_rows(X):
    """int8 rows + float32 per-row scale (what the phone stores)."""
    sc = np.abs(X).max(1) / 127.0 + 1e-12
    return np.round(X / sc[:, None]).astype(np.int8), sc.astype(np.float32)


def knn_dist(Qn, Rn, k=KNN):
    s = Qn @ Rn.T
    k = min(k, Rn.shape[0])
    return 1 - np.sort(s, axis=1)[:, -k:].mean(1)


def unit(X):
    return X / np.linalg.norm(X, axis=1, keepdims=True)


def fit_local_only(Z, y):
    """Baseline: a head trained only on the officer's local labels (no lab-trained prior)."""
    W = np.zeros((len(CLASSES), Z.shape[1])); b = np.full(len(CLASSES), -1e3)
    cl = np.unique(y)
    if len(cl) < 2:
        return None
    lc = LogisticRegression(C=1.0, max_iter=3000, class_weight='balanced').fit(Z, y)
    if len(cl) == 2:  # sklearn returns one row for two classes
        W[cl[1]], b[cl[1]] = lc.coef_[0] / 2, lc.intercept_[0] / 2
        W[cl[0]], b[cl[0]] = -lc.coef_[0] / 2, -lc.intercept_[0] / 2
    else:
        W[lc.classes_], b[lc.classes_] = lc.coef_, lc.intercept_
    return W, b


def main():
    rows, E = load()
    M, src, lab = split_masks(rows)
    y = np.array([CI.get(l, -1) for l in lab])
    mu = E[M['train']].mean(0); sd = E[M['train']].std(0) + 1e-6
    Z = (E - mu) / sd
    Zn = unit(Z)
    out = {'n': {k: int(v.sum()) for k, v in M.items()}, 'n_by_source_label': {},
           'notes': ['JMuBEN contains rotated/flipped copies of the same leaf, so in_domain_val is optimistic.',
                     'Calibration (temperature, threshold, familiarity cutoff) uses only the held-out half of BRACOL, '
                     'a different source from most training photos.',
                     'Learning-loop pool and test photos both come from RoCoLe (one region of Ecuador); real farms vary more.']}
    for s_ in np.unique(src):
        for l in np.unique(lab[src == s_]):
            out['n_by_source_label'][f'{s_}/{l}'] = int(((src == s_) & (lab == l)).sum())
    tr = M['train']; cal = M['calib']

    best = None
    for C in [0.001, 0.003, 0.01, 0.03, 0.1]:
        W, b = fit_head(Z[tr], y[tr], C)
        v = nll(logits(Z[cal], W, b), y[cal])
        if best is None or v < best[0]:
            best = (v, C, W, b)
    _, C, W, b = best
    out['C'] = C
    Lc = logits(Z[cal], W, b)
    T = float(minimize_scalar(lambda t: nll(Lc, y[cal], t), bounds=(0.05, 20), method='bounded').x)
    Pc = softmax(Lc / T, axis=1)

    # familiarity check: distance to the 10 nearest of 1,000 stored training photos (int8 on the phone)
    ref = np.concatenate([RNG.choice(np.where(tr & (y == k))[0], REF_PER_CLASS, replace=False) for k in range(len(CLASSES))])
    q, sc = quantise_rows(Zn[ref]); Rn = unit(q.astype(np.float32) * sc[:, None])
    fam = lambda Q, R=Rn: knn_dist(Q, R)
    dc = fam(Zn[cal]); cut = float(np.percentile(dc, 95))
    thr = 0.0
    for t in np.linspace(0.3, 0.99, 70):
        m = (Pc.max(1) >= t) & (dc <= cut)
        if m.sum() >= 20 and (Pc.argmax(1)[m] == y[cal][m]).mean() >= TARGET_ACC:
            thr = float(t); break
    out.update(temperature=T, threshold=thr, familiarity_cutoff=cut, knn=KNN, reference_n=int(len(ref)))

    def report(mask, Wx=W, bx=b, R=Rn):
        L = logits(Z[mask], Wx, bx); P1 = softmax(L, axis=1); P = softmax(L / T, axis=1)
        d = fam(Zn[mask], R); ans = (P.max(1) >= thr) & (d <= cut)
        yy = y[mask]; pred = P.argmax(1)
        r = {'n': int(mask.sum()), 'acc_all': float((pred == yy).mean()), 'coverage': float(ans.mean()),
             'acc_answered': float((pred[ans] == yy[ans]).mean()) if ans.any() else None,
             'ece_before_T': ece(P1, yy), 'ece_after_T': ece(P, yy), 'mean_confidence': float(P.max(1).mean()),
             'acc_healthy_vs_problem': float(((pred == 0) == (yy == 0)).mean()),
             'risk_coverage': risk_coverage(P, yy),
             'confusion': {CLASSES[t]: {CLASSES[p]: int(((yy == t) & (pred == p)).sum()) for p in range(len(CLASSES))}
                           for t in np.unique(yy)}}
        return r, P, d, ans

    out['in_domain_val'], *_ = report(M['val'])
    out['in_domain_calib'], *_ = report(cal)
    out['field'], Pf, df, ansf = report(M['field'])
    Pm = softmax(logits(Z[M['mite']], W, b) / T, axis=1); dm = fam(Zn[M['mite']])
    out['mite'] = {'n': int(M['mite'].sum()), 'abstain_rate': float(1 - ((Pm.max(1) >= thr) & (dm <= cut)).mean())}
    # which 'not sure' signal notices field photos? AUROC field vs held-out calibration photos
    cents = np.stack([Z[tr & (y == k)].mean(0) for k in range(len(CLASSES))])
    ood = {'max_softmax': (-Pc.max(1), -Pf.max(1)),
           'centroid_cosine': (centroid_dist(Z[cal], cents), centroid_dist(Z[M['field']], cents)),
           'knn10_cosine (used)': (dc, df)}
    out['ood_auroc_field_vs_heldout'] = {k: float(roc_auc_score(np.r_[np.zeros(len(a)), np.ones(len(bb))], np.r_[a, bb]))
                                         for k, (a, bb) in ood.items()}

    jm_tr = tr & np.isin(src, ['JMuBEN', 'JMuBEN2']); brm = src == 'BRACOL'
    Wj, bj = fit_head(Z[jm_tr], y[jm_tr], C)
    out['cross_source_jmuben_to_bracol_acc'] = float((logits(Z[brm], Wj, bj).argmax(1) == y[brm]).mean())

    # --- learning loop: officer labels k field photos -> head pulled toward the lab model (prior) is refit,
    #     and the labelled photos join the familiarity reference set ---
    fidx = np.where(M['field'])[0]
    sample_files = {s_['original_file'] for s_ in json.load(open(os.path.join(REPO, 'samples', 'manifest.json')))['samples']}
    ks = [0, 10, 20, 50, 100, 200]
    s0 = np.random.default_rng(100); perm = s0.permutation(fidx); pool0 = perm[:len(perm) // 2]
    inner = s0.permutation(pool0); itr, iva = inner[:50], inner[50:]
    lam_scores = {}
    for lam in [0.03, 0.1, 0.3, 1.0, 3.0]:
        Wa, ba = adapt(Z[itr], y[itr], W, b, T, lam)
        lam_scores[lam] = float((logits(Z[iva], Wa, ba).argmax(1) == y[iva]).mean())
    lam = max(lam_scores, key=lam_scores.get)
    methods = ['prior_adapt', 'local_only']
    acc = {m: {k: [] for k in ks} for m in methods}; covg = {m: {k: [] for k in ks} for m in methods}
    acca = {m: {k: [] for k in ks} for m in methods}; op50 = []
    for seed in range(5):
        r = np.random.default_rng(1000 + seed); perm = r.permutation(fidx)
        pool, test = perm[:len(perm) // 2], perm[len(perm) // 2:]
        order = r.permutation(len(pool))
        for k in ks:
            pick = pool[order[:k]]
            R = unit(np.vstack([Rn, Zn[pick]])) if k else Rn
            famt = fam(Zn[test], R) <= cut
            for meth in methods:
                if meth == 'prior_adapt':
                    Wa, ba = adapt(Z[pick], y[pick], W, b, T, lam)
                else:
                    fl = fit_local_only(Z[pick], y[pick]) if k else None
                    Wa, ba = fl if fl is not None else (W, b)
                P = softmax(logits(Z[test], Wa, ba) / T, axis=1); pr = P.argmax(1)
                ans = famt & (P.max(1) >= thr)
                acc[meth][k].append(float((pr == y[test]).mean())); covg[meth][k].append(float(ans.mean()))
                acca[meth][k].append(float((pr[ans] == y[test][ans]).mean()) if ans.any() else float('nan'))
                if meth == 'prior_adapt' and k == 50:
                    yt = y[test]
                    op50.append((ans.mean(),
                                 ((pr == CI['rust']) & ans & (yt == CI['rust'])).sum() / max(1, (ans & (yt == CI['rust'])).sum()),
                                 ((pr == CI['rust']) & ans & (yt == CI['healthy'])).sum() / max(1, (ans & (yt == CI['healthy'])).sum())))
    out['learning_loop'] = {'lambda': lam, 'lambda_scores_inner': lam_scores, 'ks': ks, 'seeds': 5, 'order': 'random',
                            'curves': {m: {'acc_all': [float(np.mean(acc[m][k])) for k in ks],
                                           'acc_all_sd': [float(np.std(acc[m][k])) for k in ks],
                                           'coverage': [float(np.mean(covg[m][k])) for k in ks],
                                           'acc_answered': [float(np.nanmean(acca[m][k])) if not all(np.isnan(acca[m][k])) else None for k in ks]}
                                       for m in methods},
                            'update_bytes_float16_head': int((W.size + b.size) * 2),
                            'update_bytes_int8_per_reference_photo': int(Z.shape[1] + 4)}
    # alternative backbone comparison (from ml/explore_shift.py runs), if present
    alt = os.path.join(RES, 'explore_emb_vit_small_patch14_dinov2.json')
    if os.path.exists(alt):
        a = json.load(open(alt))
        out['alt_backbone_dinov2_small'] = {'params_millions': 21.6, 'field_acc_no_local_labels': a['acc']['field'],
                                            'loop_prior_adapt': a['loop']['prior_adapt']}

    cov50, sens50, fpr50 = (float(np.mean([o[i] for o in op50])) for i in range(3))
    out['village_sim'] = village_sim(cov50, sens50, fpr50)
    out['village_sim']['operating_point'] = 'lab model + 50 officer labels (learning-loop average)'

    json.dump(out, open(os.path.join(RES, 'metrics.json'), 'w'), indent=1)

    # --- export what the phone runs ---
    q.tofile(os.path.join(REPO, 'model', 'reference.bin'))
    with open(os.path.join(REPO, 'model', 'reference.bin'), 'ab') as fh:
        fh.write(sc.astype('<f4').tobytes())
    head = {'version': 'v1-' + str(np.datetime64('today')), 'classes': CLASSES, 'embed_dim': int(Z.shape[1]),
            'W': np.round(W, 6).tolist(), 'b': np.round(b, 6).tolist(), 'temperature': round(T, 5),
            'threshold': round(thr, 4),
            'ood': {'metric': 'knn_cosine', 'k': KNN, 'cutoff': round(cut, 5),
                    'reference': {'file': 'reference.bin', 'n': int(len(ref)), 'dim': int(Z.shape[1]),
                                  'format': 'n*dim int8 (row-major) followed by n float32 little-endian per-row scales; '
                                            'row = int8*scale, then L2-normalise. Query: L2-normalise the embedding; '
                                            'distance = 1 - mean of the k largest cosine similarities.'}},
            'prior_strength': lam, 'standardised_in_backbone': True,
            'trained_on': 'JMuBEN+JMuBEN2 (Kenya, Kirinyaga; 1,500 sampled per class) + half of BRACOL (Brazil)',
            'calibrated_on': 'held-out half of BRACOL',
            'field_test': {'dataset': 'RoCoLe (Ecuador, robusta, on-plant)', 'coverage': round(out['field']['coverage'], 3),
                           'acc_all': round(out['field']['acc_all'], 3)}}
    json.dump(head, open(os.path.join(REPO, 'model', 'head.json'), 'w'))

    # demo update: what one officer session (50 labels) would send to other phones; excludes demo sample photos
    r = np.random.default_rng(7)
    cand = [i for i in fidx if os.path.basename(rows[i]['path']) not in sample_files]  # demo photos never in the update
    assert len(cand) == len(fidx) - len([1 for i in fidx if os.path.basename(rows[i]['path']) in sample_files])
    pick = r.choice(cand, 50, replace=False)
    Wa, ba = adapt(Z[pick], y[pick], W, b, T, lam)
    qa, sa = quantise_rows(Zn[pick])
    upd = {'kind': 'kahawa-head-update', 'base_version': head['version'], 'n_labels': 50,
           'source': 'DEMO: 50 RoCoLe field photos labelled by the dataset authors, standing in for an officer session',
           'W': np.round(Wa, 6).tolist(), 'b': np.round(ba, 6).tolist(),
           'reference_add': {'int8': qa.astype(int).tolist(), 'scale': sa.tolist()},
           'labels': [CLASSES[int(y[i])] for i in pick]}
    json.dump(upd, open(os.path.join(REPO, 'model', 'update_demo_50.json'), 'w'))
    np.savez(os.path.join(WORK, 'standardisation.npz'), mu=mu, sd=sd)
    export_backbone_with_standardisation(mu, sd)
    print(json.dumps({k: out[k] for k in ['n', 'C', 'temperature', 'threshold', 'familiarity_cutoff']}, indent=1))
    for k in ['in_domain_val', 'in_domain_calib', 'field']:
        print(k, {kk: out[k][kk] for kk in ['n', 'acc_all', 'coverage', 'acc_answered', 'acc_healthy_vs_problem', 'mean_confidence']})
    print('mite', out['mite']); print('ood auroc', out['ood_auroc_field_vs_heldout'])
    print('cross', out['cross_source_jmuben_to_bracol_acc'])
    print('loop', json.dumps(out['learning_loop']['curves']), 'lambda', lam, lam_scores)
    print('village', json.dumps(out['village_sim']))


def fit_beta_binomial(x, a):
    """Maximum-likelihood Beta(alpha, beta) prior for village flagged-shares (beta-binomial)."""
    from scipy.special import betaln
    from scipy.optimize import minimize

    def nll_bb(t):
        al, be = np.exp(t)
        return -np.sum(betaln(x + al, a - x + be) - betaln(al, be))
    m = max(x.sum() / max(a.sum(), 1), 1e-3)
    o = minimize(nll_bb, np.log([m * 10, (1 - m) * 10]), method='Nelder-Mead',
                 options={'xatol': 1e-4, 'fatol': 1e-6, 'maxiter': 2000})
    al, be = np.exp(o.x)
    k, CAP = al + be, 50.0  # the prior never counts for more than 50 photos (same cap as lib/kahawa-core.js)
    return (al * CAP / k, be * CAP / k) if k > CAP else (al, be)


def village_sim(cov, sens, fpr, reps=1000, V=40, tau=0.25, seed=7):
    """Synthetic villages (labelled synthetic). True rust prevalence: 85% Beta(2,18) (~10%), 15% Beta(8,12) (~40%).
    Photos per village 3..45. Each photo answered with prob cov; answered rust photos flagged with prob sens,
    answered healthy photos with prob fpr (measured on field photos). Target: villages with prevalence > tau.
    Same rule as the app: alert line q* = tau on the share of answered photos flagged as rust (not corrected for
    classifier error). Raw rule: share > q*. Adjusted rule: posterior P(share > q*) > 0.5 under a maximum-likelihood
    beta-binomial prior fitted across villages (empirical Bayes, capped at 50 photos). Officer capacity: top-5 visits."""
    r = np.random.default_rng(seed)
    q_star = tau
    res = {'raw': {'false_alarms': [], 'missed': [], 'top5_hits': []},
           'shrunk': {'false_alarms': [], 'missed': [], 'top5_hits': []}}
    hot_n, strength = [], []
    for _ in range(reps):
        hot = r.random(V) < 0.15
        p = np.where(hot, r.beta(8, 12, V), r.beta(2, 18, V))
        n = r.integers(3, 46, V)
        truth = p > tau
        rust = r.binomial(n, p)
        a_r = r.binomial(rust, cov); a_h = r.binomial(n - rust, cov)
        x = r.binomial(a_r, sens) + r.binomial(a_h, fpr); a = a_r + a_h
        ok = a > 0
        raw = np.where(ok, x / np.maximum(a, 1), 0)
        al, be = fit_beta_binomial(x[ok], a[ok])
        post_p = beta_dist.sf(q_star, al + x, be + a - x)
        alerts = {'raw': ok & (raw > q_star), 'shrunk': post_p > 0.5}
        scores = {'raw': raw, 'shrunk': post_p}
        hot_n.append(truth.sum()); strength.append(al + be)
        for s in res:
            res[s]['false_alarms'].append(int((alerts[s] & ~truth).sum()))
            res[s]['missed'].append(int((~alerts[s] & truth).sum()))
            res[s]['top5_hits'].append(int(truth[np.argsort(-scores[s])[:5]].sum()))
    return {'inputs': {'coverage': cov, 'sensitivity': sens, 'false_positive_rate': fpr, 'villages': V, 'reps': reps,
                       'tau': tau, 'flagged_share_threshold': q_star, 'alert_rule_adjusted': 'P(share > q*) > 0.5'},
            **{s: {kk: float(np.mean(vv)) for kk, vv in res[s].items()} for s in res},
            'mean_true_hot_villages': float(np.mean(hot_n)), 'median_prior_strength': float(np.median(strength))}


def export_backbone_with_standardisation(mu, sd):
    import timm
    meta_p = os.path.join(REPO, 'model', 'backbone_meta.json')
    meta = json.load(open(meta_p))
    base = timm.create_model(meta['backbone'], pretrained=True, num_classes=0).eval()

    class Std(torch.nn.Module):
        def __init__(self, m):
            super().__init__(); self.m = m
            self.register_buffer('mu', torch.tensor(mu, dtype=torch.float32))
            self.register_buffer('sd', torch.tensor(sd, dtype=torch.float32))

        def forward(self, x):
            return (self.m(x) - self.mu) / self.sd
    net = Std(base).eval()
    path = os.path.join(REPO, 'model', 'backbone.onnx')
    torch.onnx.export(net, torch.randn(1, 3, 224, 224), path, input_names=['input'], output_names=['embedding'],
                      dynamic_axes={'input': {0: 'n'}, 'embedding': {0: 'n'}}, opset_version=17, dynamo=False)
    meta['standardised'] = True; meta['onnx_bytes'] = os.path.getsize(path)
    json.dump(meta, open(meta_p, 'w'), indent=1)


if __name__ == '__main__':
    main()
