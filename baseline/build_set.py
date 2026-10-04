"""Build the human-baseline photo set and picture card (run once; outputs are committed).

  ../.venv/bin/python baseline/build_set.py              # photos + key + card
  ../.venv/bin/python baseline/build_set.py --candidates # contact sheets of card candidates (to scratch)

Photo set: 60 RoCoLe field photos (30 healthy, 30 rust split across rust levels 1-4 in proportion to the
pool), seeded. It excludes the 50 photos inside model/update_demo_50_labonly.json and the 7 demo samples, so the
model 'after the demo update' is scored on photos it never saw. The update file stores only embeddings,
so the 50 rows are recomputed with the same selection as ml/train_eval.py and checked against the file.
Photos are resized to max 900 px (JPEG q85, no EXIF) and named p01..p60 in shuffled order, so the name
says nothing about the class. The answer key is baseline/key.json; the labelling page never loads it.

Picture card: 2 pictures per class from the TRAINING split (one JMuBEN close-up crop, one BRACOL whole
leaf). Candidates are drawn at random (seeded) from the training split; the two shown per class were
picked by eye from those candidates for clarity (CARD below). Symptom lines come from answers.json.
"""
import os, sys, csv, json
import numpy as np
from PIL import Image, ImageOps, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(HERE)
TOP = os.path.dirname(REPO); RAW = os.path.join(TOP, 'data_raw'); WORK = os.path.join(TOP, 'data_work')
sys.path.insert(0, os.path.join(REPO, 'ml'))
SEED = 2026
N_HEALTHY, N_RUST = 30, 30
MAX_PX, QUALITY = 900, 85
CLASSES = ['healthy', 'rust', 'miner', 'cercospora', 'phoma']

# Card pictures picked by eye from the seeded training candidates (--candidates). Paths as in results/index.csv.
CARD = {
    'healthy': ['tgv3zb82nd/Healthy-20210326T083815Z-001/Healthy/1 (320).jpg',
                'yy2k5y8mxg/BRACOL/coffee-datasets/coffee-datasets/leaf/images/1370.jpg'],
    'rust': ['t2r6rszp5c/Leaf_rust-20210326T083416Z-001/Leaf rust/1 (113).jpg',
             'yy2k5y8mxg/BRACOL/coffee-datasets/coffee-datasets/leaf/images/168.jpg'],
    'miner': ['tgv3zb82nd/Miner-20210326T082341Z-001/Miner/1 (2022).jpg',
              'yy2k5y8mxg/BRACOL/coffee-datasets/coffee-datasets/leaf/images/686.jpg'],
    'cercospora': ['t2r6rszp5c/Cerscospora-20210326T085017Z-001/Cerscospora/9 (2996).jpg',
                   'yy2k5y8mxg/BRACOL/coffee-datasets/coffee-datasets/leaf/images/1252.jpg'],
    'phoma': ['t2r6rszp5c/Phoma-20210326T082051Z-001/Phoma/6 (2714).jpg',
              'yy2k5y8mxg/BRACOL/coffee-datasets/coffee-datasets/leaf/images/355.jpg'],
}


def symptom_line(text):
    """Second sentence of the answers.json 'en' text, shortened for a card:
    'It shows as round brown spots ...' -> 'Round brown spots ...'; '... was seen.' -> '...'."""
    s = text.split('. ')[1].strip().rstrip('.')
    if s.startswith('It shows as '):
        s = s[len('It shows as '):]
    s = s.replace(' was seen', '')
    return s[0].upper() + s[1:] + '.'


def unit(X):
    return X / np.linalg.norm(X, axis=1, keepdims=True)


def load_rows():
    rows = list(csv.DictReader(open(os.path.join(REPO, 'results', 'index.csv'))))
    E = np.load(os.path.join(WORK, 'embeddings.npz'))['E']
    assert len(rows) == len(E)
    return rows, E


