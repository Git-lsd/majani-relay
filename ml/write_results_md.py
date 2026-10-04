"""Write results/RESULTS.md, results/numbers.json and results/NUMBERS_KEYS.md from the results files
(numbers are never typed by hand). Run: ../.venv/bin/python ml/write_results_md.py

numbers.json keeps every key the docs already use, with its earlier meaning: those keys describe the LAB-ONLY model
(now the new-region simulation). Keys for the SHIPPED lab+field model start with SHIP_. NUMBERS_KEYS.md lists them.
"""
import os, json

HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(HERE); RES = os.path.join(REPO, 'results')
M = json.load(open(os.path.join(RES, 'metrics.json')))
O = json.load(open(os.path.join(RES, 'onnx_check.json')))
LIMS = json.load(open(os.path.join(RES, 'limits.json')))
LO = M['lab_only_new_region_simulation']; SH = M['shipped']
L = LO['learning_loop']; ks = L['ks']; pa = L['curves']['prior_adapt']; lo = L['curves']['local_only']
V = LO['village_sim']; VS = M['village_sim']; f = LO['field']; c = LO['in_domain_calib']
CV = SH['field_cv']['summary']; HO = SH['held_out']; NT = SH['n_train']; DUP = SH['rocole_identical_copies']
pct = lambda x: f'{100 * x:.0f}%'
pct1 = lambda x: f'{100 * x:.1f}%'
pts = lambda x: f'{100 * x:.1f}'          # standard deviation in percentage points
i10, i50, i200 = ks.index(10), ks.index(50), ks.index(200)
kb = lambda p: f"{os.path.getsize(os.path.join(REPO, 'model', p)) / 1e3:.0f}"

# ---------------------------------------------------------------- keys the docs already use (lab-only meaning)
N = {
    'MODEL_MB': f"{O['onnx_mb']:.1f}", 'HEAD_KB': f"{O['head_kb']:.0f}", 'REF_KB': kb('reference_labonly.bin'),
    'LATENCY_MS_LAPTOP': f"{O['cpu_ms_per_image_laptop']:.0f}",
    'LAB_ACC': pct(c['acc_all']), 'LAB_COVERAGE': pct(c['coverage']), 'LAB_ACC_ANSWERED': pct(c['acc_answered']),
    'FIELD_ACC_NO_ABSTAIN': f"{100 * f['acc_all']:.1f}%", 'FIELD_MEAN_CONFIDENCE': pct(f['mean_confidence']),
    'FIELD_NOT_SURE': f"{100 * (1 - f['coverage']):.1f}%", 'MITE_NOT_SURE': pct(LO['mite']['abstain_rate']),
    'AUROC_KNN': f"{LO['ood_auroc_field_vs_heldout']['knn10_cosine (used)']:.3f}",
    'AUROC_CONFIDENCE': f"{LO['ood_auroc_field_vs_heldout']['max_softmax']:.2f}",
    'COV_10': pct(pa['coverage'][i10]), 'ACC_ANS_10': pct(pa['acc_answered'][i10]), 'ACC_ANS_10_LOCAL_ONLY': pct(lo['acc_answered'][i10]),
    'COV_50': pct(pa['coverage'][i50]), 'ACC_ANS_50': pct(pa['acc_answered'][i50]),
    'ACC_ANS_50_LOCAL_ONLY': pct(lo['acc_answered'][i50]), 'ACC_ANS_200_LOCAL_ONLY': pct(lo['acc_answered'][i200]),
    'COV_200': pct(pa['coverage'][i200]), 'ACC_ANS_200': pct(pa['acc_answered'][i200]),
    'UPDATE_KB_HEAD': f"{L['update_bytes_float16_head'] / 1e3:.0f}",
    'UPDATE_BYTES_PER_PHOTO': f"{L['update_bytes_int8_per_reference_photo']}",
    'VILLAGE_FA_RAW': f"{V['raw']['false_alarms']:.1f}", 'VILLAGE_FA_ADJ': f"{V['shrunk']['false_alarms']:.1f}",
    'VILLAGE_MISS_RAW': f"{V['raw']['missed']:.1f}", 'VILLAGE_MISS_ADJ': f"{V['shrunk']['missed']:.1f}",
    'VILLAGE_TOP5_RAW': f"{V['raw']['top5_hits']:.1f}", 'VILLAGE_TOP5_ADJ': f"{V['shrunk']['top5_hits']:.1f}",
    'VILLAGE_HOT': f"{V['mean_true_hot_villages']:.1f}", 'ALERT_RATE': '25%', 'ALERT_PROB': '0.5',
    'N_TRAIN': str(M['n']['train']), 'N_CALIB': str(M['n']['calib']), 'N_FIELD': str(M['n']['field']), 'N_MITE': str(M['n']['mite']),
}
alt = LO.get('alt_backbone_dinov2_small')
if alt:
    N['DINO_FIELD_ACC'] = pct(alt['field_acc_no_local_labels'])
    N['DINO_COV_50'] = pct(alt['loop_prior_adapt']['50']['coverage']); N['DINO_ACC_ANS_50'] = pct(alt['loop_prior_adapt']['50']['acc_answered'])

