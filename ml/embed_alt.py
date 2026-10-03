"""Experiment: embed a subset with an alternative backbone (default DINOv2-small) to test field robustness.
Writes ../data_work/emb_<name>.npz with row indices into results/index.csv."""
import os, csv, json, sys, numpy as np, torch, timm
from PIL import Image
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(HERE)
RAW = os.path.join(os.path.dirname(REPO), 'data_raw'); WORK = os.path.join(os.path.dirname(REPO), 'data_work')
NAME = os.environ.get('ALT', 'vit_small_patch14_dinov2.lvd142m'); PER = int(os.environ.get('PER', 600))
MEAN = np.array([0.485, 0.456, 0.406], np.float32)[:, None, None]; STD = np.array([0.229, 0.224, 0.225], np.float32)[:, None, None]
def prep(p):
    im = Image.open(os.path.join(RAW, p)).convert('RGB'); w, h = im.size; s = 256 / min(w, h)
    im = im.resize((round(w * s), round(h * s)), Image.BILINEAR); w, h = im.size; l, t = (w - 224) // 2, (h - 224) // 2
    a = np.asarray(im.crop((l, t, l + 224, t + 224)), np.float32).transpose(2, 0, 1) / 255.0
    return (a - MEAN) / STD
if __name__ == '__main__':
    rows = list(csv.DictReader(open(os.path.join(REPO, 'results', 'index.csv'))))
    rng = np.random.default_rng(0); keep = []
    for lab in ['healthy', 'rust', 'miner', 'cercospora', 'phoma']:
        idx = [i for i, r in enumerate(rows) if r['source'].startswith('JMuBEN') and r['label'] == lab]
        keep += list(rng.permutation(idx)[:PER])
    keep += [i for i, r in enumerate(rows) if r['source'] in ('BRACOL', 'RoCoLe')]
    keep = sorted(keep)
    kw = {'img_size': 224} if 'vit' in NAME else {}
    m = timm.create_model(NAME, pretrained=True, num_classes=0, **kw).eval().to('mps')
    E = []
    with Pool(8) as pool:
        for s in range(0, len(keep), 64):
            x = torch.from_numpy(np.stack(pool.map(prep, [rows[i]['path'] for i in keep[s:s + 64]]))).to('mps')
            with torch.no_grad(): E.append(m(x).float().cpu().numpy())
            if s % 1280 == 0: print(s, len(keep), flush=True)
    np.savez_compressed(os.path.join(WORK, f'emb_{NAME.split(".")[0]}.npz'), E=np.concatenate(E), idx=np.array(keep))
    print('done', NAME, sum(p.numel() for p in m.parameters()) / 1e6, 'M params')
