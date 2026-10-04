"""Train, calibrate and evaluate the heads the phone runs, and run the experiments behind results/RESULTS.md.

One frozen backbone (MobileNetV3, model/backbone.onnx) and small heads on top of it:

  SHIPPED model (head v3: model/head.json + model/reference.bin)
      Head v2 setup plus a 6th class 'other' (a problem outside the five classes), trained on RoCoLe red-spider-mite
      photos. The app never shows 'other' as a diagnosis: when it is the top class, the photo goes to the officer.
      Trained on lab photos (JMuBEN/JMuBEN2 sample + half of BRACOL) PLUS RoCoLe field photos (healthy, rust, mite).
      Never trained on: the 60 human-baseline photos (baseline/key.json), the 7 demo samples (samples/manifest.json,
      one is a mite photo), identical / near-identical copies of those, and copy groups that carry two different labels
      (12 groups: 11 mite/rust, 1 mite/healthy).
      Two choices beyond the v2 setup (both stated in RESULTS.md, trade-off in metrics.json shipped.other_tradeoff):
        - the confidence threshold is chosen with the same 90% rule as v2, checked on healthy / rust / lab photos;
        - a constant is added to the 'other' score so that 1% of known-class out-of-fold field photos have 'other' as
          top class (SHIP_OTHER_BUDGET); without it 'other' takes many rust photos.
      Temperature, confidence threshold, familiarity cutoff and the 'other' constant are chosen on out-of-fold data
      only: the BRACOL calibration half plus out-of-fold predictions for the training field photos (5-fold CV).
      Headline field numbers: 5-fold cross-validation with the full decision rule (head + threshold + familiarity
      check + 'other' route; reference built from that fold's training rows only; values chosen without the scored
      fold). Held-out checks: the 60 human-baseline photos, the 7 demo samples, the mite photos never trained on.

  HEAD v2 (five classes, lab + field), kept for reference: metrics.json 'shipped_v2', files in ../data_work/shipped_v2/.
      Scored on the same folds and rows as v3.

  LAB-ONLY model (model/head_labonly.json + reference_labonly.bin + update_demo_50_labonly.json)
      Trained on lab photos only. Kept as a NEW-REGION SIMULATION: a model meeting a photo style it has never seen
      (field photos stand in for a new region). It gives the motivating finding (confidently wrong on field photos,
      caught by the familiarity check) and the learning-loop experiment (a few officer labels adapt the model to the
      new photo style). It is also the base model of ml/starter_kit.py.

  Co-op village ranking: simulation on synthetic villages, using the SHIPPED model's cross-validated error rates.

Familiarity rule (the app's, lib/kahawa-core.js and app.js predictHead): a photo is familiar when the distance to its
ood.k nearest stored rows (shipped reference + officer-labelled rows) is <= ood.cutoff, OR when officer-labelled rows
exist and 1 - (cosine to the single nearest officer-labelled row) <= ood.local_nearest_cutoff. Shipped reference rows
never count for the second part. ood.local_nearest_cutoff is read from results/familiarity_rule.json (written by
ml/eval_familiarity_rule.py; chosen on Ugandan DEV units only) and written into head.json and head_labonly.json. With no
officer rows (every cross-validated and held-out number of the shipped model) the rule is the plain k-nearest rule.
The lab-only learning loop (new-region simulation) reports the app rule and, next to it, the previous rule (k nearest
only) as *_previous_rule.

Standardisation: the embedding mean/sd baked into model/backbone.onnx are computed on the LAB training rows and are
kept unchanged for the shipped model, so backbone.onnx, every saved embedding and the lab-only files stay valid with
one backbone. The backbone is re-exported only if mu/sd ever change (pass --export-backbone to force it).

Writes results/metrics.json, results/limits.json and the model files above; removes model/update_demo_50.json
(it adapts the lab-only head; its copy for the starter kit is model/update_demo_50_labonly.json).
Run: ../.venv/bin/python ml/train_eval.py
"""
import os, sys, json, csv
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
MODEL = os.path.join(REPO, 'model')
CLASSES = ['healthy', 'rust', 'miner', 'cercospora', 'phoma']
CI = {c: i for i, c in enumerate(CLASSES)}
TARGET_ACC = 0.90      # threshold chosen so answered accuracy on calibration photos >= 90%
OOD_PCT = 97.5         # (unused) former centroid-distance cutoff
FAMILIAR_PCT = 95      # familiarity cutoff = 95th percentile of calibration distances
RNG = np.random.default_rng(0)   # lab-only split and reference draw (order of use kept, so lab-only numbers are stable)
SHIP_FOLDS = 5
SHIP_REF_FIELD_PER_CLASS = 200   # field rows added to the shipped familiarity reference, per class (healthy, rust)
SHIP_C_GRID = [0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1.0]
DUP_COS = 0.98                   # embeddings this similar are treated as copies of one photo (RoCoLe has identical images)
OTHER = 'other'                  # head v3: a 6th answer for a problem outside the five classes (sent to the officer)
SHIP_CLASSES = CLASSES + [OTHER] # head v3 classes; head v2 and the lab-only head keep the five CLASSES
SHIP_OTHER_BUDGET = 0.01         # head v3: at most 1 in 100 known-class field photos may have 'other' as top class
SHIP_OTHER_TRADEOFF = [(None, False), (None, True), (0.005, True), (0.01, True), (0.02, True), (0.05, True)]
FAM_RULE_JSON = os.path.join(RES, 'familiarity_rule.json')   # decision record of the nearest-officer-row rule


def local_nearest_cutoff():
    """ood.local_nearest_cutoff from the decision record (results/familiarity_rule.json): its c1 when the decision is
    'accept', else None (the rule is off and the app behaves as before)."""
    if not os.path.exists(FAM_RULE_JSON):
        print('WARNING: results/familiarity_rule.json missing: ood.local_nearest_cutoff left out (rule off)')
        return None
    fr = json.load(open(FAM_RULE_JSON))
    return float(fr['c1']) if fr.get('decision') == 'accept' and fr.get('c1') is not None else None


LOCAL_C1 = local_nearest_cutoff()


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


def fit_head(Z, y, C, n_classes=None, other_weight=None):
    """Multinomial logistic regression, balanced class weights. other_weight (head v3 only): the weight of the 'other'
    class as a multiple of its balanced weight (1 = balanced, as for the five known classes)."""
    cw = 'balanced'
    if other_weight is not None:
        cl, cnt = np.unique(y, return_counts=True)
        cw = {int(c): len(y) / (len(cl) * n_) for c, n_ in zip(cl, cnt)}
        cw[int(cl.max())] *= other_weight   # 'other' is the last class
    clf = LogisticRegression(C=C, max_iter=3000, class_weight=cw)
    clf.fit(Z, y)
    K = n_classes or len(CLASSES)
    W = np.zeros((K, Z.shape[1])); b = np.zeros(K)
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


def app_familiar(Qn, R_all, cut, local_n=None, c1=None, k=KNN):
    """The app's familiarity rule. R_all: shipped reference + officer rows (L2-normalised); local_n: officer rows only.
    Returns (familiar, k-nearest distance, nearest-officer-row distance or None)."""
    d = knn_dist(Qn, R_all, k); fam = d <= cut; dl = None
    if c1 is not None and local_n is not None and len(local_n):
        dl = knn_dist(Qn, local_n, 1); fam = fam | (dl <= c1)
    return fam, d, dl


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


