"""Score the human baseline (picture card) and the model on the same 60 field photos.

Reads  ../data_work/baseline/*.json  (one file per 'Send results' from baseline/index.html; the latest file
per name counts), baseline/key.json (answer key), and the model files the phone uses.
Writes results/human_baseline.json. Run: ../.venv/bin/python ml/score_baseline.py

Model, same decision rule as ml/train_eval.py and lib/kahawa-core.js:
  answered = (max softmax(logits / T) >= threshold) and (familiarity distance <= cutoff);
  familiarity distance = 1 - mean of the k largest cosine similarities to the stored reference rows.
  (a) shipped: model/head.json + model/reference.bin
  (b) after the demo update: W, b from model/update_demo_50.json, its reference rows added.
The model uses the stored embeddings of the original photos (data_work/embeddings.npz, the same numbers as all
other results). People saw 900 px copies; as a check, the ONNX backbone is also run on those copies.
"""
import os, json, csv, glob, re
from collections import Counter
from itertools import combinations
import numpy as np
from scipy.special import softmax

HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(HERE); TOP = os.path.dirname(REPO)
WORK = os.path.join(TOP, 'data_work'); SAVED = os.path.join(WORK, 'baseline')
RES = os.path.join(REPO, 'results'); BASE = os.path.join(REPO, 'baseline')
DISEASES = ['rust', 'miner', 'cercospora', 'phoma']
OPTIONS = ['healthy'] + DISEASES + ['not_sure']


def unit(X):
    return X / np.linalg.norm(X, axis=1, keepdims=True)


def norm_name(s):
    return re.sub(r'\s+', ' ', str(s or '').strip()).lower()


def score(ans, key):
    """ans: {photo id: answer or None}. Same measures for people and the model."""
    ids = list(key)
    a = [ans.get(i) for i in ids]
    truth = [key[i]['truth'] for i in ids]; lvl = [key[i]['rust_level'] for i in ids]
    answered = [x is not None and x != 'not_sure' for x in a]
    correct = [x == t for x, t in zip(a, truth)]
    hvp = [(x == 'healthy') == (t == 'healthy') for x, t in zip(a, truth)]
    na = sum(answered)
    out = {'n': len(ids), 'n_answered': na, 'share_answered': na / len(ids),
           'acc_answered': (sum(c for c, w in zip(correct, answered) if w) / na) if na else None,
           'acc_healthy_vs_problem_answered': (sum(h for h, w in zip(hvp, answered) if w) / na) if na else None,
           'correct_of_all': sum(c for c, w in zip(correct, answered) if w) / len(ids),
           'answer_counts': {o: sum(x == o for x in a) for o in OPTIONS + [None] if sum(x == o for x in a)},
           'by_rust_level': {}}
    out['answer_counts'] = {('missing' if k is None else k): v for k, v in out['answer_counts'].items()}
    for L in sorted(set(lvl)):
        m = [l == L for l in lvl]
        nL = sum(m); aL = sum(w for w, mm in zip(answered, m) if mm)
        cL = sum(c and w for c, w, mm in zip(correct, answered, m) if mm)
        pL = sum((x in DISEASES) for x, mm in zip(a, m) if mm)
        out['by_rust_level'][str(L)] = {
            'label': 'healthy' if L == 0 else f'rust level {L}', 'n': nL, 'n_answered': aL,
            'correct_of_all': cL / nL, 'acc_answered': (cL / aL) if aL else None,
            'called_a_problem_of_all': pL / nL}
    return out


def load_labellers(key, set_name):
    files = sorted(glob.glob(os.path.join(SAVED, '*.json')))
    stamp = lambda p: os.path.basename(p)[-27:-5]  # YYYYmmdd-HHMMSS-micro written by ml/serve.py
    latest, skipped = {}, []
    for p in files:
        try:
            d = json.load(open(p))
        except Exception as e:
            skipped.append(f'{os.path.basename(p)}: unreadable ({e})'); continue
        if d.get('set') != set_name:
            skipped.append(f"{os.path.basename(p)}: photo set {d.get('set')!r} is not {set_name!r}"); continue
        k = norm_name(d.get('name'))
        if not k:
            skipped.append(f'{os.path.basename(p)}: no name'); continue
        if k not in latest or stamp(p) > stamp(latest[k][0]):
            latest[k] = (p, d)
    out = []
    for k, (p, d) in sorted(latest.items()):
        rows = [r for r in d.get('answers', []) if r.get('id') in key]
        ans = {r['id']: r.get('answer') for r in rows}
        secs = [float(r.get('seconds') or 0) for r in rows if r.get('answer')]
        s = score(ans, key)
        s.update(name=d.get('name'), file=os.path.basename(p), sent_at=d.get('sent_at'),
                 n_labelled=sum(1 for r in rows if r.get('answer')),
                 median_seconds=float(np.median(secs)) if secs else None,
                 total_minutes=round(sum(secs) / 60, 1), n_changed_with_back=sum(1 for r in rows if r.get('changed')),
                 device='phone' if re.search(r'iPhone|Android|Mobile', d.get('user_agent', '')) else 'laptop/tablet')
        out.append((s, ans))
    return out, skipped


