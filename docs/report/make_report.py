"""Build the one-page report: docs/Majani_Relay_1-page_report.pdf.

Every result number comes from results/numbers.json at build time ({{KEY}} placeholders, same rule as ml/fill_docs.py).
FIRST_LOAD_MB is computed with the first_load_mb() function from ml/fill_docs.py (read from that file, not run as a script).
Steps: fill the HTML template -> docs/report/report.html -> print to PDF with headless Chrome (US Letter, one page).
Run: ../../../.venv/bin/python docs/report/make_report.py   (from the repo root: ../.venv/bin/python docs/report/make_report.py)
"""
import ast, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
HTML = os.path.join(HERE, 'report.html')
PDF = os.path.join(REPO, 'docs', 'Majani_Relay_1-page_report.pdf')
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

N = json.load(open(os.path.join(REPO, 'results', 'numbers.json')))


def first_load_mb():
    """Run only the first_load_mb() function of ml/fill_docs.py (that script writes docs when run, so it is not imported)."""
    src = open(os.path.join(REPO, 'ml', 'fill_docs.py')).read()
    fn = next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == 'first_load_mb')
    env = {'os': os, 're': re, 'json': json, 'REPO': REPO}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), 'fill_docs.first_load_mb', 'exec'), env)
    return env['first_load_mb']()


N['FIRST_LOAD_MB'] = first_load_mb()
N['APP_URL'] = 'https://git-lsd.github.io/majani-relay/'
N['REPO_URL'] = 'https://github.com/Git-lsd/majani-relay'

KEY = re.compile(r'\{\{([A-Z0-9_]+)\}\}')

TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Majani Relay: one-page report</title>
<style>
@font-face { font-family: "Fraunces"; font-weight: 600; src: url(../../fonts/fraunces-latin-600-normal.woff2) format("woff2"); }
@font-face { font-family: "IBM Plex Sans"; font-weight: 400; src: url(../../fonts/ibm-plex-sans-latin-400-normal.woff2) format("woff2"); }
@font-face { font-family: "IBM Plex Sans"; font-weight: 600; src: url(../../fonts/ibm-plex-sans-latin-600-normal.woff2) format("woff2"); }
:root {
  --paper: #f6f1e7; --ink: #231c15; --muted: #685b4e; --card: #fffcf6; --line: #dcd1be;
  --leaf: #2f5d3e; --amber: #a8681a;
}
@page { size: 8.5in 11in; margin: 0; }
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: 8.5in; height: 11in; }
body {
  position: relative;
  background: var(--paper); color: var(--ink);
  font-family: "IBM Plex Sans", sans-serif; font-size: 9.8pt; line-height: 1.26;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
  padding: 0.36in 0.42in 0;
  overflow: hidden;
}
b, strong { font-weight: 600; }
a { color: var(--leaf); text-decoration: none; }

header { border-top: 4px solid var(--ink); padding-top: 6pt; margin-bottom: 8pt; }
.toprow { display: flex; justify-content: space-between; align-items: flex-end; gap: 12pt; }
h1 { font-family: "Fraunces", serif; font-weight: 600; font-size: 28pt; line-height: 1; letter-spacing: -0.2pt; }
.track { color: var(--amber); font-weight: 600; letter-spacing: 0.5pt; text-transform: uppercase; font-size: 7.8pt; text-align: right; line-height: 1.4; }
.tagline { font-family: "Fraunces", serif; font-size: 13pt; color: var(--leaf); margin-top: 3pt; }
.meta { font-size: 8.6pt; color: var(--muted); text-align: right; line-height: 1.38; white-space: nowrap; }
.meta .team { color: var(--ink); font-weight: 600; }

