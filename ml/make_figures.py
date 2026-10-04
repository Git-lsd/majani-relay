"""Figures for the README and videos, from results/metrics.json and results/human_baseline.json.
Shipped (lab + field) model: field_cv.png, picture_card_vs_ai.png, village_alert.png.
New-region simulation (lab-only model): learning_loop.png, not_sure_signals.png.
Run: ../.venv/bin/python ml/make_figures.py"""
import os, json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(HERE)
RES = os.path.join(REPO, 'results'); FIG = os.path.join(RES, 'figs'); os.makedirs(FIG, exist_ok=True)
M = json.load(open(os.path.join(RES, 'metrics.json')))
LO = M['lab_only_new_region_simulation']; SH = M['shipped']

# reference palette (validated slots 1-3, light mode) + text tokens
S1, S2, S3 = '#2a78d6', '#eb6834', '#1baf7a'
SURF, INK, INK2, GRID = '#fcfcfb', '#0b0b0b', '#52514e', '#e4e3df'
plt.rcParams.update({'figure.facecolor': SURF, 'axes.facecolor': SURF, 'savefig.facecolor': SURF,
                     'axes.edgecolor': GRID, 'axes.labelcolor': INK2, 'xtick.color': INK2, 'ytick.color': INK2,
                     'text.color': INK, 'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': 0.8, 'lines.linewidth': 2})


def label_end(ax, x, y, text, color_ink=INK):
    ax.annotate(text, (x, y), xytext=(6, 0), textcoords='offset points', va='center', fontsize=10, color=color_ink)


# 1) the learning loop: share answered and accuracy of answers vs officer labels (lab model as prior)
L = LO['learning_loop']; ks = L['ks']; c = L['curves']['prior_adapt']; lo = L['curves']['local_only']
fig, axes = plt.subplots(1, 2, figsize=(10, 4.0))
ax = axes[0]
cov = [v * 100 for v in c['coverage']]
ax.plot(ks, cov, color=S1, marker='o', markersize=6, markeredgecolor=SURF, markeredgewidth=2)
for k, v in zip(ks, cov):
    if k in (0, 10, 50, 200):
        ax.annotate(f'{v:.0f}%', (k, v), xytext=(0, 8), textcoords='offset points', ha='center', fontsize=9, color=INK)
ax.set_xlabel('New-region photos labelled by the officer'); ax.set_ylabel('New-region photos the tool answers (%)')
ax.set_ylim(0, 108); ax.set_xlim(-8, 210)
ax.set_title('It answers more as it learns local photos', loc='left', fontsize=11)
ax = axes[1]
for cur, col, name in [(c, S1, 'Starts from the lab-only model'), (lo, S2, 'Local labels only')]:
    xs = [k for k, v in zip(ks, cur['acc_answered']) if k > 0 and v is not None]
    ys = [v * 100 for k, v in zip(ks, cur['acc_answered']) if k > 0 and v is not None]
    ax.plot(xs, ys, color=col, marker='o', markersize=6, markeredgecolor=SURF, markeredgewidth=2)
    dy = 10 if col == S1 else -14
    ax.annotate(name, (xs[0], ys[0]), xytext=(8, dy), textcoords='offset points', fontsize=10, color=INK)
ax.set_xlabel('New-region photos labelled by the officer'); ax.set_ylabel('Answers that are correct (%)')
ax.set_ylim(50, 100); ax.set_xlim(-8, 210)
ax.set_title('A starting model helps most with few labels', loc='left', fontsize=11)
fig.suptitle('New-region simulation: the lab-only model meets field photos.\nBefore any local labels it says "not sure" to '
             f"{100 * (1 - LO['field']['coverage']):.1f}% of them instead of guessing", x=0.01, ha='left', fontsize=12)
fig.tight_layout(); fig.savefig(os.path.join(FIG, 'learning_loop.png'), dpi=200); plt.close(fig)

# 2) why confidence alone is not a safe 'not sure' signal: AUROC of three signals (field vs held-out lab photos)
A = LO['ood_auroc_field_vs_heldout']
fig, ax = plt.subplots(figsize=(9, 3.2))
names = ['Model confidence', 'Distance to class average', 'Distance to nearest\nstored photos (used)']
vals = [A['max_softmax'], A['centroid_cosine'], A['knn10_cosine (used)']]
bars = ax.barh(names, vals, color=[S2, S2, S1], height=0.55)
for b_, v in zip(bars, vals):
    ax.annotate(f'{v:.2f}', (v, b_.get_y() + b_.get_height() / 2), xytext=(4, 0), textcoords='offset points',
                va='center', fontsize=9, color=INK)
ax.axvline(0.5, color=INK2, linewidth=1, linestyle=':')
ax.set_xlim(0, 1.08); ax.set_xlabel('Tells a new photo style (field) apart from the training style (lab) (AUROC, 0.5 = chance;\nbelow 0.5 = the model is MORE confident on the new style)')
ax.grid(axis='y', visible=False)
ax.set_title('New-region simulation: only the stored-photo check\nnotices an unfamiliar photo style', loc='left', fontsize=12)
fig.tight_layout(); fig.savefig(os.path.join(FIG, 'not_sure_signals.png'), dpi=200); plt.close(fig)