def demo_update_rows(rows, E):
    """Re-run the 'demo update' selection of ml/train_eval.py and check it against model/update_demo_50_labonly.json."""
    src = np.array([r['source'] for r in rows]); lab = np.array([r['label'] for r in rows])
    fidx = np.where((src == 'RoCoLe') & np.isin(lab, ['healthy', 'rust']))[0]  # = split_masks()['field']
    sample_files = {s['original_file'] for s in json.load(open(os.path.join(REPO, 'samples', 'manifest.json')))['samples']}
    r = np.random.default_rng(7)
    cand = [i for i in fidx if os.path.basename(rows[i]['path']) not in sample_files]
    pick = r.choice(cand, 50, replace=False)
    upd = json.load(open(os.path.join(REPO, 'model', 'update_demo_50_labonly.json')))
    st = np.load(os.path.join(WORK, 'standardisation.npz'))
    Zn = unit((E[pick] - st['mu']) / st['sd'])
    q = np.array(upd['reference_add']['int8'], np.float32); sc = np.array(upd['reference_add']['scale'], np.float32)
    Rn = unit(q * sc[:, None])
    cos = (Zn * Rn).sum(1)
    assert cos.min() > 0.99, f'demo-update rows do not match (min cosine {cos.min():.4f})'
    assert [rows[i]['label'] for i in pick] == upd['labels'], 'demo-update labels do not match'
    return fidx, set(int(i) for i in pick), sample_files, float(cos.min())


def choose_photos(rows, fidx, used, sample_files):
    pool = [i for i in fidx if i not in used and os.path.basename(rows[i]['path']) not in sample_files]
    det = np.array([rows[i]['detail'] for i in pool]); pool = np.array(pool)
    rng = np.random.default_rng(SEED)
    healthy = rng.choice(pool[det == 'healthy'], N_HEALTHY, replace=False)
    levels = [f'rust_level_{k}' for k in range(1, 5)]
    avail = np.array([(det == l).sum() for l in levels])
    share = avail / avail.sum() * N_RUST
    alloc = np.floor(share).astype(int)
    for k in np.argsort(-(share - alloc))[:N_RUST - alloc.sum()]:  # largest remainder
        alloc[k] += 1
    rust = np.concatenate([rng.choice(pool[det == l], n, replace=False) for l, n in zip(levels, alloc)])
    chosen = np.concatenate([healthy, rust])
    rng.shuffle(chosen)  # p01..p60 in shuffled order
    return chosen, dict(zip(levels, alloc.tolist())), dict(zip(levels, avail.tolist())), int((det == 'healthy').sum())


def save_resized(src_path, dst_path, max_px=MAX_PX):
    im = ImageOps.exif_transpose(Image.open(src_path)).convert('RGB')
    im.thumbnail((max_px, max_px), Image.LANCZOS)
    im.save(dst_path, 'JPEG', quality=QUALITY, optimize=True)  # saved without EXIF
    return im.size


def training_mask(rows):
    """The training split exactly as ml/train_eval.py makes it (module RNG reset to its seed)."""
    import train_eval as te
    te.RNG = np.random.default_rng(0)
    M, src, lab = te.split_masks(rows)
    return M['train'], src, lab