section { margin-bottom: 6pt; }
h2 {
  font-family: "Fraunces", serif; font-weight: 600; font-size: 11.8pt; line-height: 1.15;
  border-bottom: 1px solid var(--line); padding-bottom: 2pt; margin-bottom: 4pt;
  display: flex; align-items: baseline; gap: 5pt;
}
h2 .n { font-family: "IBM Plex Sans", sans-serif; font-size: 7.8pt; font-weight: 600; color: var(--amber); letter-spacing: 0.4pt; }
.cols { display: grid; grid-template-columns: 1.05fr 0.95fr; gap: 0 0.26in; }
ul { list-style: none; }
li { position: relative; padding-left: 10pt; margin-top: 2pt; }
li:first-child { margin-top: 0; }
li::before { content: ""; position: absolute; left: 1pt; top: 0.5em; width: 4pt; height: 4pt; background: var(--leaf); }
li.amber::before { background: var(--amber); }
.label { font-size: 7.8pt; font-weight: 600; letter-spacing: 0.5pt; text-transform: uppercase; color: var(--amber); margin: 5pt 0 2pt; }
.gap, .why { margin-top: 4pt; }
.small { font-size: 8.8pt; color: var(--muted); margin-bottom: 2pt; }

.quote { background: var(--card); border-left: 3px solid var(--leaf); padding: 5pt 8pt; font-size: 10pt; line-height: 1.33; }
.quote em { font-style: normal; font-weight: 600; }

.tiles { display: grid; gap: 4pt; }
.tile { background: var(--card); border-top: 2px solid var(--ink); padding: 4pt 7pt 5pt; display: grid; grid-template-columns: 0.98in 1fr; gap: 0 8pt; align-items: start; }
.tile .big { font-family: "Fraunces", serif; font-weight: 600; font-size: 15.5pt; line-height: 1.05; color: var(--leaf); white-space: nowrap; }
.tile .big small { display: block; font-family: "IBM Plex Sans", sans-serif; font-size: 7.4pt; font-weight: 600; color: var(--amber); letter-spacing: 0.4pt; text-transform: uppercase; margin-top: 2pt; line-height: 1.2; white-space: normal; }
.arr { display: inline-block; width: 0.85em; height: 0.55em; margin: 0 0.18em; vertical-align: 0.08em; }
.tile .txt { font-size: 9.5pt; line-height: 1.28; }
.tile .src { display: block; font-size: 8.2pt; color: var(--muted); margin-top: 1pt; }

.bottom { display: grid; grid-template-columns: 1.05fr 0.95fr; gap: 0 0.26in; align-items: start; }
.take p { background: var(--card); border-left: 3px solid var(--leaf); padding: 5pt 8pt; font-size: 9.9pt; line-height: 1.32; }
.take b { color: var(--ink); }

footer { position: absolute; left: 0.42in; right: 0.42in; bottom: 0.24in; white-space: nowrap; border-top: 1px solid var(--line); padding-top: 3pt; font-size: 7.8pt; color: var(--muted); display: flex; justify-content: space-between; gap: 16pt; }
</style>
</head>
<body>

<header>
  <div class="toprow">
    <div>
      <h1>Majani Relay</h1>
      <div class="tagline">From a relay farmer&#8217;s leaf photo to the officer&#8217;s next visit</div>
    </div>
    <div class="meta">
      <div class="team">Sidian Lin (Harvard Kennedy School)</div>
      <div class="team">Yicong Li (Harvard SEAS)</div>
      <div>Live app: <a href="{{APP_URL}}">git-lsd.github.io/majani-relay</a></div>
      <div>Code: <a href="{{REPO_URL}}">github.com/Git-lsd/majani-relay</a></div>
    </div>
  </div>
</header>

<section>
  <h2><span class="n">01</span>Problem statement</h2>
  <div class="quote">Because of this tool, <em>the county extension officer or cooperative agronomist will send their next visits to the villages with the most leaf rust, by the week the relay farmers&#8217; plot checks reach the cooperative</em>, that they would otherwise do late, after paper reports arrive; we know because one Kenyan extension officer typically serves 1,500&ndash;3,000 farmers and paper-based reporting has caused &#8220;delayed information flows&#8221; (Ministry of Agriculture draft data policy, 2026), and coffee-specific extension has &#8220;collapsed&#8221; in places (Coffee Development and Marketing Strategy, 2024).</div>
</section>

