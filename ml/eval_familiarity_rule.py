"""Evaluate a second familiarity rule: the nearest OFFICER-LABELLED photo.

Current rule (in the app): a photo is familiar if the distance to its 10 nearest stored rows (shipped reference
model/reference.bin + the rows the officer labelled on the phone) is <= ood.cutoff.
New rule (OR):             ALSO familiar if the distance to the single nearest officer-labelled row (never a shipped
                           reference row) is <= c1.
Distance = 1 - cosine similarity (for the 10 nearest: 1 - mean of the 10 largest similarities), as in the app.
The rule only adds familiar photos; confidence threshold, temperature, 'other' routing and the on-phone refit are
unchanged. With no officer rows it gives exactly the current decisions.

Protocol (fixed before any test result was looked at; written here before the first run):
  0. Ugandan photos (ml/eval_uganda.py embeddings): split the COARSE split units (similarity 0.70 clusters, which are
     unions of the main units) at random into DEV (40% of units) and TEST (60%). Nothing from TEST is used to pick c1.
  1. Pick c1 on DEV only. 10 seeds: DEV main split units are split 50/50 into an officer pool and a scored half; the
     officer labels k = 10, 20, 50, 100 photos (one per copy group, random order); the head is refit as on the phone
     (adapt, prior_strength) and the labelled rows join the stored rows. Candidates: c1 = f x shipped cutoff,
     f in 0.2 ... 1.0 (step 0.1), rounded to 4 decimals (the value the app would store).
     Selection rule: c1 = the LARGEST candidate for which, at every k, the photos the new rule ADDS (answered under the
     new rule but not under the current rule) are correct >= 85% (pooled over seeds, each copy group counts once).
     Why the added photos and not all answered photos: on Ugandan photos the current rule's own answers are below 85%
     correct up to 100 labels (57-81% in results/uganda_external.json, seen before this protocol), and c1 does not
     change those answers. The 90% version (the app's threshold intent) is reported next to it. If no candidate
     passes, the decision is 'reject'.
  2. Score with that c1 (both rules side by side):
     (a) Ugandan TEST units, k = 0, 10, 20, 50, 100, 5 seeds (pool/scored halves of the TEST units): answered, correct
         of answered, rust named, Phoma named, healthy flagged (each copy group counts once). Sensitivity: pool/scored
         split by coarse units. Reported, no pass/fail gate.
     (b) Ecuador new-region simulation (lab-only base, RoCoLe healthy/rust, the same 50/50 pool/test splits, seeds
         and label orders as results/metrics.json lab_only_new_region_simulation), k = 10, 20, 50.
         GATE: correct of answered under the new rule >= current rule - 3 points at every k.
     (c) Mite photos (all 167 RoCoLe red-spider-mite photos), shipped v3 model, after the officer labels k = 10, 50,
         100 RoCoLe healthy/rust photos (5 seeds; never one of the 60 human-baseline photos, the 7 demo samples or a
         near-copy, cosine > 0.98, of a mite photo). GATE: share of mite photos sent to the officer drops by no more
         than 5 points vs the current rule at every k. Note: v3 trained on 154 of these mite photos, so the level is
         optimistic; the gate is about the difference between rules. Stress test (reported, not a gate): head v2
         (no 'other' answer, never trained on mite photos; data_work/shipped_v2).
     (d) The 60 human-baseline photos, shipped model, no officer labels: decisions must be identical (no officer rows).
     Decision: 'accept' if a c1 passes step 1 and gates (b), (c), (d) pass; otherwise 'reject'.

Writes results/familiarity_rule.json. Run from kahawa-check/:  ../.venv/bin/python ml/eval_familiarity_rule.py
"""
import os, sys, csv, json, time
import numpy as np
from scipy.special import softmax

HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(HERE); ROOT = os.path.dirname(REPO)
WORK = os.path.join(ROOT, 'data_work'); RES = os.path.join(REPO, 'results'); MODEL = os.path.join(REPO, 'model')
OUT_JSON = os.path.join(RES, 'familiarity_rule.json')
sys.path.insert(0, HERE)
from train_eval import adapt, unit, knn_dist, CI  # noqa: E402  (same refit and distance as the app)
from eval_uganda import EMB_NPZ, standardisation, group_weights, UG_CLASSES  # noqa: E402

FRACTIONS = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
DEV_SHARE = 0.40
SPLIT_SEED = 777            # DEV / TEST split of the Ugandan coarse units
DEV_KS, DEV_SEEDS, DEV_SEED0 = [10, 20, 50, 100], 10, 5000
TEST_KS, TEST_SEEDS, TEST_SEED0 = [0, 10, 20, 50, 100], 5, 2000
EC_KS = [10, 20, 50]
MITE_KS, MITE_SEEDS, MITE_SEED0 = [10, 50, 100], 5, 3000
ACC_FLOOR, ACC_INTENT = 0.85, 0.90
EC_MAX_DROP, MITE_MAX_DROP = 0.03, 0.05
DUP_COS = 0.98


# ----------------------------------------------------------------------------------------------- shared
def load_head(path):
    h = json.load(open(path)); ref = h['ood']['reference']; n, dim = ref['n'], ref['dim']
    buf = open(os.path.join(os.path.dirname(path), ref['file']), 'rb').read()
    q = np.frombuffer(buf[:n * dim], np.int8).reshape(n, dim).astype(np.float32)
    sc = np.frombuffer(buf[n * dim:n * dim + 4 * n], '<f4')
    cls = list(h['classes'])
    return {'path': os.path.relpath(path, ROOT), 'version': h['version'], 'classes': cls,
            'W': np.array(h['W'], np.float64), 'b': np.array(h['b'], np.float64), 'T': float(h['temperature']),
            'thr': float(h['threshold']), 'cut': float(h['ood']['cutoff']), 'k': int(h['ood']['k']),
            'Rn': unit(q * sc[:, None]).astype(np.float64), 'lam': float(h.get('prior_strength', 0.3)),
            'other': [cls.index(c) for c in h.get('route_to_officer', []) if c in cls]}


def decisions(m, Z, Zn, W, b, Zpick_n, c1s):
    """Current rule and the new rule for each c1. Zpick_n: officer-labelled rows (L2-normalised) or None."""
    P = softmax((Z @ W.T + b) / m['T'], axis=1); pred = P.argmax(1)
    conf = P.max(1) >= m['thr']; oth = np.isin(pred, m['other'])
    if Zpick_n is None or not len(Zpick_n):
        d_app = knn_dist(Zn, m['Rn'], m['k']); d_loc = np.full(len(Z), np.inf)
    else:
        d_app = knn_dist(Zn, unit(np.vstack([m['Rn'], Zpick_n])), m['k']); d_loc = knn_dist(Zn, Zpick_n, 1)
    fam_cur = d_app <= m['cut']
    ans = {'current': conf & fam_cur & ~oth}
    for c1 in c1s:
        ans[c1] = conf & (fam_cur | (d_loc <= c1)) & ~oth
    return pred, ans


def wshare(w, num, den):
    return float(w[num & den].sum() / w[den].sum()) if w[den].sum() > 0 else float('nan')


def nanmean(v):
    v = np.array(v, float)
    return None if np.all(np.isnan(v)) else float(np.nanmean(v))


def r3(x):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), 4)


# ----------------------------------------------------------------------------------------------- Uganda
def load_uganda():
    d = np.load(EMB_NPZ, allow_pickle=False)
    mu, sd = standardisation()
    Z = ((d['E'] - mu) / sd).astype(np.float64)
    return Z, unit(Z), d['label'], d['group'], d['unit'], d['unit_coarse']