# ---------------------------------------------------------------- shipped model (new keys)
hbs = HO['human_baseline_60']; sm7 = HO['demo_samples_7']; mi = HO['mite']; ls = SH['lab_style']['bracol_calibration_half']
NS = {
    'SHIP_VERSION': json.load(open(os.path.join(REPO, 'model', 'head.json')))['version'],
    'SHIP_N_TRAIN': str(NT['total']), 'SHIP_N_TRAIN_LAB': str(NT['lab']), 'SHIP_N_TRAIN_FIELD': str(NT['field']),
    'SHIP_N_TRAIN_FIELD_HEALTHY': str(NT['field_healthy']), 'SHIP_N_TRAIN_FIELD_RUST': str(NT['field_rust']),
    'SHIP_N_COPIES_REMOVED': str(DUP['training_candidates_removed_as_copies_of_held_out']),
    'SHIP_REF_N': str(SH['reference_n']), 'SHIP_REF_N_LAB': str(SH['reference_rows']['lab']),
    'SHIP_REF_N_FIELD': str(SH['reference_rows']['field']), 'SHIP_REF_KB': f"{O['reference_kb']:.0f}",
    'SHIP_HEAD_KB': f"{O['head_kb']:.0f}", 'SHIP_ONNX_AGREE': O['onnx_vs_python_same_class'],
    'SHIP_C': f"{SH['C']:g}", 'SHIP_TEMPERATURE': f"{SH['temperature']:.2f}", 'SHIP_THRESHOLD': f"{SH['threshold']:.2f}",
    'SHIP_CUTOFF': f"{SH['familiarity_cutoff']:.3f}",
    'SHIP_CV_FOLDS': str(SH['field_cv']['folds']),
    'SHIP_CV_COVERAGE': pct(CV['coverage']), 'SHIP_CV_COVERAGE_SD': pts(CV['coverage_sd']),
    'SHIP_CV_NOT_SURE': pct(CV['not_sure']),
    'SHIP_CV_ACC_ANSWERED': pct(CV['acc_answered']), 'SHIP_CV_ACC_ANSWERED_SD': pts(CV['acc_answered_sd']),
    'SHIP_CV_ACC': pct(CV['acc_all']), 'SHIP_CV_ACC_SD': pts(CV['acc_all_sd']),
    'SHIP_CV_RUST_NAMED': pct(CV['rust_named']), 'SHIP_CV_RUST_NAMED_SD': pts(CV['rust_named_sd']),
    'SHIP_CV_HEALTHY_FLAGGED': pct(CV['healthy_flagged']), 'SHIP_CV_HEALTHY_FLAGGED_SD': pts(CV['healthy_flagged_sd']),
    'SHIP_CV_ECE': f"{CV['ece']:.2f}", 'SHIP_CV_ECE_SD': f"{CV['ece_sd']:.2f}",
    'SHIP_CV_HVP_ANSWERED': pct(CV['hvp_answered']),
    'SHIP_CV_ACC_NOT_SURE_IF_FORCED': pct(CV['acc_not_sure_if_forced']),
    'SHIP_CV_NOT_SURE_LOW_CONF': pct1(CV['not_sure_low_confidence']), 'SHIP_CV_NOT_SURE_UNFAMILIAR': pct1(CV['not_sure_unfamiliar']),
    'SHIP_CV_SENS_ANSWERED': pct(CV['sens_answered_rust']), 'SHIP_CV_FPR_ANSWERED': pct(CV['fpr_answered_healthy_as_rust']),
    'SHIP_LAB_ACC': pct(ls['acc_all']), 'SHIP_LAB_COVERAGE': pct(ls['coverage']), 'SHIP_LAB_ACC_ANSWERED': pct(ls['acc_answered']),
    'SHIP_DEMO_N': str(len(sm7)),
    'SHIP_DEMO_ANSWERED_CORRECT': str(sum(p['answered'] and p['pred'] == p['truth'] for p in sm7)),
    'SHIP_DEMO_NOT_SURE': str(sum(not p['answered'] for p in sm7)),
    'SHIP_DEMO_MITE_CALLED': ', '.join(('not sure' if not p['answered'] else p['pred']) for p in sm7 if p['truth'] == 'mite'),
    'SHIP_MITE_NOT_SURE': pct(mi['not_sure']), 'SHIP_MITE_NOT_SURE_CV': pct(mi['cv_mean_not_sure']),
    'SHIP_MITE_CALLED_RUST': str(mi['answered_as'].get('rust', 0)), 'SHIP_MITE_CALLED_HEALTHY': str(mi['answered_as'].get('healthy', 0)),
    'SHIP_MITE_AUROC_FAMILIARITY': f"{mi['auroc_mite_vs_field_cv']['familiarity_distance']:.2f}",
    'SHIP_MITE_AUROC_CONFIDENCE': f"{mi['auroc_mite_vs_field_cv']['confidence']:.2f}",
    'SHIP_VILLAGE_FA_RAW': f"{VS['raw']['false_alarms']:.1f}", 'SHIP_VILLAGE_FA_ADJ': f"{VS['shrunk']['false_alarms']:.1f}",
    'SHIP_VILLAGE_MISS_RAW': f"{VS['raw']['missed']:.1f}", 'SHIP_VILLAGE_MISS_ADJ': f"{VS['shrunk']['missed']:.1f}",
    'SHIP_VILLAGE_TOP5_RAW': f"{VS['raw']['top5_hits']:.1f}", 'SHIP_VILLAGE_TOP5_ADJ': f"{VS['shrunk']['top5_hits']:.1f}",
    'SHIP_VILLAGE_HOT': f"{VS['mean_true_hot_villages']:.1f}",
    'SHIP_VILLAGE_COVERAGE': pct(VS['inputs']['coverage']), 'SHIP_VILLAGE_SENS': pct(VS['inputs']['sensitivity']),
    'SHIP_VILLAGE_FPR': pct(VS['inputs']['false_positive_rate']),
    'RO_DUP_PAIRS': str(DUP['pairs']), 'RO_DUP_PAIRS_DIFFERENT_LABELS': str(DUP['pairs_with_different_labels']),
    'LABONLY_REF_N': str(LO['reference_n']),
}
lm = LIMS['out_of_scope_pest_after_50_labels']
NS.update({'LABONLY_MITE_NOT_SURE_AFTER_50': pct(lm['not_sure_after_50']),
           'LABONLY_MITE_RUST_AFTER_50': str(lm['answered_as_after_50'].get('rust', 0)),
           'LABONLY_MITE_HEALTHY_AFTER_50': str(lm['answered_as_after_50'].get('healthy', 0))})

