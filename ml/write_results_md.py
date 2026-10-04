"""Write results/RESULTS.md, results/numbers.json and results/NUMBERS_KEYS.md from the results files
(numbers are never typed by hand). Run: ../.venv/bin/python ml/write_results_md.py
Inputs: metrics.json, onnx_check.json, limits.json, human_baseline.json (ml/train_eval.py, check_onnx.py,
score_baseline.py), uganda_external.json (ml/eval_uganda.py; refused if it was made with other head files) and
familiarity_rule.json (ml/eval_familiarity_rule.py; refused if head.json's ood.local_nearest_cutoff differs from its c1).
UG_* keys describe the external test on Ugandan farm photos; FAM_* keys the nearest-officer-photo familiarity rule (chosen
on 40% of the Ugandan copy clusters, scored on the other 60%, the Ecuador simulation, mite photos and the 60 photos). Every limit line in RESULTS.md ends with nxt():
what, who, metric, when.

numbers.json keeps every key the docs already use, with its earlier meaning: those keys describe the LAB-ONLY model
(now the new-region simulation). Keys for the SHIPPED model start with SHIP_: they describe head v3 (lab + field photos
+ an "other" class) since it replaced head v2 in the app. SHIP_OTHER_* keys describe the "other" answer; SHIP_V2_* keys
keep head v2's values for reference. NUMBERS_KEYS.md lists every key, and every key whose value moved from v2 to v3.
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
    **({f'COV_{k_}_PREV': pct(pa['coverage_previous_rule'][ks.index(k_)]) for k_ in (10, 50, 200)} if 'coverage_previous_rule' in pa else {}),
    **({f'ACC_ANS_{k_}_PREV': pct(pa['acc_answered_previous_rule'][ks.index(k_)]) for k_ in (10, 50, 200)} if 'acc_answered_previous_rule' in pa else {}),
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

# ---------------------------------------------------------------- shipped model (SHIP_* = head v3 now)
SH2 = M['shipped_v2']; VS2 = SH2['village_sim']
HBP = os.path.join(RES, 'human_baseline.json')
HB = json.load(open(HBP)) if os.path.exists(HBP) else None
if HB and not HB.get('labellers'):
    HB = None
_cnt = lambda x: sum(round(v['correct_of_all'] * v['n']) for k, v in x['by_rust_level'].items() if k != '0')
_hcp = lambda x: str(round(x['by_rust_level']['0']['called_a_problem_of_all'] * x['by_rust_level']['0']['n']))


def ship_keys(S, VS_, head_version, head_kb, ref_kb, onnx_agree, aiS_):
    """SHIP_* keys for one shipped head (v3 now; the same function gives head v2's values for comparison)."""
    CV_ = S['field_cv']['summary']; HO_ = S['held_out']; NT_ = S['n_train']; DUP_ = S['rocole_identical_copies']
    sm7 = HO_['demo_samples_7']; mi = HO_['mite']; ls = S['lab_style']['bracol_calibration_half']
    k = {
        'SHIP_VERSION': head_version,
        'SHIP_N_TRAIN': str(NT_['total']), 'SHIP_N_TRAIN_LAB': str(NT_['lab']), 'SHIP_N_TRAIN_FIELD': str(NT_['field']),
        'SHIP_N_TRAIN_FIELD_HEALTHY': str(NT_['field_healthy']), 'SHIP_N_TRAIN_FIELD_RUST': str(NT_['field_rust']),
        'SHIP_N_COPIES_REMOVED': str(DUP_['training_candidates_removed_as_copies_of_held_out']),
        'SHIP_REF_N': str(S['reference_n']), 'SHIP_REF_N_LAB': str(S['reference_rows']['lab']),
        'SHIP_REF_N_FIELD': str(S['reference_rows']['field']), 'SHIP_REF_KB': ref_kb,
        'SHIP_HEAD_KB': head_kb, 'SHIP_ONNX_AGREE': onnx_agree,
        'SHIP_C': f"{S['C']:g}", 'SHIP_TEMPERATURE': f"{S['temperature']:.2f}", 'SHIP_THRESHOLD': f"{S['threshold']:.2f}",
        'SHIP_CUTOFF': f"{S['familiarity_cutoff']:.3f}",
        'SHIP_CV_FOLDS': str(S['field_cv']['folds']),
        'SHIP_CV_COVERAGE': pct(CV_['coverage']), 'SHIP_CV_COVERAGE_SD': pts(CV_['coverage_sd']),
        'SHIP_CV_NOT_SURE': pct(CV_['not_sure']),
        'SHIP_CV_ACC_ANSWERED': pct(CV_['acc_answered']), 'SHIP_CV_ACC_ANSWERED_SD': pts(CV_['acc_answered_sd']),
        'SHIP_CV_ACC': pct(CV_['acc_all']), 'SHIP_CV_ACC_SD': pts(CV_['acc_all_sd']),
        'SHIP_CV_RUST_NAMED': pct(CV_['rust_named']), 'SHIP_CV_RUST_NAMED_SD': pts(CV_['rust_named_sd']),
        'SHIP_CV_HEALTHY_FLAGGED': pct(CV_['healthy_flagged']), 'SHIP_CV_HEALTHY_FLAGGED_SD': pts(CV_['healthy_flagged_sd']),
        'SHIP_CV_ECE': f"{CV_['ece']:.2f}", 'SHIP_CV_ECE_SD': f"{CV_['ece_sd']:.2f}",
        'SHIP_CV_HVP_ANSWERED': pct(CV_['hvp_answered']),
        'SHIP_CV_ACC_NOT_SURE_IF_FORCED': pct(CV_['acc_not_sure_if_forced']),
        'SHIP_CV_NOT_SURE_LOW_CONF': pct1(CV_['not_sure_low_confidence']), 'SHIP_CV_NOT_SURE_UNFAMILIAR': pct1(CV_['not_sure_unfamiliar']),
        'SHIP_CV_SENS_ANSWERED': pct(CV_['sens_answered_rust']), 'SHIP_CV_FPR_ANSWERED': pct(CV_['fpr_answered_healthy_as_rust']),
        'SHIP_LAB_ACC': pct(ls['acc_all']), 'SHIP_LAB_COVERAGE': pct(ls['coverage']), 'SHIP_LAB_ACC_ANSWERED': pct(ls['acc_answered']),
        'SHIP_DEMO_N': str(len(sm7)),
        'SHIP_DEMO_ANSWERED_CORRECT': str(sum(p['answered'] and p['pred'] == p['truth'] for p in sm7)),
        'SHIP_DEMO_NOT_SURE': str(sum(not p['answered'] for p in sm7)),
        'SHIP_DEMO_MITE_CALLED': ', '.join(('not sure' if not p['answered'] else p['pred']) for p in sm7 if p['truth'] == 'mite'),
        'SHIP_MITE_NOT_SURE': pct(mi['not_sure']), 'SHIP_MITE_NOT_SURE_CV': pct(mi['cv_mean_not_sure']),
        'SHIP_MITE_CALLED_RUST': str(mi['answered_as'].get('rust', 0)), 'SHIP_MITE_CALLED_HEALTHY': str(mi['answered_as'].get('healthy', 0)),
        'SHIP_MITE_AUROC_FAMILIARITY': f"{mi['auroc_mite_vs_field_cv']['familiarity_distance']:.2f}",
        'SHIP_MITE_AUROC_CONFIDENCE': f"{mi['auroc_mite_vs_field_cv']['confidence']:.2f}",
        'SHIP_VILLAGE_FA_RAW': f"{VS_['raw']['false_alarms']:.1f}", 'SHIP_VILLAGE_FA_ADJ': f"{VS_['shrunk']['false_alarms']:.1f}",
        'SHIP_VILLAGE_MISS_RAW': f"{VS_['raw']['missed']:.1f}", 'SHIP_VILLAGE_MISS_ADJ': f"{VS_['shrunk']['missed']:.1f}",
        'SHIP_VILLAGE_TOP5_RAW': f"{VS_['raw']['top5_hits']:.1f}", 'SHIP_VILLAGE_TOP5_ADJ': f"{VS_['shrunk']['top5_hits']:.1f}",
        'SHIP_VILLAGE_HOT': f"{VS_['mean_true_hot_villages']:.1f}",
        'SHIP_VILLAGE_COVERAGE': pct(VS_['inputs']['coverage']), 'SHIP_VILLAGE_SENS': pct(VS_['inputs']['sensitivity']),
        'SHIP_VILLAGE_FPR': pct(VS_['inputs']['false_positive_rate']),
        'RO_DUP_PAIRS': str(DUP_['pairs']), 'RO_DUP_PAIRS_DIFFERENT_LABELS': str(DUP_['pairs_with_different_labels']),
        'LABONLY_REF_N': str(LO['reference_n']),
    }
    if aiS_:
        k.update({'SHIP_HB_ANSWERED': pct(aiS_['share_answered']), 'SHIP_HB_NOT_SURE': pct(1 - aiS_['share_answered']),
                  'SHIP_HB_N_ANSWERED': str(aiS_['n_answered']),
                  'SHIP_HB_ACC_ANSWERED': pct(aiS_['acc_answered']), 'SHIP_HB_HVP': pct(aiS_['acc_healthy_vs_problem_answered']),
                  'SHIP_HB_CORRECT_OF_ALL': pct(aiS_['correct_of_all']), 'SHIP_HB_RUST_NAMED': str(_cnt(aiS_)),
                  'SHIP_HB_HEALTHY_CALLED_PROBLEM': _hcp(aiS_),
                  'SHIP_HB_N_RUST': str(sum(v['n'] for kk, v in aiS_['by_rust_level'].items() if kk != '0')),
                  'SHIP_HB_N_HEALTHY': str(aiS_['by_rust_level']['0']['n'])})
    return k


V2DIR = os.path.join(os.path.dirname(REPO), 'data_work', 'shipped_v2')   # head v2 files (written by ml/train_eval.py)
hv2 = json.load(open(os.path.join(V2DIR, 'head.json')))
NS = ship_keys(SH, VS, json.load(open(os.path.join(REPO, 'model', 'head.json')))['version'], f"{O['head_kb']:.0f}",
               f"{O['reference_kb']:.0f}", O['onnx_vs_python_same_class'], HB['model']['shipped'] if HB else None)
_kb1 = lambda p_: f"{round(os.path.getsize(p_) / 1e3, 1):.0f}"   # same rounding as ml/check_onnx.py
NS2 = ship_keys(SH2, VS2, hv2['version'], _kb1(os.path.join(V2DIR, 'head.json')), _kb1(os.path.join(V2DIR, 'reference.bin')),
                '25/25 (earlier check)',
                HB['model']['shipped_v2_lab_field'] if HB else None)
# head v3 'other' answer (new keys)
MS = SH['field_cv']['mite_summary']; MS2 = SH2['field_cv']['mite_summary']
AW = SH['field_cv']['all_field_with_mite_summary']; AW2 = SH2['field_cv']['all_field_with_mite_summary']
PV = SH['paired_vs_v2']; MSP = SH['mite_split']; TR = SH['other_tradeoff']['rows']; NT = SH['n_train']
tr_ = lambda bud, tk: next(r for r in TR if r['other_budget'] == bud and r['threshold_rule_on_known_classes_only'] == tk)
t_raw, t_half = tr_(None, False), tr_(0.005, True)
dpts = lambda x: f"{100 * x:+.1f}".replace('-', '−')
NS.update({
    'SHIP_N_CLASSES': str(len(SH['classes'])),
    'SHIP_OTHER_BUDGET': pct(SH['other_budget']),
    'SHIP_OTHER_N_TRAIN': str(NT['field_other_mite']), 'SHIP_OTHER_N_MITE': str(MSP['mite_total']),
    'SHIP_OTHER_N_NEVER_TRAINED': str(MSP['mite_never_trained_v3']),
    'SHIP_OTHER_N_CONFLICT_GROUPS': str(SH['rocole_identical_copies']['groups_with_different_labels']),
    'SHIP_OTHER_N_CONFLICT_MITE': str(MSP['mite_in_groups_with_different_labels']),
    'SHIP_OTHER_MITE_TO_OFFICER_CV': pct(MS['not_sure']), 'SHIP_OTHER_MITE_TO_OFFICER_CV_SD': pts(MS['not_sure_sd']),
    'SHIP_OTHER_MITE_ROUTED_OTHER_CV': pct(MS['routed_other']), 'SHIP_OTHER_MITE_ROUTED_OTHER_CV_SD': pts(MS['routed_other_sd']),
    'SHIP_OTHER_MITE_CALLED_RUST_CV': pct(MS['called_rust']), 'SHIP_OTHER_MITE_CALLED_RUST_CV_SD': pts(MS['called_rust_sd']),
    'SHIP_OTHER_MITE_CALLED_HEALTHY_CV': pct(MS['called_healthy']), 'SHIP_OTHER_MITE_CALLED_HEALTHY_CV_SD': pts(MS['called_healthy_sd']),
    'SHIP_OTHER_MITE_ROUTED_OTHER': pct(SH['held_out']['mite']['routed_other']),
    'SHIP_OTHER_ROUTED_OTHER': pct1(CV['routed_other']), 'SHIP_OTHER_ROUTED_OTHER_SD': pts(CV['routed_other_sd']),
    'SHIP_OTHER_RUST_ROUTED_OTHER': pct1(CV['rust_routed_other']), 'SHIP_OTHER_RUST_ROUTED_OTHER_SD': pts(CV['rust_routed_other_sd']),
    'SHIP_OTHER_HEALTHY_ROUTED_OTHER': pct1(CV['healthy_routed_other']), 'SHIP_OTHER_HEALTHY_ROUTED_OTHER_SD': pts(CV['healthy_routed_other_sd']),
    'SHIP_OTHER_AUROC_P_OTHER': f"{SH['held_out']['mite']['auroc_mite_vs_field_cv']['p_other']:.2f}",
    'SHIP_OTHER_RUST_ANSWERS_MITE': pct(AW['rust_answers_that_are_mite']), 'SHIP_OTHER_RUST_ANSWERS_MITE_V2': pct(AW2['rust_answers_that_are_mite']),
    'SHIP_OTHER_ALL_COVERAGE': pct(AW['coverage']), 'SHIP_OTHER_ALL_COVERAGE_V2': pct(AW2['coverage']),
    'SHIP_OTHER_ALL_ACC_ANSWERED': pct(AW['acc_answered']), 'SHIP_OTHER_ALL_ACC_ANSWERED_V2': pct(AW2['acc_answered']),
    'SHIP_OTHER_DELTA_COVERAGE': dpts(PV['coverage']['mean_difference']),
    'SHIP_OTHER_DELTA_ACC_ANSWERED': dpts(PV['acc_answered']['mean_difference']),
    'SHIP_OTHER_DELTA_RUST_NAMED': dpts(PV['rust_named']['mean_difference']),
    'SHIP_OTHER_DELTA_HEALTHY_FLAGGED': dpts(PV['healthy_flagged']['mean_difference']),
    'SHIP_OTHER_RUST_NAMED_FOLDS_LOWER': str(PV['rust_named']['folds_lower']),
    'SHIP_OTHER_NOADJ_RUST_NAMED': pct(t_raw['rust_named']), 'SHIP_OTHER_NOADJ_COVERAGE': pct(t_raw['coverage']),
    'SHIP_OTHER_NOADJ_MITE_TO_OFFICER': pct(t_raw['mite_sent_to_officer_167']),
    'SHIP_OTHER_HALF_RUST_NAMED': pct(t_half['rust_named']), 'SHIP_OTHER_HALF_MITE_CALLED_RUST': str(t_half['mite_called_rust_167']),
    'SHIP_OTHER_HALF_MITE_TO_OFFICER': pct(t_half['mite_sent_to_officer_167']),
    'SHIP_CV_NOT_SURE_OTHER': pct1(CV['routed_other']),
})
# head v2 values kept under their own names (reference)
V2_COPY = ['SHIP_VERSION', 'SHIP_CV_COVERAGE', 'SHIP_CV_ACC_ANSWERED', 'SHIP_CV_RUST_NAMED', 'SHIP_CV_HEALTHY_FLAGGED',
           'SHIP_MITE_NOT_SURE', 'SHIP_MITE_NOT_SURE_CV', 'SHIP_MITE_CALLED_RUST', 'SHIP_MITE_CALLED_HEALTHY',
           'SHIP_HB_RUST_NAMED', 'SHIP_HB_N_ANSWERED', 'SHIP_HB_ACC_ANSWERED', 'SHIP_HB_HEALTHY_CALLED_PROBLEM']
for k_ in V2_COPY:
    if k_ in NS2:
        NS['SHIP_V2_' + k_[5:]] = NS2[k_]
        if k_ + '_SD' in NS2:
            NS['SHIP_V2_' + k_[5:] + '_SD'] = NS2[k_ + '_SD']
NS['SHIP_V2_MITE_TO_OFFICER_CV'] = pct(MS2['not_sure']); NS['SHIP_V2_MITE_TO_OFFICER_CV_SD'] = pts(MS2['not_sure_sd'])
NS['SHIP_V2_MITE_CALLED_RUST_CV'] = pct(MS2['called_rust']); NS['SHIP_V2_MITE_CALLED_RUST_CV_SD'] = pts(MS2['called_rust_sd'])
lm = LIMS['out_of_scope_pest_after_50_labels']
NS.update({'LABONLY_MITE_NOT_SURE_AFTER_50': pct(lm['not_sure_after_50']),
           'LABONLY_MITE_RUST_AFTER_50': str(lm['answered_as_after_50'].get('rust', 0)),
           'LABONLY_MITE_HEALTHY_AFTER_50': str(lm['answered_as_after_50'].get('healthy', 0))})
# HEAD_KB (an older key) gives the size of the shipped head file: head v3 now (both five-class heads were 68 KB)
HEAD_KB_BEFORE = NS2['SHIP_HEAD_KB']
N['HEAD_KB'] = NS['SHIP_HEAD_KB']

# ---------------------------------------------------------------- human baseline (picture card vs AI)
if HB:
    hum = HB['labellers']; aiS = HB['model']['shipped']; aiS2 = HB['model']['shipped_v2_lab_field']
    ai0 = HB['model']['lab_only_as_shipped']; ai1 = HB['model']['lab_only_after_demo_update_50']

    def rng_(vals, fmt):
        v = [x for x in vals if x is not None]
        if not v:
            return '-'
        lo_, hi_ = fmt(min(v)), fmt(max(v))
        return lo_ if lo_ == hi_ else f'{lo_}–{hi_}'
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
    NS.update({'LABONLY_HB_COPY_IN_UPDATE': str(ai1.get('photos_with_identical_copy_in_training', 0))})
N.update(NS)

# ---------------------------------------------------------------- Ugandan external test (results/uganda_external.json, ml/eval_uganda.py)
UG = json.load(open(os.path.join(RES, 'uganda_external.json')))


def _same_head(tag, head_file):
    """uganda_external.json must come from the head files in model/ now (the version string alone can stay the same)."""
    h_ = json.load(open(os.path.join(REPO, 'model', head_file))); u_ = UG['models'][tag]
    bad = [(k_, u_[k_], v_) for k_, v_ in [('version', h_['version']), ('threshold', h_['threshold']),
                                           ('temperature', h_['temperature']), ('cutoff', h_['ood']['cutoff']),
                                           ('reference_n', h_['ood']['reference']['n']),
                                           ('local_nearest_cutoff', h_['ood'].get('local_nearest_cutoff'))]
           if u_.get(k_) != v_]
    assert not bad, f'results/uganda_external.json was made with another {head_file} {bad}: rerun ml/eval_uganda.py'


_same_head('shipped', 'head.json'); _same_head('lab_only', 'head_labonly.json')
UGD = UG['data']; UGM = UG['models']; UGS = UGM['shipped']['group_aware']; UGL = UGM['lab_only']['group_aware']
UCI = UGM['shipped']['ci95_group_bootstrap']; ULL = UG['learning_loop']; URC = ULL['rule_comparison']
UAE, UPR, UPC = URC['app_rule_extended'], URC['previous_rule_extended'], URC['previous_rule_coarse_grouping']
UCS = ULL['sensitivity_coarse_split_units']
_uat = lambda L_, key, k_: L_['mean'][key][L_['ks'].index(k_)]
_uci = lambda a: f"{100 * a[0]:.0f}–{100 * a[1]:.0f}%"
# the app-rule runs up to 200 labels repeat the main learning loop (same seeds): check that before using them
for k_ in ULL['shipped_base']['ks']:
    for key in ('answered', 'correct_of_answered', 'forced_correct', 'rust_named', 'phoma_named', 'healthy_flagged'):
        assert abs(_uat(UAE, key, k_) - _uat(ULL['shipped_base'], key, k_)) < 1e-9, 'uganda: app-rule runs differ'
NU = dict(UG['suggested_numbers'])
assert NU['UG_SHIP_VERSION'] == NS['SHIP_VERSION']
NU.update({
    'UG_N_READABLE': f"{UGD['readable']:,}",
    **{f'UG_N_{c_.upper()}': f"{UGD['used_by_class'][c_]:,}" for c_ in ('healthy', 'rust', 'phoma')},
    **{f'UG_N_GROUPS_{c_.upper()}': f"{UGD['copy_groups_by_class'][c_]:,}" for c_ in ('healthy', 'rust', 'phoma')},
    'UG_N_SINGLETONS': f"{UGD['group_size']['singletons']:,}", 'UG_GROUP_MAX': str(UGD['group_size']['max']),
    'UG_ONNX_MAX_DIFF': f"{UGD['onnx_check']['max_abs_diff_standardised']:.0e}",
    'UG_SHIP_ANSWERED_CI': _uci(UCI['answered']), 'UG_SHIP_ACC_ANSWERED_CI': _uci(UCI['correct_of_answered']),
    'UG_SHIP_RUST_NAMED_CI': _uci(UCI['rust_named']), 'UG_SHIP_PHOMA_NAMED_CI': _uci(UCI['phoma_named']),
    'UG_SHIP_HEALTHY_FLAGGED_CI': _uci(UCI['healthy_flagged']),
    'UG_SHIP_PHOMA_ANSWERED_RUST': pct(UGS['by_class']['phoma']['answered_as'].get('rust', 0.0)),
    'UG_SHIP_FORCED_PHOMA_AS_RUST': pct(UGS['by_class']['phoma']['forced_as'].get('rust', 0.0)),
    'UG_LABONLY_NOT_SURE_UNFAMILIAR': pct(UGL['not_sure_unfamiliar']), 'UG_LABONLY_RUST_NAMED': pct(UGL['rust_named']),
    'UG_LABONLY_PHOMA_NAMED': pct(UGL['phoma_named']), 'UG_LABONLY_HEALTHY_FLAGGED': pct(UGL['healthy_flagged']),
    'UG_LABONLY_PHOMA_ANSWERED_RUST': pct(UGL['by_class']['phoma']['answered_as'].get('rust', 0.0)),
    'UG_LOOP_SEEDS': str(UAE['seeds']),
})
_lk = {'ANSWERED': 'answered', 'ACC_ANSWERED': 'correct_of_answered', 'FORCED': 'forced_correct',
       'RUST_NAMED': 'rust_named', 'PHOMA_NAMED': 'phoma_named', 'HEALTHY_FLAGGED': 'healthy_flagged'}
for k_ in UAE['ks']:
    for s_, key in _lk.items():
        NU[f'UG_LOOP{k_}_{s_}'] = pct(_uat(UAE, key, k_))
for k_ in UPR['ks']:
    for s_, key in _lk.items():
        NU[f'UG_PREVRULE_LOOP{k_}_{s_}'] = pct(_uat(UPR, key, k_))
for k_ in UPC['ks']:
    for s_ in ('ANSWERED', 'ACC_ANSWERED'):
        NU[f'UG_PREVRULE_COARSE_LOOP{k_}_{s_}'] = pct(_uat(UPC, _lk[s_], k_))
for k_ in UCS['ks']:
    for s_ in ('ANSWERED', 'ACC_ANSWERED', 'FORCED'):
        NU[f'UG_COARSE_LOOP{k_}_{s_}'] = pct(_uat(UCS, _lk[s_], k_))
N.update(NU)

# ---------------------------------------------------------------- familiarity rule (results/familiarity_rule.json, ml/eval_familiarity_rule.py)
FR = json.load(open(os.path.join(RES, 'familiarity_rule.json')))
_hood = json.load(open(os.path.join(REPO, 'model', 'head.json')))['ood']
assert FR['shipped_model'] == NS['SHIP_VERSION'], 'familiarity_rule.json was made for another head: rerun ml/eval_familiarity_rule.py'
if FR['decision'] == 'accept':
    assert _hood.get('local_nearest_cutoff') == FR['c1'], \
        f"head.json ood.local_nearest_cutoff {_hood.get('local_nearest_cutoff')} != familiarity_rule.json c1 {FR['c1']}: rerun ml/train_eval.py"
else:
    assert _hood.get('local_nearest_cutoff') is None, 'rule rejected but head.json has ood.local_nearest_cutoff'
_fk = f"c1={FR['c1']}"
_ft = FR['test_uganda']['main_grouping']; _fc = FR['test_uganda']['coarse_grouping_sensitivity']
_fe = FR['test_ecuador_new_region']; _fm = FR['test_mite_shipped_v3']; _fm2 = FR['stress_mite_head_v2']
_fd = FR['dev_selection']; _row = next(r for r in _fd['table'] if r['c1'] == FR['c1'])
_fat = lambda blk, rule, key, k_: blk['rules'][rule][key][blk['ks'].index(k_)]
NF = {'FAM_DECISION': FR['decision'], 'FAM_C1': f"{FR['c1']:.3f}", 'FAM_C1_FRACTION': f"{FR['c1_fraction_of_cutoff']:.1f}",
      'FAM_DEV_SHARE': pct(FR['uganda_split']['dev_share_of_units']),
      'FAM_DEV_GROUPS': f"{FR['uganda_split']['dev_copy_groups']:,}", 'FAM_TEST_GROUPS': f"{FR['uganda_split']['test_copy_groups']:,}",
      'FAM_FLOOR': pct(0.85), 'FAM_FRACTION_MIN': f"{min(FR['candidates']['fractions']):.1f}",
      'FAM_FRACTION_MAX': f"{max(FR['candidates']['fractions']):.1f}",
      'FAM_DEV_ADDED_CORRECT': f"{100 * min(a for a in _row['added_correct_pooled'] if a is not None):.0f}–"
                               f"{100 * max(a for a in _row['added_correct_pooled'] if a is not None):.0f}%",
      'FAM_TEST_SEEDS': str(_ft['seeds']), 'FAM_HB_ANSWERED': str(FR['test_human_baseline_60']['answered_current']),
      'FAM_HB_N': str(FR['test_human_baseline_60']['n']),
      'FAM_HB_SAME': 'identical' if FR['test_human_baseline_60']['identical_decisions'] else 'different',
      'FAM_MITE0_SENT': pct(_fm['no_labels_sent_to_officer']), 'FAM_V2_MITE0_SENT': pct(_fm2['no_labels_sent_to_officer']),
      'FAM_MITE_MAX_DROP': f"{100 * max(FR['gates']['mite_sent_to_officer_drop_max_5_points']['drop_by_k'].values()):.1f}",
      'FAM_V2_MITE_MAX_DROP': f"{100 * max(FR['gates']['stress_test_head_v2_mite_drop_not_a_gate']['drop_by_k'].values()):.1f}"}
for k_ in _ft['ks']:
    for tag_, rule_ in (('CUR', 'current'), ('NEW', _fk)):
        NF[f'FAM_UG{k_}_ANSWERED_{tag_}'] = pct(_fat(_ft, rule_, 'answered', k_))
        NF[f'FAM_UG{k_}_ACC_{tag_}'] = pct(_fat(_ft, rule_, 'correct_of_answered', k_))
        NF[f'FAM_UG{k_}_RUST_NAMED_{tag_}'] = pct(_fat(_ft, rule_, 'rust_named', k_))
        NF[f'FAM_UG{k_}_PHOMA_NAMED_{tag_}'] = pct(_fat(_ft, rule_, 'phoma_named', k_))
        NF[f'FAM_UG{k_}_HEALTHY_FLAGGED_{tag_}'] = pct1(_fat(_ft, rule_, 'healthy_flagged', k_))
    _ac = _ft['rules'][_fk]['added_correct_pooled'][_ft['ks'].index(k_)]
    if _ac is not None:
        NF[f'FAM_UG{k_}_ADDED_CORRECT'] = pct(_ac)
for k_ in (50, 100):
    NF[f'FAM_UG{k_}_COARSE_ANSWERED_NEW'] = pct(_fat(_fc, _fk, 'answered', k_))
    NF[f'FAM_UG{k_}_COARSE_ACC_NEW'] = pct(_fat(_fc, _fk, 'correct_of_answered', k_))
for k_ in _fe['ks']:
    for tag_, rule_ in (('CUR', 'current'), ('NEW', _fk)):
        NF[f'FAM_EC{k_}_ANSWERED_{tag_}'] = pct(_fat(_fe, rule_, 'answered', k_))
        NF[f'FAM_EC{k_}_ACC_{tag_}'] = pct(_fat(_fe, rule_, 'correct_of_answered', k_))
for k_ in _fm['ks']:
    i_ = _fm['ks'].index(k_)
    for tag_, rule_ in (('CUR', 'current'), ('NEW', _fk)):
        NF[f'FAM_MITE{k_}_SENT_{tag_}'] = pct(_fm['rules'][rule_]['sent_to_officer'][i_])
        NF[f'FAM_MITE{k_}_RUST_{tag_}'] = pct(_fm['rules'][rule_]['answered_rust'][i_])
    NF[f'FAM_MITE{k_}_REFIT_ONLY'] = pct(_fm['diagnostic_current_rule_sent_to_officer']['refit_only_rows_not_added'][i_])
    NF[f'FAM_MITE{k_}_ROWS_ONLY'] = pct(_fm['diagnostic_current_rule_sent_to_officer']['rows_added_no_refit'][i_])
    NF[f'FAM_MITE{k_}_DROP'] = f"{100 * FR['gates']['mite_sent_to_officer_drop_max_5_points']['drop_by_k'][str(k_)]:.1f}"
    NF[f'FAM_V2_MITE{k_}_DROP'] = f"{100 * FR['gates']['stress_test_head_v2_mite_drop_not_a_gate']['drop_by_k'][str(k_)]:.1f}"
N.update(NF)
json.dump(N, open(os.path.join(RES, 'numbers.json'), 'w'), indent=1)

# ---------------------------------------------------------------- NUMBERS_KEYS.md (meaning of the new keys)
MEANING = {
    'SHIP_VERSION': 'version string of the shipped head (model/head.json)',
    'SHIP_N_TRAIN': 'photos the shipped head is trained on (lab + field; v3 also the mite photos used for "other")',
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
    'SHIP_CV_COVERAGE': 'healthy and rust field photos the shipped model answers (not "not sure"; v3: "other" also goes to the officer), cross-validated mean',
    'SHIP_CV_NOT_SURE': 'healthy and rust field photos it sends to the officer ("not sure": low confidence, unfamiliar, or v3 "other"), cross-validated mean',
    'SHIP_CV_ACC_ANSWERED': 'answers that are correct (of answered field photos), cross-validated mean',
    'SHIP_CV_ACC': 'correct if forced to name one of the five classes for every field photo, cross-validated mean',
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
    'SHIP_MITE_NOT_SURE': 'shipped model: share of the mite photos sent to the officer ("not sure", including v3 "other"); v3: each photo scored by a head that never saw it or a copy (out-of-fold for the photos used in training)',
    'SHIP_MITE_NOT_SURE_CV': 'same, mean over the 5 cross-validation folds (v2: each fold head on all mite photos; v3: on that fold\'s mite photos)',
    'SHIP_MITE_CALLED_RUST': 'shipped model: mite photos answered "rust" (count, same scoring as SHIP_MITE_NOT_SURE)', 'SHIP_MITE_CALLED_HEALTHY': 'shipped model: mite photos answered "healthy" (count)',
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
    'SHIP_N_CLASSES': 'answers the shipped head can give (v3: five classes + "other", which is never shown as a diagnosis)',
    'SHIP_OTHER_BUDGET': 'v3: a constant is added to the "other" score so that this share of healthy / rust out-of-fold field photos has "other" as top class (chosen without the scored fold)',
    'SHIP_OTHER_N_TRAIN': 'mite photos the v3 head trains on, as "other"', 'SHIP_OTHER_N_MITE': 'mite photos in RoCoLe',
    'SHIP_OTHER_N_NEVER_TRAINED': 'mite photos v3 never trains on (the demo sample + the mite copies in label-conflicting groups)',
    'SHIP_OTHER_N_CONFLICT_GROUPS': 'copy groups (identical / near-identical images) that carry two different labels; dropped from training',
    'SHIP_OTHER_N_CONFLICT_MITE': 'mite photos in those groups (their healthy / rust copies were already out of v2 training)',
    'SHIP_OTHER_MITE_TO_OFFICER_CV': 'v3: mite photos sent to the officer (any reason), cross-validated mean over folds',
    'SHIP_OTHER_MITE_ROUTED_OTHER_CV': 'v3: mite photos sent to the officer because "other" is the top class, cross-validated',
    'SHIP_OTHER_MITE_CALLED_RUST_CV': 'v3: mite photos answered "rust", cross-validated', 'SHIP_OTHER_MITE_CALLED_HEALTHY_CV': 'v3: mite photos answered "healthy", cross-validated',
    'SHIP_OTHER_MITE_ROUTED_OTHER': 'v3: of all mite photos (scored as SHIP_MITE_NOT_SURE), share with "other" as top class',
    'SHIP_OTHER_ROUTED_OTHER': 'v3: healthy and rust field photos sent to the officer as "other", cross-validated',
    'SHIP_OTHER_RUST_ROUTED_OTHER': 'v3: rust photos wrongly sent to the officer as "other" (of all rust photos), cross-validated',
    'SHIP_OTHER_HEALTHY_ROUTED_OTHER': 'v3: healthy photos sent to the officer as "other" (of all healthy photos), cross-validated',
    'SHIP_OTHER_AUROC_P_OTHER': 'v3: how well the "other" score separates mite photos from healthy / rust field photos (0.5 = chance), cross-validated',
    'SHIP_OTHER_RUST_ANSWERS_MITE': 'v3: of the "rust" answers on all RoCoLe field photos (healthy, rust, mite in the dataset\'s mix), share that are mite photos, cross-validated',
    'SHIP_OTHER_RUST_ANSWERS_MITE_V2': 'same for head v2',
    'SHIP_OTHER_ALL_COVERAGE': 'v3: share answered of all RoCoLe field photos including mite, cross-validated', 'SHIP_OTHER_ALL_COVERAGE_V2': 'same for head v2',
    'SHIP_OTHER_ALL_ACC_ANSWERED': 'v3: answers correct of all RoCoLe field photos including mite (a mite photo answered rust or healthy counts as wrong)',
    'SHIP_OTHER_ALL_ACC_ANSWERED_V2': 'same for head v2',
    'SHIP_OTHER_DELTA_COVERAGE': 'v3 minus v2, healthy / rust photos answered, percentage points (same folds, mean of 5)',
    'SHIP_OTHER_DELTA_ACC_ANSWERED': 'v3 minus v2, answers correct, points', 'SHIP_OTHER_DELTA_RUST_NAMED': 'v3 minus v2, rust leaves named rust, points',
    'SHIP_OTHER_DELTA_HEALTHY_FLAGGED': 'v3 minus v2, healthy leaves called a problem, points',
    'SHIP_OTHER_RUST_NAMED_FOLDS_LOWER': 'folds (of 5) in which v3 names fewer rust leaves than v2',
    'SHIP_OTHER_NOADJ_RUST_NAMED': 'v3 without the two choices (no "other" constant; mite photos inside the threshold rule): rust leaves named rust, cross-validated',
    'SHIP_OTHER_NOADJ_COVERAGE': 'same setting: healthy / rust photos answered', 'SHIP_OTHER_NOADJ_MITE_TO_OFFICER': 'same setting: mite photos sent to the officer',
    'SHIP_OTHER_HALF_RUST_NAMED': 'v3 with a 0.5% "other" budget instead of 1%: rust leaves named rust, cross-validated',
    'SHIP_OTHER_HALF_MITE_CALLED_RUST': 'same setting: mite photos answered "rust" (count of 167)', 'SHIP_OTHER_HALF_MITE_TO_OFFICER': 'same setting: mite photos sent to the officer',
    'SHIP_CV_NOT_SURE_OTHER': 'v3: healthy / rust field photos set aside because "other" is the top class (same as SHIP_OTHER_ROUTED_OTHER, one decimal)',
    'SHIP_V2_VERSION': 'head v2 version string (replaced by v3 in the app; files in ../data_work/shipped_v2/)',
    'SHIP_V2_CV_COVERAGE': 'head v2: healthy / rust field photos answered, cross-validated', 'SHIP_V2_CV_ACC_ANSWERED': 'head v2: answers correct, cross-validated',
    'SHIP_V2_CV_RUST_NAMED': 'head v2: rust leaves named rust, cross-validated', 'SHIP_V2_CV_HEALTHY_FLAGGED': 'head v2: healthy leaves called a problem, cross-validated',
    'SHIP_V2_MITE_NOT_SURE': 'head v2: mite photos "not sure" (final head, all 167)', 'SHIP_V2_MITE_NOT_SURE_CV': 'head v2: same, mean of the 5 fold heads on all mite photos',
    'SHIP_V2_MITE_CALLED_RUST': 'head v2: mite photos answered "rust" (of 167)', 'SHIP_V2_MITE_CALLED_HEALTHY': 'head v2: mite photos answered "healthy"',
    'SHIP_V2_HB_RUST_NAMED': 'head v2 on the 60 picture-card photos: rust photos answered "rust"', 'SHIP_V2_HB_N_ANSWERED': 'head v2: picture-card photos answered',
    'SHIP_V2_HB_ACC_ANSWERED': 'head v2: picture-card answers correct', 'SHIP_V2_HB_HEALTHY_CALLED_PROBLEM': 'head v2: healthy picture-card photos called a problem',
    'SHIP_V2_MITE_TO_OFFICER_CV': 'head v2: mite photos sent to the officer, same rows and folds as SHIP_OTHER_MITE_TO_OFFICER_CV',
    'SHIP_V2_MITE_CALLED_RUST_CV': 'head v2: mite photos answered "rust", same rows and folds as SHIP_OTHER_MITE_CALLED_RUST_CV',
}
missing = sorted(k for k in NS if k not in MEANING and not k.endswith('_SD'))
assert not missing, f'NUMBERS_KEYS.md: no meaning for {missing}'
kmd = ['# numbers.json keys (generated by ml/write_results_md.py — do not edit by hand)', '',
       'Keys that existed before the lab+field model keep their earlier meaning: they describe the **lab-only model**, '
       'now used as the new-region simulation (FIELD_ACC_NO_ABSTAIN, FIELD_MEAN_CONFIDENCE, FIELD_NOT_SURE, MITE_NOT_SURE, '
       'AUROC_*, COV_*, ACC_ANS_*, LAB_*, VILLAGE_* (lab-only + 50 labels operating point), DINO_*, HB_AI_*, '
       'HB_RUST_NAMED_AI, REF_KB (1,000-row lab-only reference), N_TRAIN (lab photos)). '
       'MODEL_MB and LATENCY_MS_LAPTOP describe files both models share. HEAD_KB is the size of the shipped head file. '
       'HB_HUMAN_* and HB_AGREE_* describe the two people and are unchanged.', '',
       f"## Keys re-pointed to head v3 ({NS['SHIP_VERSION']})", '',
       'Head v3 (lab + field photos + an "other" class) replaced head v2 in the app. Every `SHIP_*` key keeps its name and '
       'now describes head v3. The keys below changed value; any doc sentence that uses one should be re-read. '
       'Keys not listed here have the same value for both heads.', '',
       '| Key | Head v2 value (before) | Head v3 value (now) | Meaning |', '|---|---|---|---|']
_both = [k for k in NS2 if not k.endswith('_SD') and k in NS and k != 'SHIP_ONNX_AGREE'  # v2 not re-checked with ONNX
         and (NS2[k] != NS[k] or NS2.get(k + '_SD') != NS.get(k + '_SD'))]
for k in _both:
    sd2 = f" (sd {NS2[k + '_SD']})" if k + '_SD' in NS2 else ''
    sd3 = f" (sd {NS[k + '_SD']})" if k + '_SD' in NS else ''
    kmd.append(f"| `{k}` | {NS2[k]}{sd2} | {NS[k]}{sd3} | {MEANING[k]} |")
if HEAD_KB_BEFORE != N['HEAD_KB']:
    kmd.append(f"| `HEAD_KB` | {HEAD_KB_BEFORE} | {N['HEAD_KB']} | size of the shipped head file model/head.json (KB) |")
kmd += ['', 'All shipped-model keys (`SHIP_*` = head v3, `SHIP_OTHER_*` = the "other" answer, `SHIP_V2_*` = head v2 for '
        'reference; `*_SD` = standard deviation across the 5 folds, in percentage points):', '',
        '| Key | Value now | Meaning |', '|---|---|---|']
for k in NS:
    if k.endswith('_SD'):
        continue
    sd = f" (sd {NS[k + '_SD']})" if k + '_SD' in NS else ''
    kmd.append(f"| `{k}` | {NS[k]}{sd} | {MEANING[k]} |")


def _ug_meaning(k):
    """Meaning of a UG_* key (Ugandan external test)."""
    import re
    fixed = {
        'UG_N_PHOTOS': 'Ugandan photos used, after dropping empty files and label conflicts',
        'UG_N_GROUPS': 'distinct leaves among them (groups of copies; every Ugandan share counts each group once)',
        'UG_N_LISTED': 'files listed in the Mendeley dataset', 'UG_N_EMPTY': 'empty files dropped',
        'UG_N_READABLE': 'files downloaded and readable',
        'UG_N_CONFLICT': 'photos dropped because a near-identical copy sits in another class folder (label unknown)',
        'UG_N_IDENTICAL': 'files that are byte-identical copies of another file',
        'UG_N_HEALTHY': 'healthy photos used', 'UG_N_RUST': 'rust photos used', 'UG_N_PHOMA': 'Phoma photos used',
        'UG_N_GROUPS_HEALTHY': 'distinct healthy leaves', 'UG_N_GROUPS_RUST': 'distinct rust leaves',
        'UG_N_GROUPS_PHOMA': 'distinct Phoma leaves', 'UG_N_SINGLETONS': 'copy groups that are a single photo',
        'UG_GROUP_MAX': 'photos in the largest copy group',
        'UG_ONNX_MAX_DIFF': 'phone ONNX backbone vs Python embeddings on Ugandan photos: largest difference',
        'UG_SHIP_VERSION': 'head tested (must equal SHIP_VERSION; write_results_md.py checks the head file too)',
        'UG_SHIP_ANSWERED': 'shipped model, no officer labels: Ugandan photos answered',
        'UG_SHIP_NOT_SURE': 'same: Ugandan photos sent to the officer',
        'UG_SHIP_ACC_ANSWERED': 'same: answers correct', 'UG_SHIP_FORCED': 'same: right if forced to answer every photo',
        'UG_SHIP_RUST_NAMED': 'same: rust leaves answered "rust", of all rust leaves',
        'UG_SHIP_PHOMA_NAMED': 'same: Phoma leaves answered "Phoma", of all Phoma leaves',
        'UG_SHIP_HEALTHY_FLAGGED': 'same: healthy leaves answered as a problem, of all healthy leaves',
        'UG_SHIP_SICK_PROBLEM': 'same: rust and Phoma leaves answered as a problem, of all rust and Phoma leaves',
        'UG_SHIP_NOT_SURE_UNFAMILIAR': 'same: photos sent to the officer because they look unfamiliar',
        'UG_SHIP_FORCED_RUST_AS_RUST': 'same, if forced to answer: rust leaves called rust',
        'UG_SHIP_FORCED_PHOMA_AS_PHOMA': 'same, if forced: Phoma leaves called Phoma',
        'UG_SHIP_FORCED_HEALTHY_AS_HEALTHY': 'same, if forced: healthy leaves called healthy',
        'UG_SHIP_FORCED_PHOMA_AS_RUST': 'same, if forced: Phoma leaves called rust',
        'UG_SHIP_PHOMA_ANSWERED_RUST': 'shipped model, no officer labels: Phoma leaves answered "rust", of all Phoma leaves',
        'UG_SHIP_ANSWERED_CI': '95% interval for UG_SHIP_ANSWERED (resampling copy groups)',
        'UG_SHIP_ACC_ANSWERED_CI': '95% interval for UG_SHIP_ACC_ANSWERED', 'UG_SHIP_RUST_NAMED_CI': '95% interval for UG_SHIP_RUST_NAMED',
        'UG_SHIP_PHOMA_NAMED_CI': '95% interval for UG_SHIP_PHOMA_NAMED', 'UG_SHIP_HEALTHY_FLAGGED_CI': '95% interval for UG_SHIP_HEALTHY_FLAGGED',
        'UG_LABONLY_ANSWERED': 'lab-only model, no officer labels: Ugandan photos answered',
        'UG_LABONLY_ACC_ANSWERED': 'same: answers correct', 'UG_LABONLY_FORCED': 'same: right if forced',
        'UG_LABONLY_NOT_SURE_UNFAMILIAR': 'same: sent to the officer because unfamiliar',
        'UG_LABONLY_RUST_NAMED': 'same: rust leaves answered "rust"', 'UG_LABONLY_PHOMA_NAMED': 'same: Phoma leaves answered "Phoma"',
        'UG_LABONLY_HEALTHY_FLAGGED': 'same: healthy leaves called a problem',
        'UG_LABONLY_PHOMA_ANSWERED_RUST': 'same: Phoma leaves answered "rust"',
        'UG_FAMILIAR_IF_ALL_UG_STORED': 'share of Ugandan photos that would count as familiar if every other Ugandan photo (outside its own copy cluster) were stored',
        'UG_LOOP_SEEDS': 'random pool/test splits and label orders averaged in the Uganda learning loop',
        'EC_LOOP50_ANSWERED': 'context: Ecuador field photos, lab-only base, after 50 officer labels, app rule: photos answered (same as COV_50)',
    }
    if k in fixed:
        v_ = fixed[k]
        if v_.startswith('same'):   # spell out which model, so each row reads on its own
            who_ = 'shipped model' if k.startswith('UG_SHIP_') else 'lab-only model'
            v_ = f"{who_}, no officer labels{', if forced' if v_.startswith('same, if forced') else ''}: " + v_.split(': ', 1)[1]
        return v_
    m_ = re.fullmatch(r'UG_(LABONLY_|PREVRULE_COARSE_|PREVRULE_|COARSE_|APPRULE_)?LOOP(\d+)_(\w+)', k)
    if not m_:
        return None
    base = {'': 'shipped base, app rule: 10 nearest stored photos OR the nearest officer-labelled photo within FAM_C1; that '
                'cutoff was chosen on 40% of these copy clusters, which this loop includes (FAM_UG* keys: the other 60% only)',
            'LABONLY_': 'lab-only base, app rule',
            'PREVRULE_': 'shipped base, previous rule (10 nearest stored photos only, the app before the nearest-officer-photo check)',
            'PREVRULE_COARSE_': 'previous rule, coarser copy grouping',
            'COARSE_': 'shipped base, app rule, coarser copy grouping (check for near-copies across the split)',
            'APPRULE_': 'shipped base, app rule (same runs as UG_LOOP*)'}[m_.group(1) or '']
    what = {'ANSWERED': 'Ugandan test photos answered', 'ACC_ANSWERED': 'answers correct',
            'FORCED': 'right if forced to answer every photo', 'RUST_NAMED': 'rust leaves answered "rust", of all rust leaves',
            'PHOMA_NAMED': 'Phoma leaves answered "Phoma", of all Phoma leaves',
            'HEALTHY_FLAGGED': 'healthy leaves called a problem, of all healthy leaves'}[m_.group(3)]
    return f'Uganda learning loop after {m_.group(2)} officer labels ({base}): {what}'


_ug_missing = sorted(k for k in NU if _ug_meaning(k) is None)
assert not _ug_missing, f'NUMBERS_KEYS.md: no meaning for {_ug_missing}'
kmd += ['', f"## Ugandan external test (`UG_*`, from results/uganda_external.json, written by ml/eval_uganda.py)", '',
        f"Head tested: {NU['UG_SHIP_VERSION']} (the shipped head) and the lab-only head. Every share counts each group of "
        f"copies once. Learning-loop keys are means over {NU['UG_LOOP_SEEDS']} random pool/test splits, on the test half.", '',
        '| Key | Value now | Meaning |', '|---|---|---|']
def _ug_order(k):
    import re
    m_ = re.fullmatch(r'UG_(\w*?)LOOP(\d+)_(\w+)', k)
    return (0, k, 0, '') if not m_ else (1, m_.group(1), int(m_.group(2)), m_.group(3))


kmd += [f"| `{k}` | {NU[k]} | {_ug_meaning(k)} |" for k in sorted(NU, key=_ug_order)]


def _fam_meaning(k):
    """Meaning of a FAM_* key (nearest-officer-photo familiarity rule, results/familiarity_rule.json)."""
    import re
    fixed = {
        'FAM_DECISION': 'decision on the rule (accept: in head.json and the app)',
        'FAM_C1': 'ood.local_nearest_cutoff: a photo also counts as familiar when 1 - cosine to its nearest officer-labelled photo is at most this',
        'FAM_C1_FRACTION': 'FAM_C1 as a multiple of the shipped familiarity cutoff (SHIP_CUTOFF)',
        'FAM_FRACTION_MIN': 'smallest candidate multiple tried', 'FAM_FRACTION_MAX': 'largest candidate multiple tried (larger values were not tested)',
        'FAM_DEV_SHARE': 'share of Ugandan coarse copy clusters used to choose FAM_C1 (DEV part); the rest is the TEST part',
        'FAM_DEV_GROUPS': 'Ugandan copy groups in the DEV part', 'FAM_TEST_GROUPS': 'Ugandan copy groups in the TEST part',
        'FAM_FLOOR': 'selection rule: photos the new rule adds must be at least this share correct at 10, 20, 50 and 100 labels (DEV part)',
        'FAM_DEV_ADDED_CORRECT': 'DEV part, chosen FAM_C1: photos the new rule adds, share correct (range over 10, 20, 50, 100 labels)',
        'FAM_TEST_SEEDS': 'random pool/scored splits and label orders on the TEST part',
        'FAM_HB_N': 'human-baseline photos checked', 'FAM_HB_ANSWERED': 'of them answered by the shipped model under both rules (no officer labels)',
        'FAM_HB_SAME': 'decisions on those photos, new rule against previous rule',
        'FAM_MITE0_SENT': 'mite photos sent to the officer by the shipped head before any officer label (optimistic: head v3 trained on most of them; the fair figure is SHIP_MITE_NOT_SURE)',
        'FAM_V2_MITE0_SENT': 'same for head v2 (no "other" answer, never trained on mite photos)',
        'FAM_MITE_MAX_DROP': 'largest drop, in points, in mite photos sent to the officer, new rule against previous rule (gate: at most 5)',
        'FAM_V2_MITE_MAX_DROP': 'same with head v2 (stress test, not a gate)'}
    if k in fixed:
        return fixed[k]
    m_ = re.fullmatch(r'FAM_UG(\d+)_(COARSE_)?(ANSWERED|ACC|RUST_NAMED|PHOMA_NAMED|HEALTHY_FLAGGED|ADDED_CORRECT)(?:_(CUR|NEW))?', k)
    if m_:
        what = {'ANSWERED': 'photos answered', 'ACC': 'answers correct', 'RUST_NAMED': 'rust leaves answered "rust", of all rust leaves',
                'PHOMA_NAMED': 'Phoma leaves answered "Phoma", of all Phoma leaves',
                'HEALTHY_FLAGGED': 'healthy leaves called a problem, of all healthy leaves',
                'ADDED_CORRECT': 'photos the new rule adds (answered under it, not under the previous rule), share correct'}[m_.group(3)]
        rule = {'CUR': 'previous rule', 'NEW': 'app rule (new)', None: 'app rule (new)'}[m_.group(4)]
        grp = ', coarser copy grouping' if m_.group(2) else ''
        return f'Ugandan TEST part (never used to choose FAM_C1), shipped head, after {m_.group(1)} officer labels, {rule}{grp}: {what}'
    m_ = re.fullmatch(r'FAM_EC(\d+)_(ANSWERED|ACC)_(CUR|NEW)', k)
    if m_:
        return (f"Ecuador new-region simulation (lab-only base), after {m_.group(1)} labels, "
                f"{'previous rule' if m_.group(3) == 'CUR' else 'app rule (new)'}: "
                f"{'photos answered' if m_.group(2) == 'ANSWERED' else 'answers correct'}")
    m_ = re.fullmatch(r'FAM_(V2_)?MITE(\d+)_(SENT_CUR|SENT_NEW|RUST_CUR|RUST_NEW|REFIT_ONLY|ROWS_ONLY|DROP)', k)
    if m_:
        head_ = 'head v2' if m_.group(1) else 'shipped head v3'
        what = {'SENT_CUR': 'mite photos sent to the officer, previous rule', 'SENT_NEW': 'mite photos sent to the officer, app rule (new)',
                'RUST_CUR': 'mite photos answered "rust", previous rule', 'RUST_NEW': 'mite photos answered "rust", app rule (new)',
                'REFIT_ONLY': 'mite photos sent to the officer, previous rule, head refit but labelled rows NOT added (diagnostic)',
                'ROWS_ONLY': 'mite photos sent to the officer, previous rule, labelled rows added but NO refit (diagnostic)',
                'DROP': 'drop in mite photos sent to the officer, new rule against previous rule, points'}[m_.group(3)]
        return f'{head_}, after {m_.group(2)} officer labels of RoCoLe healthy/rust photos: {what}'
    return None


_fam_missing = sorted(k for k in NF if _fam_meaning(k) is None)
assert not _fam_missing, f'NUMBERS_KEYS.md: no meaning for {_fam_missing}'
kmd += ['', '## Familiarity rule (`FAM_*`, from results/familiarity_rule.json, written by ml/eval_familiarity_rule.py)', '',
        f"Decision: **{NF['FAM_DECISION']}**, ood.local_nearest_cutoff = {NF['FAM_C1']}. Chosen on the DEV part "
        f"({NF['FAM_DEV_SHARE']} of the Ugandan coarse copy clusters), scored on the TEST part. Every Ugandan share counts "
        'each copy group once.', '',
        '**Keys whose meaning changed with this rule.** The app now uses it, so every learning-loop key that simulates the '
        'app uses it too: `UG_LOOP*`, `UG_LABONLY_LOOP*`, `UG_COARSE_LOOP*`, `UG_APPRULE_LOOP*`, `EC_LOOP50_ANSWERED`, '
        '`COV_*`, `ACC_ANS_*` (the `*_LOCAL_ONLY` baselines too), the lab-only `VILLAGE_*` operating point '
        'and `HB_AI_UPD_*` (the lab-only demo update). The previous rule stays as `UG_PREVRULE_*` and `COV_*_PREV` / '
        '`ACC_ANS_*_PREV`. Removed: `UG_OPTION_*` and `UG_OPTION_COARSE_*` (the rule they simulated is now the app rule, '
        'up to a 0.00003 difference in the cutoff and the officer rows also joining the 10-nearest check); any doc '
        'sentence using them, or calling the "not sure" check slow in Uganda, needs rewording.', '',
        '| Key | Value now | Meaning |', '|---|---|---|']
kmd += [f"| `{k}` | {NF[k]} | {_fam_meaning(k)} |" for k in NF]
kmd += ['', '## Previous-rule keys for the new-region simulation', '', '| Key | Value now | Meaning |', '|---|---|---|']
kmd += [f"| `{k}` | {N[k]} | Ecuador new-region simulation (lab-only base), previous familiarity rule (10 nearest only), "
        f"after {k.split('_')[-2]} labels: {'photos answered' if k.startswith('COV') else 'answers correct'} |"
        for k in N if k.endswith('_PREV')]
open(os.path.join(RES, 'NUMBERS_KEYS.md'), 'w').write('\n'.join(kmd) + '\n')

# ---------------------------------------------------------------- RESULTS.md
x = N
S_ = {'cv': '3.1', 'route': '3.2', 'ug': '3.3', 'card': '3.4', 'village': '3.5', 'lab': '3.6', 'size': '3.7', 'limits': '3.8'}


def nxt(what, who, metric, when):
    """Every limit or simplification line in RESULTS.md ends with this: what, who, metric, when."""
    return f"**Next step:** {what}. Who: {who}. Metric: {metric}. When: {when}."


NX = {
    'phone': nxt('time the app on a low-cost Android phone and on an iPhone', 'the team',
                 'median seconds from photo to answer, and first-load time', 'before the pilot starts'),
    'kenya': nxt('keep the first 200 officer-labelled Kenyan pilot photos aside as a Kenyan test set, never trained on',
                 'the team with the cooperative extension officer',
                 'photos answered, answers correct and rust leaves named rust', 'first pilot month'),
    'plant': nxt('record plot and plant with every pilot photo, so tests can hold out whole farms',
                 'the team adds the fields to the app; relay farmers fill them in',
                 'answers correct on held-out farms against randomly held-out photos', 'from the first pilot visit'),
    'labels': nxt('the extension officer relabels 100 random RoCoLe photos and 100 random Ugandan photos',
                  'cooperative extension officer', 'share of photos where the officer agrees with the dataset label',
                  'pilot week 1'),
    'conflict': nxt('the extension officer relabels the photos in these groups; groups with an agreed label go back into training',
                    'extension officer', f"share of the {x['SHIP_OTHER_N_CONFLICT_GROUPS']} groups with an agreed label",
                    'pilot onboarding, week 1'),
    'ug_copies': nxt('ask the dataset authors for the original file list (before copies were made) and rerun with exact groups',
                     'the team, by email', 'photos answered and answers correct with exact groups against ours',
                     'after the challenge'),
    'ug_style': nxt('on the first 100 pilot photos, compare full-size photos with the same photos cut to 256 × 256 px',
                    'the team', 'photos answered and answers correct, full-size against cut', 'pilot week 1'),
    'species': nxt('record the coffee species at each plot visit and report results by species',
                   'the extension officer at each plot visit', 'answers correct by species', 'from the first pilot visit'),
    'opens': nxt('report photos answered and answers correct on the first 200 officer-labelled Kenyan pilot photos (the '
                 'sealed Kenyan test set), with the app rule and the previous rule side by side', 'ML lead',
                 'photos answered and answers correct after 50 and 100 labels; healthy leaves called a problem (must stay '
                 'under 2%)', 'first pilot month'),
    'other_refit': nxt('keep the "other" weights fixed during the on-phone refit, or mix stored "other" rows into it, and '
                       'rerun the mite test of ml/eval_familiarity_rule.py', 'ML lead',
                       'mite photos sent to the officer after 10, 50 and 100 healthy/rust labels (target: within 5 points '
                       'of the no-label level) with rust leaves named rust unchanged', 'before the pilot starts'),
    'phoma': nxt('train a head on half of the Ugandan copy groups (Phoma field photos included) and test it on the other half',
                 'ML lead', 'Phoma leaves answered "rust" and rust leaves named rust, on the held-out half',
                 'before the pilot starts'),
    'tune': nxt('re-tune the learning-step strength, answer threshold and familiarity cutoff on the first pilot labels, '
                'using an inner split of the labelled photos only', 'ML lead',
                'photos answered and answers correct after 50 labels', 'after the first 50 pilot labels'),
    'mite_rust': nxt('the extension officer labels every "Different problem" photo in the review queue, and the ML lead '
                     'retrains "other" with them', 'extension officer and ML lead',
                     'mite-like photos counted as rust (must fall) and rust leaves named rust (must stay within 3 points '
                     'of head v3, cross-validated); the update is kept only if both hold', 'pilot week 4'),
    'other_scope': nxt('keep 1 in 5 officer-labelled "Different problem" photos out of training as a test set for the "other" answer',
                       'ML lead', f"share of those photos sent to the officer (target: above head v3's "
                       f"{x['SHIP_MITE_NOT_SURE']} on mite photos)", 'report at pilot week 4'),
    'dp_update': nxt('test the on-phone update with 1–20 officer labels that include "Different problem", and add a rule '
                     '(a stronger pull toward the shipped model for "other", or a minimum number of healthy and rust '
                     'labels) if healthy photos go to "other"', 'ML lead',
                     f"healthy field photos sent to \"other\" after the update (shipped model: "
                     f"{x['SHIP_OTHER_HEALTHY_ROUTED_OTHER']})", 'before the pilot starts'),
    'budget': nxt('fix the "other" setting before the Kenyan test set is opened, then report on that set', 'ML lead',
                  'rust leaves named rust and mite-like photos sent to the officer, on the Kenyan test set',
                  'before the Kenyan test set is opened (first pilot month)'),
    'village': nxt('replay both alert rules on pilot visit data and re-set the alert line',
                   'ML lead with the cooperative extension officer',
                   "false alarms and missed outbreaks against the officer's own village checks",
                   'after the first 3 months of pilot visits'),
    'card': nxt('repeat the card test with relay farmers trained by the cooperative, on 60 officer-labelled Kenyan pilot photos',
                'the team with the cooperative', 'rust photos named rust and healthy-vs-problem correct, next to the AI '
                'on the same photos', 'first pilot month'),
    'card_field': nxt('add field photos of each problem to the picture card before that test', 'the team',
                      'rust photos named rust by people using the new card', 'before the relay-farmer card test'),
    'card_copy': nxt('rebuild the 50-label demo update without that photo', 'ML lead',
                     'the lab-only "after 50 labels" row on the 60 photos', 'after the challenge'),
}


def _tr_name(r):
    if r['other_budget'] is None and not r['threshold_rule_on_known_classes_only']:
        return 'Head v3, "other" as trained, mite photos inside the threshold rule'
    if r['other_budget'] is None:
        return 'Head v3, threshold rule as v2, no "other" constant'
    nm = f"Head v3, threshold rule as v2, \"other\" constant at {100 * r['other_budget']:g}%"
    return f'**{nm} (shipped)**' if r.get('shipped') else nm


md = f"""# Results (generated by ml/write_results_md.py from results/*.json — do not edit by hand)

Every limit or simplification below ends with its next step: what, who, the metric that decides it, and when.

## 1. What the phone runs
- Frozen MobileNetV3-Large image backbone (ImageNet weights, Apache-2.0): **{x['MODEL_MB']} MB** ONNX, ~{x['LATENCY_MS_LAPTOP']} ms per photo on a laptop CPU. Phone speed is not yet measured. {NX['phone']}
- Shipped head **{x['SHIP_VERSION']}** (trained on lab + field photos, with an "other" answer for problems outside the five classes): **{x['SHIP_HEAD_KB']} KB** JSON. Familiarity reference: **{x['SHIP_REF_N']}** stored training photos as int8 vectors ({x['SHIP_REF_N_LAB']} lab, {x['SHIP_REF_N_FIELD']} field), **{x['SHIP_REF_KB']} KB**.
- The "other" answer is never shown as a diagnosis. When it is the top class, the app sends the photo to the officer ("looks like a different problem"), says the usual "not sure" sentence, and never counts the photo as rust.
- The ONNX path reproduces the Python pipeline: {O['onnx_vs_python_same_class']} same class on field photos, max embedding difference {O['onnx_vs_python_max_abs_diff']}; same decision on {O.get('samples_same_decision_as_python', '?')} demo samples; on Ugandan photos the embeddings differ by at most {x['UG_ONNX_MAX_DIFF']}.
- One backbone serves every head: the embedding standardisation baked into the ONNX file is computed on the lab training photos and kept for the shipped head, so the lab-only files (new-region simulation, starter kit) run on the same backbone.

## 2. Data
- **Lab photos** ({x['N_TRAIN']} for training): 1,500 sampled per class from JMuBEN/JMuBEN2 (Kenya, Kirinyaga, arabica; many are rotated/flipped copies) plus half of the BRACOL photos we could recover (Brazil, arabica; 1,342 usable of 1,747). The other half of BRACOL ({x['N_CALIB']} photos) is the lab calibration set, and lab accuracy is reported on it. JMuBEN's own validation split holds rotated or flipped copies of training leaves, so its score (100%) is not used.
- **Field photos**: RoCoLe (Ecuador, robusta, leaves on the plant, smartphone), {x['N_FIELD']} healthy/rust photos labelled by the dataset authors, plus {x['N_MITE']} red-spider-mite photos.
  - The shipped model trains on **{x['SHIP_N_TRAIN_FIELD']}** healthy/rust photos ({x['SHIP_N_TRAIN_FIELD_HEALTHY']} healthy, {x['SHIP_N_TRAIN_FIELD_RUST']} rust) and **{x['SHIP_OTHER_N_TRAIN']}** mite photos as "other".
  - Never trained on: the 60 picture-card photos, the 7 demo samples (one is a mite photo), {x['SHIP_N_COPIES_REMOVED']} healthy/rust photos that are identical or near-identical copies of a held-out photo, and every photo in the {x['SHIP_OTHER_N_CONFLICT_GROUPS']} copy groups that carry two different labels ({x['SHIP_OTHER_N_CONFLICT_MITE']} mite photos and their rust or healthy copies). RoCoLe holds {x['RO_DUP_PAIRS']} pairs of identical or near-identical images ({x['RO_DUP_PAIRS_DIFFERENT_LABELS']} pairs carry two different labels, mostly mite vs rust); copies are always kept on the same side of every split.
- **Ugandan farm photos (external test; never used for training; one setting of the familiarity rule, `ood.local_nearest_cutoff`, was chosen on {x['FAM_DEV_SHARE']} of the copy clusters and is scored on the other part, section {S_['ug']})**: "{UG['dataset']['name']}" ({UG['dataset']['institution']}, Mendeley Data, doi {UG['dataset']['doi']}, {UG['dataset']['license']}). Close-ups of leaves on the plant, 256 × 256 px, labelled healthy, rust or Phoma by folder.
  - Of {x['UG_N_LISTED']} listed files, {x['UG_N_EMPTY']} were empty. {x['UG_N_CONFLICT']} photos have a near-identical copy in another class folder (rust vs Phoma), so their label is unknown and they are dropped. That leaves **{x['UG_N_PHOTOS']}** photos ({x['UG_N_HEALTHY']} healthy, {x['UG_N_RUST']} rust, {x['UG_N_PHOMA']} Phoma).
  - The dataset mixes in rotated, flipped and brightened copies ({x['UG_N_IDENTICAL']} files are byte-identical copies of another file). We group copies by image similarity into **{x['UG_N_GROUPS']}** distinct leaves ({x['UG_N_GROUPS_HEALTHY']} healthy, {x['UG_N_GROUPS_RUST']} rust, {x['UG_N_GROUPS_PHOMA']} Phoma; {x['UG_N_SINGLETONS']} are single photos, the largest group has {x['UG_GROUP_MAX']}). Each group counts once in every Ugandan number.
- **Lab-only model**: the same lab photos, no field photos. It gives the motivating finding (section {S_['lab']}), simulates a model meeting a new region's photo style, and is the starter-kit base.
- **Head v2** (the previous shipped head: lab + field photos, five classes, no "other") is kept for comparison; it is scored on the same folds and photos.

## 3. Findings

### 3.1 The shipped model on field photos (5-fold cross-validation)
Trained on lab photos plus field photos, the shipped model answers **{x['SHIP_CV_COVERAGE']}** of healthy and rust field photos it has not seen and is right on **{x['SHIP_CV_ACC_ANSWERED']}** of those answers. It names rust on **{x['SHIP_CV_RUST_NAMED']}** of rust leaves and calls **{x['SHIP_CV_HEALTHY_FLAGGED']}** of healthy leaves a problem. Its confidence matches its accuracy (calibration error {x['SHIP_CV_ECE']}; 0 = perfect). Lab-style photos still work: {x['SHIP_LAB_ACC']} right on held-out BRACOL photos ({x['LAB_ACC']} for the lab-only model).

Compared with head v2 on the same folds, the "other" answer changes rust leaves named rust by **{x['SHIP_OTHER_DELTA_RUST_NAMED']} points** (lower in {x['SHIP_OTHER_RUST_NAMED_FOLDS_LOWER']} of 5 folds); {x['SHIP_OTHER_RUST_ROUTED_OTHER']} of rust leaves now go to the officer as "other" instead of being counted. The other three measures move by {max(abs(100 * PV[k_]['mean_difference']) for k_ in ('coverage', 'acc_answered', 'healthy_flagged')):.1f} points or less. What it buys is in section {S_['route']}: far fewer mite photos counted as rust.

| Field photos (healthy + rust), never trained on | Shipped (head v3), mean of {x['SHIP_CV_FOLDS']} folds | Spread (sd, points) | Head v2, same folds | v3 minus v2 (points) |
|---|---|---|---|---|
| Answered (not "not sure") | {x['SHIP_CV_COVERAGE']} | {x['SHIP_CV_COVERAGE_SD']} | {x['SHIP_V2_CV_COVERAGE']} | {x['SHIP_OTHER_DELTA_COVERAGE']} |
| Answers that are correct | {x['SHIP_CV_ACC_ANSWERED']} | {x['SHIP_CV_ACC_ANSWERED_SD']} | {x['SHIP_V2_CV_ACC_ANSWERED']} | {x['SHIP_OTHER_DELTA_ACC_ANSWERED']} |
| Rust leaves named rust (of all rust leaves) | {x['SHIP_CV_RUST_NAMED']} | {x['SHIP_CV_RUST_NAMED_SD']} | {x['SHIP_V2_CV_RUST_NAMED']} | {x['SHIP_OTHER_DELTA_RUST_NAMED']} |
| Healthy leaves called a problem (of all healthy leaves) | {x['SHIP_CV_HEALTHY_FLAGGED']} | {x['SHIP_CV_HEALTHY_FLAGGED_SD']} | {x['SHIP_V2_CV_HEALTHY_FLAGGED']} | {x['SHIP_OTHER_DELTA_HEALTHY_FLAGGED']} |
| Rust leaves sent to the officer as "other" | {x['SHIP_OTHER_RUST_ROUTED_OTHER']} | {x['SHIP_OTHER_RUST_ROUTED_OTHER_SD']} | 0% (no "other") | |
| Correct if forced to name one of the five classes | {x['SHIP_CV_ACC']} | {x['SHIP_CV_ACC_SD']} | | |
| Calibration error (ECE) | {x['SHIP_CV_ECE']} | {x['SHIP_CV_ECE_SD']} | | |

Second check on photos kept out from the start (the 60 picture-card photos, section {S_['card']}): it answers {x['SHIP_HB_N_ANSWERED']} of 60, {x['SHIP_HB_ACC_ANSWERED']} of them correctly (head v2: {x['SHIP_V2_HB_N_ANSWERED']} of 60, {x['SHIP_V2_HB_ACC_ANSWERED']}). On the app's demo samples it answers {x['SHIP_DEMO_ANSWERED_CORRECT']} of the {int(x['SHIP_DEMO_N']) - 1} healthy/rust photos correctly and says "not sure" to {x['SHIP_DEMO_NOT_SURE']}.

How it was measured: each fold's head was trained on all lab photos plus the other four folds (healthy, rust and mite photos; copy groups stay in one fold); its familiarity reference held only those folds' healthy and rust photos; its temperature, confidence threshold, familiarity cutoff and "other" constant were chosen on the BRACOL calibration half plus the other folds' out-of-fold predictions, so nothing was tuned on the photos it was scored on. The shipped head uses all training photos, with those values chosen the same way on all out-of-fold predictions (threshold {x['SHIP_THRESHOLD']}, cutoff {x['SHIP_CUTOFF']}, temperature {x['SHIP_TEMPERATURE']}). Head v2 used the same folds and the same healthy/rust photos.

### 3.2 "Not sure" and "other problem" routing
The app answers only when three checks pass: the model is confident, the photo looks like the stored training photos, and the top class is not "other". Every other photo goes to the officer's review queue and stays out of the rust count until the officer labels it.

- **It sets aside the photos it would get wrong.** On the {x['SHIP_CV_NOT_SURE']} of healthy and rust field photos the shipped model sends to the officer, it would have been right only {x['SHIP_CV_ACC_NOT_SURE_IF_FORCED']} of the time if forced to answer, against {x['SHIP_CV_ACC_ANSWERED']} on the photos it answers. Reasons: low confidence ({x['SHIP_CV_NOT_SURE_LOW_CONF']} of photos), unfamiliar look ({x['SHIP_CV_NOT_SURE_UNFAMILIAR']}) and "looks like a different problem" ({x['SHIP_CV_NOT_SURE_OTHER']}).
- **It protects the count when the photo style is new.** On farm photos from Uganda (section {S_['ug']}), the shipped model would be right on only {x['UG_SHIP_FORCED']} if forced to answer; the app sends {x['UG_SHIP_NOT_SURE']} of them to the officer instead, almost all because they look unfamiliar ({x['UG_SHIP_NOT_SURE_UNFAMILIAR']} of all photos). In the new-region simulation (section {S_['lab']}), confidence gives no warning (AUROC {x['AUROC_CONFIDENCE']}, worse than a coin flip), while comparing each photo with the stored training photos separates the new style almost perfectly (AUROC {x['AUROC_KNN']}).

#### Problems outside the five classes: the "other" answer
**What head v3 adds.** Head v2 had five answers, so a photo of a pest it was never taught got one of them: it called {x['SHIP_V2_MITE_CALLED_RUST']} of the {x['N_MITE']} red-spider-mite photos rust, which would inflate a village's rust count. Head v3 learns a sixth answer, "other", from {x['SHIP_OTHER_N_TRAIN']} mite photos. The app never shows "other" as a diagnosis: the photo goes to the officer with the reason "looks like a different problem", and it never counts as rust.

Each mite photo below is scored by a head that never saw it or a copy of it (out-of-fold for the {x['SHIP_OTHER_N_TRAIN']} photos used in training, the final head for the {x['SHIP_OTHER_N_NEVER_TRAINED']} never trained on):

| {x['N_MITE']} mite photos | Shipped (head v3) | Head v2 |
|---|---|---|
| Sent to the officer (any reason) | **{x['SHIP_MITE_NOT_SURE']}** | {x['SHIP_V2_MITE_NOT_SURE']} |
| of which because "other" is the top class | {x['SHIP_OTHER_MITE_ROUTED_OTHER']} | — |
| Answered "rust" (counted as rust) | **{x['SHIP_MITE_CALLED_RUST']}** | {x['SHIP_V2_MITE_CALLED_RUST']} |
| Answered "healthy" | {x['SHIP_MITE_CALLED_HEALTHY']} | {x['SHIP_V2_MITE_CALLED_HEALTHY']} |
| Cross-validated, same mite photos and folds: sent to the officer | {x['SHIP_OTHER_MITE_TO_OFFICER_CV']} (sd {x['SHIP_OTHER_MITE_TO_OFFICER_CV_SD']}) | {x['SHIP_V2_MITE_TO_OFFICER_CV']} (sd {x['SHIP_V2_MITE_TO_OFFICER_CV_SD']}) |
| Cross-validated, same mite photos and folds: answered "rust" | {x['SHIP_OTHER_MITE_CALLED_RUST_CV']} (sd {x['SHIP_OTHER_MITE_CALLED_RUST_CV_SD']}) | {x['SHIP_V2_MITE_CALLED_RUST_CV']} (sd {x['SHIP_V2_MITE_CALLED_RUST_CV_SD']}) |

What it means for a rust count: across all RoCoLe field photos in the dataset's own mix (healthy, rust and mite), mite photos make up {x['SHIP_OTHER_RUST_ANSWERS_MITE']} of the "rust" answers with head v3, against {x['SHIP_OTHER_RUST_ANSWERS_MITE_V2']} with head v2 (cross-validated). The "other" score separates mite photos from healthy and rust field photos with AUROC {x['SHIP_OTHER_AUROC_P_OTHER']}; the familiarity distance does so with {x['SHIP_MITE_AUROC_FAMILIARITY']} and confidence with {x['SHIP_MITE_AUROC_CONFIDENCE']}. The familiarity reference is the same {x['SHIP_REF_N']} stored photos as head v2 (no mite photos), so the "unfamiliar" rule works as before; only the "other" score is new.

**What it costs, and the setting we ship.** Mite and rust look alike in these photos ({x['SHIP_OTHER_N_CONFLICT_GROUPS']} copy groups even carry both labels). Trained as is, "other" takes many rust photos. Two choices beyond the v2 setup keep that in check: (1) the confidence threshold uses the same 90% rule as v2, checked on healthy, rust and lab photos; (2) a constant is added to the "other" score so that {x['SHIP_OTHER_BUDGET']} of healthy and rust field photos (out-of-fold, chosen without the scored fold) have "other" as top class. Each setting below is cross-validated the same way:

| Setting | Rust leaves named rust | Healthy + rust photos answered | Mite photos sent to the officer | Mite photos answered "rust" (of {x['N_MITE']}) |
|---|---|---|---|---|
| Head v2 (no "other") | {x['SHIP_V2_CV_RUST_NAMED']} | {x['SHIP_V2_CV_COVERAGE']} | {x['SHIP_V2_MITE_NOT_SURE']} | {x['SHIP_V2_MITE_CALLED_RUST']} |
""" + ''.join(f"| {_tr_name(r)} | {pct(r['rust_named'])} | {pct(r['coverage'])} | {pct(r['mite_sent_to_officer_167'])} | {r['mite_called_rust_167']} |\n" for r in TR) + f"""
We ship the {x['SHIP_OTHER_BUDGET']} setting: it names rust on {x['SHIP_CV_RUST_NAMED']} of rust leaves ({x['SHIP_OTHER_DELTA_RUST_NAMED']} points against head v2, lower in {x['SHIP_OTHER_RUST_NAMED_FOLDS_LOWER']} of 5 folds) and cuts mite photos counted as rust from {x['SHIP_V2_MITE_CALLED_RUST']} to {x['SHIP_MITE_CALLED_RUST']}. The {x['SHIP_OTHER_RUST_ROUTED_OTHER']} of rust leaves sent to the officer as "other" are not lost: they wait in the officer's queue and count once labelled. If the team prefers a smaller drop in rust named, the {100 * t_half['other_budget']:g}% setting gives {x['SHIP_OTHER_HALF_RUST_NAMED']} rust named and {x['SHIP_OTHER_HALF_MITE_CALLED_RUST']} mite photos counted as rust. The setting was picked after seeing this table, so the head v3 numbers carry a small selection effect. {NX['budget']}

What "other" does not fix yet (mite photos still counted as rust; one pest from one dataset; officer labels of only healthy and rust photos wear the "other" answer down) is in section {S_['limits']}, with the next step for each. The {x['SHIP_MITE_NOT_SURE']} of mite photos sent to the officer holds before any officer labels.

### 3.3 External test on Ugandan farm photos, and the officer learning loop there
The closest test we have to a new region: {x['UG_N_PHOTOS']} photos of healthy, rust and Phoma leaves from farms in Uganda ({x['UG_N_GROUPS']} distinct leaves after grouping copies; section 2). No Ugandan photo was used for training. One setting, the second familiarity check's cutoff, was chosen on {x['FAM_DEV_SHARE']} of the copy clusters; its clean numbers below come from the other part only. Each group of copies counts once.

**Without officer labels (the app as shipped).**

| Ugandan photos, never trained on | Shipped model (head v3) | 95% interval | Lab-only model |
|---|---|---|---|
| Photos answered (the rest go to the officer) | {x['UG_SHIP_ANSWERED']} | {x['UG_SHIP_ANSWERED_CI']} | {x['UG_LABONLY_ANSWERED']} |
| Answers that are correct | {x['UG_SHIP_ACC_ANSWERED']} | {x['UG_SHIP_ACC_ANSWERED_CI']} | {x['UG_LABONLY_ACC_ANSWERED']} |
| Right if forced to answer every photo | {x['UG_SHIP_FORCED']} | | {x['UG_LABONLY_FORCED']} |
| Sent to the officer because the photo looks unfamiliar | {x['UG_SHIP_NOT_SURE_UNFAMILIAR']} | | {x['UG_LABONLY_NOT_SURE_UNFAMILIAR']} |
| Rust leaves named rust (of all rust leaves) | {x['UG_SHIP_RUST_NAMED']} | {x['UG_SHIP_RUST_NAMED_CI']} | {x['UG_LABONLY_RUST_NAMED']} |
| Phoma leaves named Phoma (of all Phoma leaves) | {x['UG_SHIP_PHOMA_NAMED']} | {x['UG_SHIP_PHOMA_NAMED_CI']} | {x['UG_LABONLY_PHOMA_NAMED']} |
| Phoma leaves answered "rust" (of all Phoma leaves) | {x['UG_SHIP_PHOMA_ANSWERED_RUST']} | | {x['UG_LABONLY_PHOMA_ANSWERED_RUST']} |
| Healthy leaves called a problem (of all healthy leaves) | {x['UG_SHIP_HEALTHY_FLAGGED']} | {x['UG_SHIP_HEALTHY_FLAGGED_CI']} | {x['UG_LABONLY_HEALTHY_FLAGGED']} |

The 95% intervals come from resampling copy groups. What it means: the "not sure" check does its job in a new country. Forced to answer, the shipped model would be right on only {x['UG_SHIP_FORCED']} of Ugandan photos; the app instead sends {x['UG_SHIP_NOT_SURE']} of them to the officer, mostly because they look unlike any stored photo, and calls only {x['UG_SHIP_HEALTHY_FLAGGED']} of healthy leaves a problem. When forced, it calls {x['UG_SHIP_FORCED_RUST_AS_RUST']} of rust leaves rust but only {x['UG_SHIP_FORCED_PHOMA_AS_PHOMA']} of Phoma leaves Phoma ({x['UG_SHIP_FORCED_PHOMA_AS_RUST']} of Phoma leaves would be called rust), so Phoma is the look-alike most likely to reach a rust count here. {NX['phoma']}

**With officer labels, the tool learns the new country and starts answering.** On the part of the Ugandan photos never used to choose any setting ({x['FAM_TEST_GROUPS']} copy groups), with the app's familiarity rule:

| Officer labels | Photos answered | Answers correct | Rust leaves named rust | Phoma leaves named Phoma | Healthy leaves called a problem | Previous rule: answered (correct) |
|---|---|---|---|---|---|---|
""" + ''.join(f"| {k_} | **{x[f'FAM_UG{k_}_ANSWERED_NEW']}** | **{x[f'FAM_UG{k_}_ACC_NEW']}** | {x[f'FAM_UG{k_}_RUST_NAMED_NEW']} | {x[f'FAM_UG{k_}_PHOMA_NAMED_NEW']} | {x[f'FAM_UG{k_}_HEALTHY_FLAGGED_NEW']} | {x[f'FAM_UG{k_}_ANSWERED_CUR']} ({x[f'FAM_UG{k_}_ACC_CUR']}) |\n" for k_ in _ft['ks']) + f"""
"Named" counts only answered photos; a photo sent to the officer counts as not named. Mean of {x['FAM_TEST_SEEDS']} random pool/scored splits and label orders; the dataset's folder labels stand in for the officer.

- **What it means.** After 50 officer labels the tool answers {x['FAM_UG50_ANSWERED_NEW']} of Ugandan photos and is right on {x['FAM_UG50_ACC_NEW']} of them; after 100, it answers {x['FAM_UG100_ANSWERED_NEW']} ({x['FAM_UG100_ACC_NEW']} correct), so the officer labels fewer photos by hand as the tool learns. The photos the new rule adds are right {x['FAM_UG50_ADDED_CORRECT']} of the time after 50 labels and {x['FAM_UG100_ADDED_CORRECT']} after 100. With no labels the two rules are the same ({x['FAM_UG0_ANSWERED_NEW']} answered, {x['FAM_UG0_ACC_NEW']} correct).
- **The rule.** A photo counts as familiar when its 10 nearest stored photos (shipped + officer-labelled) are close, as before, OR when its single nearest officer-labelled photo is within {x['FAM_C1']} (`ood.local_nearest_cutoff` in `model/head.json`; {x['FAM_C1_FRACTION']} × the shipped cutoff). The shipped stored photos never count for the second part, and with no officer labels the app behaves exactly as before. Threshold, temperature, the "other" route and the on-phone refit are unchanged. The previous rule needed 10 close stored photos, which the varied Ugandan photos rarely have: if every other Ugandan photo were stored, {x['UG_FAMILIAR_IF_ALL_UG_STORED']} would count as familiar.
- **How the setting was chosen (written down before the first run).** The Ugandan coarse copy clusters were split at random: {x['FAM_DEV_SHARE']} for choosing ({x['FAM_DEV_GROUPS']} copy groups) and the rest for testing ({x['FAM_TEST_GROUPS']}). Candidates were {x['FAM_FRACTION_MIN']} to {x['FAM_FRACTION_MAX']} × the shipped cutoff; the rule was the largest value for which the photos the new rule adds are at least {x['FAM_FLOOR']} correct at 10, 20, 50 and 100 labels. Every candidate passed; the chosen one's added photos were {x['FAM_DEV_ADDED_CORRECT']} correct. {x['FAM_C1_FRACTION']} × cutoff is the top of the candidate list; larger values were not tested.
- **Checks on other photos (pass/fail gates set in advance).** Ecuador new-region simulation: answers correct {x['FAM_EC10_ACC_CUR']} / {x['FAM_EC20_ACC_CUR']} / {x['FAM_EC50_ACC_CUR']} → {x['FAM_EC10_ACC_NEW']} / {x['FAM_EC20_ACC_NEW']} / {x['FAM_EC50_ACC_NEW']} at 10 / 20 / 50 labels (gate: no drop over 3 points), answered {x['FAM_EC10_ANSWERED_CUR']} / {x['FAM_EC20_ANSWERED_CUR']} / {x['FAM_EC50_ANSWERED_CUR']} → {x['FAM_EC10_ANSWERED_NEW']} / {x['FAM_EC20_ANSWERED_NEW']} / {x['FAM_EC50_ANSWERED_NEW']}. Mite photos with the shipped model: the share sent to the officer drops by {x['FAM_MITE10_DROP']}, {x['FAM_MITE50_DROP']} and {x['FAM_MITE100_DROP']} points at 10, 50 and 100 labels (gate: at most 5); with head v2, which never trained on mite photos, {x['FAM_V2_MITE10_DROP']}, {x['FAM_V2_MITE50_DROP']} and {x['FAM_V2_MITE100_DROP']} points (reported, not a gate). The {x['FAM_HB_N']} picture-card photos: decisions {x['FAM_HB_SAME']} ({x['FAM_HB_ANSWERED']} of {x['FAM_HB_N']} answered under both rules).
- **What it costs.** Healthy leaves called a problem rise from {x['FAM_UG50_HEALTHY_FLAGGED_CUR']} to {x['FAM_UG50_HEALTHY_FLAGGED_NEW']} after 50 labels and from {x['FAM_UG100_HEALTHY_FLAGGED_CUR']} to {x['FAM_UG100_HEALTHY_FLAGGED_NEW']} after 100: roughly double, still under 2%. With few labels the officer still sees most photos ({x['FAM_UG10_ANSWERED_NEW']} answered after 10 labels). With a stricter grouping of near-copies, {x['FAM_UG100_COARSE_ANSWERED_NEW']} are answered after 100 labels, {x['FAM_UG100_COARSE_ACC_NEW']} correctly. {NX['opens']}
- **The head itself learns too.** On all Ugandan photos (both parts; same refit and rule), right if forced rises from {x['UG_LOOP0_FORCED']} to {x['UG_LOOP10_FORCED']} after 10 labels, {x['UG_LOOP50_FORCED']} after 50 and {x['UG_LOOP100_FORCED']} after 100 (coarser grouping: {x['UG_COARSE_LOOP100_FORCED']} after 100). The all-photo numbers with the app rule ({x['UG_LOOP50_ANSWERED']} answered, {x['UG_LOOP50_ACC_ANSWERED']} correct after 50 labels; {x['UG_LOOP100_ANSWERED']} and {x['UG_LOOP100_ACC_ANSWERED']} after 100; {x['UG_LOOP200_ANSWERED']} answered after 200) include the clusters used to choose the cutoff; the table above does not. Starting from the lab-only model: {x['UG_LABONLY_LOOP50_ANSWERED']} answered after 50 labels and {x['UG_LABONLY_LOOP100_ANSWERED']} after 100. The earlier figure of {x['UG_PREVRULE_LOOP100_ANSWERED']} answered after 100 labels ({x['UG_PREVRULE_LOOP100_ACC_ANSWERED']} correct) is the previous rule on all photos.

Figure: `results/figs/uganda_learning_loop.png`. The limits of this test (Uganda, not Kenya; photo style; species; copies; folder labels; settings not tuned for Uganda) are in section {S_['limits']}, each with its next step.
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
### 3.4 People with a picture card vs the shipped AI (one-evening test)
{group.capitalize()}, with no coffee training, labelled the same {ps['n']} field photos using only a picture card (two pictures and one line per problem), on a phone or laptop. The shipped AI was scored on the same photos with the same rule as the app. It was never trained on these photos.

| Who | Photos answered (not "not sure") | Answers correct | Healthy vs problem correct (of answered) | Correct out of all {ps['n']} | Median seconds per photo |
|---|---|---|---|---|---|
"""
    md += ''.join(row_(f"{h['name']} (picture card)", h, sec_(h['median_seconds'])) for h in hum)
    md += row_('**AI as shipped** (head v3: lab + field photos + "other")', aiS, '—')
    md += row_('Reference: head v2 (lab + field photos, five classes)', aiS2, '—')
    md += row_('Context: lab-only AI, no field labels (new-region simulation)', ai0, '—')
    md += row_('Context: lab-only AI after 50 officer-style field labels', ai1, '—')
    md += '\nRight answer by true class, out of all photos of that class ("not sure" counts as not right):\n\n' + lvl_head
    md += ''.join(lvl_row(h['name'], h) for h in hum) + lvl_row('AI as shipped', aiS) + lvl_row('Reference: head v2', aiS2) + lvl_row('Context: lab-only AI after 50 labels', ai1)
    md += f"""
What it means: with only the card, both people told sick leaves from healthy ones well ({x['HB_HUMAN_HVP']} of answers) but named rust on only {x['HB_RUST_NAMED_HUMAN']} of the {x['SHIP_HB_N_RUST']} rust photos; they often chose "brown eye spot" ({x['HB_CERCOSPORA_ANSWERS']} times each). The shipped AI named rust on **{x['SHIP_HB_RUST_NAMED']} of {x['SHIP_HB_N_RUST']}** (head v2: {x['SHIP_V2_HB_RUST_NAMED']}), called {x['SHIP_HB_HEALTHY_CALLED_PROBLEM']} of {x['SHIP_HB_N_HEALTHY']} healthy leaves a problem, and sent {x['SHIP_HB_NOT_SURE']} of photos to the officer instead of guessing. The two people gave the same answer on {x.get('HB_AGREE_SAME')} of photos. A card is enough to notice that something is wrong; the AI adds a consistent rust label, which is what a village rust count needs.

How "right" is decided: every RoCoLe photo carries the dataset authors' label (healthy, or rust at level 1 to 4). "Named rust" means the answer "rust" on a photo the authors labelled rust; the five answer options were the same for people and AI (healthy, rust, leaf miner, brown eye spot, Phoma, plus "not sure"). The AI's "other" answer counts as "not sure" here, because the app shows it that way. People saw copies resized to 900 px and the AI used the originals; on the resized copies the shipped AI makes the same decision on {same.get('shipped')} of {ps['n']} photos.

What this test is and is not:
- {group.capitalize()} (not farmers or plant experts, standing in for relay farmers) labelled {ps['n']} photos from one dataset (RoCoLe: Ecuador, robusta, on-plant; {ps['healthy']} healthy and {sum(rl.values())} rust at levels 1 to 4: {', '.join(str(v) for v in rl.values())} photos) in one evening. Relay farmers trained by the cooperative may do better. {NX['card']}
- The shipped AI has seen field photos of healthy, rust and red-spider-mite leaves from this dataset (never these {ps['n']}); the people saw only lab-style pictures on the card. {NX['card_field']}
- The lab-only rows are context from the new-region simulation; one of the {ps['n']} photos is an identical copy of a photo in its 50-label update. {NX['card_copy']}
"""
md += f"""
### 3.5 Village ranking (simulation at the shipped model's error rates)
Synthetic villages; the classifier's error rates are the shipped model's cross-validated rates (answers {x['SHIP_VILLAGE_COVERAGE']} of photos; calls {x['SHIP_VILLAGE_SENS']} of answered rust photos rust and {x['SHIP_VILLAGE_FPR']} of answered healthy photos rust). It ranks rust already seen; it does not predict outbreaks. Across 40 villages per round with about {x['SHIP_VILLAGE_HOT']} real outbreaks (rust share above 25%):

| Rule | False alarms per round | Missed outbreaks per round | Real outbreaks among the 5 villages visited first |
|---|---|---|---|
| Raw share of rust photos | {x['SHIP_VILLAGE_FA_RAW']} | {x['SHIP_VILLAGE_MISS_RAW']} | {x['SHIP_VILLAGE_TOP5_RAW']} |
| Small-sample adjusted (the app's rule: alert when P(share > 25%) > 0.5) | {x['SHIP_VILLAGE_FA_ADJ']} | {x['SHIP_VILLAGE_MISS_ADJ']} | {x['SHIP_VILLAGE_TOP5_ADJ']} |

The adjustment cuts false alarms ({x['SHIP_VILLAGE_FA_RAW']} → {x['SHIP_VILLAGE_FA_ADJ']}) and sends the officer to more real outbreaks first ({x['SHIP_VILLAGE_TOP5_RAW']} → {x['SHIP_VILLAGE_TOP5_ADJ']} of 5). It misses more villages that sit near the 25% line ({x['SHIP_VILLAGE_MISS_RAW']} → {x['SHIP_VILLAGE_MISS_ADJ']}); those villages still appear in the ranked list, just below the alert line. At head v2's error rates the same comparison gives {VS2['raw']['false_alarms']:.1f} → {VS2['shrunk']['false_alarms']:.1f} false alarms and {VS2['raw']['missed']:.1f} → {VS2['shrunk']['missed']:.1f} misses; with the lab-only model after 50 labels (a less accurate operating point), {x['VILLAGE_FA_RAW']} → {x['VILLAGE_FA_ADJ']} false alarms and {x['VILLAGE_MISS_RAW']} → {x['VILLAGE_MISS_ADJ']} misses. The villages are synthetic and hold only healthy and rust leaves, so this table does not show the main gain of the "other" answer (fewer mite photos counted as rust, section {S_['route']}). {NX['village']}

### 3.6 Why the shipped model trains on field photos (the lab-only result)
This is the finding that shaped the design. Trained on lab photos only, the head is right {x['LAB_ACC']} of the time on held-out lab photos but only **{x['FIELD_ACC_NO_ABSTAIN']}** on field photos if forced to answer, while reporting **{x['FIELD_MEAN_CONFIDENCE']}** average confidence (it calls almost every field leaf Phoma). Its confidence gives no warning (AUROC {x['AUROC_CONFIDENCE']}); comparing each photo with the stored training photos does (AUROC {x['AUROC_KNN']}), and the app says "not sure" to {x['FIELD_NOT_SURE']} of those field photos instead of guessing.

Three design choices follow from it:
- **Train on photos taken the way relay farmers will take them.** Adding field photos to training lifts forced field accuracy to {x['SHIP_CV_ACC']} (cross-validated), and lab accuracy stays at {x['SHIP_LAB_ACC']}.
- **Keep the familiarity check for photo styles the model has not seen.** It did the same job on the Ugandan photos (section {S_['ug']}).
- **Let the officer's labels adapt the model.** We simulate a new region by starting from the lab-only model and treating the field photos as the new region's photos. When the officer labels photos, the head is refit on the phone (pulled toward the starting model) and the labelled photos join the familiarity reference:

| Officer labels | Photos answered | Answers correct | Answers correct, local labels only (no starting model) |
|---|---|---|---|
""" + '\n'.join(f"| {k} | {pct(pa['coverage'][i])} | {'—' if pa['acc_answered'][i] is None else pct(pa['acc_answered'][i])} | {'—' if lo['acc_answered'][i] is None else pct(lo['acc_answered'][i])} |" for i, k in enumerate(ks)) + f"""

After 50 labels the tool answers {x['COV_50']} of the new region's photos, {x['ACC_ANS_50']} correctly. A starting model matters most when labels are few ({x['ACC_ANS_10']} vs {x['ACC_ANS_10_LOCAL_ONLY']} correct at 10 labels). An update to share with other phones is ~{x['UPDATE_KB_HEAD']} KB for the head plus {x['UPDATE_BYTES_PER_PHOTO']} bytes per labelled photo. These numbers use the app's familiarity rule, including the nearest-officer-photo check; with the previous rule (10 nearest stored photos only) the tool answered {x['COV_10_PREV']} after 10 labels and {x['COV_50_PREV']} after 50 ({x['ACC_ANS_50_PREV']} correct). On the more varied Ugandan photos the check opens more slowly (section {S_['ug']}).
"""
if alt:
    md += f"""
### 3.7 Size vs accuracy
In the new-region setting (lab-only training, no field labels), a 5x larger backbone (DINOv2-small, 21.6M parameters, ~87 MB) is right {x['DINO_FIELD_ACC']} of the time on field photos (vs {x['FIELD_ACC_NO_ABSTAIN']} for MobileNetV3); after 50 labels it answers {x['DINO_COV_50']} of photos with {x['DINO_ACC_ANS_50']} correct. Training the small backbone on field photos does better than that ({x['SHIP_CV_ACC']} forced accuracy, cross-validated), so we ship the {x['MODEL_MB']} MB backbone that fits the side-loading constraint. A larger backbone remains an option where phones allow it.
"""
md += f"""
### 3.8 Remaining limits and the next step for each
**Where the evidence comes from**
- **No Kenyan farm photos yet.** Field training photos are Ecuadorian robusta (RoCoLe); the external test is from Uganda (healthy, rust, Phoma). None comes from Kenyan farms, where the tool would be used. {NX['kenya']}
- **No plant IDs in RoCoLe.** Leaves of one plant can sit in both a training and a test fold, so the cross-validated numbers may be optimistic. We keep identical and near-identical images on one side of every split, and the 60 picture-card photos give a second check. {NX['plant']}
- **Labels come from the dataset authors.** RoCoLe's labels and the Ugandan folder labels stand in for an extension officer, in the cross-validation and in both learning loops. Some photos in the Ugandan Phoma folder show rust-like orange spots, so some label noise likely remains after dropping the {x['UG_N_CONFLICT']} photos with a copy in another folder. {NX['labels']}
- **RoCoLe copy groups with two labels are dropped.** {x['SHIP_OTHER_N_CONFLICT_GROUPS']} groups of identical or near-identical RoCoLe images carry two labels (mostly mite and rust). They are out of training and out of the cross-validation; their {x['SHIP_OTHER_N_CONFLICT_MITE']} mite photos are scored only in the {x['N_MITE']}-photo count of section {S_['route']}. {NX['conflict']}
- **Copies in the Ugandan photos.** We group copies by image similarity; copies that were also cropped or strongly brightened can escape the grouping, so a few near-copies may sit in both the pool and the test half of the learning loop. The stricter grouping (section {S_['ug']}) shows how much this matters: on the Ugandan test part, {x['FAM_UG100_COARSE_ANSWERED_NEW']} answered after 100 labels ({x['FAM_UG100_COARSE_ACC_NEW']} correct) against {x['FAM_UG100_ANSWERED_NEW']} ({x['FAM_UG100_ACC_NEW']}). {NX['ug_copies']}
- **Ugandan photo style.** Close-ups of single leaves on the plant, outdoors in daylight, stored at 256 × 256 px; a check by eye of about 70 photos found a few with soil behind the leaf, so some may be fallen or held leaves. The phone sees full-size photos framed by a relay farmer. {NX['ug_style']}
- **Coffee species in the Ugandan photos is not stated** (Uganda grows robusta and arabica). {NX['species']}

**What the tool does in a new region**
- **With few officer labels, the officer still sees most photos in a new region.** On the Ugandan test part the app answers {x['FAM_UG10_ANSWERED_NEW']} of photos after 10 labels and {x['FAM_UG50_ANSWERED_NEW']} after 50 (Ecuador simulation: {x['COV_50']} after 50). The second familiarity check that opens it was chosen on Ugandan photos (a separate part) and checked on Ecuador and mite photos, not on Kenyan photos; it roughly doubles healthy leaves called a problem ({x['FAM_UG100_HEALTHY_FLAGGED_CUR']} → {x['FAM_UG100_HEALTHY_FLAGGED_NEW']} after 100 labels). {NX['opens']}
- **Phoma reaches the rust count in Uganda.** {x['UG_SHIP_PHOMA_ANSWERED_RUST']} of Ugandan Phoma leaves are answered "rust", against {x['UG_SHIP_PHOMA_NAMED']} named Phoma; if forced, {x['UG_SHIP_FORCED_PHOMA_AS_RUST']} would be called rust. The shipped head has seen Phoma only in lab photos. {NX['phoma']}
- **Settings not tuned for a new region.** The learning-step strength (how hard the on-phone update pulls toward the shipped head), the answer threshold and the familiarity cutoff are the shipped values; none was tuned on Ugandan or Kenyan photos. {NX['tune']}

**Problems outside the five classes**
- **Mite photos still reach the rust count.** {x['SHIP_MITE_CALLED_RUST']} of {x['N_MITE']} mite photos are still answered "rust", and the demo's mite sample is answered "{x['SHIP_DEMO_MITE_CALLED']}". In the app now: 1 in 10 answered photos also goes to the officer as a spot check, the officer's "Different problem (not in list)" label trains the "other" class in the on-phone update, and the plot card never says a plot is disease-free. {NX['mite_rust']}
- **Officer labels of only healthy and rust photos wear down the "other" answer** (found by the mite test of the familiarity rule; not caused by that rule). With the shipped head and no labels, {x['FAM_MITE0_SENT']} of the {x['N_MITE']} mite photos go to the officer (flattering: head v3 trained on {x['SHIP_OTHER_N_TRAIN']} of them; the fair figure is {x['SHIP_MITE_NOT_SURE']}, section {S_['route']}). After 10 officer labels of healthy and rust photos it is {x['FAM_MITE10_SENT_CUR']}, after 100 {x['FAM_MITE100_SENT_CUR']}; most of the rest are answered "rust" ({x['FAM_MITE10_RUST_CUR']} after 10 labels, {x['FAM_MITE100_RUST_CUR']} after 100). The cause is the head refit, not the added photos: refitting alone gives {x['FAM_MITE10_REFIT_ONLY']} / {x['FAM_MITE50_REFIT_ONLY']} / {x['FAM_MITE100_REFIT_ONLY']} after 10 / 50 / 100 labels; adding the photos without refitting stays at {x['FAM_MITE10_ROWS_ONLY']}. So the {x['SHIP_MITE_NOT_SURE']} figure holds only before any officer labels; the officer's spot check and "Different problem" labels remain the safeguard. {NX['other_refit']}
- **"Other" knows one pest from one dataset** (red spider mite, Ecuadorian robusta). Brown eye spot in the field, other pests and nutrient deficiency are not in it. Without "other", photos of an untaught problem are no longer caught once field photos are familiar: the lab-only model after 50 field labels says "not sure" to only {x['LABONLY_MITE_NOT_SURE_AFTER_50']} of mite photos. {NX['other_scope']}
- **A few "Different problem" labels can swing the on-phone update** (found in a browser check on the {x['SHIP_DEMO_N']} demo photos, 3 Oct; not part of this pipeline). An update built from one "Different problem" label and no healthy label sent the healthy demo photos to the officer as "looks like a different problem"; with one healthy and one rust label added, every demo photo came back as before. This errs toward the officer (more photos queued), not toward a wrong answer. {NX['dp_update']}
- **Two choices beyond the v2 setup, one picked after seeing results** (section {S_['route']}): the threshold rule is checked on healthy, rust and lab photos only, and a constant on the "other" score sends {x['SHIP_OTHER_BUDGET']} of healthy and rust photos to "other". The {x['SHIP_OTHER_BUDGET']} value was picked after seeing the cross-validated trade-off, so the head v3 numbers carry a small selection effect. {NX['budget']}

**Simulations and small tests**
- **The village ranking is a simulation** with synthetic villages; only the classifier's error rates are measured. {NX['village']}
- **The picture-card test** used {(group if HB else 'team members')} for one evening, on 60 RoCoLe photos. {NX['card']}
- **Phone speed is not measured**; the ~{x['LATENCY_MS_LAPTOP']} ms per photo is on a laptop CPU. {NX['phone']}
"""
open(os.path.join(RES, 'RESULTS.md'), 'w').write(md)
print(md[:800]); print('numbers.json keys:', len(N), '| new SHIP_/LABONLY_/RO_ keys:', len(NS), '| UG_ keys:', len(NU))