def held_out_files():
    """Original file names never used for training the shipped model: 60 human-baseline photos, 7 demo samples."""
    key = json.load(open(os.path.join(REPO, 'baseline', 'key.json')))
    hb = {v['original_file'] for v in key['photos'].values()}
    assert len(hb) == key['meta']['n'] == 60, 'baseline/key.json should list 60 photos'
    samples = {s['original_file'] for s in json.load(open(os.path.join(REPO, 'samples', 'manifest.json')))['samples']}
    return hb, samples


def choose_scalars(L, d, yy, other=None, dmask=None, thr_mask=None):
    """Temperature (NLL), familiarity cutoff (95th percentile of distances) and confidence threshold (smallest t with
    >= 90% accuracy on the answered photos, at least 20 answered) on one calibration set.
    Head v3 (other = index of the 'other' class): photos whose top class is 'other' go to the officer, so they are not
    'answered'; the cutoff is taken on the photos of the five known classes only (dmask), as in v2. thr_mask: rows the
    90% accuracy rule for the threshold is checked on (None = all rows)."""
    T = float(minimize_scalar(lambda t: nll(L, yy, t), bounds=(0.05, 20), method='bounded').x)
    P = softmax(L / T, axis=1)
    cut = float(np.percentile(d if dmask is None else d[dmask], FAMILIAR_PCT))
    keep = np.ones(len(yy), bool) if other is None else (P.argmax(1) != other)
    if thr_mask is not None:
        keep = keep & thr_mask
    thr = 0.0
    for t in np.linspace(0.3, 0.99, 70):
        m = (P.max(1) >= t) & (d <= cut) & keep
        if m.sum() >= 20 and (P.argmax(1)[m] == yy[m]).mean() >= TARGET_ACC:
            thr = float(t); break
    return T, thr, cut


def route(P, d, thr, cut, other=None):
    """The app's decision. answered = confident, familiar and (head v3) top class not 'other'. Every other photo goes to
    the officer; reason 'other' (v3: top class is 'other') comes first, then 'unfamiliar', then 'low confidence'."""
    pred = P.argmax(1); conf = P.max(1) >= thr; fam = d <= cut
    oth = (pred == other) if other is not None else np.zeros(len(pred), bool)
    return pred, conf, fam, oth, conf & fam & ~oth


def forced_pred(P, other=None):
    """Answer if forced to name one of the five known classes (v3: 'other' is not a diagnosis, so it is skipped)."""
    if other is None:
        return P.argmax(1)
    Q = P.copy(); Q[:, other] = -1
    return Q.argmax(1)


def rule_metrics(L, d, yy, T, thr, cut, other=None):
    """Full decision rule on photos with known class (healthy / rust for field photos)."""
    P = softmax(L / T, axis=1)
    pred, conf, fam, oth, ans = route(P, d, thr, cut, other)
    fp = forced_pred(P, other)
    rust = yy == CI['rust']; hl = yy == CI['healthy']; R_ = CI['rust']
    nan = float('nan')
    extra = {} if other is None else {
        'routed_other': float(oth.mean()),
        'rust_routed_other': float((oth & rust).sum() / max(1, rust.sum())),
        'healthy_routed_other': float((oth & hl).sum() / max(1, hl.sum()))}
    return {'n': int(len(yy)), 'coverage': float(ans.mean()), 'not_sure': float(1 - ans.mean()),
            'acc_answered': float((pred[ans] == yy[ans]).mean()) if ans.any() else nan,
            'acc_all': float((fp == yy).mean()),
            'acc_not_sure_if_forced': float((fp[~ans] == yy[~ans]).mean()) if (~ans).any() else nan,
            'hvp_answered': float(((pred[ans] == 0) == (yy[ans] == 0)).mean()) if ans.any() else nan,
            'rust_named': float(((pred == R_) & ans & rust).sum() / max(1, rust.sum())),
            'healthy_flagged': float(((pred != CI['healthy']) & ans & hl).sum() / max(1, hl.sum())),
            'sens_answered_rust': float(((pred == R_) & ans & rust).sum() / max(1, (ans & rust).sum())),
            'fpr_answered_healthy_as_rust': float(((pred == R_) & ans & hl).sum() / max(1, (ans & hl).sum())),
            'ece': ece(P, yy), 'mean_confidence': float(P.max(1).mean()),
            'not_sure_low_confidence': float((~conf & fam & ~oth).mean()), 'not_sure_unfamiliar': float((~fam & ~oth).mean()),
            **extra}


def out_of_scope_metrics(L, d, T, thr, cut, other=None, classes=None):
    """Photos of something outside the five classes (mite): share sent to the officer ('not sure': low confidence,
    unfamiliar or, head v3, top class 'other') and what the answered ones are called."""
    classes = classes or CLASSES
    P = softmax(L / T, axis=1)
    pred, conf, fam, oth, ans = route(P, d, thr, cut, other)
    called = {classes[k]: int(((pred == k) & ans).sum()) for k in range(len(classes)) if ((pred == k) & ans).any()}
    n = max(1, len(L))
    out = {'n': int(len(L)), 'not_sure': float(1 - ans.mean()) if len(L) else float('nan'), 'answered_as': called,
           'not_sure_low_confidence': float((~conf & fam & ~oth).mean()) if len(L) else float('nan'),
           'not_sure_unfamiliar': float((~fam & ~oth).mean()) if len(L) else float('nan'),
           'called_rust': float(((pred == CI['rust']) & ans).sum() / n),
           'called_healthy': float(((pred == CI['healthy']) & ans).sum() / n)}
    if other is not None:
        out['routed_other'] = float(oth.sum() / n)
    return out


