"""Check that model/backbone.onnx + model/head.json + model/reference.bin (the shipped lab+field model, what the
phone runs) give the same answers as the Python evaluation, and time one image on CPU.
The backbone bakes in the lab-only standardisation (../data_work/standardisation.npz, identical to
standardisation_labonly.npz), which both heads use. Run: ../.venv/bin/python ml/check_onnx.py"""
import os, json, time
import numpy as np
import onnxruntime as ort
from PIL import Image
from scipy.special import softmax

HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(HERE)
meta = json.load(open(os.path.join(REPO, 'model', 'backbone_meta.json')))
head = json.load(open(os.path.join(REPO, 'model', 'head.json')))
sess = ort.InferenceSession(os.path.join(REPO, 'model', 'backbone.onnx'), providers=['CPUExecutionProvider'])
W = np.array(head['W']); b = np.array(head['b'])
ref = head['ood']['reference']; n, D = ref['n'], ref['dim']
raw = open(os.path.join(REPO, 'model', ref['file']), 'rb').read()
assert len(raw) == n * D + 4 * n, f"{ref['file']} has {len(raw)} bytes, head.json expects n={n} rows"
q = np.frombuffer(raw[:n * D], np.int8).reshape(n, D).astype(np.float32)
sc = np.frombuffer(raw[n * D:], '<f4')
R = q * sc[:, None]; R /= np.linalg.norm(R, axis=1, keepdims=True)


def prep(p):
    im = Image.open(p).convert('RGB'); w, h = im.size; s = meta['resize_shorter'] / min(w, h)
    im = im.resize((round(w * s), round(h * s)), Image.BILINEAR); w, h = im.size; c = meta['input_size']
    l, t = (w - c) // 2, (h - c) // 2
    a = np.asarray(im.crop((l, t, l + c, t + c)), np.float32).transpose(2, 0, 1) / 255.0
    return ((a - np.array(meta['mean'], np.float32)[:, None, None]) / np.array(meta['std'], np.float32)[:, None, None])[None]


man = json.load(open(os.path.join(REPO, 'samples', 'manifest.json')))['samples']
times = []
sample_rows = []
for s in man:
    x = prep(os.path.join(REPO, 'samples', s['file']))
    t0 = time.perf_counter(); e = sess.run(None, {'input': x})[0][0]; times.append(time.perf_counter() - t0)
    P = softmax((W @ e + b) / head['temperature'])
    en = e / np.linalg.norm(e); d = 1 - np.sort(R @ en)[-head['ood']['k']:].mean()
    ans = P.max() >= head['threshold'] and d <= head['ood']['cutoff']
    sample_rows.append({'file': s['file'], 'truth': s['truth'], 'pred': head['classes'][int(P.argmax())],
                 'p': round(float(P.max()), 3), 'dist': round(float(d), 3), 'answered': bool(ans)})
for r in sample_rows:
    print(r)
# same decisions as the Python evaluation on the original photos (results/metrics.json, shipped model)?
py = {p['original_file']: p for p in json.load(open(os.path.join(REPO, 'results', 'metrics.json')))['shipped']['held_out']['demo_samples_7']}
same_samples = sum(1 for s, r in zip(man, sample_rows) if s['original_file'] in py and py[s['original_file']]['answered'] == r['answered']
                   and (not r['answered'] or py[s['original_file']]['pred'] == r['pred']))
n_samples = len(sample_rows)
print('demo samples (app copies, ONNX) vs Python (original photos): same decision on', same_samples, 'of', n_samples)
# agreement with the Python pipeline on original field images
import csv
from scipy.special import softmax as sm
rows = list(csv.DictReader(open(os.path.join(REPO, 'results', 'index.csv'))))
E = np.load(os.path.join(os.path.dirname(REPO), 'data_work', 'embeddings.npz'))['E']
st = np.load(os.path.join(os.path.dirname(REPO), 'data_work', 'standardisation.npz'))
RAW = os.path.join(os.path.dirname(REPO), 'data_raw')
pick = [i for i, r in enumerate(rows) if r['source'] == 'RoCoLe'][:25]
agree = 0; maxdiff = 0
for i in pick:
    e = sess.run(None, {'input': prep(os.path.join(RAW, rows[i]['path']))})[0][0]
    z = (E[i] - st['mu']) / st['sd']
    maxdiff = max(maxdiff, float(np.abs(e - z).max()))
    agree += int(np.argmax(W @ e + b) == np.argmax(W @ z + b))
print('ONNX vs Python: same class on', agree, 'of', len(pick), '; max abs embedding diff', round(maxdiff, 4))
out = {'head_version': head['version'], 'reference_rows': int(n),
       'samples_same_decision_as_python': f'{same_samples}/{n_samples}',
       'onnx_vs_python_same_class': f'{agree}/{len(pick)}', 'onnx_vs_python_max_abs_diff': round(maxdiff, 4),
       'reference_kb': round(os.path.getsize(os.path.join(REPO, 'model', ref['file'])) / 1e3, 1), 'onnx_mb': round(os.path.getsize(os.path.join(REPO, 'model', 'backbone.onnx')) / 1e6, 1),
       'head_kb': round(os.path.getsize(os.path.join(REPO, 'model', 'head.json')) / 1e3, 1),
       'cpu_ms_per_image_laptop': round(1000 * float(np.median(times[1:] or times)), 1), 'samples': sample_rows}
json.dump(out, open(os.path.join(REPO, 'results', 'onnx_check.json'), 'w'), indent=1)
print({k: v for k, v in out.items() if k != 'samples'})