# ---------------------------------------------------------------- human baseline (picture card vs AI)
HBP = os.path.join(RES, 'human_baseline.json')
HB = json.load(open(HBP)) if os.path.exists(HBP) else None
if HB and not HB.get('labellers'):
    HB = None
if HB:
    hum = HB['labellers']; aiS = HB['model']['shipped_v2_lab_field']
    ai0 = HB['model']['lab_only_as_shipped']; ai1 = HB['model']['lab_only_after_demo_update_50']

    def rng_(vals, fmt):
        v = [x for x in vals if x is not None]
        if not v:
            return '-'
        lo_, hi_ = fmt(min(v)), fmt(max(v))
        return lo_ if lo_ == hi_ else f'{lo_}–{hi_}'
    _cnt = lambda x: sum(round(v['correct_of_all'] * v['n']) for k, v in x['by_rust_level'].items() if k != '0')
    _hcp = lambda x: str(round(x['by_rust_level']['0']['called_a_problem_of_all'] * x['by_rust_level']['0']['n']))
    _rn = [_cnt(x) for x in hum]
    _ce = [x['answer_counts'].get('cercospora', 0) for x in hum]
    _ag = list(HB.get('labeller_agreement', {}).values())
    _rng = lambda v: f"{min(v)}–{max(v)}" if min(v) != max(v) else str(v[0])
    N.update({'HB_N_LABELLERS': str(len(hum)), 'HB_N_PHOTOS': str(HB['photo_set']['n']),
              'HB_HUMAN_ANSWERED': rng_([h['share_answered'] for h in hum], pct),
              'HB_HUMAN_ACC_ANSWERED': rng_([h['acc_answered'] for h in hum], pct),
              'HB_HUMAN_HVP': rng_([h['acc_healthy_vs_problem_answered'] for h in hum], pct),
              'HB_HUMAN_CORRECT_OF_ALL': rng_([h['correct_of_all'] for h in hum], pct),
              'HB_HUMAN_MEDIAN_SECONDS': rng_([h['median_seconds'] for h in hum], lambda x: f'{x:.1f}'),
              'HB_AI_SHIPPED_NOT_SURE': pct(1 - ai0['share_answered']),
              'HB_AI_UPD_ANSWERED': pct(ai1['share_answered']), 'HB_AI_UPD_ACC_ANSWERED': pct(ai1['acc_answered']),
              'HB_AI_UPD_HVP': pct(ai1['acc_healthy_vs_problem_answered']), 'HB_AI_UPD_CORRECT_OF_ALL': pct(ai1['correct_of_all']),
              'HB_RUST_NAMED_HUMAN': _rng(_rn), 'HB_CERCOSPORA_ANSWERS': _rng(_ce), 'HB_RUST_NAMED_AI': str(_cnt(ai1)),
              'HB_AI_HEALTHY_CALLED_PROBLEM': _hcp(ai1)})
    if _ag:
        N.update({'HB_AGREE_SAME': pct(_ag[0]['same_answer']), 'HB_AGREE_HVP': pct(_ag[0]['same_healthy_vs_problem_both_answered'])})
    NS.update({'SHIP_HB_ANSWERED': pct(aiS['share_answered']), 'SHIP_HB_NOT_SURE': pct(1 - aiS['share_answered']),
               'SHIP_HB_N_ANSWERED': str(aiS['n_answered']),
               'SHIP_HB_ACC_ANSWERED': pct(aiS['acc_answered']), 'SHIP_HB_HVP': pct(aiS['acc_healthy_vs_problem_answered']),
               'SHIP_HB_CORRECT_OF_ALL': pct(aiS['correct_of_all']), 'SHIP_HB_RUST_NAMED': str(_cnt(aiS)),
               'SHIP_HB_HEALTHY_CALLED_PROBLEM': _hcp(aiS),
               'SHIP_HB_N_RUST': str(sum(v['n'] for k, v in aiS['by_rust_level'].items() if k != '0')),
               'SHIP_HB_N_HEALTHY': str(aiS['by_rust_level']['0']['n']),
               'LABONLY_HB_COPY_IN_UPDATE': str(ai1.get('photos_with_identical_copy_in_training', 0))})
N.update(NS)
json.dump(N, open(os.path.join(RES, 'numbers.json'), 'w'), indent=1)