def dev_test_split(unit_c):
    uu = np.random.default_rng(SPLIT_SEED).permutation(np.unique(unit_c))
    dev_u = set(uu[:int(round(DEV_SHARE * len(uu)))].tolist())
    dev = np.array([u in dev_u for u in unit_c])
    return np.where(dev)[0], np.where(~dev)[0]


def uganda_loop(m, Z, Zn, yname, group, units, part, ks, seeds, seed0, c1s):
    """Officer labels k photos from a pool half of `part` (split by `units`), one per copy group, random order; scored
    on the other half. Returns per (rule, k) lists over seeds of group-weighted metrics, plus pooled sums for the
    photos the new rule adds."""
    ci = {c: i for i, c in enumerate(m['classes'])}; y = np.array([ci[c] for c in yname])
    rules = ['current'] + list(c1s)
    keys = ['answered', 'correct_of_answered', 'rust_named', 'phoma_named', 'healthy_flagged', 'forced_correct']
    runs = {r_: {k: {key: [] for key in keys} for k in ks} for r_ in rules}
    added = {c1: {k: {'w_added': 0.0, 'w_added_right': 0.0, 'w_scored': 0.0, 'share_added': []} for k in ks} for c1 in c1s}
    nsz = []
    for s in range(seeds):
        r = np.random.default_rng(seed0 + s)
        uu = r.permutation(np.unique(units[part])); pool_u = set(uu[:len(uu) // 2].tolist())
        in_pool = np.array([u in pool_u for u in units[part]])
        prow, score = part[in_pool], part[~in_pool]
        pool = np.array([r.choice(prow[group[prow] == g]) for g in r.permutation(np.unique(group[prow]))])
        w = group_weights(group[score]); yt = yname[score]
        nsz.append((len(pool), len(np.unique(group[score])), len(score)))
        for k in ks:
            pick = pool[:k]
            Wa, ba = adapt(Z[pick], y[pick], m['W'], m['b'], m['T'], m['lam']) if k else (m['W'], m['b'])
            pred_i, ans = decisions(m, Z[score], Zn[score], Wa, ba, Zn[pick] if k else None, c1s)
            pred = np.array(m['classes'])[pred_i]; allm = np.ones(len(score), bool)
            for r_ in rules:
                a = ans[r_]; right = a & (pred == yt)
                vals = {'answered': wshare(w, a, allm), 'correct_of_answered': wshare(w, right, a),
                        'rust_named': wshare(w, a & (pred == 'rust'), yt == 'rust'),
                        'phoma_named': wshare(w, a & (pred == 'phoma'), yt == 'phoma'),
                        'healthy_flagged': wshare(w, a & (pred != 'healthy'), yt == 'healthy'),
                        'forced_correct': wshare(w, pred == yt, allm)}
                for key in keys:
                    runs[r_][k][key].append(vals[key])
            for c1 in c1s:
                add = ans[c1] & ~ans['current']
                A = added[c1][k]
                A['w_added'] += float(w[add].sum()); A['w_added_right'] += float(w[add & (pred == yt)].sum())
                A['w_scored'] += float(w.sum()); A['share_added'].append(float(w[add].sum() / w.sum()))
    summ = {}
    for r_ in rules:
        name = 'current' if r_ == 'current' else f'c1={r_}'
        summ[name] = {key: [r3(nanmean(runs[r_][k][key])) for k in ks] for key in keys}
        summ[name]['sd'] = {key: [r3(np.nanstd(runs[r_][k][key])) for k in ks] for key in keys}
    for c1 in c1s:
        summ[f'c1={c1}']['added_share'] = [r3(added[c1][k]['w_added'] / added[c1][k]['w_scored']) for k in ks]
        summ[f'c1={c1}']['added_correct_pooled'] = [
            r3(added[c1][k]['w_added_right'] / added[c1][k]['w_added']) if added[c1][k]['w_added'] > 0 else None
            for k in ks]
    return {'ks': ks, 'seeds': seeds, 'pool_copy_groups_mean': float(np.mean([n[0] for n in nsz])),
            'scored_copy_groups_mean': float(np.mean([n[1] for n in nsz])),
            'scored_photos_mean': float(np.mean([n[2] for n in nsz])), 'rules': summ}


def select_c1(dev, c1s, floor):
    """Largest c1 whose ADDED photos are correct >= floor at every dev k (k with no added photo passes)."""
    ok = []
    for c1 in c1s:
        acc = dev['rules'][f'c1={c1}']['added_correct_pooled']
        if all(a is None or a >= floor for a in acc):
            ok.append(c1)
    return max(ok) if ok else None


# ----------------------------------------------------------------------------------------------- RoCoLe
def load_rocole():
    rows = list(csv.DictReader(open(os.path.join(RES, 'index.csv'))))
    E = np.load(os.path.join(WORK, 'embeddings.npz'))['E']; assert len(rows) == len(E)
    mu, sd = standardisation()
    Z = ((E - mu) / sd).astype(np.float64)
    src = np.array([r['source'] for r in rows]); lab = np.array([r['label'] for r in rows])
    name = np.array([os.path.basename(r['path']) for r in rows])
    return Z, unit(Z), src, lab, name


def ecuador(Z, Zn, src, lab, c1s):
    """Lab-only base, the new-region simulation of ml/train_eval.py (same seeds, splits and label order)."""
    m = load_head(os.path.join(MODEL, 'head_labonly.json'))
    fidx = np.where((src == 'RoCoLe') & np.isin(lab, ['healthy', 'rust']))[0]
    y = np.array([CI.get(l_, -1) for l_ in lab])
    rules = ['current'] + list(c1s)
    acc = {r_: {k: [] for k in EC_KS} for r_ in rules}; cov = {r_: {k: [] for k in EC_KS} for r_ in rules}
    for seed in range(5):
        r = np.random.default_rng(1000 + seed); perm = r.permutation(fidx)
        pool, test = perm[:len(perm) // 2], perm[len(perm) // 2:]
        order = r.permutation(len(pool))
        for k in EC_KS:
            pick = pool[order[:k]]
            Wa, ba = adapt(Z[pick], y[pick], m['W'], m['b'], m['T'], m['lam'])
            pred, ans = decisions(m, Z[test], Zn[test], Wa, ba, Zn[pick], c1s)
            for r_ in rules:
                a = ans[r_]
                cov[r_][k].append(float(a.mean()))
                acc[r_][k].append(float((pred[a] == y[test][a]).mean()) if a.any() else float('nan'))
    out = {'base': m['version'], 'cutoff': m['cut'], 'ks': EC_KS, 'seeds': 5,
           'test_photos': int(len(fidx) - len(fidx) // 2), 'rules': {}}
    for r_ in rules:
        out['rules']['current' if r_ == 'current' else f'c1={r_}'] = {
            'answered': [r3(np.mean(cov[r_][k])) for k in EC_KS],
            'correct_of_answered': [r3(nanmean(acc[r_][k])) for k in EC_KS]}
    try:  # check: the current rule reproduces the published simulation (metrics.json keeps it as *_previous_rule
          # since ml/train_eval.py uses the app's rule, which now includes the nearest-officer-row check)
        L = json.load(open(os.path.join(RES, 'metrics.json')))['lab_only_new_region_simulation']['learning_loop']
        cv_ = L['curves']['prior_adapt']
        pub = [cv_.get('coverage_previous_rule', cv_['coverage'])[L['ks'].index(k)] for k in EC_KS]
        out['check_current_rule_vs_metrics_json'] = {'published_answered': [r3(x) for x in pub],
                                                     'max_abs_diff': r3(max(abs(a - b) for a, b in zip(pub, out['rules']['current']['answered'])))}
    except Exception as e:
        out['check_current_rule_vs_metrics_json'] = {'missing': str(e)}
    return out


def held_out_names():
    key = json.load(open(os.path.join(REPO, 'baseline', 'key.json')))
    hb = {v['original_file'] for v in key['photos'].values()}
    sm = {s['original_file'] for s in json.load(open(os.path.join(REPO, 'samples', 'manifest.json')))['samples']}
    assert len(hb) == 60
    return hb, sm


def mite_test(m, Z, Zn, src, lab, name, c1s):
    """All 167 mite photos; officer labels k RoCoLe healthy/rust photos; share sent to the officer, both rules."""
    hb, sm = held_out_names()
    mite = np.where((src == 'RoCoLe') & (lab == 'mite'))[0]
    field = np.where((src == 'RoCoLe') & np.isin(lab, ['healthy', 'rust']))[0]
    near_mite = (Zn[field] @ Zn[mite].T).max(1) > DUP_COS
    cand = field[~np.isin(name[field], list(hb | sm)) & ~near_mite]
    ci = {c: i for i, c in enumerate(m['classes'])}; y = np.array([ci.get(l_, -1) for l_ in lab])
    rules = ['current'] + list(c1s)
    sent = {r_: {k: [] for k in MITE_KS} for r_ in rules}; rust = {r_: {k: [] for k in MITE_KS} for r_ in rules}
    diag = {'refit_only_rows_not_added': {k: [] for k in MITE_KS}, 'rows_added_no_refit': {k: [] for k in MITE_KS}}
    pred0, ans0 = decisions(m, Z[mite], Zn[mite], m['W'], m['b'], None, c1s)
    for s in range(MITE_SEEDS):
        order = np.random.default_rng(MITE_SEED0 + s).permutation(cand)
        for k in MITE_KS:
            pick = order[:k]
            Wa, ba = adapt(Z[pick], y[pick], m['W'], m['b'], m['T'], m['lam'])
            pred, ans = decisions(m, Z[mite], Zn[mite], Wa, ba, Zn[pick], c1s)
            for r_ in rules:
                sent[r_][k].append(float(1 - ans[r_].mean()))
                rust[r_][k].append(float((ans[r_] & (pred == ci['rust'])).mean()))
            # which part of the officer update moves the mite photos (current rule): the refit or the added rows?
            diag['refit_only_rows_not_added'][k].append(float(1 - decisions(m, Z[mite], Zn[mite], Wa, ba, None, [])[1]['current'].mean()))
            diag['rows_added_no_refit'][k].append(float(1 - decisions(m, Z[mite], Zn[mite], m['W'], m['b'], Zn[pick], [])[1]['current'].mean()))
    out = {'model': m['version'], 'n_mite': int(len(mite)), 'officer_label_candidates': int(len(cand)),
           'excluded_near_copies_of_mite': int(near_mite.sum()), 'ks': MITE_KS, 'seeds': MITE_SEEDS,
           'no_labels_sent_to_officer': r3(1 - ans0['current'].mean()),
           'diagnostic_current_rule_sent_to_officer': {n_: [r3(np.mean(v[k])) for k in MITE_KS] for n_, v in diag.items()},
           'rules': {}}
    for r_ in rules:
        out['rules']['current' if r_ == 'current' else f'c1={r_}'] = {
            'sent_to_officer': [r3(np.mean(sent[r_][k])) for k in MITE_KS],
            'sent_to_officer_sd': [r3(np.std(sent[r_][k])) for k in MITE_KS],
            'answered_rust': [r3(np.mean(rust[r_][k])) for k in MITE_KS]}
    return out


def human_baseline_check(m, Z, Zn, src, lab, name, c1s):
    hb, _ = held_out_names()
    idx = np.where((src == 'RoCoLe') & np.isin(name, list(hb)))[0]
    assert len(idx) == 60
    pred, ans = decisions(m, Z[idx], Zn[idx], m['W'], m['b'], None, c1s)
    same = all(np.array_equal(ans['current'], ans[c1]) for c1 in c1s)
    return {'n': int(len(idx)), 'answered_current': int(ans['current'].sum()),
            'answered_new_rule': {f'c1={c1}': int(ans[c1].sum()) for c1 in c1s}, 'identical_decisions': bool(same)}


# ----------------------------------------------------------------------------------------------- main
def main():
    t0 = time.time()
    ship = load_head(os.path.join(MODEL, 'head.json'))
    c1s = [round(f * ship['cut'], 4) for f in FRACTIONS]
    Z, Zn, yname, group, unit_f, unit_c = load_uganda()
    dev, test = dev_test_split(unit_c)
    split = {'unit': 'coarse split units (similarity 0.70)', 'seed': SPLIT_SEED, 'dev_share_of_units': DEV_SHARE,
             'dev_photos': int(len(dev)), 'test_photos': int(len(test)),
             'dev_copy_groups': int(len(np.unique(group[dev]))), 'test_copy_groups': int(len(np.unique(group[test]))),
             'dev_copy_groups_by_class': {c: int(len(np.unique(group[dev][yname[dev] == c]))) for c in UG_CLASSES},
             'test_copy_groups_by_class': {c: int(len(np.unique(group[test][yname[test] == c]))) for c in UG_CLASSES}}
    assert not set(unit_f[dev]) & set(unit_f[test]), 'a main split unit sits in both DEV and TEST'

    # 1. choose c1 on DEV only
    dev_res = uganda_loop(ship, Z, Zn, yname, group, unit_f, dev, DEV_KS, DEV_SEEDS, DEV_SEED0, c1s)
    c1 = select_c1(dev_res, c1s, ACC_FLOOR); c1_90 = select_c1(dev_res, c1s, ACC_INTENT)
    print(f'dev done {time.time() - t0:.0f} s; chosen c1 = {c1} (90% version: {c1_90})', flush=True)
    dev_table = [{'c1': c, 'fraction_of_cutoff': f, 'ks': DEV_KS,
                  'added_share': dev_res['rules'][f'c1={c}']['added_share'],
                  'added_correct_pooled': dev_res['rules'][f'c1={c}']['added_correct_pooled'],
                  'answered': dev_res['rules'][f'c1={c}']['answered'],
                  'correct_of_answered': dev_res['rules'][f'c1={c}']['correct_of_answered'],
                  'passes_85': select_c1(dev_res, [c], ACC_FLOOR) is not None,
                  'passes_90': select_c1(dev_res, [c], ACC_INTENT) is not None}
                 for c, f in zip(c1s, FRACTIONS)]
    res = {'what': ('Second familiarity rule: a photo also counts as familiar when its single nearest officer-labelled '
                    'row (rows added on the phone, never model/reference.bin) is within c1. c1 chosen on Ugandan DEV '
                    'units only, then scored on Ugandan TEST units, the Ecuador new-region simulation, the mite photos '
                    'and the 60 human-baseline photos.'),
           'generated_by': 'ml/eval_familiarity_rule.py', 'shipped_model': ship['version'],
           'shipped_cutoff': ship['cut'], 'candidates': {'fractions': FRACTIONS, 'c1': c1s},
           'protocol': __doc__.split('Protocol')[1].split('Writes results')[0].strip(),
           'uganda_split': split,
           'dev_selection': {'rule': (f'largest c1 whose added photos (answered under the new rule, not under the '
                                      f'current rule) are correct >= {ACC_FLOOR:.0%} at every k in {DEV_KS}, pooled over '
                                      f'{DEV_SEEDS} seeds, each copy group counted once'),
                             'chosen_c1': c1, 'chosen_fraction_of_cutoff': FRACTIONS[c1s.index(c1)] if c1 else None,
                             'largest_c1_at_90pct': c1_90, 'current_rule_dev': dev_res['rules']['current'],
                             'table': dev_table, 'pool_copy_groups_mean': dev_res['pool_copy_groups_mean'],
                             'scored_copy_groups_mean': dev_res['scored_copy_groups_mean']}}
    if c1 is None:
        res['decision'] = 'reject'; res['reason'] = 'no candidate c1 met the dev rule'
        json.dump(res, open(OUT_JSON, 'w'), indent=1); print('reject: no c1 passes dev'); return
    show = [c1] + ([c1_90] if c1_90 and c1_90 != c1 else [])

    # 2a. Ugandan TEST units
    tmain = uganda_loop(ship, Z, Zn, yname, group, unit_f, test, TEST_KS, TEST_SEEDS, TEST_SEED0, show)
    tcoarse = uganda_loop(ship, Z, Zn, yname, group, unit_c, test, TEST_KS, TEST_SEEDS, TEST_SEED0, show)
    print(f'uganda test done {time.time() - t0:.0f} s', flush=True)
    # 2b-d. RoCoLe
    Zr, Znr, src, lab, name = load_rocole()
    ec = ecuador(Zr, Znr, src, lab, show)
    mite_v3 = mite_test(ship, Zr, Znr, src, lab, name, show)
    v2p = os.path.join(WORK, 'shipped_v2', 'head.json')
    mite_v2 = mite_test(load_head(v2p), Zr, Znr, src, lab, name, show) if os.path.exists(v2p) else {'missing': v2p}
    hbc = human_baseline_check(ship, Zr, Znr, src, lab, name, show)
    print(f'rocole checks done {time.time() - t0:.0f} s', flush=True)

    key = f'c1={c1}'
    ec_drop = [None if a is None or b is None else r3(b - a) for a, b in
               zip(ec['rules'][key]['correct_of_answered'], ec['rules']['current']['correct_of_answered'])]
    mite_drop = [r3(b - a) for a, b in zip(mite_v3['rules'][key]['sent_to_officer'], mite_v3['rules']['current']['sent_to_officer'])]
    gates = {'ecuador_accuracy_drop_max_3_points': {'drop_by_k': dict(zip(map(str, EC_KS), ec_drop)),
                                                    'pass': all(d is not None and d <= EC_MAX_DROP for d in ec_drop)},
             'mite_sent_to_officer_drop_max_5_points': {'drop_by_k': dict(zip(map(str, MITE_KS), mite_drop)),
                                                        'pass': all(d <= MITE_MAX_DROP for d in mite_drop)},
             'human_baseline_unchanged': {'pass': hbc['identical_decisions']}}
    if isinstance(mite_v2, dict) and 'rules' in mite_v2:
        gates['stress_test_head_v2_mite_drop_not_a_gate'] = {'drop_by_k': dict(zip(map(str, MITE_KS), [
            r3(b - a) for a, b in zip(mite_v2['rules'][key]['sent_to_officer'], mite_v2['rules']['current']['sent_to_officer'])]))}
    decision = 'accept' if all(g['pass'] for n_, g in gates.items() if 'pass' in g) else 'reject'
    try:  # check: ml/train_eval.py's app-rule curve (metrics.json) equals this script's new rule with the same c1
        L = json.load(open(os.path.join(RES, 'metrics.json')))['lab_only_new_region_simulation']['learning_loop']
        if L.get('local_nearest_cutoff') is not None and abs(L['local_nearest_cutoff'] - c1) < 1e-9:
            pub = [L['curves']['prior_adapt']['coverage'][L['ks'].index(k)] for k in EC_KS]
            ec['check_app_rule_vs_metrics_json'] = {'published_answered': [r3(x) for x in pub], 'max_abs_diff': r3(
                max(abs(a - b) for a, b in zip(pub, ec['rules'][key]['answered'])))}
        else:
            ec['check_app_rule_vs_metrics_json'] = {'skipped': f"metrics.json local_nearest_cutoff = {L.get('local_nearest_cutoff')}"}
    except Exception as e:
        ec['check_app_rule_vs_metrics_json'] = {'missing': str(e)}
    res.update({'decision': decision, 'c1': c1, 'c1_fraction_of_cutoff': FRACTIONS[c1s.index(c1)], 'gates': gates,
                'test_uganda': {'main_grouping': tmain, 'coarse_grouping_sensitivity': tcoarse},
                'test_ecuador_new_region': ec, 'test_mite_shipped_v3': mite_v3, 'stress_mite_head_v2': mite_v2,
                'test_human_baseline_60': hbc,
                'spec': {'head_json_field': 'ood.local_nearest_cutoff', 'value': c1,
                         'rule': ('familiar = (distance to the k=ood.k nearest of [shipped reference rows + officer '
                                  'rows] <= ood.cutoff) OR (1 - max cosine similarity to the officer rows <= '
                                  'ood.local_nearest_cutoff); officer rows = rows labelled on this phone or received in '
                                  'an officer update (localRefs), never model/reference.bin rows; field absent = '
                                  'current rule; no officer rows = current rule'),
                         'unchanged': 'threshold, temperature, ood.cutoff, ood.k, route_to_officer, on-phone refit'}})
    res['suggested_numbers'] = suggested_numbers(res)
    json.dump(res, open(OUT_JSON, 'w'), indent=1)
    print(json.dumps({'decision': decision, 'c1': c1, 'gates': gates}, indent=1))
    print(json.dumps(res['suggested_numbers'], indent=1))
    print(f'total {time.time() - t0:.0f} s')


def suggested_numbers(res):
    """Ready-made strings for numbers.json (the integration step decides which to adopt)."""
    p = lambda x: 'n/a' if x is None else f'{100 * x:.0f}%'
    key = f"c1={res['c1']}"; T = res['test_uganda']['main_grouping']; ks = T['ks']
    cur, new = T['rules']['current'], T['rules'][key]
    ec = res['test_ecuador_new_region']; mi = res['test_mite_shipped_v3']
    out = {'FAM_DECISION': res['decision'], 'FAM_C1': f"{res['c1']:.3f}",
           'FAM_C1_FRACTION': f"{res['c1_fraction_of_cutoff']:.1f}"}
    for k in (50, 100):
        i = ks.index(k)
        out.update({f'FAM_UG{k}_ANSWERED_CUR': p(cur['answered'][i]), f'FAM_UG{k}_ANSWERED_NEW': p(new['answered'][i]),
                    f'FAM_UG{k}_ACC_CUR': p(cur['correct_of_answered'][i]), f'FAM_UG{k}_ACC_NEW': p(new['correct_of_answered'][i]),
                    f'FAM_UG{k}_RUST_NAMED_NEW': p(new['rust_named'][i]), f'FAM_UG{k}_PHOMA_NAMED_NEW': p(new['phoma_named'][i]),
                    f'FAM_UG{k}_HEALTHY_FLAGGED_NEW': p(new['healthy_flagged'][i])})
    i = ec['ks'].index(50)
    out.update({'FAM_EC50_ANSWERED_CUR': p(ec['rules']['current']['answered'][i]),
                'FAM_EC50_ANSWERED_NEW': p(ec['rules'][key]['answered'][i]),
                'FAM_EC50_ACC_CUR': p(ec['rules']['current']['correct_of_answered'][i]),
                'FAM_EC50_ACC_NEW': p(ec['rules'][key]['correct_of_answered'][i])})
    for k in (10, 100):
        i = mi['ks'].index(k)
        out[f'FAM_MITE{k}_SENT_CUR'] = p(mi['rules']['current']['sent_to_officer'][i])
        out[f'FAM_MITE{k}_SENT_NEW'] = p(mi['rules'][key]['sent_to_officer'][i])
    return out


if __name__ == '__main__':
    main()
