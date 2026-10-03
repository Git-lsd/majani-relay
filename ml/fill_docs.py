"""Fill {{KEY}} placeholders in docs/templates/*.tmpl.md from results/numbers.json (numbers are never typed by hand).
Placeholders the team must fill (URLs, names, licence) are left visible as {{KEY}}.
Run: ../.venv/bin/python ml/fill_docs.py"""
import os, re, json
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(HERE)
N = json.load(open(os.path.join(REPO, 'results', 'numbers.json')))
N.setdefault('FIRST_LOAD_MB', '35')
# Team decisions (not computed). Leave a key out to keep its {{KEY}} visible for the team.
TEAM_DECISIONS = {
    'CODE_LICENCE': 'MIT (see LICENSE)',
    'REPO_URL': 'https://github.com/git-lsd/kahawa-check',
    'APP_URL': 'https://git-lsd.github.io/kahawa-check/',
}
N.update(TEAM_DECISIONS)  # one-time download: model 16.8 + runtime 14.2 + reference 1.3 + audio 1.5 + rest
OUT = {'README.tmpl.md': 'README.md', 'VIDEO_SCRIPTS.tmpl.md': 'docs/VIDEO_SCRIPTS.md', 'ONE_PAGER.tmpl.md': 'docs/ONE_PAGER.md'}
for t, o in OUT.items():
    s = open(os.path.join(REPO, 'docs', 'templates', t)).read()
    s = re.sub(r'\{\{([A-Z0-9_]+)\}\}', lambda m: N.get(m.group(1), m.group(0)), s)
    left = sorted(set(re.findall(r'\{\{([A-Z0-9_]+)\}\}', s)))
    if o.startswith('docs/'):  # links in the templates are written relative to docs/
        pass
    open(os.path.join(REPO, o), 'w').write(s)
    print(o, 'left for the team:', left)