def candidates(rows):
    tr, src, lab = training_mask(rows)
    rng = np.random.default_rng(SEED)
    out = os.environ.get('OUT', HERE)
    for c in CLASSES:
        tiles = []
        for s_ in (['JMuBEN', 'JMuBEN2'], ['BRACOL']):
            idx = np.where(tr & (lab == c) & np.isin(src, s_))[0]
            for i in rng.choice(idx, 8, replace=False):
                im = Image.open(os.path.join(RAW, rows[i]['path'])).convert('RGB')
                im.thumbnail((256, 256)); tile = Image.new('RGB', (256, 280), 'white'); tile.paste(im, (0, 0))
                ImageDraw.Draw(tile).text((4, 262), f'{i}', fill='black'); tiles.append(tile)
        sheet = Image.new('RGB', (256 * 8, 280 * 2), 'white')
        for k, t in enumerate(tiles):
            sheet.paste(t, ((k % 8) * 256, (k // 8) * 280))
        sheet.save(os.path.join(out, f'cand_{c}.jpg'), quality=80)
        print(c, os.path.join(out, f'cand_{c}.jpg'))


def build_card(rows, ans):
    tr, src, lab = training_mask(rows)
    path_to_i = {r['path']: i for i, r in enumerate(rows)}
    os.makedirs(os.path.join(HERE, 'card'), exist_ok=True)
    names = {'healthy': 'Healthy', 'rust': 'Leaf rust', 'miner': 'Leaf miner',
             'cercospora': 'Brown eye spot (Cercospora)', 'phoma': 'Phoma'}
    card = {'classes': [], 'credits': [], 'note': 'Card pictures come from the training photos (Kenya close-up crops and '
                                                   'Brazil whole leaves), not from the photos you will label.'}
    for c in CLASSES:
        pics = []
        for k, p in enumerate(CARD[c]):
            i = path_to_i[p]
            assert tr[i] and lab[i] == c, f'{p} is not a training photo of {c}'
            fn = f'{c}_{k + 1}.jpg'
            size = save_resized(os.path.join(RAW, p), os.path.join(HERE, 'card', fn), 600)
            kind = 'close-up crop, Kenya (JMuBEN)' if src[i].startswith('JMuBEN') else 'whole leaf, Brazil (BRACOL)'
            pics.append({'file': 'card/' + fn, 'kind': kind, 'size': list(size), 'source_path': p})
        text = ans['result_' + c]['en']
        card['classes'].append({'id': c, 'name': names[c], 'line': symptom_line(text), 'answers_json_en': text,
                                'pictures': pics})
    card['credits'] = [
        'JMuBEN and JMuBEN2: Jepkoech, Mugo, Kenduiywo, Too (2021), Mendeley Data, CC BY 4.0.',
        'BRACOL: Krohling, Esgario, Ventura (2019), Mendeley Data, CC BY 4.0.',
        'Photos to label: RoCoLe, Parraga-Alava, Cusme, Loor, Santander (2019), Mendeley Data, CC BY 4.0.',
        'Pictures resized; no other changes.']
    json.dump(card, open(os.path.join(HERE, 'card', 'card.json'), 'w'), indent=1, ensure_ascii=False)
    return card


def main():
    rows, E = load_rows()
    if '--candidates' in sys.argv:
        candidates(rows); return
    fidx, used, sample_files, mincos = demo_update_rows(rows, E)
    chosen, alloc, avail, n_h_pool = choose_photos(rows, fidx, used, sample_files)
    assert not (set(chosen.tolist()) & used)
    assert not ({os.path.basename(rows[i]['path']) for i in chosen} & sample_files)
    os.makedirs(os.path.join(HERE, 'photos'), exist_ok=True)
    key = {}
    for k, i in enumerate(chosen):
        pid = f'p{k + 1:02d}'
        size = save_resized(os.path.join(RAW, rows[i]['path']), os.path.join(HERE, 'photos', pid + '.jpg'))
        d = rows[i]['detail']
        key[pid] = {'truth': rows[i]['label'], 'rust_level': int(d[-1]) if d.startswith('rust_level_') else 0,
                    'original_file': os.path.basename(rows[i]['path']), 'index_row': int(i), 'shown_size': list(size)}
    meta = {'set': f'rocole60-seed{SEED}', 'seed': SEED, 'n': len(key), 'healthy': N_HEALTHY, 'rust_by_level': alloc,
            'pool_available': {'healthy': n_h_pool, **avail},
            'excluded': {'demo_update_50': len(used), 'demo_samples': len(sample_files)},
            'demo_update_check_min_cosine': round(mincos, 5),
            'source': 'RoCoLe (Parraga-Alava et al. 2019), Ecuador, robusta, on-plant field photos, CC BY 4.0'}
    json.dump({'meta': meta, 'photos': key}, open(os.path.join(HERE, 'key.json'), 'w'), indent=1)
    json.dump({'set': f'rocole60-seed{SEED}', 'ids': list(key)}, open(os.path.join(HERE, 'photos', 'list.json'), 'w'))
    ans = json.load(open(os.path.join(REPO, 'answers.json')))
    if CARD:
        build_card(rows, ans)
    print(json.dumps(meta, indent=1))


if __name__ == '__main__':
    main()
