"""Experiment: which 'not sure' check notices field photos, and how does the learning loop behave
when officer-labelled photos also expand what the tool counts as familiar?
Usage: ../.venv/bin/python ml/explore_shift.py [embeddings.npz]   (default: MobileNetV3 full set)"""
import os, sys, csv, json
import numpy as np
from scipy.special import softmax
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from train_eval import adapt, nll, CLASSES, CI
from scipy.optimize import minimize_scalar

HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(HERE)
WORK = os.path.join(os.path.dirname(REPO), 'data_work')
f = sys.argv[1] if len(sys.argv) > 1 else os.path.join(WORK, 'embeddings.npz')
d = np.load(f); E = d['E']
rows = list(csv.DictReader(open(os.path.join(REPO, 'results', 'index.csv'))))
idx = d['idx'] if 'idx' in d.files else np.arange(len(rows))
rows = [rows[i] for i in idx]
src = np.array([r['source'] for r in rows]); lab = np.array([r['label'] for r in rows])
y = np.array([CI.get(l, -1) for l in lab])
rng = np.random.default_rng(0)
n = len(rows)
jm = np.isin(src, ['JMuBEN', 'JMuBEN2']); br = src == 'BRACOL'
val = np.zeros(n, bool); val[np.where(jm)[0][rng.random(jm.sum()) < 0.15]] = True
train = jm & ~val
calib = np.zeros(n, bool)
for c in range(5):
    ii = np.where(br & (y == c))[0]; rng.shuffle(ii); h = len(ii) // 2
    train[ii[:h]] = True; calib[ii[h:]] = True
field = (src == 'RoCoLe') & (y >= 0); mite = (src == 'RoCoLe') & (lab == 'mite')
mu, sd = E[train].mean(0), E[train].std(0) + 1e-6
Z = (E - mu) / sd
Zn = Z / np.linalg.norm(Z, axis=1, keepdims=True)

clf = LogisticRegression(C=0.01, max_iter=3000, class_weight='balanced').fit(Z[train], y[train])
W, b = clf.coef_, clf.intercept_
T = float(minimize_scalar(lambda t: nll(Z[calib] @ W.T + b, y[calib], t), bounds=(0.05, 20), method='bounded').x)
P = softmax((Z @ W.T + b) / T, axis=1)

# reference set for the k-nearest-neighbour familiarity check (what the phone would store)
REF_N = 1000
ref = rng.choice(np.where(train)[0], REF_N, replace=False)


def knn_dist(Q, R, k=10):
    s = Q @ R.T
    k = min(k, R.shape[0])
    return 1 - np.sort(s, axis=1)[:, -k:].mean(1)


cents = np.stack([Z[train & (y == c)].mean(0) for c in range(5)]); Cn = cents / np.linalg.norm(cents, axis=1, keepdims=True)
scores = {'max_softmax': -P.max(1), 'centroid_cos': 1 - (Zn @ Cn.T).max(1), 'knn10_cos': knn_dist(Zn, Zn[ref])}
held = calib  # cross-source held-out photos (BRACOL half not used for training)
out = {'file': os.path.basename(f), 'acc': {}, 'ood': {}}
for name, mask in [('val', val), ('calib', calib), ('field', field)]:
    out['acc'][name] = float((P[mask].argmax(1) == y[mask]).mean())
for k, s in scores.items():
    cut = np.percentile(s[held], 95)
    out['ood'][k] = {'auroc_field_vs_heldout': float(roc_auc_score(np.r_[np.zeros(held.sum()), np.ones(field.sum())], np.r_[s[held], s[field]])),
                     'field_accept_rate': float((s[field] <= cut).mean()),
                     'mite_accept_rate': float((s[mite] <= cut).mean()),
                     'heldout_accept_rate': float((s[held] <= cut).mean())}

# learning loop with familiarity expansion: officer labels k photos; head adapted toward prior;
# labelled photos are added to the reference set, so similar photos stop being 'unfamiliar'.
cut_knn = np.percentile(scores['knn10_cos'][held], 95)
thr = 0.0
for t in np.linspace(0.3, 0.99, 70):  # threshold on held-out cross-source photos only
    m = (P[held].max(1) >= t) & (scores['knn10_cos'][held] <= cut_knn)
    if m.sum() >= 20 and (P[held].argmax(1)[m] == y[held][m]).mean() >= 0.90:
        thr = float(t); break
out['threshold'] = thr; out['knn_cutoff'] = float(cut_knn); out['temperature'] = T
fidx = np.where(field)[0]; ks = [0, 10, 20, 50, 100, 200]
res = {m: {k: {'acc_all': [], 'coverage': [], 'acc_answered': []} for k in ks} for m in ['prior_adapt', 'local_only']}
for seed in range(5):
    r = np.random.default_rng(1000 + seed); perm = r.permutation(fidx)
    pool, test = perm[:len(perm) // 2], perm[len(perm) // 2:]
    order = r.permutation(len(pool))
    for k in ks:
        pick = pool[order[:k]]
        R = np.vstack([Zn[ref], Zn[pick]]) if k else Zn[ref]
        fam = knn_dist(Zn[test], R) <= cut_knn
        for meth in res:
            if meth == 'prior_adapt':
                Wa, ba = adapt(Z[pick], y[pick], W, b, T, 0.3)
            else:
                if k == 0 or len(np.unique(y[pick])) < 2:
                    Wa, ba = W, b
                else:
                    lc = LogisticRegression(C=1.0, max_iter=3000, class_weight='balanced').fit(Z[pick], y[pick])
                    Wa = np.full_like(W, 0.0); ba = np.full_like(b, -1e3)
                    Wa[lc.classes_] = lc.coef_; ba[lc.classes_] = lc.intercept_
            Pt = softmax((Z[test] @ Wa.T + ba) / T, axis=1)
            ans = fam & (Pt.max(1) >= thr)
            pr = Pt.argmax(1)
            res[meth][k]['acc_all'].append(float((pr == y[test]).mean()))
            res[meth][k]['coverage'].append(float(ans.mean()))
            res[meth][k]['acc_answered'].append(float((pr[ans] == y[test][ans]).mean()) if ans.any() else float('nan'))
out['loop'] = {m: {str(k): {kk: float(np.nanmean(v)) for kk, v in res[m][k].items()} for k in ks} for m in res}
print(json.dumps(out, indent=1))
json.dump(out, open(os.path.join(REPO, 'results', f'explore_{os.path.basename(f)[:-4]}.json'), 'w'), indent=1)