<div class="cols">
<div class="col">

  <section>
    <h2><span class="n">02</span>Where it sits in the user&#8217;s day</h2>
    <ul>
      <li><b>Relay farmer, on a plot visit</b> (a farmer the co-op trains to visit members&#8217; plots): asks consent, takes 15 leaf photos, plays each answer in Swahili. Offline.</li>
      <li><b>Extension officer, on meeting the relay farmer:</b> labels the &#8220;not sure&#8221; photos, makes the final call, updates the model.</li>
      <li><b>Co-op office, planning visits:</b> ranks villages by rust, so the officer goes first where rust is highest.</li>
    </ul>
    <p class="gap"><b>The gap:</b> one officer per 1,500&ndash;3,000 farmers; late reports.</p>
  </section>

  <section>
    <h2><span class="n">03</span>What the AI does, and why AI</h2>
    <ul>
      <li><b>Turns photos into counts:</b> names each leaf (healthy, rust, leaf miner, brown eye spot, Phoma) or says &#8220;not sure&#8221;.</li>
      <li><b>Knows when it does not know:</b> an unfamiliar-photo check and an &#8220;other problem&#8221; answer.</li>
      <li><b>Learns from the local officer&#8217;s labels</b>, on the phone.</li>
    </ul>
    <p class="why"><b>Why not SMS, a spreadsheet or a search?</b> SMS cannot read a photo, a spreadsheet cannot look at a leaf, and a search needs signal and gives general pictures. A paper form holds each person&#8217;s guess; the AI applies one rule on every phone.</p>
    <div class="label">Guardrails built in the app</div>
    <ul>
      <li class="amber">&#8220;Not sure&#8221; when unsure, unfamiliar or another problem; those photos wait for the officer, out of the count.</li>
      <li class="amber">The officer makes the final call; the relay farmer can disagree; 1 in 10 answers are spot-checked.</li>
      <li class="amber">A fixed list of 24 answers; it never writes its own text; no pesticide names or doses.</li>
      <li class="amber">Consent first; no names, phone numbers or locations stored; offline, on the phone.</li>
    </ul>
  </section>

</div>
<div class="col">

  <section>
    <h2><span class="n">04</span>Results at a glance</h2>
    <div class="tiles">
      <div class="tile">
        <div class="big">{{SHIP_CV_COVERAGE}}<small>answered</small></div>
        <div class="txt"><b>Healthy and rust field photos</b> never trained on: answers {{SHIP_CV_COVERAGE}}, and {{SHIP_CV_ACC_ANSWERED}} of those are right; the rest go to the officer.<span class="src">RoCoLe, Ecuador; cross-validated</span></div>
      </div>
      <div class="tile">
        <div class="big">{{UG_SHIP_NOT_SURE}}<small>to the officer</small></div>
        <div class="txt"><b>New country:</b> {{UG_SHIP_NOT_SURE}} go to the officer, not a guess (forced: right on only {{UG_SHIP_FORCED}}). After 100 officer labels: answers {{FAM_UG100_ANSWERED_NEW}}, {{FAM_UG100_ACC_NEW}} of those right.<span class="src">Uganda farm photos; dataset labels stand in for the officer</span></div>
      </div>
      <div class="tile">
        <div class="big">{{SHIP_VILLAGE_FA_RAW}}<svg class="arr" viewBox="0 0 16 10" aria-label="to"><path d="M1 5h12.5M9.5 1.2 13.5 5l-4 3.8" stroke="currentColor" stroke-width="1.7" fill="none"/></svg>{{SHIP_VILLAGE_FA_ADJ}}<small>false alarms</small></div>
        <div class="txt"><b>Village ranking:</b> false alarms per 40 villages, with the small-sample adjustment. Misses near the alert line: {{SHIP_VILLAGE_MISS_RAW}}<svg class="arr" viewBox="0 0 16 10" aria-label="to"><path d="M1 5h12.5M9.5 1.2 13.5 5l-4 3.8" stroke="currentColor" stroke-width="1.7" fill="none"/></svg>{{SHIP_VILLAGE_MISS_ADJ}}.<span class="src">Simulated villages, at measured error rates</span></div>
      </div>
    </div>
  </section>

  <section>
    <h2><span class="n">05</span>Tech stack</h2>
    <ul>
      <li><b>Static web app (PWA):</b> plain HTML, CSS, JavaScript; no server, no account.</li>
      <li><b>On-phone AI:</b> MobileNetV3 backbone ({{MODEL_MB}} MB, ONNX) + small head ({{SHIP_HEAD_KB}} KB) + familiarity set ({{SHIP_REF_KB}} KB) in onnxruntime-web.</li>
      <li><b>On-phone refit</b> from officer labels; updates shared by WhatsApp or Bluetooth.</li>
      <li><b>Offline</b> after a first load of about {{FIRST_LOAD_MB}} MB; records in IndexedDB.</li>
      <li><b>Village ranking:</b> Beta-binomial statistics, not AI.</li>
    </ul>
  </section>



</div>
</div>

<div class="bottom">
  <section>
    <h2><span class="n">06</span>Next: a 90-day pilot (proposed)</h2>
    <p class="small">One Kirinyaga co-op, 5 relay farmers, one officer, the co-op manager.</p>
    <ul>
      <li><b>Before:</b> per-officer PINs replace the demo PIN; an offline visit timed on a low-cost Android phone.</li>
      <li><b>Week 1:</b> a Swahili-speaking officer reviews all 24 answers.</li>
      <li><b>Weeks 3&ndash;8:</b> the first 200 officer-labelled Kenyan photos are sealed as a test; below 70% correct, AI answers switch off.</li>
      <li><b>Week 12:</b> continue, change or stop, decided with the co-op.</li>
    </ul>
  </section>

<section class="take">
  <h2><span class="n">07</span>Our take: localizing AI</h2>
  <p>Localizing AI is not translating an app. Our first model, trained on lab photos, was right on {{LAB_ACC}} of held-out lab photos but on only {{FIELD_ACC_NO_ABSTAIN}} of Ecuador field photos, while {{FIELD_MEAN_CONFIDENCE}} confident on average. So we retrained it on field photos, taught it to say &#8220;not sure&#8221;, and let the local officer teach it on the phone. <b>To us, localizing AI means the people closest to the farm teach it, correct it, and stay in charge.</b></p>
</section>
</div>

<footer>
  <span>Small AI for Development &middot; Agriculture track &middot; demo PIN 2026 (Officer, Co-op tabs)</span>
  <span>Numbers from results/numbers.json &middot; full details in the README</span>
</footer>

</body>
</html>
"""


def fill(text):
    missing = sorted({k for k in KEY.findall(text) if k not in N})
    if missing:
        sys.exit('missing keys in numbers.json: %s' % missing)
    return KEY.sub(lambda m: N[m.group(1)], text)


def main():
    used = sorted(set(KEY.findall(TEMPLATE)) - {'APP_URL', 'REPO_URL', 'FIRST_LOAD_MB'})
    open(HTML, 'w').write(fill(TEMPLATE))
    if os.path.exists(PDF):
        os.remove(PDF)
    cmd = [CHROME, '--headless=new', '--disable-gpu', '--no-pdf-header-footer', '--no-first-run',
           '--virtual-time-budget=4000', '--print-to-pdf=' + PDF, 'file://' + HTML]
    p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        p.wait(timeout=60)
    except subprocess.TimeoutExpired:
        p.kill(); p.wait()
        sys.exit('Chrome timed out and was stopped')
    if not os.path.exists(PDF):
        sys.exit('no PDF written')
    raw = open(PDF, 'rb').read()
    pages = len(re.findall(rb'/Type\s*/Page(?![s\w])', raw))
    print('wrote', HTML)
    print('wrote', PDF, '| pages:', pages)
    print('numbers.json keys used:', ', '.join(used))
    print('FIRST_LOAD_MB (computed as in ml/fill_docs.py):', N['FIRST_LOAD_MB'])
    if pages != 1:
        sys.exit('expected exactly one page, got %d' % pages)


if __name__ == '__main__':
    main()