# ---------------------------------------------------------------- NUMBERS_KEYS.md (meaning of the new keys)
MEANING = {
    'SHIP_VERSION': 'version string of the shipped head (model/head.json)',
    'SHIP_N_TRAIN': 'photos the shipped head is trained on (lab + field)',
    'SHIP_N_TRAIN_LAB': 'lab photos in the shipped training set (same as N_TRAIN)',
    'SHIP_N_TRAIN_FIELD': 'RoCoLe field photos in the shipped training set',
    'SHIP_N_TRAIN_FIELD_HEALTHY': 'of which healthy', 'SHIP_N_TRAIN_FIELD_RUST': 'of which rust',
    'SHIP_N_COPIES_REMOVED': 'field photos left out of training because they are identical copies of a held-out photo (human-baseline, demo or mite)',
    'SHIP_REF_N': 'stored photos in the shipped familiarity reference (model/reference.bin)',
    'SHIP_REF_N_LAB': 'of which lab photos', 'SHIP_REF_N_FIELD': 'of which field photos (healthy + rust)',
    'SHIP_REF_KB': 'size of model/reference.bin (KB)', 'SHIP_HEAD_KB': 'size of model/head.json (KB)',
    'SHIP_ONNX_AGREE': 'ONNX backbone + shipped head vs Python: same class on this many field photos',
    'SHIP_C': 'logistic-regression C of the shipped head (chosen on calibration NLL)',
    'SHIP_TEMPERATURE': 'shipped temperature', 'SHIP_THRESHOLD': 'shipped confidence threshold',
    'SHIP_CUTOFF': 'shipped familiarity cutoff (distance)',
    'SHIP_CV_FOLDS': 'number of cross-validation folds over the training field photos',
    'SHIP_CV_COVERAGE': 'field photos the shipped model answers (not "not sure"), cross-validated mean',
    'SHIP_CV_NOT_SURE': 'field photos it says "not sure" to, cross-validated mean',
    'SHIP_CV_ACC_ANSWERED': 'answers that are correct (of answered field photos), cross-validated mean',
    'SHIP_CV_ACC': 'correct if forced to answer every field photo, cross-validated mean',
    'SHIP_CV_RUST_NAMED': 'rust leaves answered "rust", out of all rust leaves, cross-validated mean',
    'SHIP_CV_HEALTHY_FLAGGED': 'healthy leaves answered as a problem, out of all healthy leaves, cross-validated mean',
    'SHIP_CV_ECE': 'expected calibration error on field photos (0 = confidence matches accuracy), cross-validated mean',
    'SHIP_CV_HVP_ANSWERED': 'healthy-vs-problem correct, of answered field photos',
    'SHIP_CV_ACC_NOT_SURE_IF_FORCED': 'accuracy the model would have had on the photos it set aside as "not sure", if forced',
    'SHIP_CV_NOT_SURE_LOW_CONF': 'field photos set aside because confidence is below the threshold',
    'SHIP_CV_NOT_SURE_UNFAMILIAR': 'field photos set aside because they look unlike the stored photos',
    'SHIP_CV_SENS_ANSWERED': 'answered rust photos called rust (input to the village simulation)',
    'SHIP_CV_FPR_ANSWERED': 'answered healthy photos called rust (input to the village simulation)',
    'SHIP_LAB_ACC': 'shipped model on held-out lab-style photos (BRACOL calibration half), forced',
    'SHIP_LAB_COVERAGE': 'shipped model: lab-style photos answered', 'SHIP_LAB_ACC_ANSWERED': 'shipped model: lab-style answers correct',
    'SHIP_DEMO_N': 'demo sample photos in the app', 'SHIP_DEMO_ANSWERED_CORRECT': 'demo samples answered correctly by the shipped model',
    'SHIP_DEMO_NOT_SURE': 'demo samples answered "not sure"', 'SHIP_DEMO_MITE_CALLED': 'what the shipped model answers on the mite demo sample',
    'SHIP_MITE_NOT_SURE': 'shipped model: mite photos answered "not sure" (never trained on mite)',
    'SHIP_MITE_NOT_SURE_CV': 'same, mean over the 5 cross-validation models',
    'SHIP_MITE_CALLED_RUST': 'shipped model: mite photos answered "rust"', 'SHIP_MITE_CALLED_HEALTHY': 'shipped model: mite photos answered "healthy"',
    'SHIP_MITE_AUROC_FAMILIARITY': 'how well the familiarity distance separates mite photos from known field photos (0.5 = chance)',
    'SHIP_MITE_AUROC_CONFIDENCE': 'same for model confidence',
    'SHIP_VILLAGE_FA_RAW': 'village simulation at the shipped operating point: false alarms per round, raw shares',
    'SHIP_VILLAGE_FA_ADJ': 'same, small-sample adjusted', 'SHIP_VILLAGE_MISS_RAW': 'missed outbreaks per round, raw shares',
    'SHIP_VILLAGE_MISS_ADJ': 'missed outbreaks per round, adjusted', 'SHIP_VILLAGE_TOP5_RAW': 'real outbreaks among the top-5 villages, raw',
    'SHIP_VILLAGE_TOP5_ADJ': 'real outbreaks among the top-5 villages, adjusted', 'SHIP_VILLAGE_HOT': 'mean real outbreaks per round (of 40 villages)',
    'SHIP_VILLAGE_COVERAGE': 'operating point used: share answered', 'SHIP_VILLAGE_SENS': 'operating point: answered rust called rust',
    'SHIP_VILLAGE_FPR': 'operating point: answered healthy called rust',
    'SHIP_HB_ANSWERED': 'shipped model on the 60 picture-card photos: share answered', 'SHIP_HB_NOT_SURE': 'same: share "not sure"',
    'SHIP_HB_N_ANSWERED': 'same: photos answered (count)', 'SHIP_HB_ACC_ANSWERED': 'same: answers correct',
    'SHIP_HB_HVP': 'same: healthy-vs-problem correct of answered', 'SHIP_HB_CORRECT_OF_ALL': 'same: correct out of all 60',
    'SHIP_HB_RUST_NAMED': 'same: rust photos answered "rust" (count)', 'SHIP_HB_HEALTHY_CALLED_PROBLEM': 'same: healthy photos called a problem (count)',
    'SHIP_HB_N_RUST': 'rust photos among the 60', 'SHIP_HB_N_HEALTHY': 'healthy photos among the 60',
    'RO_DUP_PAIRS': 'pairs of identical or near-identical images in RoCoLe (embedding cosine > 0.98; healthy, rust and mite photos)',
    'RO_DUP_PAIRS_DIFFERENT_LABELS': 'of which the two copies carry different labels',
    'LABONLY_REF_N': 'stored photos in the lab-only reference (reference_labonly.bin)',
    'LABONLY_MITE_NOT_SURE_AFTER_50': 'lab-only model after the 50-label demo update: mite photos answered "not sure"',
    'LABONLY_MITE_RUST_AFTER_50': 'same: mite photos answered "rust"', 'LABONLY_MITE_HEALTHY_AFTER_50': 'same: mite photos answered "healthy"',
    'LABONLY_HB_COPY_IN_UPDATE': 'picture-card photos with an identical copy among the 50 demo-update photos',
}
missing = sorted(k for k in NS if k not in MEANING and not k.endswith('_SD'))
assert not missing, f'NUMBERS_KEYS.md: no meaning for {missing}'
kmd = ['# numbers.json keys (generated by ml/write_results_md.py — do not edit by hand)', '',
       'Keys that existed before the lab+field model keep their earlier meaning: they describe the **lab-only model**, '
       'now used as the new-region simulation (FIELD_ACC_NO_ABSTAIN, FIELD_MEAN_CONFIDENCE, FIELD_NOT_SURE, MITE_NOT_SURE, '
       'AUROC_*, COV_*, ACC_ANS_*, LAB_*, VILLAGE_* (lab-only + 50 labels operating point), DINO_*, HB_AI_*, '
       'HB_RUST_NAMED_AI, REF_KB (1,000-row lab-only reference), N_TRAIN (lab photos)). '
       'MODEL_MB, HEAD_KB and LATENCY_MS_LAPTOP describe files both models share or that have the same size. '
       'HB_HUMAN_* and HB_AGREE_* describe the two people and are unchanged.', '',
       'New keys (shipped lab+field model = `SHIP_*`; `*_SD` = standard deviation across the 5 folds, in percentage points):', '',
       '| Key | Value now | Meaning |', '|---|---|---|']
