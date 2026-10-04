"""Fill {{KEY}} placeholders in docs/templates/*.tmpl.md from results/numbers.json (numbers are never typed by hand).
Placeholders the team must fill (URLs, names, licence) are left visible as {{KEY}}.
FIRST_LOAD_MB is computed here from the real sizes of the files sw.js saves for offline use.
Run: ../.venv/bin/python ml/fill_docs.py
Also fill any other file (keys not in numbers.json, such as {{IMG_*}}, stay as they are):
     ../.venv/bin/python ml/fill_docs.py --also SOURCE OUTPUT"""
import os, re, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(HERE)
N = json.load(open(os.path.join(REPO, 'results', 'numbers.json')))


def first_load_mb():
    """Bytes the service worker downloads on the first visit: CORE + the reference file named in head.json
    + OPTIONAL + the sample photos + the audio files named in answers.json (same rules as precache() in sw.js)."""
    sw = open(os.path.join(REPO, 'sw.js')).read()
    def arr(name):
        m = re.search(r'const %s = \[(.*?)\];' % name, sw, re.S)
        return re.findall(r"'([^']+)'", m.group(1)) if m else []
    paths = ['index.html' if p == './' else p for p in arr('CORE')]
    head = json.load(open(os.path.join(REPO, 'model', 'head.json')))
    paths.append('model/' + head['ood']['reference']['file'])
    paths += arr('OPTIONAL')
    try:
        paths += ['samples/' + s['file'] for s in json.load(open(os.path.join(REPO, 'samples', 'manifest.json')))['samples']]
    except (OSError, KeyError, ValueError):
        pass
    try:
        a = json.load(open(os.path.join(REPO, 'answers.json'))); a = a.get('answers', a)
        paths += sorted({p for e in a.values() if isinstance(e, dict) and isinstance(e.get('audio'), dict)
                         for p in e['audio'].values() if isinstance(p, str) and p})
    except (OSError, ValueError):
        pass
    total = sum(os.path.getsize(os.path.join(REPO, p)) for p in paths if os.path.exists(os.path.join(REPO, p)))
    return str(round(total / 1e6))


def guide_counts():
    """Counts for the "What does this mean?" guides, read from guides.json: guides, sections, and the machine
    back-translation marks of the Swahili ('ok' / 'check'; docs/GUIDES.md explains them)."""
    try:
        g = json.load(open(os.path.join(REPO, 'guides.json')))['guides']
    except (OSError, KeyError, ValueError):
        return {}
    secs = [s for v in g.values() for s in v.get('sections', [])]
    return {'GUIDES_N': str(len(g)), 'GUIDES_N_SECTIONS': str(len(secs)),
            'GUIDES_SW_OK': str(sum(s.get('sw_backtranslation_match') == 'ok' for s in secs)),
            'GUIDES_SW_CHECK': str(sum(s.get('sw_backtranslation_match') == 'check' for s in secs))}


N['FIRST_LOAD_MB'] = first_load_mb()
N.update(guide_counts())
# Team decisions (not computed). Leave a key out to keep its {{KEY}} visible for the team.
# Product name since 4 Oct: "Majani Relay" (user-facing text only; internal identifiers such as the folder name
# kahawa-check, the database name and lib/kahawa-core.js stay as they are, so saved data keeps working).
TEAM_DECISIONS = {
    'CODE_LICENCE': 'MIT (see LICENSE)',
    'REPO_URL': 'https://github.com/git-lsd/majani-relay',
    'APP_URL': 'https://git-lsd.github.io/majani-relay/',
    'TEAMMATE': 'Yicong Li',
}
N.update(TEAM_DECISIONS)
# Links inside the templates are written relative to where the filled file lands (repo root for README, docs/ otherwise).
OUT = {
    'README.tmpl.md': 'README.md',
    'VIDEO_SCRIPTS.tmpl.md': 'docs/VIDEO_SCRIPTS.md',
    'ONE_PAGER.tmpl.md': 'docs/ONE_PAGER.md',
    'PILOT_PLAN.tmpl.md': 'docs/PILOT_PLAN.md',
    'RESPONSIBLE_AI.tmpl.md': 'docs/RESPONSIBLE_AI.md',
    'DATA_CARD.tmpl.md': 'docs/DATA_CARD.md',
    'PRIOR_ART.tmpl.md': 'docs/PRIOR_ART.md',
    'HANDOFF.tmpl.md': 'docs/HANDOFF.md',
    'WHY.tmpl.md': 'docs/WHY.md',
}
KEY = re.compile(r'\{\{([A-Z0-9_]+)\}\}')


def fill(text):
    return KEY.sub(lambda m: N.get(m.group(1), m.group(0)), text)


if len(sys.argv) == 4 and sys.argv[1] == '--also':
    s = fill(open(sys.argv[2]).read())
    open(sys.argv[3], 'w').write(s)
    print(sys.argv[3], 'left as placeholders:', sorted(set(KEY.findall(s))))
    sys.exit(0)

print('FIRST_LOAD_MB =', N['FIRST_LOAD_MB'])
for t, o in OUT.items():
    src = os.path.join(REPO, 'docs', 'templates', t)
    if not os.path.exists(src):
        print('missing template:', t); continue
    s = fill(open(src).read())
    open(os.path.join(REPO, o), 'w').write(s)
    print(o, 'left for the team:', sorted(set(KEY.findall(s))))