def model_answers(key):
    rows = list(csv.DictReader(open(os.path.join(RES, 'index.csv'))))
    E = np.load(os.path.join(WORK, 'embeddings.npz'))['E']
    st = np.load(os.path.join(WORK, 'standardisation.npz'))
    ids = list(key)
    for i in ids:  # the key's rows must still be the same photos
        assert os.path.basename(rows[key[i]['index_row']]['path']) == key[i]['original_file'], i
    Z = (E[[key[i]['index_row'] for i in ids]] - st['mu']) / st['sd']
    head = json.load(open(os.path.join(REPO, 'model', 'head.json')))
    ref = head['ood']['reference']; n, D = ref['n'], ref['dim']
    raw = open(os.path.join(REPO, 'model', ref['file']), 'rb').read()
    R = unit(np.frombuffer(raw[:n * D], np.int8).reshape(n, D).astype(np.float32) * np.frombuffer(raw[n * D:n * D + 4 * n], '<f4')[:, None])
    upd = json.load(open(os.path.join(REPO, 'model', 'update_demo_50.json')))
    Ru = unit(np.array(upd['reference_add']['int8'], np.float32) * np.array(upd['reference_add']['scale'], np.float32)[:, None])
    classes = head['classes']; T, thr, cut, k = head['temperature'], head['threshold'], head['ood']['cutoff'], head['ood']['k']

    def decide(Zx, W, b, Rx):
        P = softmax((Zx @ np.asarray(W).T + np.asarray(b)) / T, axis=1)
        d = 1 - np.sort(unit(Zx) @ Rx.T, axis=1)[:, -k:].mean(1)
        conf = P.max(1) >= thr; fam = d <= cut
        pred = [classes[j] for j in P.argmax(1)]
        ans = {i: (p if c and f else 'not_sure') for i, p, c, f in zip(ids, pred, conf, fam)}
        forced = {i: p for i, p in zip(ids, pred)}
        why = Counter('answered' if c and f else ('unfamiliar' if not f else 'low_confidence') for c, f in zip(conf, fam))
        return ans, forced, dict(why), d, P

    Rall = np.vstack([R, Ru])
    shipped = decide(Z, head['W'], head['b'], R)
    updated = decide(Z, upd['W'], upd['b'], Rall)
    res = {}
    for name, (ans, forced, why, d, P) in [('shipped', shipped), ('after_demo_update_50', updated)]:
        s = score(ans, key)
        f = score(forced, key)
        s.update(not_sure_reasons=why, forced_acc_all=f['correct_of_all'], forced_acc_healthy_vs_problem=sum(
            (forced[i] == 'healthy') == (key[i]['truth'] == 'healthy') for i in key) / len(key),
                 median_familiarity_distance=float(np.median(d)), mean_confidence=float(P.max(1).mean()))
        res[name] = (s, ans)
    settings = {'threshold': thr, 'familiarity_cutoff': cut, 'knn': k, 'temperature': T,
                'reference_rows_shipped': int(n), 'reference_rows_added_by_update': int(len(Ru)),
                'head_version': head.get('version'), 'update_base_version': upd.get('base_version')}
    check = resized_copy_check(ids, head, R, Rall, upd, {nm: v[1] for nm, v in res.items()})
    return res, settings, check


def resized_copy_check(ids, head, R, Rall, upd, ans_orig):
    """Run the ONNX backbone on the 900 px copies people saw; count same decisions as on the originals."""
    try:
        import onnxruntime as ort
        from PIL import Image
    except Exception as e:
        return {'skipped': f'onnxruntime/PIL not available ({e})'}
    meta = json.load(open(os.path.join(REPO, 'model', 'backbone_meta.json')))
    sess = ort.InferenceSession(os.path.join(REPO, 'model', 'backbone.onnx'), providers=['CPUExecutionProvider'])
    mean = np.array(meta['mean'], np.float32)[:, None, None]; std = np.array(meta['std'], np.float32)[:, None, None]

    def prep(p):
        im = Image.open(p).convert('RGB'); w, h = im.size; s = meta['resize_shorter'] / min(w, h)
        im = im.resize((round(w * s), round(h * s)), Image.BILINEAR); w, h = im.size; c = meta['input_size']
        l, t = (w - c) // 2, (h - c) // 2
        a = np.asarray(im.crop((l, t, l + c, t + c)), np.float32).transpose(2, 0, 1) / 255.0
        return ((a - mean) / std)[None]
    Z = np.concatenate([sess.run(None, {'input': prep(os.path.join(BASE, 'photos', i + '.jpg'))})[0] for i in ids])
    classes = head['classes']; T, thr, cut, k = head['temperature'], head['threshold'], head['ood']['cutoff'], head['ood']['k']
    out = {}
    for name, W, b, Rx in [('shipped', head['W'], head['b'], R), ('after_demo_update_50', upd['W'], upd['b'], Rall)]:
        P = softmax((Z @ np.asarray(W).T + np.asarray(b)) / T, axis=1)
        d = 1 - np.sort(unit(Z) @ Rx.T, axis=1)[:, -k:].mean(1)
        a = {i: (classes[j] if (p >= thr and dd <= cut) else 'not_sure') for i, j, p, dd in zip(ids, P.argmax(1), P.max(1), d)}
        out[name] = {'same_decision_as_original': int(sum(a[i] == ans_orig[name][i] for i in ids)), 'n': len(ids)}
    return out