# 3) village early warning: raw shares vs shrunk estimates (synthetic villages, measured error rates)
V = M['village_sim']
fig, ax = plt.subplots(figsize=(8, 4.2))
cats = ['False alarms\nper round', 'Missed outbreaks\nper round', 'True outbreaks among\ntop-5 villages to visit']
keys = ['false_alarms', 'missed', 'top5_hits']
import numpy as np
x = np.arange(len(cats)); w = 0.36
for i, (s, col, name) in enumerate([('raw', S2, 'Raw share of rust photos'), ('shrunk', S1, 'Small-sample adjusted (empirical Bayes)')]):
    vals = [V[s][k] for k in keys]
    bars = ax.bar(x + (i - 0.5) * (w + 0.02), vals, w, color=col, label=name)
    for b_, v in zip(bars, vals):
        ax.annotate(f'{v:.1f}', (b_.get_x() + b_.get_width() / 2, v), xytext=(0, 3), textcoords='offset points',
                    ha='center', fontsize=9, color=INK)
ax.set_xticks(x); ax.set_xticklabels(cats); ax.grid(axis='x', visible=False)
ax.legend(frameon=False, fontsize=9, loc='upper right', ncol=1)
ax.set_title('Co-op early warning, 40 simulated villages per round\n(synthetic villages; error rates of the shipped model, cross-validated on field photos)', loc='left', fontsize=11)
ax.set_ylim(0, 1.3 * max(V[s][k] for s in ('raw', 'shrunk') for k in keys))
fig.tight_layout(); fig.savefig(os.path.join(FIG, 'village_alert.png'), dpi=200); plt.close(fig)

# 4) the shipped model on field photos it was not trained on (5-fold cross-validation, mean and spread across folds)
CVs = SH['field_cv']['summary']
items = [('Field photos answered\n(not "not sure")', 'coverage'), ('Answers that are correct', 'acc_answered'),
         ('Rust leaves named rust\n(of all rust leaves)', 'rust_named'),
         ('Healthy leaves called a problem\n(of all healthy leaves)', 'healthy_flagged')]
fig, ax = plt.subplots(figsize=(9, 3.6))
ys = np.arange(len(items))[::-1]
vals = [100 * CVs[k] for _, k in items]; sds = [100 * CVs[k + '_sd'] for _, k in items]
bars = ax.barh(ys, vals, height=0.5, color=[S1, S1, S1, S2])
ax.errorbar(vals, ys, xerr=sds, fmt='none', ecolor=INK2, elinewidth=1.2, capsize=3)
for y_, v, sd_ in zip(ys, vals, sds):
    ax.annotate(f'{v:.0f}%', (v + sd_, y_), xytext=(6, 0), textcoords='offset points', va='center', fontsize=10, color=INK)
ax.set_yticks(ys); ax.set_yticklabels([t for t, _ in items]); ax.set_xlim(0, 110); ax.grid(axis='y', visible=False)
ax.set_xlabel('% of field photos (bar = mean of 5 folds; line = spread across folds)')
ax.set_title(f"Shipped model (lab + field photos) on field photos it was not trained on\n"
             f"(5-fold cross-validation over {sum(CVs['n_per_fold'])} RoCoLe photos)", loc='left', fontsize=11)
fig.tight_layout(); fig.savefig(os.path.join(FIG, 'field_cv.png'), dpi=200); plt.close(fig)

# 5) picture card vs shipped AI on the same 60 photos (never trained on): rust named, healthy called a problem
HBP = os.path.join(RES, 'human_baseline.json')
if os.path.exists(HBP):
    HB = json.load(open(HBP))
    who = [(h['name'] + '\n(picture card)', h, S2) for h in HB['labellers']]
    who.append(('AI as shipped', HB['model']['shipped_v2_lab_field'], S1))
    rust_n = lambda r: sum(round(v['correct_of_all'] * v['n']) for k, v in r['by_rust_level'].items() if k != '0')
    n_rust = sum(v['n'] for k, v in who[-1][1]['by_rust_level'].items() if k != '0')
    hz = who[-1][1]['by_rust_level']['0']; n_h = hz['n']
    healthy_p = lambda r: round(r['by_rust_level']['0']['called_a_problem_of_all'] * r['by_rust_level']['0']['n'])
    notsure = lambda r: r['answer_counts'].get('not_sure', 0)
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.4), sharey=True)
    ys = np.arange(len(who))[::-1]
    for ax, fn, n_, ttl in [(axes[0], rust_n, n_rust, f'Rust leaves named rust (of {n_rust})'),
                            (axes[1], healthy_p, n_h, f'Healthy leaves called a problem (of {n_h})')]:
        v = [fn(r) for _, r, _ in who]
        ax.barh(ys, v, height=0.5, color=[c_ for _, _, c_ in who])
        for y_, vv in zip(ys, v):
            ax.annotate(str(vv), (vv, y_), xytext=(5, 0), textcoords='offset points', va='center', fontsize=10, color=INK)
        ax.set_xlim(0, n_ * 1.12); ax.grid(axis='y', visible=False); ax.set_title(ttl, loc='left', fontsize=11)
    axes[0].set_yticks(ys); axes[0].set_yticklabels([w for w, _, _ in who])
    fig.suptitle(f"Same {HB['photo_set']['n']} field photos (RoCoLe; authors' labels). The AI sends "
                 f"{notsure(who[-1][1])} of {HB['photo_set']['n']} to the officer as \"not sure\".",
                 x=0.01, ha='left', fontsize=11)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, 'picture_card_vs_ai.png'), dpi=200); plt.close(fig)
print('figures written to', FIG)
