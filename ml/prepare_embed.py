"""Index the coffee-leaf datasets, sample up to 1,500 JMuBEN photos per class, and embed every image
with the frozen backbone (same preprocessing as the web app). DEDUP=1 groups augmented copies instead;
it is off by default because the hash is too coarse for these crops.

Outputs results/index.csv and ../data_work/embeddings.npz (not committed: large).
Run: ../.venv/bin/python ml/prepare_embed.py
"""
import os, glob, json, csv, sys
import numpy as np
from PIL import Image
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
RAW = os.path.join(os.path.dirname(REPO), 'data_raw')
WORK = os.path.join(os.path.dirname(REPO), 'data_work')
os.makedirs(WORK, exist_ok=True)
CAP = int(os.environ.get('CAP', 1500))  # max JMuBEN photos sampled per class (groups when DEDUP=1)
CLASSES = ['healthy', 'rust', 'miner', 'cercospora', 'phoma']


def jmuben_items():
    spec = [('t2r6rszp5c', 'Leaf_rust-*/Leaf rust', 'rust', 'JMuBEN'),
            ('t2r6rszp5c', 'Cerscospora-*/Cerscospora', 'cercospora', 'JMuBEN'),
            ('t2r6rszp5c', 'Phoma-*/Phoma', 'phoma', 'JMuBEN'),
            ('tgv3zb82nd', 'Healthy-*/Healthy', 'healthy', 'JMuBEN2'),
            ('tgv3zb82nd', 'Miner-*/Miner', 'miner', 'JMuBEN2')]
    out = []
    for ds, pat, lab, src in spec:
        for p in sorted(glob.glob(os.path.join(RAW, ds, pat, '*'))):
            if p.lower().endswith(('.jpg', '.jpeg', '.png')):
                out.append({'source': src, 'label': lab, 'path': p})
    return out


def bracol_items():
    base = os.path.join(RAW, 'yy2k5y8mxg', 'BRACOL', 'coffee-datasets', 'coffee-datasets', 'leaf')
    lab_map = {0: 'healthy', 1: 'miner', 2: 'rust', 3: 'phoma', 4: 'cercospora'}  # predominant_stress
    out = []
    with open(os.path.join(base, 'dataset.csv')) as f:
        for r in csv.DictReader(f):
            p = os.path.join(base, 'images', r['id'] + '.jpg')
            ps = int(r['predominant_stress'])
            if ps in lab_map and os.path.exists(p):
                out.append({'source': 'BRACOL', 'label': lab_map[ps], 'path': p})
    return out


def rocole_items():
    base = os.path.join(RAW, 'rocole', 'ds')
    out = []
    for f in sorted(glob.glob(os.path.join(base, 'ann', '*.json'))):
        a = json.load(open(f))
        cl = sorted(set(o['classTitle'] for o in a['objects']) - {'unhealthy'})
        if len(cl) != 1:
            continue  # 4 images with both healthy and rust polygons, or no specific class: dropped
        c = cl[0]
        lab = 'rust' if c.startswith('rust') else ('healthy' if c == 'healthy' else 'mite')
        out.append({'source': 'RoCoLe', 'label': lab, 'path': os.path.join(base, 'img', os.path.basename(f)[:-5]),
                    'detail': c})
    return out


def dihedral_hash(path):
    """64-bit DCT perceptual hash, minimised over the 8 flips/rotations, so augmented copies collide."""
    from scipy.fft import dctn
    try:
        g = np.asarray(Image.open(path).convert('L').resize((32, 32), Image.BILINEAR), dtype=np.float32)
    except Exception:
        return None
    best = None
    for k in range(4):
        for flip in (False, True):
            a = np.rot90(g, k)
            a = a[:, ::-1] if flip else a
            d = dctn(a, norm='ortho')[:8, :8].ravel()
            bits = (d > np.median(d[1:])).astype(np.uint8)
            h = int(''.join(map(str, bits)), 2)
            best = h if best is None or h < best else best
    return best