def lab_only_experiments(rows, Z, Zn, y, M, src):
    """The lab-only model and the new-region simulation (unchanged method; numbers as published before)."""
    out = {'what': 'Lab-only model (trained on lab photos only), used as a new-region simulation: field photos play '
                   'the photos of a region whose style the model has never seen.'}
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
    dc = fam(Zn[cal]); cut = float(np.percentile(dc, FAMILIAR_PCT))
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
    covp = {m: {k: [] for k in ks} for m in methods}; accap = {m: {k: [] for k in ks} for m in methods}
    for seed in range(5):
        r = np.random.default_rng(1000 + seed); perm = r.permutation(fidx)
        pool, test = perm[:len(perm) // 2], perm[len(perm) // 2:]
        order = r.permutation(len(pool))
        for k in ks:
            pick = pool[order[:k]]
            R = unit(np.vstack([Rn, Zn[pick]])) if k else Rn
            famt, d_t, _ = app_familiar(Zn[test], R, cut, Zn[pick] if k else None, LOCAL_C1)   # the app's rule
            famp = d_t <= cut                                                                   # previous rule
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
                ansp = famp & (P.max(1) >= thr)
                covp[meth][k].append(float(ansp.mean()))
                accap[meth][k].append(float((pr[ansp] == y[test][ansp]).mean()) if ansp.any() else float('nan'))
                if meth == 'prior_adapt' and k == 50:
                    yt = y[test]
                    op50.append((ans.mean(),
                                 ((pr == CI['rust']) & ans & (yt == CI['rust'])).sum() / max(1, (ans & (yt == CI['rust'])).sum()),
                                 ((pr == CI['rust']) & ans & (yt == CI['healthy'])).sum() / max(1, (ans & (yt == CI['healthy'])).sum())))
    out['learning_loop'] = {'lambda': lam, 'lambda_scores_inner': lam_scores, 'ks': ks, 'seeds': 5, 'order': 'random',
                            'curves': {m: {'acc_all': [float(np.mean(acc[m][k])) for k in ks],
                                           'acc_all_sd': [float(np.std(acc[m][k])) for k in ks],
                                           'coverage': [float(np.mean(covg[m][k])) for k in ks],
                                           'acc_answered': [float(np.nanmean(acca[m][k])) if not all(np.isnan(acca[m][k])) else None for k in ks],
                                           'coverage_previous_rule': [float(np.mean(covp[m][k])) for k in ks],
                                           'acc_answered_previous_rule': [float(np.nanmean(accap[m][k])) if not all(np.isnan(accap[m][k])) else None for k in ks]}
                                       for m in methods},
                            'familiarity_rule': ('app rule: k nearest of stored + officer rows within the cutoff, OR the '
                                                 f'nearest officer row within local_nearest_cutoff = {LOCAL_C1}; '
                                                 '*_previous_rule: k nearest only'),
                            'local_nearest_cutoff': LOCAL_C1,
                            'update_bytes_float16_head': int((W.size + b.size) * 2),
                            'update_bytes_int8_per_reference_photo': int(Z.shape[1] + 4)}
    # alternative backbone comparison (from ml/explore_shift.py runs), if present
    alt = os.path.join(RES, 'explore_emb_vit_small_patch14_dinov2.json')
    if os.path.exists(alt):
        a = json.load(open(alt))
        out['alt_backbone_dinov2_small'] = {'params_millions': 21.6, 'field_acc_no_local_labels': a['acc']['field'],
                                            'loop_prior_adapt': a['loop']['prior_adapt'],
                                            'setting': 'lab-only training, then the new-region learning loop'}

    cov50, sens50, fpr50 = (float(np.mean([o[i] for o in op50])) for i in range(3))
    out['village_sim'] = village_sim(cov50, sens50, fpr50)
    out['village_sim']['operating_point'] = 'lab-only model + 50 officer labels (learning-loop average)'

    # demo update: what one officer session (50 labels) would send to other phones; excludes demo sample photos
    r = np.random.default_rng(7)
    cand = [i for i in fidx if os.path.basename(rows[i]['path']) not in sample_files]  # demo photos never in the update
    assert len(cand) == len(fidx) - len([1 for i in fidx if os.path.basename(rows[i]['path']) in sample_files])
    pick = r.choice(cand, 50, replace=False)
    Wa, ba = adapt(Z[pick], y[pick], W, b, T, lam)
    qa, sa = quantise_rows(Zn[pick])
    # limit found: once field photos are familiar, the untaught pest is no longer caught (lab-only + demo update)
    Ru = unit(qa.astype(np.float32) * sa[:, None]); Rall = np.vstack([Rn, Ru])
    mite_i = np.where(M['mite'])[0]
    before = out_of_scope_metrics(logits(Z[mite_i], W, b), fam(Zn[mite_i]), T, thr, cut)
    fam_m, d_m, _ = app_familiar(Zn[mite_i], Rall, cut, Ru, LOCAL_C1)
    d_eff = np.where(fam_m, np.minimum(d_m, cut), d_m)   # familiar under the app rule <=> d_eff <= cut
    after = out_of_scope_metrics(logits(Z[mite_i], Wa, ba), d_eff, T, thr, cut)
    after_prev = out_of_scope_metrics(logits(Z[mite_i], Wa, ba), d_m, T, thr, cut)
    out['mite_after_demo_update_50'] = {'before': before, 'after': after, 'after_previous_rule': after_prev}

    art = dict(W=W, b=b, T=T, thr=thr, cut=cut, lam=lam, ref=ref, q=q, sc=sc, Rn=Rn, C=C,
               upd=dict(W=Wa, b=ba, q=qa, sc=sa, pick=pick))
    return out, art


def shipped_model(rows, Z, Zn, y, M, lab, lab_art, other=False, other_weight=None, other_budget=None, thr_known_only=False):
    """Shipped head. other=False: head v2 (five classes; lab + field photos). other=True: head v3 = v2 setup plus a 6th
    class 'other', trained on RoCoLe red-spider-mite photos (a problem outside the five; the app sends it to the officer).
    Scalars on out-of-fold data; 5-fold CV headline; held-out checks. Both versions are scored on the same rows.
    other_weight: weight of 'other' in training, as a multiple of its balanced weight (None = balanced).
    other_budget: if set, a constant is added to the 'other' score so that this share of known-class (healthy / rust)
    out-of-fold field photos has 'other' as top class; chosen without the scored fold, like the other scalars."""
    classes = SHIP_CLASSES if other else CLASSES
    K = len(classes); OI = classes.index(OTHER) if other else None
    name = np.array([os.path.basename(r['path']) for r in rows])
    hb_files, sample_files = held_out_files()
    field = np.where(M['field'])[0]
    hb_idx = field[np.isin(name[field], list(hb_files))]
    sm_idx = field[np.isin(name[field], list(sample_files))]          # demo samples of healthy / rust leaves
    sm_all = np.where(np.isin(name, list(sample_files)))[0]            # all 7 demo samples (one is a mite photo)
    assert len(hb_idx) == 60 and len(sm_all) == 7 and not set(hb_idx) & set(sm_all)
    lab_tr = np.where(M['train'])[0]; cal = np.where(M['calib'])[0]; mite = np.where(M['mite'])[0]
    yy = y.copy()
    if other:
        yy[mite] = OI
    # RoCoLe holds identical copies of some images (some under two labels). Group copies (cosine > DUP_COS), keep every
    # copy of a held-out photo out of training, and keep copies in one CV fold.
    ro = np.r_[field, mite]; S = Zn[ro] @ Zn[ro].T; np.fill_diagonal(S, -1)
    parent = np.arange(len(ro))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    pa, pb = np.where(np.triu(S > DUP_COS, 1))
    for a_, b_ in zip(pa, pb):
        parent[find(a_)] = find(b_)
    group = {int(ro[k]): int(find(k)) for k in range(len(ro))}
    glabels = {}
    for i in ro:
        glabels.setdefault(group[int(i)], set()).add(str(lab[i]))
    conflict = {g for g, s_ in glabels.items() if len(s_) > 1}           # copy groups carrying two different labels
    held = {group[int(i)] for i in np.r_[hb_idx, sm_all]}                # human-baseline photos and demo samples
    held_v2 = held | {group[int(i)] for i in mite}                       # v2 also kept every mite photo out
    cand = field[~np.isin(field, np.r_[hb_idx, sm_idx])]
    dup_held = cand[[group[int(i)] in held_v2 for i in cand]]
    ftr = cand[~np.isin(cand, dup_held)]                                 # training field photos (healthy / rust)
    # the same healthy / rust rows under the v3 rule (drop held-out and label-conflicting copy groups)
    ftr_v3 = cand[[group[int(i)] not in held and group[int(i)] not in conflict for i in cand]]
    assert set(ftr_v3.tolist()) == set(ftr.tolist()), 'v2 and v3 healthy/rust training rows differ'
    # mite photos a v3 head may train on: not a demo sample or a copy of a held-out photo, not in a conflicting group
    mcand = mite[~np.isin(mite, sm_all)]
    mtr = mcand[[group[int(i)] not in held and group[int(i)] not in conflict for i in mcand]]
    mout = mite[~np.isin(mite, mtr)]                                     # never trained on by v3
    mite_conflict = mite[[group[int(i)] in conflict for i in mite]]
    dups = {'cosine_threshold': DUP_COS, 'pairs': int(len(pa)),
            'pairs_with_different_labels': int((lab[ro][pa] != lab[ro][pb]).sum()),
            'label_pairs': {f'{a_}/{b_}': int(n_) for (a_, b_), n_ in
                            zip(*np.unique(np.sort(np.c_[lab[ro][pa], lab[ro][pb]], axis=1), axis=0, return_counts=True))},
            'groups_with_different_labels': int(len(conflict)),
            'photos_in_groups_with_different_labels': {l_: int(sum(group[int(i)] in conflict for i in ro if lab[i] == l_))
                                                       for l_ in ('healthy', 'rust', 'mite')},
            'training_candidates_removed_as_copies_of_held_out': int(len(dup_held))}
    yf = yy[ftr]; yc = yy[cal]; ym = yy[mtr]
    lab_ref = lab_art['ref']

    # stratified 5-fold assignment over the training field photos; identical copies share a fold (as in v2)
    rf = np.random.default_rng(2026); fold = np.empty(len(ftr), int)
    gf = np.array([group[int(i)] for i in ftr])
    for k in (CI['healthy'], CI['rust']):
        ug = np.unique(gf[yf == k]); ug = ug[~np.isin(ug, gf[yf != k])] if k == CI['rust'] else ug
        rf.shuffle(ug); gfold = {g: j % SHIP_FOLDS for j, g in enumerate(ug)}
        for j in np.where(np.isin(gf, ug))[0]:
            fold[j] = gfold[gf[j]]
    # mite photos get their own fold assignment (copy groups together); v2 only scores them, v3 also trains on them
    rm = np.random.default_rng(2028); gm = np.array([group[int(i)] for i in mtr]); ugm = np.unique(gm); rm.shuffle(ugm)
    gmf = {g: j % SHIP_FOLDS for j, g in enumerate(ugm)}; mfold = np.array([gmf[g] for g in gm], int)
    rref = np.random.default_rng(2027)

    def reference(field_rows):
        pick = np.concatenate([rref.choice(field_rows[y[field_rows] == k], SHIP_REF_FIELD_PER_CLASS, replace=False)
                               for k in (CI['healthy'], CI['rust'])])
        rr = np.concatenate([lab_ref, pick])
        q, sc = quantise_rows(Zn[rr])
        return rr, q, sc, unit(q.astype(np.float32) * sc[:, None])

    def train_rows(f=None):
        rows_ = [lab_tr, ftr if f is None else ftr[fold != f]]
        if other:
            rows_.append(mtr if f is None else mtr[mfold != f])
        return np.concatenate(rows_)

    # C on calibration NLL: out-of-fold field logits + BRACOL calibration logits (mean of the fold heads)
    c_scores, heads_by_C = {}, {}
    for C in SHIP_C_GRID:
        Lo = np.zeros((len(ftr), K)); Lmo = np.zeros((len(mtr), K)); Lcal = np.zeros((len(cal), K)); heads = []
        for f in range(SHIP_FOLDS):
            trn = train_rows(f)
            W_, b_ = fit_head(Z[trn], yy[trn], C, K, other_weight if other else None)
            Lo[fold == f] = logits(Z[ftr[fold == f]], W_, b_); Lcal += logits(Z[cal], W_, b_) / SHIP_FOLDS
            Lmo[mfold == f] = logits(Z[mtr[mfold == f]], W_, b_)
            heads.append((W_, b_))
        if other:
            c_scores[C] = nll(np.vstack([Lcal, Lo, Lmo]), np.r_[yc, yf, ym])
        else:
            c_scores[C] = nll(np.vstack([Lcal, Lo]), np.r_[yc, yf])
        heads_by_C[C] = heads
    C = min(c_scores, key=c_scores.get); heads = heads_by_C[C]

    # out-of-fold predictions and distances (reference from that fold's training rows only)
    Lo = np.zeros((len(ftr), K)); do = np.zeros(len(ftr)); Lmo = np.zeros((len(mtr), K)); dmo = np.zeros(len(mtr))
    per_fold = []
    for f, (W_, b_) in enumerate(heads):
        te_ = fold == f; tm = mfold == f
        _, _, _, Rf = reference(ftr[~te_])
        Lo[te_] = logits(Z[ftr[te_]], W_, b_); do[te_] = knn_dist(Zn[ftr[te_]], Rf)
        Lmo[tm] = logits(Z[mtr[tm]], W_, b_); dmo[tm] = knn_dist(Zn[mtr[tm]], Rf)
        per_fold.append(dict(Lcal=logits(Z[cal], W_, b_), dcal=knn_dist(Zn[cal], Rf),
                             Lmite=logits(Z[mite], W_, b_), dmite=knn_dist(Zn[mite], Rf)))

    def shift(L, bo):
        if not other or not bo:
            return L
        L = L.copy(); L[:, OI] += bo
        return L

    def other_bias(f=None):
        """constant added to the 'other' score: at most other_budget of the known-class out-of-fold field photos
        (of the other folds when f is given) get 'other' as top class"""
        if not other or other_budget is None:
            return 0.0
        L = Lo if f is None else Lo[fold != f]
        m = L[:, OI] - np.delete(L, OI, axis=1).max(1)      # 'other' wins when m + bias > 0
        return float(-np.quantile(m, 1 - other_budget))

    def scalars(Lc, dc, f=None, bo=0.0):
        """T, threshold, cutoff on BRACOL calibration + out-of-fold rows (of the other folds when f is given).
        Lc must already include the 'other' bias bo."""
        o = np.ones(len(ftr), bool) if f is None else fold != f
        if not other:
            return choose_scalars(np.vstack([Lc, Lo[o]]), np.r_[dc, do[o]], np.r_[yc, yf[o]])
        om = np.ones(len(mtr), bool) if f is None else mfold != f
        dmask = np.r_[np.ones(len(cal) + o.sum(), bool), np.zeros(om.sum(), bool)]
        return choose_scalars(np.vstack([Lc, shift(Lo[o], bo), shift(Lmo[om], bo)]), np.r_[dc, do[o], dmo[om]],
                              np.r_[yc, yf[o], ym[om]], other=OI, dmask=dmask, thr_mask=dmask if thr_known_only else None)

    # cross-validated headline: fold f scored with scalars chosen on BRACOL calibration + the OTHER folds' OOF rows
    cv, cv_mite_all, cv_mite, cv_scalars, cv_auroc, cv_comb = [], [], [], [], [], []
    for f, pf in enumerate(per_fold):
        te_ = fold == f; tm = mfold == f
        bo = other_bias(f)
        T_, thr_, cut_ = scalars(shift(pf['Lcal'], bo), pf['dcal'], f, bo)
        cv_scalars.append({'temperature': T_, 'threshold': thr_, 'familiarity_cutoff': cut_, 'other_bias': bo})
        Lt = shift(Lo[te_], bo); Lmt = shift(Lmo[tm], bo)
        cv.append(rule_metrics(Lt, do[te_], yf[te_], T_, thr_, cut_, OI))
        # mite photos of this fold (never trained on by this fold's head, in either version)
        cv_mite.append(out_of_scope_metrics(Lmt, dmo[tm], T_, thr_, cut_, OI, classes))
        if not other:  # v2: every mite photo is outside training, so each fold head is also scored on all of them
            cv_mite_all.append(out_of_scope_metrics(pf['Lmite'], pf['dmite'], T_, thr_, cut_))
        # all field photos of this fold together (healthy, rust, mite): what a village rust count would be built from
        Pt = softmax(Lt / T_, axis=1); Pm = softmax(Lmt / T_, axis=1)
        pt, _, _, _, at = route(Pt, do[te_], thr_, cut_, OI); pm, _, _, _, am = route(Pm, dmo[tm], thr_, cut_, OI)
        rust_ans = ((pt == CI['rust']) & at).sum() + ((pm == CI['rust']) & am).sum()
        cv_comb.append({'n': int(te_.sum() + tm.sum()), 'coverage': float((at.sum() + am.sum()) / (te_.sum() + tm.sum())),
                        'acc_answered': float((pt[at] == yf[te_][at]).sum() / max(1, at.sum() + am.sum())),
                        'rust_answers_that_are_mite': float(((pm == CI['rust']) & am).sum() / max(1, rust_ans))})
        # can the 'not sure' signals tell an untaught pest from known field leaves? (mite = positive class)
        Lm_ = pf['Lmite'] if not other else Lmt; dm_ = pf['dmite'] if not other else dmo[tm]
        conf_t = softmax(Lt / T_, axis=1).max(1); conf_m = softmax(Lm_ / T_, axis=1).max(1)
        lab01 = np.r_[np.zeros(te_.sum()), np.ones(len(Lm_))]
        au = {'confidence': float(roc_auc_score(lab01, -np.r_[conf_t, conf_m])),
              'familiarity_distance': float(roc_auc_score(lab01, np.r_[do[te_], dm_]))}
        if other:
            au['p_other'] = float(roc_auc_score(lab01, np.r_[softmax(Lt / T_, axis=1)[:, OI], softmax(Lm_ / T_, axis=1)[:, OI]]))
        cv_auroc.append(au)
    summ = lambda lst: {**{k: float(np.nanmean([c[k] for c in lst])) for k in lst[0] if isinstance(lst[0][k], float)},
                        **{k + '_sd': float(np.nanstd([c[k] for c in lst])) for k in lst[0] if isinstance(lst[0][k], float)}}
    cv_sum = summ(cv); cv_sum['n_per_fold'] = [c['n'] for c in cv]
    mite_cv_sum = summ(cv_mite); mite_cv_sum['n_per_fold'] = [c['n'] for c in cv_mite]
    comb_sum = summ(cv_comb); comb_sum['n_per_fold'] = [c['n'] for c in cv_comb]
    mite_all = cv_mite_all if not other else cv_mite
    mite_cv = {'not_sure': float(np.mean([m['not_sure'] for m in mite_all])),
               'not_sure_sd': float(np.std([m['not_sure'] for m in mite_all])),
               'auroc_mite_vs_field': {k: float(np.mean([a[k] for a in cv_auroc])) for k in cv_auroc[0]}}

    # final shipped head: all training rows; scalars on BRACOL calibration + all out-of-fold rows
    all_tr = train_rows()
    W, b = fit_head(Z[all_tr], yy[all_tr], C, K, other_weight if other else None)
    bo = other_bias()
    if other:
        b = b.copy(); b[OI] += bo           # the 'other' bias is baked into the exported head
    ref_rows, q, sc, R = reference(ftr)
    T, thr, cut = scalars(logits(Z[cal], W, b), knn_dist(Zn[cal], R), None, bo)

    ev = lambda idx: rule_metrics(logits(Z[idx], W, b), knn_dist(Zn[idx], R), yy[idx], T, thr, cut, OI)
    held_out = {'human_baseline_60': ev(hb_idx), 'demo_samples_healthy_rust': ev(sm_idx)}
    Ps = softmax(logits(Z[sm_all], W, b) / T, axis=1); ds = knn_dist(Zn[sm_all], R)
    ps_, cs_, fs_, os_, as_ = route(Ps, ds, thr, cut, OI)
    held_out['demo_samples_7'] = [
        {'original_file': str(name[i]), 'truth': str(lab[i]), 'pred': classes[int(p.argmax())],
         'confidence': round(float(p.max()), 3), 'distance': round(float(dd), 3), 'answered': bool(a_),
         'route': 'answered' if a_ else ('other' if o_ else ('unfamiliar' if not f_ else 'low_confidence'))}
        for i, p, dd, a_, o_, f_ in zip(sm_all, Ps, ds, as_, os_, fs_)]
    if not other:
        held_out['mite'] = out_of_scope_metrics(logits(Z[mite], W, b), knn_dist(Zn[mite], R), T, thr, cut)
        held_out['mite']['how'] = 'final head on all mite photos (none trained on)'
    else:
        # every mite photo scored by a head that never saw it or a copy of it: out-of-fold for the photos used in
        # training (each with its fold's scalars), the final head for the others (demo sample, copies, conflicting groups)
        Lmo_b = Lmo.copy(); Lmo_b[:, OI] += np.array([cv_scalars[f]['other_bias'] for f in mfold])
        Lp = np.vstack([Lmo_b, logits(Z[mout], W, b)]); dp = np.r_[dmo, knn_dist(Zn[mout], R)]
        Tp = np.r_[[cv_scalars[f]['temperature'] for f in mfold], np.full(len(mout), T)]
        thp = np.r_[[cv_scalars[f]['threshold'] for f in mfold], np.full(len(mout), thr)]
        cp = np.r_[[cv_scalars[f]['familiarity_cutoff'] for f in mfold], np.full(len(mout), cut)]
        Pp = softmax(Lp / Tp[:, None], axis=1)
        pred = Pp.argmax(1); conf = Pp.max(1) >= thp; fam = dp <= cp; oth = pred == OI; ans = conf & fam & ~oth
        held_out['mite'] = {'n': int(len(Lp)), 'not_sure': float(1 - ans.mean()), 'routed_other': float(oth.mean()),
                            'answered_as': {classes[k]: int(((pred == k) & ans).sum()) for k in range(K) if ((pred == k) & ans).any()},
                            'not_sure_low_confidence': float((~conf & fam & ~oth).mean()),
                            'not_sure_unfamiliar': float((~fam & ~oth).mean()),
                            'how': f'out-of-fold for the {len(mtr)} mite photos used in training (5-fold, scalars chosen '
                                   f'without the fold), final head for the {len(mout)} never trained on'}
        held_out['mite_never_trained'] = out_of_scope_metrics(logits(Z[mout], W, b), knn_dist(Zn[mout], R), T, thr, cut, OI, classes)
    held_out['mite']['cv_mean_not_sure'] = mite_cv['not_sure']; held_out['mite']['cv_sd_not_sure'] = mite_cv['not_sure_sd']
    held_out['mite']['auroc_mite_vs_field_cv'] = mite_cv['auroc_mite_vs_field']
    # lab-style photos are still handled (calibration half: used only for the three scalars, never for the head)
    lab_style = {'bracol_calibration_half': rule_metrics(logits(Z[cal], W, b), knn_dist(Zn[cal], R), yc, T, thr, cut, OI),
                 'jmuben_val_optimistic': rule_metrics(logits(Z[M['val']], W, b), knn_dist(Zn[M['val']], R), y[M['val']], T, thr, cut, OI)}
    # near-duplicate check: closest training field photo to each held-out human-baseline photo (cosine similarity)
    trf = np.r_[ftr, mtr] if other else ftr
    sim = (Zn[hb_idx] @ Zn[trf].T).max(1)
    dup = {'max_cosine_to_training_field': float(sim.max()), 'median_cosine_to_training_field': float(np.median(sim)),
           'n_above_dup_threshold': int((sim > DUP_COS).sum())}

    n_tr = {'lab': int(len(lab_tr)), 'field': int(len(ftr)), 'field_healthy': int((yf == CI['healthy']).sum()),
            'field_rust': int((yf == CI['rust']).sum()), 'field_other_mite': int(len(mtr)) if other else 0,
            'total': int(len(all_tr))}
    mite_split = {'mite_total': int(len(mite)), 'mite_used_for_training_v3': int(len(mtr)),
                  'mite_never_trained_v3': int(len(mout)), 'mite_demo_sample': int(len(np.intersect1d(sm_all, mite))),
                  'mite_in_groups_with_different_labels': int(len(mite_conflict)),
                  'mite_copies_of_held_out_photos': int(len(mout) - len(np.intersect1d(sm_all, mite))
                                                        - len(np.setdiff1d(mite_conflict, sm_all)))}
    ver = 'v3 (lab + field photos + "other" class from mite photos)' if other else 'v2 (lab + field photos)'
    out = {'what': f'Shipped model head {ver}. Field numbers are 5-fold cross-validated.', 'classes': classes,
           'C': C, 'c_scores_calibration_nll': {str(k): v for k, v in c_scores.items()},
           'other_weight': other_weight if other else None, 'other_budget': other_budget if other else None,
           'other_bias': bo if other else None, 'threshold_rule_on_known_classes_only': bool(thr_known_only) if other else None,
           'temperature': T, 'threshold': thr, 'familiarity_cutoff': cut, 'knn': KNN,
           'reference_n': int(len(ref_rows)), 'reference_rows': {'lab': int(len(lab_ref)), 'field': int(len(ref_rows) - len(lab_ref))},
           'prior_strength': lab_art['lam'], 'n_train': n_tr, 'mite_split': mite_split,
           'held_out_never_trained': {'human_baseline': 60, 'demo_samples': 7, 'mite': int(len(mout) if other else len(mite))},
           'field_cv': {'folds': SHIP_FOLDS, 'summary': cv_sum, 'per_fold': cv, 'scalars_per_fold': cv_scalars,
                        'mite_summary': mite_cv_sum, 'mite_per_fold': cv_mite,
                        'all_field_with_mite_summary': comb_sum, 'all_field_with_mite_per_fold': cv_comb,
                        'mite_all_167_per_fold_v2': cv_mite_all,
                        'method': 'Stratified 5-fold CV over the training field photos (healthy, rust; copy groups kept '
                                  'in one fold). The mite photos that v3 may train on get their own 5-fold assignment; '
                                  'v2 only scores them, v3 also trains on the other 4 folds. Each fold: head trained on '
                                  'all lab training rows + the other 4 folds; familiarity reference = the 1,000 lab rows + '
                                  '200 healthy + 200 rust from the other 4 folds (int8, as on the phone; no mite photos); '
                                  'temperature, threshold and cutoff chosen on the BRACOL calibration half + out-of-fold '
                                  'rows of the other 4 folds (v3: the cutoff on the photos of the five known classes, '
                                  'the threshold counting only photos whose top class is not "other" as answered); scored '
                                  'with the full decision rule on the held-out fold.'},
           'held_out': held_out, 'lab_style': lab_style, 'rocole_identical_copies': dups,
           'near_duplicate_check_human_baseline': dup}
    art = dict(W=W, b=b, T=T, thr=thr, cut=cut, q=q, sc=sc, ref_n=int(len(ref_rows)), C=C, classes=classes)
    return out, art


def write_reference(q, sc, path):
    q.tofile(path)
    with open(path, 'ab') as fh:
        fh.write(sc.astype('<f4').tobytes())


def head_json(version, W, b, T, thr, cut, ref_file, ref_n, lam, dim, classes=None, local_c1=None, **extra):
    h = {'version': version, 'classes': list(classes or CLASSES), 'embed_dim': int(dim),
         'W': np.round(W, 6).tolist(), 'b': np.round(b, 6).tolist(), 'temperature': round(T, 5),
         'threshold': round(thr, 4),
         'ood': {'metric': 'knn_cosine', 'k': KNN, 'cutoff': round(cut, 5),
                 'reference': {'file': ref_file, 'n': int(ref_n), 'dim': int(dim),
                               'format': 'n*dim int8 (row-major) followed by n float32 little-endian per-row scales; '
                                         'row = int8*scale, then L2-normalise. Query: L2-normalise the embedding; '
                                         'distance = 1 - mean of the k largest cosine similarities.'}},
         'prior_strength': lam, 'standardised_in_backbone': True}
    if local_c1 is not None:   # nearest-officer-row rule (results/familiarity_rule.json)
        h['ood']['local_nearest_cutoff'] = round(float(local_c1), 4)
        h['ood']['local_nearest_rule'] = ('A photo also counts as familiar when officer-labelled rows exist (labelled on '
                                          'this phone or received in an officer update; never reference rows) and '
                                          '1 - cosine similarity to the single nearest of them <= local_nearest_cutoff.')
    h.update(extra)
    return h


def main():
    rows, E = load()
    M, src, lab = split_masks(rows)
    y = np.array([CI.get(l, -1) for l in lab])
    # standardisation: lab training rows (kept for the shipped model; see module docstring)
    mu = E[M['train']].mean(0); sd = E[M['train']].std(0) + 1e-6
    p_lab = os.path.join(WORK, 'standardisation_labonly.npz')
    if os.path.exists(p_lab):
        s0 = np.load(p_lab)
        assert np.array_equal(s0['mu'], mu) and np.array_equal(s0['sd'], sd), 'lab-only standardisation changed'
    else:
        np.savez(p_lab, mu=mu, sd=sd)
    Z = (E - mu) / sd
    Zn = unit(Z)
    out = {'n': {k: int(v.sum()) for k, v in M.items()}, 'n_by_source_label': {},
           'notes': ['Standardisation: the embedding mean/sd baked into model/backbone.onnx are computed on the 7,045 lab '
                     'training rows and are kept unchanged for the shipped lab+field model, so backbone.onnx, every saved '
                     'embedding and the lab-only files work with the same backbone.',
                     'Shipped model: the RoCoLe copy has no plant IDs, so leaves of one plant can sit in both a training '
                     'and a test fold of the cross-validation; the cross-validated field numbers may be optimistic. '
                     'The 60 human-baseline photos are a second check that was never trained on.',
                     'All field photos (training and test) are Ecuadorian robusta from one dataset (RoCoLe); no photo '
                     'comes from Kenyan farms.',
                     'Shipped model: temperature, threshold and familiarity cutoff are chosen on the BRACOL calibration '
                     'half plus out-of-fold field predictions; in the cross-validation each fold is scored with values '
                     'chosen without that fold.',
                     'Shipped model: prior_strength (how hard the on-phone learning step pulls toward the shipped head) '
                     'is the value chosen in the lab-only new-region simulation; no held-out new-region photos exist '
                     'to tune it for the shipped head.',
                     'Lab-only model: JMuBEN contains rotated/flipped copies of the same leaf, so in_domain_val is optimistic.',
                     'Lab-only model: calibration (temperature, threshold, familiarity cutoff) uses only the held-out half '
                     'of BRACOL, a different source from most training photos.',
                     'Lab-only learning loop: pool and test photos both come from RoCoLe (one region of Ecuador); real '
                     'farms vary more.']}
    for s_ in np.unique(src):
        for l in np.unique(lab[src == s_]):
            out['n_by_source_label'][f'{s_}/{l}'] = int(((src == s_) & (lab == l)).sum())

    lab_out, la = lab_only_experiments(rows, Z, Zn, y, M, src)
    ship_v2, sa2 = shipped_model(rows, Z, Zn, y, M, lab, la, other=False)   # head v2, kept for reference
    ship_out, sa = shipped_model(rows, Z, Zn, y, M, lab, la, other=True, other_budget=SHIP_OTHER_BUDGET,
                                 thr_known_only=True)                        # head v3 (shipped)
    # paired comparison on the same folds (healthy / rust rows and fold assignment are identical in v2 and v3)
    pf2, pf3 = ship_v2['field_cv']['per_fold'], ship_out['field_cv']['per_fold']
    ship_out['paired_vs_v2'] = {k: {'per_fold_difference': [b_[k] - a_[k] for a_, b_ in zip(pf2, pf3)],
                                    'mean_difference': float(np.mean([b_[k] - a_[k] for a_, b_ in zip(pf2, pf3)])),
                                    'folds_lower': int(sum(b_[k] < a_[k] for a_, b_ in zip(pf2, pf3)))}
                                for k in ('coverage', 'acc_answered', 'rust_named', 'healthy_flagged', 'acc_all')}
    # the trade-off behind the choice of SHIP_OTHER_BUDGET (each setting cross-validated the same way)
    trade = []
    for bud, tk in SHIP_OTHER_TRADEOFF:
        o_, _ = shipped_model(rows, Z, Zn, y, M, lab, la, other=True, other_budget=bud, thr_known_only=tk)
        c_ = o_['field_cv']['summary']; m_ = o_['field_cv']['mite_summary']; hm_ = o_['held_out']['mite']
        trade.append({'other_budget': bud, 'threshold_rule_on_known_classes_only': tk, 'shipped': (bud, tk) == (SHIP_OTHER_BUDGET, True),
                      **{k: c_[k] for k in ('coverage', 'acc_answered', 'rust_named', 'healthy_flagged', 'rust_routed_other')},
                      'mite_sent_to_officer_cv': m_['not_sure'], 'mite_routed_other_cv': m_['routed_other'],
                      'mite_sent_to_officer_167': hm_['not_sure'], 'mite_called_rust_167': hm_['answered_as'].get('rust', 0),
                      'mite_called_healthy_167': hm_['answered_as'].get('healthy', 0),
                      'rust_answers_that_are_mite': o_['field_cv']['all_field_with_mite_summary']['rust_answers_that_are_mite']})
    ship_out['other_tradeoff'] = {'what': 'Head v3 settings, each 5-fold cross-validated like the shipped head. other_budget = '
                                          'share of known-class out-of-fold field photos allowed to have "other" as top class '
                                          '(None = no adjustment); threshold_rule_on_known_classes_only = the 90% accuracy rule '
                                          'for the confidence threshold is checked on healthy / rust / lab photos only, as in '
                                          'v2 (False = mite photos answered as rust or healthy count as errors in that rule).',
                                  'rows': trade}
    s2 = ship_v2['field_cv']['summary']
    ship_v2['village_sim'] = village_sim(s2['coverage'], s2['sens_answered_rust'], s2['fpr_answered_healthy_as_rust'])
    ship_v2['village_sim']['operating_point'] = 'head v2 (lab + field), 5-fold cross-validated on field photos'
    out['shipped'] = ship_out
    out['shipped_v2'] = ship_v2
    out['lab_only_new_region_simulation'] = lab_out
    s = ship_out['field_cv']['summary']
    out['village_sim'] = village_sim(s['coverage'], s['sens_answered_rust'], s['fpr_answered_healthy_as_rust'])
    out['village_sim']['operating_point'] = ('shipped model (head v3: lab + field + "other"), 5-fold cross-validated on '
                                             'healthy and rust field photos')
    json.dump(out, open(os.path.join(RES, 'metrics.json'), 'w'), indent=1)

    # limits.json: the out-of-scope pest, for both models
    lm = lab_out['mite_after_demo_update_50']; sm = ship_out['held_out']['mite']; sm2 = ship_v2['held_out']['mite']
    lim = {'out_of_scope_pest_after_50_labels': {
               'model': 'lab-only model + the 50-label demo update (new-region simulation)',
               'dataset': f"RoCoLe red spider mite ({lm['after']['n']} photos)",
               'not_sure_before': round(lm['before']['not_sure'], 3), 'not_sure_after_50': round(lm['after']['not_sure'], 3),
               'answered_as_after_50': lm['after']['answered_as']},
           'out_of_scope_pest_shipped_model': {
               'model': 'shipped model, head v3 (lab + field + "other" class trained on mite photos)',
               'dataset': f"RoCoLe red spider mite ({sm['n']} photos; each scored by a head that never saw it or a copy)",
               'sent_to_officer': round(sm['not_sure'], 3), 'routed_other': round(sm['routed_other'], 3),
               'answered_as': sm['answered_as'], 'how': sm['how'],
               'sent_to_officer_cv_mean': round(sm['cv_mean_not_sure'], 3),
               'auroc_mite_vs_field_cv': {k: round(v, 3) for k, v in sm['auroc_mite_vs_field_cv'].items()}},
           'out_of_scope_pest_shipped_v2': {
               'model': 'head v2 (lab + field, five classes), kept for reference',
               'dataset': f"RoCoLe red spider mite ({sm2['n']} photos, never trained on)",
               'not_sure': round(sm2['not_sure'], 3), 'answered_as': sm2['answered_as'],
               'not_sure_cv_mean': round(sm2['cv_mean_not_sure'], 3),
               'auroc_mite_vs_field_cv': {k: round(v, 3) for k, v in sm2['auroc_mite_vs_field_cv'].items()}},
           'meaning': 'Once field photos are familiar, the familiarity check no longer catches a pest the model was never '
                      'taught: those photos look like the field photos it knows (head v2 and the lab-only model after 50 '
                      'labels). Head v3 adds an "other" answer learned from mite photos; the app sends those photos to the '
                      'officer and never counts them as rust. It has learned one pest from one dataset only.',
           'mitigations': [
               'Head v3 "other" class (trained on RoCoLe mite photos): top class "other" means the photo goes to the officer.',
               'Officer review screen offers "different problem / not in list"; that label trains the "other" class in the '
               'on-phone update.',
               'Spot-check: 1 in 10 answered photos is also queued for the officer, so errors and drift are seen.',
               'Plot card never says a plot is disease-free; the checklist covers what photos cannot see.'],
           'plan': ['Collect officer-labelled field photos of other look-alike problems (other pests, brown eye spot, '
                    'nutrient deficiency) through the "different problem" label during a pilot; they train the same '
                    '"other" class.',
                    'Keep a set of those photos out of training to test the "other" class on problems it has not seen.']}
    json.dump(lim, open(os.path.join(RES, 'limits.json'), 'w'), indent=1)

    # --- export: lab-only files (starter kit, new-region simulation) ---
    today = str(np.datetime64('today'))
    write_reference(la['q'], la['sc'], os.path.join(MODEL, 'reference_labonly.bin'))
    hl = head_json('v1-' + today, la['W'], la['b'], la['T'], la['thr'], la['cut'], 'reference_labonly.bin',
                   len(la['ref']), la['lam'], Z.shape[1], local_c1=LOCAL_C1,
                   role='lab-only base model for the new-region simulation and ml/starter_kit.py (not shipped in the app)',
                   trained_on='JMuBEN+JMuBEN2 (Kenya, Kirinyaga; 1,500 sampled per class) + half of BRACOL (Brazil)',
                   calibrated_on='held-out half of BRACOL',
                   field_test={'dataset': 'RoCoLe (Ecuador, robusta, on-plant)', 'coverage': round(lab_out['field']['coverage'], 3),
                               'acc_all': round(lab_out['field']['acc_all'], 3)})
    json.dump(hl, open(os.path.join(MODEL, 'head_labonly.json'), 'w'))
    u = la['upd']
    upd = {'kind': 'kahawa-head-update', 'base_version': hl['version'], 'base_head': 'head_labonly.json', 'n_labels': 50,
           'source': 'DEMO: 50 RoCoLe field photos labelled by the dataset authors, standing in for an officer session',
           'W': np.round(u['W'], 6).tolist(), 'b': np.round(u['b'], 6).tolist(),
           'reference_add': {'int8': u['q'].astype(int).tolist(), 'scale': u['sc'].tolist()},
           'labels': [CLASSES[int(y[i])] for i in u['pick']]}
    json.dump(upd, open(os.path.join(MODEL, 'update_demo_50_labonly.json'), 'w'))
    old_upd = os.path.join(MODEL, 'update_demo_50.json')
    if os.path.exists(old_upd):  # it adapts the lab-only head; the app would reject it against the shipped head
        os.remove(old_upd)

    # --- export: what the phone runs (shipped model, head v3) ---
    write_reference(sa['q'], sa['sc'], os.path.join(MODEL, 'reference.bin'))
    cv = ship_out['field_cv']['summary']; nt = ship_out['n_train']; msum = ship_out['field_cv']['mite_summary']
    head = head_json(f'v3-{today}-lab+field+other', sa['W'], sa['b'], sa['T'], sa['thr'], sa['cut'], 'reference.bin',
                     sa['ref_n'], la['lam'], Z.shape[1], classes=sa['classes'], local_c1=LOCAL_C1,
                     route_to_officer=[OTHER],
                     route_to_officer_note='Classes listed here are never shown as a diagnosis: when one is the top class, '
                                           'the photo goes to the officer ("looks like a different problem").',
                     trained_on=f"JMuBEN+JMuBEN2 (Kenya, Kirinyaga; 1,500 sampled per class) + half of BRACOL (Brazil) "
                                f"+ {nt['field']} RoCoLe field photos (Ecuador, robusta, on-plant; {nt['field_healthy']} healthy, "
                                f"{nt['field_rust']} rust) + {nt['field_other_mite']} RoCoLe red-spider-mite photos as 'other'. "
                                f"Not trained on: 60 human-baseline photos, 7 demo samples (one is a mite photo), copies of "
                                f"those, and copy groups that carry two different labels.",
                     calibrated_on='held-out half of BRACOL + out-of-fold predictions for the training field photos (5-fold)',
                     field_test={'dataset': 'RoCoLe (Ecuador, robusta, on-plant)', 'method': '5-fold cross-validation',
                                 'coverage': round(cv['coverage'], 3), 'acc_answered': round(cv['acc_answered'], 3),
                                 'acc_all': round(cv['acc_all'], 3),
                                 'mite_sent_to_officer': round(msum['not_sure'], 3)},
                     standardisation='lab training rows (same as head_labonly.json)')
    json.dump(head, open(os.path.join(MODEL, 'head.json'), 'w'))
    if LOCAL_C1 is not None:
        fr = json.load(open(FAM_RULE_JSON))
        if abs(float(fr.get('shipped_cutoff', -1)) - round(sa['cut'], 5)) > 1e-9:
            print(f"WARNING: results/familiarity_rule.json chose c1 for cutoff {fr.get('shipped_cutoff')}, the new head has "
                  f"{round(sa['cut'], 5)}: rerun ml/eval_familiarity_rule.py and check its decision")
    # head v2 (five classes), kept outside the app for reference and for ml/score_baseline.py
    d2 = os.path.join(WORK, 'shipped_v2'); os.makedirs(d2, exist_ok=True)
    write_reference(sa2['q'], sa2['sc'], os.path.join(d2, 'reference.bin'))
    cv2 = ship_v2['field_cv']['summary']
    json.dump(head_json(f'v2-{today}-lab+field', sa2['W'], sa2['b'], sa2['T'], sa2['thr'], sa2['cut'], 'reference.bin',
                        sa2['ref_n'], la['lam'], Z.shape[1], local_c1=LOCAL_C1, role='head v2, replaced by head v3 in the app; reference only',
                        field_test={'dataset': 'RoCoLe (Ecuador, robusta, on-plant)', 'method': '5-fold cross-validation',
                                    'coverage': round(cv2['coverage'], 3), 'acc_answered': round(cv2['acc_answered'], 3),
                                    'acc_all': round(cv2['acc_all'], 3)},
                        standardisation='lab training rows (same as head_labonly.json)'),
              open(os.path.join(d2, 'head.json'), 'w'))

    p_std = os.path.join(WORK, 'standardisation.npz')
    same = os.path.exists(p_std) and all(np.array_equal(np.load(p_std)[k], v) for k, v in (('mu', mu), ('sd', sd)))
    if not same or '--export-backbone' in sys.argv:
        np.savez(p_std, mu=mu, sd=sd)
        export_backbone_with_standardisation(mu, sd)
        print('backbone.onnx re-exported')
    else:
        print('standardisation unchanged: backbone.onnx left as is')

    for nm_, so_ in (('V2', ship_v2), ('V3', ship_out)):
        print(nm_, 'CV', json.dumps({k: round(v, 3) for k, v in so_['field_cv']['summary'].items() if isinstance(v, float) and not k.endswith('_sd')}))
        print(nm_, 'mite CV', json.dumps({k: round(v, 3) for k, v in so_['field_cv']['mite_summary'].items() if isinstance(v, float)}))
        print(nm_, 'all+mite CV', json.dumps({k: round(v, 3) for k, v in so_['field_cv']['all_field_with_mite_summary'].items() if isinstance(v, float)}))
        print(nm_, 'mite held/pooled', so_['held_out']['mite'])
        print(nm_, 'C', so_['C'], 'T', round(so_['temperature'], 3), 'thr', so_['threshold'], 'cut', round(so_['familiarity_cutoff'], 4))
    print('mite split', ship_out['mite_split'], 'dups', ship_out['rocole_identical_copies'])
    print('SHIPPED C', ship_out['C'], 'T', round(ship_out['temperature'], 3), 'thr', ship_out['threshold'],
          'cut', round(ship_out['familiarity_cutoff'], 4), 'n_train', nt)
    print('CV', json.dumps({k: round(v, 3) for k, v in cv.items() if isinstance(v, float)}))
    for k, v in ship_out['held_out'].items():
        print(k, v if isinstance(v, list) else {kk: (round(vv, 3) if isinstance(vv, float) else vv) for kk, vv in v.items()})
    print('lab style', {k: round(v['acc_all'], 3) for k, v in ship_out['lab_style'].items()})
    print('near-dup', ship_out['near_duplicate_check_human_baseline'])
    print('LAB-ONLY', {k: lab_out[k] for k in ['C', 'temperature', 'threshold', 'familiarity_cutoff']})
    for k in ['in_domain_val', 'in_domain_calib', 'field']:
        print(k, {kk: lab_out[k][kk] for kk in ['n', 'acc_all', 'coverage', 'acc_answered', 'acc_healthy_vs_problem', 'mean_confidence']})
    print('mite', lab_out['mite']); print('ood auroc', lab_out['ood_auroc_field_vs_heldout'])
    print('loop', json.dumps(lab_out['learning_loop']['curves']), 'lambda', lab_out['learning_loop']['lambda'])
    print('mite after demo update', lab_out['mite_after_demo_update_50'])
    print('village (shipped)', json.dumps(out['village_sim']))
    print('village (lab-only +50)', json.dumps(lab_out['village_sim']))


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
