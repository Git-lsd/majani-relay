/* Kahawa Check service worker.
   - Precaches every app file (page, code, model, onnxruntime wasm) so the app works in airplane mode.
   - Cache-first. Small text files (html/js/css/json) and model/reference.bin are also refreshed in
     the background when online, so the next visit gets updates. The backbone, the wasm runtime,
     photos and audio are only re-downloaded when VERSION changes.
   - Bump VERSION whenever backbone.onnx, audio or the vendor files change (safest: on every deploy). */
const VERSION = 'kahawa-v9';

// Files the app cannot work without. Install fails (and the page falls back to the network) if one is missing.
const CORE = [
  './', 'index.html', 'app.js', 'styles.css', 'manifest.webmanifest',
  'icons/icon-192.png', 'icons/icon-512.png', 'icons/icon-maskable-512.png',
  'icons/apple-touch-icon.png', 'icons/favicon-32.png',
  'vendor/ort/ort.wasm.min.js', 'vendor/ort/ort-wasm-simd-threaded.mjs',
  'vendor/ort/ort-wasm-simd-threaded.wasm', 'vendor/ort/LICENSE.txt', 'lib/kahawa-core.js',
  'model/backbone.onnx', 'model/head.json', 'model/backbone_meta.json',
];
// Files that may not exist yet (written by other team members). Cached if present.
const OPTIONAL = ['answers.json', 'samples/manifest.json', 'model/update_demo_50.json'];
// Answer ids from SPEC.md; audio/<lang>/<id>.m4a is cached for each one that exists.
const ANSWER_IDS = ['result_healthy', 'result_rust', 'result_miner', 'result_cercospora', 'result_phoma',
  'result_not_sure', 'retake_photo', 'action_healthy', 'action_rust', 'action_miner', 'action_cercospora',
  'action_phoma', 'action_not_sure', 'plot_all_healthy', 'plot_some_problem', 'plot_officer_alert',
  'check_q1_old_trees', 'check_q2_no_fertiliser', 'check_q3_weeding', 'check_q4_berry_spots',
  'check_q5_berry_holes', 'check_q6_dry_flowering', 'disclaimer_final_call', 'consent_photos'];
const LANGS = ['sw', 'en', 'kik'];

const abs = (p) => new URL(p, self.registration.scope).href;

async function tell(msg) {
  const all = await self.clients.matchAll({ includeUncontrolled: true });
  all.forEach((c) => c.postMessage(msg));
}

// Fetch one file into the cache. Pinned vendor files are copied from an older cache when possible.
async function addOne(cache, path, required) {
  const url = abs(path);
  if (path.startsWith('vendor/')) {
    const prev = await caches.match(url);
    if (prev) { await cache.put(url, prev); return true; }
  }
  let res;
  try { res = await fetch(url, { cache: 'no-cache' }); } catch (e) { if (required) throw e; return false; }
  if (!res.ok) { if (required) throw new Error(path + ' ' + res.status); return false; }
  await cache.put(url, res);
  return true;
}

// Run tasks with a small concurrency limit (weak connections do not like 70 parallel requests).
async function pool(items, n, fn) {
  const queue = items.slice();
  const workers = Array.from({ length: n }, async () => { while (queue.length) await fn(queue.shift()); });
  await Promise.all(workers);
}

async function precache() {
  const cache = await caches.open(VERSION);
  let done = 0;
  for (const p of CORE) {
    await addOne(cache, p, true);
    done += 1;
    tell({ type: 'precache', done, total: CORE.length });
  }
  // The familiarity reference file named in head.json (model/reference.bin) is required too.
  try {
    const head = await (await cache.match(abs('model/head.json'))).clone().json();
    const ref = head.ood && head.ood.reference && head.ood.reference.file;
    if (ref) await addOne(cache, 'model/' + ref, true);
  } catch (e) { throw new Error('familiarity reference missing: ' + e.message); }
  for (const p of OPTIONAL) await addOne(cache, p, false);
  // Sample photos listed in samples/manifest.json
  const extra = [];
  try {
    const m = await (await cache.match(abs('samples/manifest.json'))).json();
    (m.samples || []).forEach((s) => s.file && extra.push('samples/' + s.file));
  } catch (e) { /* no samples */ }
  // Audio: the paths named in answers.json ("audio": {sw: path or null, ...}). If answers.json has no
  // audio field, try the standard audio/<lang>/<id>.m4a for every answer id.
  let named = false;
  try {
    let a = await (await cache.match(abs('answers.json'))).json();
    if (a && a.answers && typeof a.answers === 'object') a = a.answers;
    for (const e of Object.values(a || {})) {
      if (!e || typeof e !== 'object' || !e.audio || typeof e.audio !== 'object') continue;
      named = true;
      Object.values(e.audio).forEach((p) => typeof p === 'string' && p && extra.push(p));
    }
  } catch (e) { /* no answers.json yet */ }
  if (!named) for (const id of ANSWER_IDS) for (const l of LANGS) extra.push(`audio/${l}/${id}.m4a`);
  await pool([...new Set(extra)], 6, (p) => addOne(cache, p, false));
  tell({ type: 'precache-done' });
}

self.addEventListener('install', (e) => {
  e.waitUntil(precache().then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil((async () => {
    for (const k of await caches.keys()) if (k.startsWith('kahawa-') && k !== VERSION) await caches.delete(k);
    await self.clients.claim();
  })());
});

// Refreshed in the background when online (cheap if unchanged). reference.bin is included so it never
// falls out of step with head.json. backbone.onnx and the wasm runtime are only replaced when VERSION changes.
const SMALL = /\.(html|js|mjs|css|json|webmanifest|bin)$/;

async function refresh(cache, req) {
  try {
    const res = await fetch(req, { cache: 'no-cache' });
    if (res.ok) await cache.put(req, res);
  } catch (e) { /* offline: keep the cached copy */ }
}

async function handle(e) {
  const req = e.request;
  const url = new URL(req.url);
  const cache = await caches.open(VERSION);
  const isNav = req.mode === 'navigate';
  let hit = await cache.match(req, { ignoreSearch: true });
  if (!hit && isNav) hit = await cache.match(abs('index.html'));
  const small = isNav || SMALL.test(url.pathname);
  if (hit) {
    // The backbone, wasm, photos and audio are not re-fetched until VERSION changes.
    if (small && !url.pathname.includes('/vendor/')) e.waitUntil(refresh(cache, isNav ? abs('index.html') : req));
    return hit;
  }
  try {
    const res = await fetch(req);
    if (res.ok && res.type === 'basic') e.waitUntil(cache.put(req, res.clone()));
    return res;
  } catch (err) {
    return new Response('Offline and not saved on this phone yet.', { status: 503, headers: { 'Content-Type': 'text/plain' } });
  }
}

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  if (new URL(req.url).origin !== self.location.origin) return;
  if (req.headers.has('range')) return; // let the browser handle media range requests directly
  e.respondWith(handle(e));
});