def main():
    rng = np.random.default_rng(0)
    jm = jmuben_items()
    print('JMuBEN raw images:', len(jm), flush=True)
    stats = {}
    sel = []
    if os.environ.get('DEDUP', '0') == '1':
        # Dihedral perceptual-hash grouping. NOTE: too coarse for 128x128 leaf crops (healthy collapsed
        # to 15 groups in a test run), so it is off by default.
        with Pool(max(2, os.cpu_count() - 2)) as pool:
            hashes = pool.map(dihedral_hash, [x['path'] for x in jm], chunksize=256)
        groups = {}
        for x, h in zip(jm, hashes):
            if h is not None:
                groups.setdefault((x['label'], h), []).append(x)
        for lab in CLASSES:
            keys = [k for k in groups if k[0] == lab]; rng.shuffle(keys)
            stats[lab] = {'raw_images': sum(1 for x in jm if x['label'] == lab), 'dedup_groups': len(keys)}
            for k in keys[:CAP]:
                x = dict(groups[k][0]); x['group'] = f'{lab}-{k[1]:016x}'; sel.append(x)
    else:
        # Random sample of up to CAP images per class. JMuBEN contains rotated/flipped copies of the same
        # leaf, so an in-domain JMuBEN validation split is optimistic; headline numbers use other sources.
        for lab in CLASSES:
            pool_ = [x for x in jm if x['label'] == lab]
            idx = rng.permutation(len(pool_))[:CAP]
            stats[lab] = {'raw_images': len(pool_), 'sampled': int(len(idx))}
            for i in idx:
                x = dict(pool_[i]); x['group'] = f'{lab}-' + os.path.basename(x['path']); sel.append(x)
    print('JMuBEN stats:', stats, flush=True)
    br = bracol_items(); ro = rocole_items()
    for i, x in enumerate(br):
        x['group'] = 'bracol-' + os.path.basename(x['path'])
    for x in ro:
        x['group'] = 'rocole-' + os.path.basename(x['path'])
    items = sel + br + ro
    print('selected:', len(sel), 'BRACOL:', len(br), 'RoCoLe:', len(ro), flush=True)
    json.dump({'jmuben': stats, 'n_selected_jmuben': len(sel), 'n_bracol': len(br), 'n_rocole': len(ro), 'cap': CAP},
              open(os.path.join(REPO, 'results', 'data_stats.json'), 'w'), indent=1)

    # Embed with the frozen backbone (torch on Apple GPU; identical weights to model/backbone.onnx)
    import torch, timm
    dev = 'mps' if torch.backends.mps.is_available() else 'cpu'
    meta = json.load(open(os.path.join(REPO, 'model', 'backbone_meta.json')))
    m = timm.create_model(meta['backbone'], pretrained=True, num_classes=0).eval().to(dev)
    embs = np.zeros((len(items), meta['embed_dim']), np.float32)
    ok = np.ones(len(items), bool)
    B = 128
    with Pool(max(2, os.cpu_count() - 2)) as pool:
        for s in range(0, len(items), B):
            batch = items[s:s + B]
            arrs = pool.map(_safe_load_factory(meta), [x['path'] for x in batch])
            good = [i for i, a in enumerate(arrs) if a is not None]
            for i, a in enumerate(arrs):
                if a is None:
                    ok[s + i] = False
            if good:
                x = torch.from_numpy(np.stack([arrs[i] for i in good])).to(dev)
                with torch.no_grad():
                    e = m(x).float().cpu().numpy()
                embs[[s + i for i in good]] = e
            if (s // B) % 20 == 0:
                print(f'embedded {s + len(batch)}/{len(items)}', flush=True)
    items = [x for x, k in zip(items, ok) if k]; embs = embs[ok]
    np.savez_compressed(os.path.join(WORK, 'embeddings.npz'), E=embs)
    with open(os.path.join(REPO, 'results', 'index.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['source', 'label', 'detail', 'group', 'path'])
        w.writeheader()
        for x in items:
            w.writerow({k: x.get(k, '') for k in w.fieldnames} | {'path': os.path.relpath(x['path'], RAW)})
    print('done', embs.shape, 'unreadable dropped:', int((~ok).sum()))


class _safe_load_factory:
    def __init__(self, meta):
        self.meta = meta
        self.mean = np.array(meta['mean'], np.float32)[:, None, None]
        self.std = np.array(meta['std'], np.float32)[:, None, None]

    def __call__(self, p):
        try:
            im = Image.open(p).convert('RGB')
            w, h = im.size; s = self.meta['resize_shorter'] / min(w, h)
            im = im.resize((max(1, round(w * s)), max(1, round(h * s))), Image.BILINEAR)
            w, h = im.size; c = self.meta['input_size']; l, t = (w - c) // 2, (h - c) // 2
            a = np.asarray(im.crop((l, t, l + c, t + c)), np.float32).transpose(2, 0, 1) / 255.0
            return (a - self.mean) / self.std
        except Exception:
            return None


if __name__ == '__main__':
    main()