for k in NS:
    if k.endswith('_SD'):
        continue
    sd = f" (sd {NS[k + '_SD']})" if k + '_SD' in NS else ''
    kmd.append(f"| `{k}` | {NS[k]}{sd} | {MEANING[k]} |")
open(os.path.join(RES, 'NUMBERS_KEYS.md'), 'w').write('\n'.join(kmd) + '\n')

# ---------------------------------------------------------------- RESULTS.md
x = N
md = f"""# Results (generated by ml/write_results_md.py from results/*.json — do not edit by hand)

## 1. What the phone runs
- Frozen MobileNetV3-Large image backbone (ImageNet weights, Apache-2.0): **{x['MODEL_MB']} MB** ONNX, ~{x['LATENCY_MS_LAPTOP']} ms per photo on a laptop CPU (phone speed not yet measured).
- Shipped head **{x['SHIP_VERSION']}** (trained on lab + field photos): **{x['SHIP_HEAD_KB']} KB** JSON. Familiarity reference: **{x['SHIP_REF_N']}** stored training photos as int8 vectors ({x['SHIP_REF_N_LAB']} lab, {x['SHIP_REF_N_FIELD']} field), **{x['SHIP_REF_KB']} KB**.
- The ONNX path reproduces the Python pipeline: {O['onnx_vs_python_same_class']} same class on field photos, max embedding difference {O['onnx_vs_python_max_abs_diff']}; same decision on {O.get('samples_same_decision_as_python', '?')} demo samples.
- One backbone serves both heads: the embedding standardisation baked into the ONNX file is computed on the lab training photos and kept for the shipped head, so the lab-only files (new-region simulation, starter kit) run on the same backbone.

## 2. Data
- **Lab photos** ({x['N_TRAIN']} for training): 1,500 sampled per class from JMuBEN/JMuBEN2 (Kenya, Kirinyaga, arabica; many are rotated/flipped copies) plus half of the BRACOL photos we could recover (Brazil, arabica; 1,342 usable of 1,747). The other half of BRACOL ({x['N_CALIB']} photos) is the lab calibration set.
- **Field photos**: RoCoLe (Ecuador, robusta, leaves on the plant, smartphone), {x['N_FIELD']} healthy/rust photos labelled by the dataset authors, plus {x['N_MITE']} red-spider-mite photos.
  - The shipped model trains on **{x['SHIP_N_TRAIN_FIELD']}** of them ({x['SHIP_N_TRAIN_FIELD_HEALTHY']} healthy, {x['SHIP_N_TRAIN_FIELD_RUST']} rust).
  - Never trained on: the 60 picture-card photos, the 7 demo samples, all mite photos, and {x['SHIP_N_COPIES_REMOVED']} photos that are identical or near-identical copies of one of those. RoCoLe holds {x['RO_DUP_PAIRS']} pairs of identical or near-identical images ({x['RO_DUP_PAIRS_DIFFERENT_LABELS']} pairs carry two different labels, mostly mite vs rust); copies are always kept on the same side of every split.
- **Lab-only model**: the same lab photos, no field photos. Used to simulate a model meeting a new region's photo style (sections 3.5–3.7) and as the starter-kit base.

## 3. Findings

### 3.1 The shipped model on field photos (5-fold cross-validation)
Trained on lab photos plus field photos, the shipped model answers **{x['SHIP_CV_COVERAGE']}** of field photos it has not seen and is right on **{x['SHIP_CV_ACC_ANSWERED']}** of those answers. It names rust on **{x['SHIP_CV_RUST_NAMED']}** of rust leaves and calls **{x['SHIP_CV_HEALTHY_FLAGGED']}** of healthy leaves a problem. Its confidence matches its accuracy (calibration error {x['SHIP_CV_ECE']}; 0 = perfect). Lab-style photos still work: {x['SHIP_LAB_ACC']} right on held-out BRACOL photos ({x['LAB_ACC']} for the lab-only model).

| Field photos (healthy + rust), never trained on | Mean of {x['SHIP_CV_FOLDS']} folds | Spread (sd, points) |
|---|---|---|
| Answered (not "not sure") | {x['SHIP_CV_COVERAGE']} | {x['SHIP_CV_COVERAGE_SD']} |
| Answers that are correct | {x['SHIP_CV_ACC_ANSWERED']} | {x['SHIP_CV_ACC_ANSWERED_SD']} |
| Rust leaves named rust (of all rust leaves) | {x['SHIP_CV_RUST_NAMED']} | {x['SHIP_CV_RUST_NAMED_SD']} |
| Healthy leaves called a problem (of all healthy leaves) | {x['SHIP_CV_HEALTHY_FLAGGED']} | {x['SHIP_CV_HEALTHY_FLAGGED_SD']} |
| Correct if forced to answer every photo | {x['SHIP_CV_ACC']} | {x['SHIP_CV_ACC_SD']} |
| Calibration error (ECE) | {x['SHIP_CV_ECE']} | {x['SHIP_CV_ECE_SD']} |

Second check on photos kept out from the start (the 60 picture-card photos, section 3.3): it answers {x['SHIP_HB_N_ANSWERED']} of 60, {x['SHIP_HB_ACC_ANSWERED']} of them correctly. On the app's demo samples it answers {x['SHIP_DEMO_ANSWERED_CORRECT']} of the {int(x['SHIP_DEMO_N']) - 1} healthy/rust photos correctly and says "not sure" to {x['SHIP_DEMO_NOT_SURE']}.

How it was measured: each fold's head was trained on all lab photos plus the other four folds; its familiarity reference held only those folds' photos; its temperature, confidence threshold and familiarity cutoff were chosen on the BRACOL calibration half plus the other folds' out-of-fold predictions, so nothing was tuned on the photos it was scored on. The shipped head uses all training photos, with those three values chosen the same way on all out-of-fold predictions (threshold {x['SHIP_THRESHOLD']}, cutoff {x['SHIP_CUTOFF']}, temperature {x['SHIP_TEMPERATURE']}).

### 3.2 The "not sure" check
- **It sets aside the photos it would get wrong.** On the {x['SHIP_CV_NOT_SURE']} of field photos the shipped model sends to the officer, it would have been right only {x['SHIP_CV_ACC_NOT_SURE_IF_FORCED']} of the time if forced to answer, against {x['SHIP_CV_ACC_ANSWERED']} on the photos it answers. Reasons: low confidence ({x['SHIP_CV_NOT_SURE_LOW_CONF']} of photos) and unfamiliar look ({x['SHIP_CV_NOT_SURE_UNFAMILIAR']}).
- **It protects the app when it meets a new photo style.** In the new-region simulation (section 3.5), a model trained only on lab photos is confidently wrong on field photos, and its confidence does not warn us (AUROC {x['AUROC_CONFIDENCE']}, worse than a coin flip). Comparing each photo with the stored training photos separates the new style almost perfectly (AUROC {x['AUROC_KNN']}): the app says "not sure" to {x['FIELD_NOT_SURE']} of those photos instead of guessing. The same check runs on top of the shipped model when it reaches Kenyan farms.
"""
if HB:
    nh = len(hum); ps = HB['photo_set']; rl = ps['rust_by_level']; chk = HB.get('model_on_resized_copies', {})
    p_ = lambda v: '—' if v is None else pct(v)
    sec_ = lambda v: '—' if v is None else f'{v:.1f}'
    group = {1: 'one team member', 2: 'two team members', 3: 'three team members'}.get(nh, f'{nh} team members')
    row_ = lambda who_, r, secs: (f"| {who_} | {p_(r['share_answered'])} | {p_(r['acc_answered'])} | "
                                  f"{p_(r['acc_healthy_vs_problem_answered'])} | {p_(r['correct_of_all'])} | {secs} |\n")
    levels = list(aiS['by_rust_level'].values())
    lvl_head = '| Who | ' + ' | '.join(f"{v['label'].capitalize()} ({v['n']})" for v in levels) + ' |\n|---|' + '---|' * len(levels) + '\n'
    lvl_row = lambda who_, r: f'| {who_} | ' + ' | '.join(pct(v['correct_of_all']) for v in r['by_rust_level'].values()) + ' |\n'
    same = {k: chk.get(k, {}).get('same_decision_as_original', '?') for k in HB['model']}
    md += f"""
### 3.3 People with a picture card vs the shipped AI (one-evening test)
{group.capitalize()}, with no coffee training, labelled the same {ps['n']} field photos using only a picture card (two pictures and one line per problem), on a phone or laptop. The shipped AI was scored on the same photos with the same rule as the app. It was never trained on these photos.

| Who | Photos answered (not "not sure") | Answers correct | Healthy vs problem correct (of answered) | Correct out of all {ps['n']} | Median seconds per photo |
|---|---|---|---|---|---|
"""
    md += ''.join(row_(f"{h['name']} (picture card)", h, sec_(h['median_seconds'])) for h in hum)
    md += row_('**AI as shipped** (lab + field photos)', aiS, '—')
    md += row_('Context: lab-only AI, no field labels (new-region simulation)', ai0, '—')
    md += row_('Context: lab-only AI after 50 officer-style field labels', ai1, '—')
    md += '\nRight answer by true class, out of all photos of that class ("not sure" counts as not right):\n\n' + lvl_head
    md += ''.join(lvl_row(h['name'], h) for h in hum) + lvl_row('AI as shipped', aiS) + lvl_row('Context: lab-only AI after 50 labels', ai1)
    md += f"""
What it means: with only the card, both people told sick leaves from healthy ones well ({x['HB_HUMAN_HVP']} of answers) but named rust on only {x['HB_RUST_NAMED_HUMAN']} of the {x['SHIP_HB_N_RUST']} rust photos; they often chose "brown eye spot" ({x['HB_CERCOSPORA_ANSWERS']} times each). The shipped AI named rust on **{x['SHIP_HB_RUST_NAMED']} of {x['SHIP_HB_N_RUST']}**, called {x['SHIP_HB_HEALTHY_CALLED_PROBLEM']} of {x['SHIP_HB_N_HEALTHY']} healthy leaves a problem, and sent {x['SHIP_HB_NOT_SURE']} of photos to the officer instead of guessing. The two people gave the same answer on {x.get('HB_AGREE_SAME')} of photos. A card is enough to notice that something is wrong; the AI adds a consistent rust label, which is what a village rust count needs.

How "right" is decided: every RoCoLe photo carries the dataset authors' label (healthy, or rust at level 1 to 4). "Named rust" means the answer "rust" on a photo the authors labelled rust; the five answer options were the same for people and AI (healthy, rust, leaf miner, brown eye spot, Phoma, plus "not sure").

What this test is and is not:
- The labellers are team members who are not farmers or plant experts, standing in for relay farmers; relay farmers trained by the cooperative may do better. Next step: run the same card test with relay farmers during the pilot.
- {ps['n']} photos from one dataset (RoCoLe: Ecuador, robusta, on-plant): {ps['healthy']} healthy and {sum(rl.values())} rust (levels 1 to 4: {', '.join(str(v) for v in rl.values())} photos).
- The shipped AI has seen field photos of healthy and rust leaves from this dataset (never these 60); the people saw only lab-style pictures on the card. Field photos of look-alike problems are the next training addition (section 4).
- People saw copies resized to 900 px; the AI used the originals. On the resized copies the shipped AI makes the same decision on {same.get('shipped_v2_lab_field')} of {ps['n']} photos.
- The lab-only rows are context from the new-region simulation; one of the 60 photos is an identical copy of a photo in its 50-label update.
"""
md += f"""
### 3.4 Village ranking (simulation at the shipped model's error rates)
Synthetic villages; the classifier's error rates are the shipped model's cross-validated rates (answers {x['SHIP_VILLAGE_COVERAGE']} of photos; calls {x['SHIP_VILLAGE_SENS']} of answered rust photos rust and {x['SHIP_VILLAGE_FPR']} of answered healthy photos rust). It ranks rust already seen; it does not predict outbreaks. Across 40 villages per round with about {x['SHIP_VILLAGE_HOT']} real outbreaks (rust share above 25%):

| Rule | False alarms per round | Missed outbreaks per round | Real outbreaks among the 5 villages visited first |
|---|---|---|---|
| Raw share of rust photos | {x['SHIP_VILLAGE_FA_RAW']} | {x['SHIP_VILLAGE_MISS_RAW']} | {x['SHIP_VILLAGE_TOP5_RAW']} |
| Small-sample adjusted (the app's rule: alert when P(share > 25%) > 0.5) | {x['SHIP_VILLAGE_FA_ADJ']} | {x['SHIP_VILLAGE_MISS_ADJ']} | {x['SHIP_VILLAGE_TOP5_ADJ']} |

The adjustment cuts false alarms ({x['SHIP_VILLAGE_FA_RAW']} → {x['SHIP_VILLAGE_FA_ADJ']}) and sends the officer to more real outbreaks first ({x['SHIP_VILLAGE_TOP5_RAW']} → {x['SHIP_VILLAGE_TOP5_ADJ']} of 5). It misses more villages that sit near the 25% line ({x['SHIP_VILLAGE_MISS_RAW']} → {x['SHIP_VILLAGE_MISS_ADJ']}); those villages still appear in the ranked list, just below the alert line, and the alert line can be re-set with pilot data. With the lab-only model after 50 labels (a less accurate operating point) the same comparison gives {x['VILLAGE_FA_RAW']} → {x['VILLAGE_FA_ADJ']} false alarms and {x['VILLAGE_MISS_RAW']} → {x['VILLAGE_MISS_ADJ']} misses.

### 3.5 The learning loop in a new region (simulation, lab-only base)
To test how the app adapts when it meets a photo style it has never seen (for example the first Kenyan farms), we start from the lab-only model and treat the field photos as the new region. When the officer labels photos, the head is refit on the phone (pulled toward the starting model) and the labelled photos join the familiarity reference:

| Officer labels | Photos answered | Answers correct | Answers correct, local labels only (no starting model) |
|---|---|---|---|
""" + '\n'.join(f"| {k} | {pct(pa['coverage'][i])} | {'—' if pa['acc_answered'][i] is None else pct(pa['acc_answered'][i])} | {'—' if lo['acc_answered'][i] is None else pct(lo['acc_answered'][i])} |" for i, k in enumerate(ks)) + f"""

After 50 labels the tool answers {x['COV_50']} of the new region's photos, {x['ACC_ANS_50']} correctly. A starting model matters most when labels are few ({x['ACC_ANS_10']} vs {x['ACC_ANS_10_LOCAL_ONLY']} correct at 10 labels). An update to share with other phones is ~{x['UPDATE_KB_HEAD']} KB for the head plus {x['UPDATE_BYTES_PER_PHOTO']} bytes per labelled photo.

### 3.6 Why the shipped model trains on field photos
The lab-only model is right {x['LAB_ACC']} of the time on held-out lab photos but only **{x['FIELD_ACC_NO_ABSTAIN']}** on field photos if forced to answer, while reporting **{x['FIELD_MEAN_CONFIDENCE']}** average confidence (it calls almost every field leaf Phoma). Adding field photos to training lifts forced field accuracy to {x['SHIP_CV_ACC']} (cross-validated), and lab accuracy stays at {x['SHIP_LAB_ACC']}. The lesson for a new region: train on photos taken the way relay farmers will take them, and keep the familiarity check for the style the model has not seen yet.
"""
if alt:
    md += f"""
### 3.7 Size vs accuracy
In the new-region setting (lab-only training, no field labels), a 5x larger backbone (DINOv2-small, 21.6M parameters, ~87 MB) is right {x['DINO_FIELD_ACC']} of the time on field photos (vs {x['FIELD_ACC_NO_ABSTAIN']} for MobileNetV3); after 50 labels it answers {x['DINO_COV_50']} of photos with {x['DINO_ACC_ANS_50']} correct. Training the small backbone on field photos does better than that ({x['SHIP_CV_ACC']} forced accuracy, cross-validated), so we ship the {x['MODEL_MB']} MB backbone that fits the side-loading constraint. A larger backbone remains an option where phones allow it.
"""
md += f"""
### 3.8 Limit found: pests the model was never taught
The shipped model has five classes. On {x['N_MITE']} red-spider-mite photos (never trained on), it says "not sure" to {x['SHIP_MITE_NOT_SURE']}; it calls {x['SHIP_MITE_CALLED_RUST']} of them rust (the officer still hears about a problem) and {x['SHIP_MITE_CALLED_HEALTHY']} healthy. These photos come from the same dataset and region as the field training photos, so they look familiar (the familiarity distance separates them from known field leaves with AUROC {x['SHIP_MITE_AUROC_FAMILIARITY']}; confidence {x['SHIP_MITE_AUROC_CONFIDENCE']}). The demo's mite sample is answered "{x['SHIP_DEMO_MITE_CALLED']}". The same happens to the lab-only model once 50 field labels make field photos familiar ({x['LABONLY_MITE_NOT_SURE_AFTER_50']} "not sure").
- In the app now: the officer review offers "different problem / not in list", and those photos stay in the not-sure lane for similar photos; 1 in 10 answered photos is also queued for the officer, so errors are seen; the plot card never says a plot is disease-free.
- Plan: collect officer-labelled field photos of look-alike problems (pests, brown eye spot, nutrient deficiency) through the "different problem" label during a pilot, add an "other problem" class, and accept it only if it raises the "not sure" or "problem" rate on these mite photos, which stay out of training as the test.

## 4. Simplifications and what we do about each
- **One field dataset.** Every field photo (training and test) is Ecuadorian robusta from RoCoLe; none comes from Kenyan farms. Rust looks similar across coffee species, but this is a proxy. Plan: in a pilot, the officer's labels from the not-sure lane feed the learning loop (section 3.5 simulates this), and the first 200 labelled Kenyan photos are kept aside as a Kenyan test set.
- **No plant IDs in RoCoLe.** Leaves of one plant can sit in both a training and a test fold, so the cross-validated numbers may be optimistic. We keep identical and near-identical images on one side of every split and report a second check on the 60 picture-card photos. Plan: pilot photos record plot and plant, so tests can hold out whole farms.
- **Field training photos show only healthy and rust leaves.** The field-style look of other problems is not yet learned (section 3.8). Plan: as in 3.8.
- **Labels come from the dataset authors**, standing in for an extension officer, in both the cross-validation and the learning loop. Plan: measure officer–author agreement on the first pilot batch.
- **Learning-step strength** (how hard the on-phone update pulls toward the shipped head) is the value chosen in the new-region simulation; no new-region photos exist yet to tune it for the shipped head. Plan: re-tune it on the first pilot labels.
- **The village ranking is a simulation** with synthetic villages; only the classifier's error rates are measured. Plan: replay the rule on pilot visit data.
- **The picture-card test** used two team members for one evening. Plan: repeat with relay farmers trained by the cooperative.
- **Lab validation**: JMuBEN contains augmented copies of the same leaf, so its in-domain validation score (100%) is optimistic and not used as a headline; lab accuracy is reported on the BRACOL half instead.
"""
open(os.path.join(RES, 'RESULTS.md'), 'w').write(md)
print(md[:800]); print('numbers.json keys:', len(N), '| new SHIP_/LABONLY_/RO_ keys:', len(NS))