def main():
    K = json.load(open(os.path.join(BASE, 'key.json')))
    key, meta = K['photos'], K['meta']
    labellers, skipped = load_labellers(key, meta['set'])
    for s in skipped:
        print('skipped', s)
    if not labellers:
        print(f'No labeller files for set {meta["set"]} in {SAVED}; nothing written.')
        if os.path.exists(os.path.join(RES, 'human_baseline.json')):
            print('Note: an older results/human_baseline.json exists and was left unchanged.')
        return
    model, settings, check = model_answers(key)
    agree = {}
    for (s1, a1), (s2, a2) in combinations(labellers, 2):
        agree[f"{s1['name']} | {s2['name']}"] = {
            'same_answer': sum(a1.get(i) == a2.get(i) for i in key) / len(key),
            'same_healthy_vs_problem_both_answered': (lambda both: (sum((a1[i] == 'healthy') == (a2[i] == 'healthy') for i in both) / len(both)) if both else None)(
                [i for i in key if a1.get(i) not in (None, 'not_sure') and a2.get(i) not in (None, 'not_sure')])}
    out = {'generated_by': 'ml/score_baseline.py (do not edit by hand)',
           'photo_set': {'set': meta['set'], 'n': meta['n'], 'healthy': meta['healthy'], 'rust_by_level': meta['rust_by_level'],
                         'source': meta['source'], 'excluded': meta['excluded'],
                         'shown_to_people': 'resized to max 900 px, JPEG quality 85, one at a time, order fixed per name'},
           'labellers': [s for s, _ in labellers], 'labeller_agreement': agree,
           'model': {k: v[0] for k, v in model.items()}, 'model_settings': settings, 'model_on_resized_copies': check,
           'definitions': {
               'share_answered': 'photos not answered "not sure", out of all photos',
               'acc_answered': 'exact class correct (healthy or rust), out of answered photos',
               'acc_healthy_vs_problem_answered': 'healthy vs any problem correct, out of answered photos',
               'correct_of_all': 'exact class correct, out of all photos ("not sure" counts as not correct)',
               'by_rust_level': 'per true class/level; called_a_problem_of_all = any of the four problems chosen',
               'median_seconds': 'median seconds a photo was on screen with the page visible (all visits added up)'},
           'notes': ['Labellers are team members who are not farmers or plant experts, standing in for relay farmers.',
                     'The labellers may have known that this dataset holds only healthy and rust leaves; a relay farmer would not.',
                     '60 photos from one dataset (RoCoLe: Ecuador, robusta, on-plant); one-evening test.',
                     'The 50 photos inside the demo update and the 7 demo samples are excluded from the 60.']}
    if skipped:
        out['skipped_files'] = skipped
    json.dump(out, open(os.path.join(RES, 'human_baseline.json'), 'w'), indent=1)
    pct = lambda x: '-' if x is None else f'{100 * x:.0f}%'
    print(f"{'who':28s} answered  correct(ans)  healthy-vs-problem(ans)  correct/all  median s")
    for s in out['labellers']:
        print(f"{s['name'][:28]:28s} {pct(s['share_answered']):>8s}  {pct(s['acc_answered']):>12s}  {pct(s['acc_healthy_vs_problem_answered']):>23s}  {pct(s['correct_of_all']):>11s}  {s['median_seconds']:.1f}")
    for nm, s in out['model'].items():
        print(f"{'model ' + nm:28s} {pct(s['share_answered']):>8s}  {pct(s['acc_answered']):>12s}  {pct(s['acc_healthy_vs_problem_answered']):>23s}  {pct(s['correct_of_all']):>11s}  -")
    print('model on resized copies:', check)
    print('wrote', os.path.join(RES, 'human_baseline.json'))


if __name__ == '__main__':
    main()
