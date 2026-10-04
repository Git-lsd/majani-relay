/* Majani Relay (earlier name: Kahawa Check): offline coffee leaf check for cooperative relay farmers.
   Internal identifiers keep the old name so saved data keeps working (database 'kahawa-check', update kind
   'kahawa-head-update', window.__kahawa, KahawaCore, localStorage prefix 'kahawa.').
   Plain JavaScript, no build step. Sections:
   1 constants and built-in English text   2 helpers   3 storage (IndexedDB)
   4 languages and answer texts            5 model (onnxruntime-web backbone + small head)
   6 learning loop (officer labels -> refit head on the phone)
   7 co-op statistics (Beta-binomial empirical Bayes)   8 screens   9 boot */
(() => {
'use strict';

// ---------------------------------------------------------------- 1. Constants
const ANSWER_IDS = ['result_healthy', 'result_rust', 'result_miner', 'result_cercospora', 'result_phoma',
  'result_not_sure', 'retake_photo', 'action_healthy', 'action_rust', 'action_miner', 'action_cercospora',
  'action_phoma', 'action_not_sure', 'plot_all_healthy', 'plot_some_problem', 'plot_officer_alert',
  'check_q1_old_trees', 'check_q2_no_fertiliser', 'check_q3_weeding', 'check_q4_berry_spots',
  'check_q5_berry_holes', 'check_q6_dry_flowering', 'disclaimer_final_call', 'consent_photos'];

// Built-in English, used when answers.json is missing or lacks a text. Fixed list: the app never generates text.
// Rules (SPEC): never name a pesticide product or dose; every disease result says the officer makes the final call.
const OFFICER_DECIDES = 'Tell the extension officer. The officer makes the final call on what to do.';
const EN = {
  result_healthy: 'This leaf looks healthy.',
  result_rust: 'This leaf may have coffee leaf rust.',
  result_miner: 'This leaf may have leaf miner damage.',
  result_cercospora: 'This leaf may have brown eye spot (Cercospora).',
  result_phoma: 'This leaf may have Phoma leaf spot.',
  result_not_sure: 'Not sure. The officer will look at this photo.',
  retake_photo: 'This photo is hard to read. Please take it again: underside of the leaf, close up, in shade.',
  action_healthy: 'No action needed for this leaf. Go on to the next leaf.',
  action_rust: OFFICER_DECIDES,
  action_miner: OFFICER_DECIDES,
  action_cercospora: OFFICER_DECIDES,
  action_phoma: OFFICER_DECIDES,
  action_not_sure: 'The photo is saved for the officer. Go on to the next leaf.',
  plot_all_healthy: 'All checked leaves look healthy.',
  plot_some_problem: 'Some leaves may have a problem. The officer will check and make the final call.',
  plot_officer_alert: 'Many leaves may have a problem. Ask the officer to visit this farm soon.',
  check_q1_old_trees: 'Are most coffee trees very old (about 20 years or more) and not renewed?',
  check_q2_no_fertiliser: 'Was no fertiliser or manure used this season?',
  check_q3_weeding: 'Are there many weeds under the coffee trees?',
  check_q4_berry_spots: 'Are there dark, sunken spots on the green berries? (Possible coffee berry disease: tell the officer.)',
  check_q5_berry_holes: 'Are there small holes in the berries? (Possible berry borer: tell the officer.)',
  check_q6_dry_flowering: 'Was there a long dry spell when the trees were flowering?',
  disclaimer_final_call: 'This tool can be wrong. The extension officer makes the final call.',
  consent_photos: 'May I take photos of coffee leaves on your farm? The photos stay on this phone. They are shared only with the cooperative officer, for checking.',
};
const CHECK_IDS = ['check_q1_old_trees', 'check_q2_no_fertiliser', 'check_q3_weeding',
  'check_q4_berry_spots', 'check_q5_berry_holes', 'check_q6_dry_flowering'];
const REFER_IDS = ['check_q4_berry_spots', 'check_q5_berry_holes']; // "yes" means tell the officer

// English display names for the officer screens. Unknown class names from a new head.json show as-is.
const CLASS_NAMES = { healthy: 'Healthy', rust: 'Leaf rust', miner: 'Leaf miner',
  cercospora: 'Brown eye spot', phoma: 'Phoma leaf spot', other: 'Different problem' };
const className = (c) => CLASS_NAMES[c] || String(c);

const PROTOCOL = { trees: 5, leaves: 3 }; // 3 leaves x 5 trees = 15 photos
const ALERT_RATE = 0.25;  // village alert: P(rust share > 25%) ...
const ALERT_PROB = 0.5;   // ... above 50%. Same rule as the simulation in ml/train_eval.py (village_sim).
const REFIT_STEPS = 200;
const SPOT_CHECK_RATE = 0.1; // 1 in 10 answered photos is also queued for the officer (random)

const LANGS = ['sw', 'en', 'kik'];
const LANG_NAMES = { sw: 'Kiswahili', en: 'English', kik: 'Gĩkũyũ' };
const LANG_LABEL = { sw: 'Swahili', en: 'English', kik: 'Kikuyu' };
const HTML_LANG = { sw: 'sw', en: 'en', kik: 'ki' };
const CHAIN = { sw: ['sw', 'en'], en: ['en'], kik: ['kik', 'sw', 'en'] }; // fallback order
// Audio fallback order. There is no English audio, so English screens play the Swahili recording
// (marked "Audio in Swahili"): the relay farmer can read English and play Swahili to the farmer.
const AUDIO_CHAIN = { sw: ['sw', 'en'], en: ['en', 'sw'], kik: ['kik', 'sw', 'en'] };

// Wording corrections: a relay farmer or officer reports a wrong or unnatural phrase. They are saved on the
// phone and exported for review; the text on screen never changes by itself.
const APP_VERSION = 'kahawa-v19'; // keep equal to VERSION in sw.js
const APP_NAME = 'Majani Relay'; // user-facing name (pronounced mah-JAH-nee)
const FILE_PREFIX = 'majani-relay'; // start of exported file names
const WHO = { relay_farmer: 'Relay farmer', extension_officer: 'Extension officer', farmer: 'Farmer', other: 'Other' };
const WC_KEY = 'wording_corrections'; // meta record: { key, items: [...] }
const WC_FIELDS = ['id', 'lang', 'shown_text', 'english', 'suggestion', 'who', 'note', 'created', 'app_version', 'head_version'];

// Plot visit: three optional taps for the officer. Saved with the plot record; the AI does not use them.
const FARM_TAPS = [
  { key: 'variety', label: 'Variety', cols: 3, options: [['sl28_sl34', 'SL28/SL34'], ['ruiru_11', 'Ruiru 11'], ['batian', 'Batian'], ['other', 'Other'], ['unknown', 'Don\'t know']] },
  { key: 'last_spray', label: 'Last spray', cols: 3, options: [['never', 'Never'], ['under_1m', 'Under 1 month'], ['1_3m', '1–3 months'], ['over_3m', 'Over 3 months'], ['unknown', 'Don\'t know']] },
  { key: 'fruit_load', label: 'Fruit load', cols: 4, options: [['low', 'Low'], ['medium', 'Medium'], ['high', 'High'], ['unknown', 'Don\'t know']] },
];
const FARM_NOTE = 'For the officer; the AI does not use this';
const farmValue = (key, code) => { const t = FARM_TAPS.find((x) => x.key === key); const o = t && t.options.find(([k]) => k === code); return o ? o[1] : null; };

// "I think it's something else": the relay farmer disagrees with an AI answer. The photo joins the officer queue
// and stays out of the village numbers until the officer labels it (then the officer's label counts).
const DISPUTE_REASON = 'relay farmer disagrees';

// ---------------------------------------------------------------- 2. Helpers
const $ = (sel) => document.querySelector(sel);
const SVGNS = 'http://www.w3.org/2000/svg';

// Build DOM safely (text is never parsed as HTML).
function h(tag, props, ...kids) {
  const el = document.createElement(tag);
  if (props) for (const [k, v] of Object.entries(props)) {
    if (v == null || v === false) continue;
    if (k === 'class') el.className = v;
    else if (k.startsWith('on') && typeof v === 'function') el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v === true ? '' : v);
  }
  for (const kid of kids.flat(Infinity)) {
    if (kid == null || kid === false) continue;
    el.append(kid instanceof Node ? kid : String(kid));
  }
  return el;
}
function icon(name, cls = 'ic') {
  const s = document.createElementNS(SVGNS, 'svg');
  s.setAttribute('class', cls);
  s.setAttribute('aria-hidden', 'true');
  const u = document.createElementNS(SVGNS, 'use');
  u.setAttribute('href', '#i-' + name);
  s.append(u);
  return s;
}
const pct = (x, digits = 0) => (x == null || !isFinite(x)) ? '–' : (100 * x).toFixed(digits) + '%';
// Probabilities near 0 or 1 are shown as "<1%" / ">99%" rather than a misleading 0% or 100%.
const pctP = (p) => p == null ? '–' : p > 0.995 ? '>99%' : p < 0.005 ? '<1%' : pct(p);
const absUrl = (p) => new URL(p, document.baseURI).href;
const uid = () => (crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(36) + Math.random().toString(36).slice(2));
const fmtDate = (t) => new Date(t).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }); // screen text is English
const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`;
const clamp = (x, lo, hi) => Math.min(hi, Math.max(lo, x));

let toastTimer = 0;
function toast(msg, action, ms) {
  const t = $('#toast');
  const kids = [h('span', null, msg)];
  if (action) kids.push(h('button', { type: 'button', onclick: () => { t.hidden = true; action.fn(); } }, action.label));
  t.replaceChildren(...kids);
  t.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { t.hidden = true; }, ms || (action ? 7000 : 3500));
}

function download(name, text, type) {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const a = h('a', { href: url, download: name });
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 10000);
}

async function sha256Hex(text) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  return Array.from(new Uint8Array(buf), (x) => x.toString(16).padStart(2, '0')).join('');
}

const store = { // localStorage, for small per-phone conveniences only (may be unavailable)
  get(k, d) { try { const v = localStorage.getItem('kahawa.' + k); return v == null ? d : v; } catch (e) { return d; } },
  set(k, v) { try { localStorage.setItem('kahawa.' + k, v); } catch (e) { /* ignore */ } },
  clear() { try { Object.keys(localStorage).filter((k) => k.startsWith('kahawa.')).forEach((k) => localStorage.removeItem(k)); } catch (e) { /* ignore */ } },
};

async function fetchJSON(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(url + ': ' + r.status);
  return r.json();
}

// Download with progress (used for the 17 MB backbone). Handles servers that compress (length unknown).
async function fetchBytes(url, onProgress) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(url + ': ' + r.status);
  const total = +r.headers.get('content-length') || 0;
  if (!r.body || !r.body.getReader) return new Uint8Array(await r.arrayBuffer());
  const reader = r.body.getReader();
  const chunks = [];
  let got = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
    got += value.length;
    if (onProgress) onProgress(got, total);
  }
  const out = new Uint8Array(got);
  let off = 0;
  for (const c of chunks) { out.set(c, off); off += c.length; }
  return out;
}

function bytesToB64(u8) {
  let s = '';
  for (let i = 0; i < u8.length; i += 0x8000) s += String.fromCharCode.apply(null, u8.subarray(i, i + 0x8000));
  return btoa(s);
}
function b64ToBytes(b64) {
  const s = atob(b64);
  const u8 = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) u8[i] = s.charCodeAt(i);
  return u8;
}

// ---------------------------------------------------------------- 3. Storage (IndexedDB)
// Stores: plots (plot records), photos (thumbnail + embedding + result), meta (adapted head).
const DB = {
  name: 'kahawa-check',
  _db: null,
  mem: null, // in-memory fallback when IndexedDB is unavailable or hangs (records are then not kept)
  open() {
    if (!this._db) this._db = Promise.race([
      new Promise((resolve, reject) => {
        const r = indexedDB.open(this.name, 1);
        r.onupgradeneeded = () => {
          const d = r.result;
          d.createObjectStore('plots', { keyPath: 'id' });
          d.createObjectStore('photos', { keyPath: 'id' }).createIndex('plot_id', 'plot_id');
          d.createObjectStore('meta', { keyPath: 'key' });
        };
        r.onsuccess = () => resolve(r.result);
        r.onerror = () => reject(r.error);
      }),
      // Some browsers (private modes, embedded previews) never answer; fall back after 5 s.
      new Promise((_, reject) => setTimeout(() => reject(new Error('IndexedDB did not open in 5 s')), 5000)),
    ]).catch((e) => {
      console.warn('Using in-memory storage:', e);
      this.mem = { plots: new Map(), photos: new Map(), meta: new Map() };
      throw e;
    });
    return this._db;
  },
  _key(s, val) { return s === 'meta' ? val.key : val.id; },
  async run(storeName, mode, fn) {
    if (this.mem) return undefined;
    const d = await this.open();
    return new Promise((resolve, reject) => {
      const tx = d.transaction(storeName, mode);
      const req = fn(tx.objectStore(storeName));
      tx.oncomplete = () => resolve(req ? req.result : undefined);
      tx.onerror = () => reject(tx.error);
      tx.onabort = () => reject(tx.error);
    });
  },
  async get(s, key) { if (this.mem) return this.mem[s].get(key); return this.run(s, 'readonly', (o) => o.get(key)); },
  async all(s) { if (this.mem) return [...this.mem[s].values()]; return this.run(s, 'readonly', (o) => o.getAll()); },
  async put(s, val) { if (this.mem) { this.mem[s].set(this._key(s, val), val); return; } return this.run(s, 'readwrite', (o) => o.put(val)); },
  async del(s, key) { if (this.mem) { this.mem[s].delete(key); return; } return this.run(s, 'readwrite', (o) => o.delete(key)); },
  async deleteAll() {
    if (this.mem) { Object.values(this.mem).forEach((m) => m.clear()); return; }
    if (this._db) { (await this._db).close(); this._db = null; }
    await new Promise((resolve) => {
      const r = indexedDB.deleteDatabase(this.name);
      r.onsuccess = r.onerror = r.onblocked = () => resolve();
    });
  },
};

let persistAsked = false;
function askPersist() { // ask the browser not to evict saved records (best effort)
  if (persistAsked) return;
  persistAsked = true;
  try { if (navigator.storage && navigator.storage.persist) navigator.storage.persist(); } catch (e) { /* ignore */ }
}

// ---------------------------------------------------------------- 4. Languages and answer texts
let lang = LANGS.includes(store.get('lang')) ? store.get('lang') : 'sw';
let answers = {};          // id -> {en, sw, kik, sw_verified, kik_verified, ...}
let answersLoaded = false; // false: answers.json missing, all text is built-in English

async function loadAnswers() {
  try {
    let j = await fetchJSON('answers.json');
    if (j && j.answers && typeof j.answers === 'object') j = j.answers;
    const out = {};
    for (const [k, v] of Object.entries(j || {})) if (v && typeof v === 'object' && !Array.isArray(v)) out[k] = v;
    answers = out;
    answersLoaded = true;
  } catch (e) {
    answers = {};
    answersLoaded = false;
  }
}

function isVerified(entry, l) {
  if (l === 'en') return true;
  if (!entry) return false;
  if (typeof entry[l + '_verified'] === 'boolean') return entry[l + '_verified'];
  if (entry.verified && typeof entry.verified === 'object') return !!entry.verified[l];
  if (typeof entry.verified === 'boolean') return entry.verified;
  return false;
}

// Text for an answer id in the selected language, walking the fallback chain.
function answerText(id) {
  const entry = answers[id];
  for (const l of CHAIN[lang]) {
    const v = entry && typeof entry[l] === 'string' ? entry[l].trim() : '';
    if (v) return { text: v, lang: l, fallback: l !== lang, verified: isVerified(entry, l), partial: l === 'kik' && entry.kik_partial === true };
  }
  return { text: EN[id] || id, lang: 'en', fallback: lang !== 'en', verified: true, builtin: true };
}

// Audio: audio/<lang>/<id>.m4a (or a path in answers.json "audio" field). A file in the offline copy is read
// once into a blob, so that tapping play starts audio immediately (iPhone needs play() inside the tap) and
// plays with no network: the browser asks for audio in parts ("range" requests), which the offline worker
// does not answer, so playing the plain file address fails offline.
const audioState = new Map(); // url -> Promise<'yes'|'no'|'unknown'>
const audioBlob = new Map(); // url -> object URL of the offline copy
let swSettled = Promise.resolve();
// Does this audio file exist? 'yes' | 'no' | 'unknown'. Only a real "not found" disables the play button:
// some phone browsers (iPhone Safari on a plain-http test server) fail the check for other reasons.
function audioCheck(url) {
  if (!audioState.has(url)) audioState.set(url, (async () => {
    await Promise.race([swSettled, new Promise((r) => setTimeout(r, 3000))]); // never wait long for the offline worker
    try {
      const hit = window.caches ? await caches.match(url) : null;
      if (hit) { audioBlob.set(url, URL.createObjectURL(await hit.blob())); return 'yes'; }
    } catch (e) { /* cache storage not available here */ }
    // Not in the offline copy. That copy can be incomplete for a while (an app update still saving, or an
    // older copy made before the audio existed), so when online ask the server instead of greying the button.
    if (!navigator.onLine) return (navigator.serviceWorker && navigator.serviceWorker.controller) ? 'no' : 'unknown';
    try {
      const res = await fetch(url, { method: 'HEAD', cache: 'no-store' });
      return res.ok ? 'yes' : (res.status === 404 ? 'no' : 'unknown');
    } catch (e) { return 'unknown'; }
  })());
  return audioState.get(url);
}
// Check again once the offline copy is complete (or a new app version takes over): play buttons that
// were greyed out while it was still saving become usable without reloading the page.
function recheckAudio() {
  audioState.clear();
  document.querySelectorAll('.answer[data-answer]').forEach((el) => {
    const btn = el.querySelector('.play');
    if (btn && btn.disabled) wireAudio(btn, el.dataset.answer, el.dataset.textLang, el.querySelector('.tags'));
  });
}
let player = null;
function playAudio(src, btn) {
  if (player) { player.pause(); document.querySelectorAll('.play.playing').forEach((b) => b.classList.remove('playing')); }
  player = new Audio(src);
  btn.classList.add('playing');
  const stop = () => btn.classList.remove('playing');
  player.onended = stop;
  player.onerror = () => { stop(); toast('Could not play this audio.'); };
  player.play().catch(() => { stop(); toast('Could not play this audio.'); });
}
// textLang: language of the text shown beside the button. When the audio is in another language, the
// block gets a visible "Audio in ..." marker so nobody mistakes it for a reading of the text on screen.
async function wireAudio(btn, id, textLang, tagsEl) {
  const entry = answers[id];
  for (const l of AUDIO_CHAIN[lang]) {
    // answers.json names each audio file (null = none); without that field, try audio/<lang>/<id>.m4a
    const path = (entry && entry.audio && typeof entry.audio === 'object') ? entry.audio[l] : `audio/${l}/${id}.m4a`;
    if (typeof path !== 'string' || !path) continue;
    const url = absUrl(path);
    if ((await audioCheck(url)) === 'no') continue;
    btn.disabled = false;
    const label = l === textLang ? 'Play audio' : `Play ${LANG_LABEL[l]} audio`;
    btn.title = label;
    btn.setAttribute('aria-label', label);
    btn.onclick = () => playAudio(audioBlob.get(url) || url, btn); // offline copy if saved, else the server
    if (l !== textLang && tagsEl && !tagsEl.querySelector('.tag-audio')) {
      tagsEl.append(h('span', { class: 'tag tag-audio' }, `Audio in ${LANG_LABEL[l]}`));
      tagsEl.hidden = false;
    }
    return;
  }
  btn.title = 'No audio recorded yet';
  btn.setAttribute('aria-label', 'No audio recorded yet');
}

// One fixed answer: text in the selected language + markers + play button.
function answerBlock(id) {
  const a = answerText(id);
  const tags = [];
  if (a.fallback) tags.push(h('span', { class: 'tag warn' }, `Not yet in ${LANG_LABEL[lang]}: shown in ${LANG_LABEL[a.lang]}`));
  if (a.partial) tags.push(h('span', { class: 'tag warn' }, 'Short Kikuyu phrase, rest in Swahili'));
  if (!a.verified) tags.push(h('span', { class: 'tag warn' }, 'Not yet checked by a native speaker'));
  const tagsEl = h('div', { class: 'tags', hidden: !tags.length }, tags);
  const btn = h('button', { class: 'play', type: 'button', disabled: true, title: 'Looking for audio', 'aria-label': 'Looking for audio' }, icon('play'));
  wireAudio(btn, id, a.lang, tagsEl);
  // Reports are for Swahili and Kikuyu wording; the English text is the team's own source text.
  const fix = a.lang === 'en' ? null : h('button', { class: 'link-btn', type: 'button', lang: 'en', onclick: () => openWordingSheet(id) }, 'Wording wrong?');
  return h('div', { class: 'answer', 'data-answer': id, 'data-text-lang': a.lang },
    h('div', { class: 'txt', lang: HTML_LANG[a.lang] }, h('p', null, a.text), tagsEl, fix),
    btn);
}

// ----- Wording corrections (stored in the meta store, record key 'wording_corrections')
async function wordingList() {
  try { const m = await DB.get('meta', WC_KEY); return (m && Array.isArray(m.items)) ? m.items : []; } catch (e) { return []; }
}
const wcKey = (c) => [c.id, c.lang, c.suggestion, c.created].join('\u0001'); // same item = same id, language, suggestion and time
// Keep only the known fields, as short strings (records can come from files made on other phones).
function wcClean(c) {
  if (!c || typeof c !== 'object') return null;
  const out = {};
  for (const f of WC_FIELDS) out[f] = c[f] == null ? null : String(c[f]).slice(0, 2000);
  return (out.id && out.lang && out.suggestion && out.created) ? out : null;
}
// Add records, skipping ones already saved. Returns how many were added.
async function mergeWordingCorrections(list) {
  if (!Array.isArray(list) || !list.length) return 0;
  const items = await wordingList();
  const seen = new Set(items.map(wcKey));
  let added = 0;
  for (const raw of list) {
    const c = wcClean(raw);
    if (!c || seen.has(wcKey(c))) continue;
    seen.add(wcKey(c));
    items.push(c);
    added += 1;
  }
  if (added) await DB.put('meta', { key: WC_KEY, items });
  return added;
}

// opts (optional, for text outside answers.json, e.g. a guide section): { text, lang, english, back }.
// back: called instead of closing, so a report started from the guide returns to the guide.
function openWordingSheet(id, opts) {
  const o = opts || {};
  const a = o.text ? { text: o.text, lang: o.lang || 'en' } : answerText(id); // the text as shown right now
  const entry = answers[id];
  const english = o.english || (entry && typeof entry.en === 'string' && entry.en.trim()) || EN[id] || id;
  const leave = () => { if (o.back) o.back(); else closeSheet(); };
  const s = $('#sheet');
  const sugg = h('textarea', { id: 'wc-suggestion', rows: 4, required: true, lang: HTML_LANG[a.lang], autocomplete: 'off', spellcheck: 'false' });
  sugg.value = a.text; // start from the current text: changing one word is easier than typing it all on a phone
  const who = h('select', { id: 'wc-who' }, Object.entries(WHO).map(([k, label]) => h('option', { value: k }, label)));
  who.value = WHO[store.get('wcWho')] ? store.get('wcWho') : 'relay_farmer';
  const note = h('textarea', { id: 'wc-note', rows: 2, autocomplete: 'off' });
  const err = h('p', { class: 'notice', role: 'alert', hidden: true });
  const save = async () => {
    const text = sugg.value.trim();
    const problem = !text ? 'Please write how it should say this.' : (text === a.text.trim() ? 'The text is the same as now. Change it first, or tap Cancel.' : null);
    if (problem) { err.textContent = problem; err.hidden = false; sugg.focus(); return; }
    store.set('wcWho', who.value);
    const rec = {
      id, lang: a.lang, shown_text: a.text, english, suggestion: text, who: who.value, note: note.value.trim() || null,
      created: new Date().toISOString(), app_version: APP_VERSION, head_version: Model.active ? Model.active.version : null,
    };
    try {
      const items = await wordingList();
      items.push(rec);
      await DB.put('meta', { key: WC_KEY, items });
    } catch (e) { toast('Could not save: ' + (e.message || e)); return; }
    leave();
    toast('Saved on this phone. It goes out with the officer\'s next update file or corrections CSV. The app\'s wording does not change until someone reviews it.', null, 8000);
    if (currentTab !== 'visit') renderCurrent(); // the Officer and About screens show the count
  };
  s.replaceChildren(h('div', { class: 'sheet-body', role: 'dialog', 'aria-modal': 'true', 'aria-labelledby': 'wc-title' },
    h('div', { class: 'row' }, h('h3', { class: 'grow', id: 'wc-title', style: 'margin:0' }, 'Wording wrong?'),
      h('button', { class: 'btn secondary small', type: 'button', onclick: leave }, icon('close'), o.back ? 'Back' : 'Close')),
    h('p', { class: 'small' }, 'Report a wrong or unnatural phrase. It is saved on this phone for the team to review. The app keeps showing the current text until then.'),
    h('div', { class: 'stack' },
      h('div', null, h('span', { class: 'small' }, `${LANG_LABEL[a.lang]} text now shown · sentence ${id}`),
        h('blockquote', { class: 'wc-quote', lang: HTML_LANG[a.lang] }, a.text)),
      a.lang !== 'en' ? h('div', null, h('span', { class: 'small' }, 'English meaning'), h('blockquote', { class: 'wc-quote', lang: 'en' }, english)) : null,
      h('label', { class: 'field' }, h('span', null, 'How should it say this? (required)'), sugg),
      h('label', { class: 'field' }, h('span', null, 'Who is correcting?'), who),
      h('label', { class: 'field' }, h('span', null, 'Note (optional). Please do not write names.'), note),
      err,
      h('div', { class: 'btn-grid' },
        h('button', { class: 'btn', type: 'button', id: 'wc-save', onclick: save }, icon('check'), 'Save'),
        h('button', { class: 'btn secondary', type: 'button', id: 'wc-cancel', onclick: leave }, 'Cancel')))));
  s.hidden = false;
  s.onclick = null; // typed text is not thrown away by a tap outside the sheet
}

// ----- "What does this mean?" guides (guides.json: fixed text, written by the team from the sources it lists)
let guides = null; // { meta: { sources: [...] }, guides: { id: { title, sections: [{ key, heading, text, source_ids }], sw_verified } } }
async function loadGuides() {
  try {
    const j = await fetchJSON('guides.json');
    guides = (j && j.guides && typeof j.guides === 'object') ? j : null;
  } catch (e) { guides = null; }
}
// Result -> guide id. Every photo sent to the officer (low confidence, unfamiliar, "different problem") uses 'not_sure'.
function guideIdFor(r) {
  const id = r.not_sure ? 'not_sure' : r.label;
  return guides && guides.guides[id] && Array.isArray(guides.guides[id].sections) ? id : null;
}
// Text of a {en, sw, ...} field in the selected language, walking the same fallback chain as the answers.
function pickLang(obj) {
  for (const l of CHAIN[lang]) {
    const v = obj && typeof obj[l] === 'string' ? obj[l].trim() : '';
    if (v) return { text: v, lang: l, fallback: l !== lang };
  }
  return { text: '', lang: 'en', fallback: lang !== 'en' };
}
// Short source name for the "Sources" line: drop bracketed asides, keep the part before the first ':' or ';'.
const shortSource = (t) => String(t).replace(/\s*\([^()]*\)/g, '').split(/[:;]/)[0].trim();

function openGuide(id) {
  const g = guides && guides.guides[id];
  if (!g) return;
  const title = pickLang(g.title);
  const main = title.lang;
  const tagsFor = (l, fallback) => [
    fallback ? h('span', { class: 'tag warn' }, `Not yet in ${LANG_LABEL[lang]}: shown in ${LANG_LABEL[l]}`) : null,
    l !== 'en' && !isVerified(g, l) ? h('span', { class: 'tag warn' }, 'Not yet checked by a native speaker') : null,
  ].filter(Boolean);
  const topTags = tagsFor(main, title.fallback);
  const sourceIds = [];
  const sections = g.sections.map((sec) => {
    const hd = pickLang(sec.heading), tx = pickLang(sec.text);
    (sec.source_ids || []).forEach((sid) => { if (!sourceIds.includes(sid)) sourceIds.push(sid); });
    const own = tx.lang !== main ? tagsFor(tx.lang, tx.fallback) : [];
    const english = sec.text && typeof sec.text.en === 'string' ? sec.text.en.trim() : null;
    return h('section', { class: 'guide-sec' },
      h('h3', { lang: HTML_LANG[hd.lang] }, hd.text),
      h('p', { lang: HTML_LANG[tx.lang] }, tx.text),
      own.length ? h('div', { class: 'tags' }, own) : null,
      tx.lang === 'en' ? null : h('button', { class: 'link-btn', type: 'button', lang: 'en',
        onclick: () => openWordingSheet(`guide.${id}.${sec.key}`, { text: tx.text, lang: tx.lang, english, back: () => openGuide(id) }) }, 'Wording wrong?'));
  });
  const srcList = (guides.meta && Array.isArray(guides.meta.sources)) ? guides.meta.sources : [];
  const used = sourceIds.map((sid) => srcList.find((x) => x && x.id === sid) || { id: sid, title: sid });
  const s = $('#sheet');
  s.replaceChildren(h('div', { class: 'sheet-body guide', role: 'dialog', 'aria-modal': 'true', 'aria-labelledby': 'guide-title' },
    h('div', { class: 'row' },
      h('h3', { class: 'grow', id: 'guide-title', style: 'margin:0', lang: HTML_LANG[main] }, title.text),
      h('button', { class: 'btn secondary small', type: 'button', onclick: closeSheet }, icon('close'), 'Close')),
    topTags.length ? h('div', { class: 'tags' }, topTags) : null,
    h('p', { class: 'small' }, 'Fixed text written by the team from the sources below, not by the AI. The extension officer makes the final call.'),
    sections,
    used.length ? h('p', { class: 'small guide-sources' }, h('b', null, 'Sources: '), used.map((x) => shortSource(x.title || x.id)).join('; '), '.') : null,
    used.length ? h('details', { class: 'small' }, h('summary', null, 'Full source list'),
      h('ul', { class: 'src-list' }, used.map((x) => h('li', null, x.title || x.id,
        [x.year, x.country].filter(Boolean).length ? ` (${[x.year, x.country].filter(Boolean).join('; ')})` : '',
        x.url && /^https:\/\//.test(x.url) ? [' ', h('a', { href: x.url, target: '_blank', rel: 'noopener' }, 'link')] : null)))) : null,
    h('button', { class: 'btn secondary block', type: 'button', onclick: closeSheet }, 'Close')));
  s.hidden = false;
  s.onclick = (e) => { if (e.target === s) closeSheet(); };
}

// ---------------------------------------------------------------- 5. Model
// Frozen ImageNet backbone (model/backbone.onnx) gives a 1280-number embedding per photo.
// A small head (model/head.json) turns it into 5 class probabilities, or "not sure".
const Model = {
  session: null, meta: null, headRaw: null, shipped: null, adapted: null, active: null,
  adaptedMismatch: null, ready: false, error: null, inputName: 'input', outputName: 'embedding',
};
let resolveModelReady;
const modelReady = new Promise((r) => { resolveModelReady = r; });

function normalize(v) {
  let s = 0;
  for (let i = 0; i < v.length; i++) s += v[i] * v[i];
  s = Math.sqrt(s) || 1;
  const out = new Float32Array(v.length);
  for (let i = 0; i < v.length; i++) out[i] = v[i] / s;
  return out;
}
function dot(a, b) { let s = 0; for (let i = 0; i < a.length; i++) s += a[i] * b[i]; return s; }

// Read head.json (schema v1 in SPEC.md). Classes and embed_dim come from the file, never hard-coded.
// The backbone output is already standardised (standardised_in_backbone), so the embedding is used as is.
// route_to_officer (optional, head v3): classes that are never shown as a diagnosis (the "other" class for a
// problem outside the list). When one is the top class, the photo goes to the officer like a "not sure" photo.
function parseHead(raw) {
  const classes = raw.classes;
  const C = classes.length;
  const D = raw.embed_dim;
  if (!Array.isArray(raw.W) || raw.W.length !== C || raw.W.some((r) => r.length !== D)) throw new Error('head.json: W is not classes x embed_dim');
  if (!Array.isArray(raw.b) || raw.b.length !== C) throw new Error('head.json: b length does not match classes');
  const W = new Float32Array(C * D);
  raw.W.forEach((row, i) => W.set(row, i * D));
  const ood = raw.ood || {};
  const head = {
    version: String(raw.version), classes: classes.slice(), C, D, W, b: Float32Array.from(raw.b),
    toOfficer: Array.isArray(raw.route_to_officer) ? raw.route_to_officer.filter((c) => classes.includes(c)) : [],
    temperature: Number(raw.temperature) || 1,
    threshold: Number.isFinite(raw.threshold) ? raw.threshold : 0.5,
    cutoff: Number.isFinite(ood.cutoff) ? ood.cutoff : Infinity,
    // Second familiarity check (optional field; absent = the k-nearest check alone): a photo also counts as familiar
    // when its single nearest officer-labelled row (localRefs; never reference.bin rows) is within this distance.
    localCutoff: Number.isFinite(ood.local_nearest_cutoff) ? ood.local_nearest_cutoff : null,
    // Familiarity check: k nearest stored photos (reference.bin, filled in by loadModel).
    // Older heads with class centroids use the nearest centroid instead (k = 1).
    refRows: [], k: 1, refFile: null,
    localRefs: [],
    prior_strength: Number.isFinite(raw.prior_strength) ? raw.prior_strength : 1,
    // "high" confidence band: optional field in head.json, else halfway between threshold and 1.
    highCut: Number.isFinite(raw.high_band) ? raw.high_band : raw.threshold + (1 - raw.threshold) / 2,
  };
  if (ood.reference && ood.reference.file) {
    head.refFile = ood.reference;
    head.k = ood.k || 10;
  } else if (Array.isArray(ood.centroids)) {
    head.refRows = ood.centroids.map((c) => normalize(Float32Array.from(c)));
  }
  return head;
}

// Apply a stored adapted head (from officer labels) on top of the shipped head.
function withAdapted(shipped, ad) {
  return Object.assign({}, shipped, {
    W: ad.W instanceof Float32Array ? ad.W : Float32Array.from(ad.W),
    b: ad.b instanceof Float32Array ? ad.b : Float32Array.from(ad.b),
    version: ad.version,
    localRefs: (ad.ref_add || []).map((c) => c instanceof Float32Array ? c : Float32Array.from(c)),
    isAdapted: true,
  });
}

function softmax(z) {
  const m = Math.max(...z);
  const e = z.map((v) => Math.exp(v - m));
  const s = e.reduce((a, b) => a + b, 0);
  return e.map((v) => v / s);
}

// probs = softmax((W e + b) / T). "Not sure" (sent to the officer) if the top class is a route_to_officer class
// ("looks like a different problem"), OR the photo is unfamiliar, OR max prob < threshold. Same order as ml/train_eval.py.
// Familiar: distance = 1 - mean cosine similarity to the k most similar stored photos (shipped + officer-labelled)
// <= cutoff, OR (head.localCutoff set and officer-labelled rows exist) 1 - cosine similarity to the single nearest
// officer-labelled row <= localCutoff. The shipped reference rows never count for the second check.
function predictHead(head, e) {
  const { C, D, W, b, temperature: T } = head;
  const z = new Array(C);
  for (let c = 0; c < C; c++) {
    let s = b[c];
    const off = c * D;
    for (let d = 0; d < D; d++) s += W[off + d] * e[d];
    z[c] = s / T;
  }
  const probs = softmax(z);
  let idx = 0;
  for (let c = 1; c < C; c++) if (probs[c] > probs[idx]) idx = c;
  const refs = head.localRefs.length ? head.refRows.concat(head.localRefs) : head.refRows;
  const dist = refs.length ? KahawaCore.familiarityDistance(e, refs, Math.min(head.k, refs.length)) : null;
  const localDist = head.localCutoff != null && head.localRefs.length ? KahawaCore.nearestDistance(e, head.localRefs) : null;
  const lowConfidence = probs[idx] < head.threshold;
  const unfamiliar = dist != null && !KahawaCore.isFamiliar(dist, head.cutoff, localDist == null ? Infinity : localDist, head.localCutoff);
  const otherProblem = (head.toOfficer || []).includes(head.classes[idx]);
  const notSure = lowConfidence || unfamiliar || otherProblem;
  return {
    label: notSure ? null : head.classes[idx], top: head.classes[idx], class_index: idx,
    probs, max_prob: probs[idx], not_sure: notSure,
    reason: otherProblem ? 'other_problem' : (unfamiliar ? 'unfamiliar' : (lowConfidence ? 'low_confidence' : null)),
    band: notSure ? null : (probs[idx] >= head.highCut ? 'high' : 'medium'),
    ood_distance: dist, local_distance: localDist,
    familiar_by: dist == null || unfamiliar ? null : (dist <= head.cutoff ? 'stored_photos' : 'officer_photo'),
    head_version: head.version,
  };
}

function loadImage(blob) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(blob);
    const img = new Image();
    img.onload = () => { URL.revokeObjectURL(url); resolve(img); };
    img.onerror = () => { URL.revokeObjectURL(url); reject(new Error('could not read this image')); };
    img.src = url;
  });
}
function canvas(w, hgt) {
  const c = document.createElement('canvas');
  c.width = w; c.height = hgt;
  return c;
}

// Resize shorter side to 256 and centre-crop 224 (values from backbone_meta.json), the same way as the
// Python pipeline (PIL Image.resize with BILINEAR, which smooths when shrinking; then a centre crop).
// The resize below copies PIL's filter and rounding, so the phone sees the same pixels as the evaluation.
// Simplification: photos more than twice the needed size are first halved by the browser (2x2 averaging),
// so very large phone photos differ slightly from a direct PIL resize.
const roundHalfEven = (x) => { const r = Math.round(x); return (Math.abs(x % 1) === 0.5 && r % 2) ? r - 1 : r; };

// PIL precompute_coeffs (Resample.c) for the bilinear filter, as 22-bit fixed-point integers.
function pilCoeffs(inSize, outSize) {
  const scale = inSize / outSize;
  const fs = Math.max(scale, 1);
  const support = fs; // bilinear filter support = 1
  const ksize = Math.ceil(support) * 2 + 1;
  const k = new Float64Array(outSize * ksize);
  const lo = new Int32Array(outSize), n = new Int32Array(outSize);
  for (let o = 0; o < outSize; o++) {
    const center = (o + 0.5) * scale;
    let xmin = Math.trunc(center - support + 0.5); if (xmin < 0) xmin = 0;
    let xmax = Math.trunc(center + support + 0.5); if (xmax > inSize) xmax = inSize;
    xmax -= xmin;
    let ww = 0;
    for (let x = 0; x < xmax; x++) {
      const t = Math.abs((x + xmin - center + 0.5) / fs);
      const w = t < 1 ? 1 - t : 0;
      k[o * ksize + x] = w; ww += w;
    }
    for (let x = 0; x < xmax; x++) {
      const v = ww ? k[o * ksize + x] / ww : 0;
      k[o * ksize + x] = v < 0 ? Math.trunc(-0.5 + v * 4194304) : Math.trunc(0.5 + v * 4194304); // 2^22
    }
    lo[o] = xmin; n[o] = xmax;
  }
  return { k, lo, n, ksize };
}
const clip8 = (ss) => { const v = Math.floor(ss / 4194304); return v < 0 ? 0 : v > 255 ? 255 : v; };

function centreCrop(img) {
  const R = (Model.meta && Model.meta.resize_shorter) || 256;
  const S = (Model.meta && Model.meta.input_size) || 224;
  let src = img;
  let w = img.naturalWidth || img.width;
  let hh = img.naturalHeight || img.height;
  while (Math.min(w, hh) / 2 >= 2 * R) { // keep at least 2x the target size for the exact filter below
    const c = canvas(Math.round(w / 2), Math.round(hh / 2));
    const cx = c.getContext('2d');
    cx.imageSmoothingQuality = 'high';
    cx.drawImage(src, 0, 0, c.width, c.height);
    src = c; w = c.width; hh = c.height;
  }
  const full = canvas(w, hh);
  const fctx = full.getContext('2d', { willReadFrequently: true });
  fctx.drawImage(src, 0, 0, w, hh);
  const px = fctx.getImageData(0, 0, w, hh).data;
  const s = R / Math.min(w, hh);
  const ow = Math.max(1, roundHalfEven(w * s)), oh = Math.max(1, roundHalfEven(hh * s));
  const left = Math.floor((ow - S) / 2), top = Math.floor((oh - S) / 2);
  const cx = pilCoeffs(w, ow), cy = pilCoeffs(hh, oh);
  // Horizontal pass (only the S output columns we keep, only the input rows the vertical pass needs).
  const y0 = cy.lo[top], y1 = cy.lo[top + S - 1] + cy.n[top + S - 1];
  const tmp = new Uint8ClampedArray(S * (y1 - y0) * 3);
  for (let y = y0; y < y1; y++) {
    for (let j = 0; j < S; j++) {
      const o = left + j, base = o * cx.ksize, x0 = cx.lo[o];
      let r = 2097152, g = 2097152, b = 2097152; // 2^21: rounding, as in PIL
      for (let t = 0; t < cx.n[o]; t++) {
        const kk = cx.k[base + t], p = (y * w + x0 + t) * 4;
        r += px[p] * kk; g += px[p + 1] * kk; b += px[p + 2] * kk;
      }
      const q = ((y - y0) * S + j) * 3;
      tmp[q] = clip8(r); tmp[q + 1] = clip8(g); tmp[q + 2] = clip8(b);
    }
  }
  // Vertical pass into an S x S RGBA image.
  const out = canvas(S, S);
  const octx = out.getContext('2d', { willReadFrequently: true });
  const id = octx.createImageData(S, S);
  for (let i = 0; i < S; i++) {
    const o = top + i, base = o * cy.ksize, ys = cy.lo[o];
    for (let j = 0; j < S; j++) {
      let r = 2097152, g = 2097152, b = 2097152;
      for (let t = 0; t < cy.n[o]; t++) {
        const kk = cy.k[base + t], q = ((ys + t - y0) * S + j) * 3;
        r += tmp[q] * kk; g += tmp[q + 1] * kk; b += tmp[q + 2] * kk;
      }
      const p = (i * S + j) * 4;
      id.data[p] = clip8(r); id.data[p + 1] = clip8(g); id.data[p + 2] = clip8(b); id.data[p + 3] = 255;
    }
  }
  octx.putImageData(id, 0, 0);
  return out;
}

// Simple photo check before the AI: too dark, too bright, or almost no detail -> ask to retake.
// Thresholds are rough guesses, not tuned on data.
function photoQuality(px, n) {
  let s = 0, s2 = 0;
  for (let i = 0; i < px.length; i += 4) {
    const y = (0.299 * px[i] + 0.587 * px[i + 1] + 0.114 * px[i + 2]) / 255;
    s += y; s2 += y * y;
  }
  const mean = s / n;
  const sd = Math.sqrt(Math.max(0, s2 / n - mean * mean));
  const reason = mean < 0.12 ? 'too dark' : mean > 0.92 ? 'too bright' : sd < 0.035 ? 'almost no detail' : null;
  return { mean, sd, bad: !!reason, reason };
}

let runChain = Promise.resolve(); // one inference at a time
async function embedCanvas(crop) {
  const S = crop.width;
  const px = crop.getContext('2d', { willReadFrequently: true }).getImageData(0, 0, S, S).data;
  const mean = (Model.meta && Model.meta.mean) || [0.485, 0.456, 0.406];
  const std = (Model.meta && Model.meta.std) || [0.229, 0.224, 0.225];
  const n = S * S;
  const x = new Float32Array(3 * n);
  for (let i = 0, p = 0; i < n; i++, p += 4) {
    x[i] = (px[p] / 255 - mean[0]) / std[0];
    x[n + i] = (px[p + 1] / 255 - mean[1]) / std[1];
    x[2 * n + i] = (px[p + 2] / 255 - mean[2]) / std[2];
  }
  const quality = photoQuality(px, n);
  const job = runChain.then(async () => {
    const out = await Model.session.run({ [Model.inputName]: new ort.Tensor('float32', x, [1, 3, S, S]) });
    return new Float32Array(out[Model.outputName].data);
  });
  runChain = job.catch(() => {});
  return { embedding: await job, quality };
}

function thumbOf(crop, size = 160) {
  const c = canvas(size, size);
  const cx = c.getContext('2d');
  cx.imageSmoothingQuality = 'high';
  cx.drawImage(crop, 0, 0, size, size);
  return c.toDataURL('image/jpeg', 0.72);
}

async function classifyImage(img) {
  await modelReady;
  if (!Model.ready) throw new Error(Model.error || 'model not loaded');
  const t0 = performance.now();
  const crop = centreCrop(img);
  const { embedding, quality } = await embedCanvas(crop);
  const r = predictHead(Model.active, embedding);
  return Object.assign(r, { embedding, quality, thumb: thumbOf(crop), ms: Math.round(performance.now() - t0) });
}

function setModelStatus(text, kind) {
  const el = $('#model-status');
  el.textContent = text;
  el.className = 'chip ' + (kind === 'ok' ? 'chip-ok' : kind === 'bad' ? 'chip-bad' : 'chip-wait');
}

async function loadModel() {
  try {
    if (typeof ort === 'undefined') throw new Error('onnxruntime-web did not load');
    // GitHub Pages cannot send the headers needed for multi-threading, so use 1 thread (also safest on iPhone).
    ort.env.wasm.wasmPaths = absUrl('vendor/ort/'); // './vendor/ort/' made absolute, works under any sub-path
    ort.env.wasm.numThreads = 1;
    ort.env.wasm.proxy = false;
    setModelStatus('Loading model', 'wait');
    const [bytes, headRaw, meta] = await Promise.all([
      fetchBytes('model/backbone.onnx', (got, total) => {
        setModelStatus('Loading model ' + (total ? Math.min(99, Math.round(100 * got / total)) + '%' : Math.round(got / 1e6) + ' MB'), 'wait');
      }),
      fetchJSON('model/head.json'),
      fetchJSON('model/backbone_meta.json').catch(() => null),
    ]);
    if (typeof KahawaCore === 'undefined') throw new Error('lib/kahawa-core.js did not load');
    Model.meta = meta;
    Model.headRaw = headRaw;
    Model.shipped = parseHead(headRaw);
    if (meta && meta.embed_dim && meta.embed_dim !== Model.shipped.D) throw new Error('head.json embed_dim does not match the backbone');
    const ref = Model.shipped.refFile;
    if (ref) { // stored training photos for the familiarity check (int8 rows + per-row scales)
      const r = await fetch('model/' + ref.file);
      if (!r.ok) throw new Error('model/' + ref.file + ': ' + r.status);
      const buf = await r.arrayBuffer();
      if (buf.byteLength !== ref.n * ref.dim + 4 * ref.n) throw new Error('model/' + ref.file + ' does not match head.json (an old copy?). Go online and reload.');
      Model.shipped.refRows = KahawaCore.parseReference(buf, ref.n, ref.dim);
    }
    Model.session = await ort.InferenceSession.create(bytes, { executionProviders: ['wasm'], graphOptimizationLevel: 'all' });
    Model.inputName = Model.session.inputNames.includes('input') ? 'input' : Model.session.inputNames[0];
    Model.outputName = Model.session.outputNames.includes('embedding') ? 'embedding' : Model.session.outputNames[0];
    await applyStoredAdaptedHead();
    Model.ready = true;
    setModelStatus('Model ready', 'ok');
  } catch (e) {
    console.warn('Model failed to load:', e);
    Model.error = String(e && e.message || e);
    setModelStatus('Model error', 'bad');
  }
  resolveModelReady();
  renderCurrent();
}

async function applyStoredAdaptedHead() {
  Model.adapted = null;
  Model.adaptedMismatch = null;
  Model.active = Model.shipped;
  let ad = null;
  try { ad = await DB.get('meta', 'adapted_head'); } catch (e) { /* no storage */ }
  if (!ad) return;
  if (ad.base_version !== Model.shipped.version || ad.classes.join() !== Model.shipped.classes.join()) {
    Model.adaptedMismatch = ad; // made for another shipped head: ignored (labels are kept; refit to rebuild)
    return;
  }
  Model.adapted = ad;
  Model.active = withAdapted(Model.shipped, ad);
}

// ---------------------------------------------------------------- 6. Learning loop
// Refit the head on officer-labelled embeddings, on the phone (mirrors adapt() in ml/train_eval.py):
//   minimise  mean_i CE(softmax((W x_i + b)/T), y_i) + (prior_strength/2) (||W - W0||^2 + ||b - b0||^2)
// W0, b0 = shipped head. Temperature and threshold are kept. Python uses L-BFGS; here it is full-batch
// gradient descent (200 steps) with a backtracking step size: the step halves when the loss would not
// go down enough, and grows a little after each good step.
function refitHead(base, X, y, steps = REFIT_STEPS) {
  const { C, D, temperature: T } = base;
  const lam = base.prior_strength;
  const W0 = base.W, b0 = base.b, n = X.length;
  const W = Float64Array.from(W0), b = Float64Array.from(b0);
  const Wn = new Float64Array(C * D), bn = new Float64Array(C);
  const gW = new Float64Array(C * D), gb = new Float64Array(C), z = new Float64Array(C);
  // Loss (and, if asked, gradient into gW/gb) at weights (w, v).
  function evaluate(w, v, withGrad) {
    let reg = 0, ce = 0, correct = 0;
    for (let k = 0; k < C * D; k++) { const dl = w[k] - W0[k]; reg += dl * dl; if (withGrad) gW[k] = lam * dl; }
    for (let c = 0; c < C; c++) { const dl = v[c] - b0[c]; reg += dl * dl; if (withGrad) gb[c] = lam * dl; }
    for (let i = 0; i < n; i++) {
      const x = X[i];
      let m = -Infinity, arg = 0;
      for (let c = 0; c < C; c++) {
        let s = v[c];
        const off = c * D;
        for (let d = 0; d < D; d++) s += w[off + d] * x[d];
        z[c] = s / T;
        if (z[c] > m) { m = z[c]; arg = c; }
      }
      let sum = 0;
      for (let c = 0; c < C; c++) { z[c] = Math.exp(z[c] - m); sum += z[c]; }
      for (let c = 0; c < C; c++) z[c] /= sum; // probabilities
      ce -= Math.log(Math.max(z[y[i]], 1e-12));
      if (arg === y[i]) correct++;
      if (!withGrad) continue;
      for (let c = 0; c < C; c++) {
        const g = (z[c] - (c === y[i] ? 1 : 0)) / (T * n);
        gb[c] += g;
        const off = c * D;
        for (let d = 0; d < D; d++) gW[off + d] += g * x[d];
      }
    }
    return { loss: ce / n + 0.5 * lam * reg, correct };
  }
  let cur = evaluate(W, b, true);
  const res = { n, steps, lossBefore: cur.loss, correctBefore: cur.correct };
  // First step size: 1 / (upper bound on curvature).
  let L = lam;
  for (const x of X) L += 0.5 * (dot(x, x) + 1) / (T * T * n);
  let lr = 1 / L, done = 0;
  const gnorm = () => { let s = 0; for (let k = 0; k < C * D; k++) s += gW[k] * gW[k]; for (let c = 0; c < C; c++) s += gb[c] * gb[c]; return s; };
  res.gradBefore = Math.sqrt(gnorm());
  for (let it = 0; it < steps; it++) {
    const g2 = gnorm();
    if (g2 < 1e-16) break;
    let ok = false;
    for (let tries = 0; tries < 40 && !ok; tries++) {
      for (let k = 0; k < C * D; k++) Wn[k] = W[k] - lr * gW[k];
      for (let c = 0; c < C; c++) bn[c] = b[c] - lr * gb[c];
      if (evaluate(Wn, bn, false).loss <= cur.loss - 0.5 * lr * g2) ok = true; else lr *= 0.5;
    }
    if (!ok) break;
    W.set(Wn); b.set(bn);
    cur = evaluate(W, b, true);
    lr *= 1.5;
    done++;
  }
  Object.assign(res, { lossAfter: cur.loss, correctAfter: cur.correct, stepsDone: done, gradAfter: Math.sqrt(gnorm()) });
  res.W = Float32Array.from(W);
  res.b = Float32Array.from(b);
  return res;
}

// Officer labels: a class name, 'other' (a problem not in the list) or 'skip' (cannot tell).
// An AI answer of 'other' never exists (the photo is "not sure"), so it never counts as rust.
// A photo the relay farmer disputed ("I think it's something else") counts only once the officer labels it.
const finalLabel = (p) => (p.officer_label && p.officer_label !== 'skip') ? p.officer_label : ((p.not_sure || p.disputed) ? null : p.label);
// The label the officer's "Different problem (not in list)" button saves: the head's "other" class when it has one.
const otherLabel = () => (Model.shipped && Model.shipped.toOfficer && Model.shipped.toOfficer[0]) || 'other';
// Classes the AI can give as an answer (route_to_officer classes are never shown as a diagnosis).
const answerClasses = () => (Model.shipped ? Model.shipped.classes.filter((c) => !(Model.shipped.toOfficer || []).includes(c)) : []);

async function officerLabelled() {
  const classes = Model.shipped ? Model.shipped.classes : [];
  return (await DB.all('photos')).filter((p) => classes.includes(p.officer_label) && p.embedding);
}

async function updateModelOnPhone() {
  const base = Model.shipped;
  const L = await officerLabelled();
  if (!L.length) return null;
  const X = L.map((p) => p.embedding instanceof Float32Array ? p.embedding : Float32Array.from(p.embedding));
  const y = L.map((p) => base.classes.indexOf(p.officer_label));
  const fit = refitHead(base, X, y);
  const counts = {};
  L.forEach((p) => { counts[p.officer_label] = (counts[p.officer_label] || 0) + 1; });
  const ad = {
    key: 'adapted_head', source: 'this phone', base_version: base.version, classes: base.classes,
    version: `${base.version}+local${L.length}`, n_labels: L.length, label_counts: counts,
    labels: L.map((p) => p.officer_label),
    W: fit.W, b: fit.b,
    // Officer-labelled photos join the familiarity reference, so similar photos stop being "not sure".
    // "Different problem" photos train the head's "other" class when it has one (head v3); with an older head without
    // it they are left out of the refit (officerLabelled keeps only labels that are classes of the head).
    ref_add: X.map((x) => normalize(x)),
    created: Date.now(), steps: fit.steps, steps_done: fit.stepsDone,
    loss_before: fit.lossBefore, loss_after: fit.lossAfter, correct_before: fit.correctBefore, correct_after: fit.correctAfter,
    grad_before: fit.gradBefore, grad_after: fit.gradAfter,
  };
  await DB.put('meta', ad);
  await applyStoredAdaptedHead();
  return ad;
}

// Update file (format in SPEC.md, kind 'kahawa-head-update'): adapted W, b and the added reference rows
// (L2-normalised embeddings stored as int8 with one scale per row). No photos are included.
function quantRow(v) {
  let mx = 0;
  for (let i = 0; i < v.length; i++) mx = Math.max(mx, Math.abs(v[i]));
  const scale = mx / 127 || 1;
  return { q: Array.from(v, (x) => Math.round(x / scale)), scale };
}
async function buildUpdate() {
  const base = Model.shipped, ad = Model.adapted;
  const corrections = await wordingList();
  const rows = (ad.ref_add || []).map(quantRow);
  const W = base.classes.map((c, k) => Array.from(ad.W.subarray(k * base.D, (k + 1) * base.D), (v) => +v.toFixed(6)));
  const out = {
    kind: 'kahawa-head-update', base_version: base.version, n_labels: ad.n_labels,
    source: ad.source === 'this phone' ? `Officer labels on one phone (${new Date(ad.created).toISOString().slice(0, 10)})` : ad.source,
    W, b: Array.from(ad.b, (v) => +v.toFixed(6)),
    reference_add: { int8: rows.map((r) => r.q), scale: rows.map((r) => r.scale) },
    labels: ad.labels || [],
    wording_corrections: corrections, // reports of wrong wording, for review (they change nothing by themselves)
  };
  return out;
}
async function exportUpdate() {
  const out = await buildUpdate();
  const text = JSON.stringify(out);
  download(`${FILE_PREFIX}-update-${out.base_version}-${out.n_labels}labels.json`, text, 'application/json');
  return { size: text.length, corrections: out.wording_corrections.length };
}
async function importUpdateJSON(j, sourceNote) {
  const base = Model.shipped;
  if (!j || j.kind !== 'kahawa-head-update') throw new Error(`this is not a ${APP_NAME} update file`);
  if (j.base_version !== base.version) throw new Error(`made for model ${j.base_version}, this phone has ${base.version}`);
  if (!Array.isArray(j.W) || j.W.length !== base.C || j.W.some((r) => r.length !== base.D) || !Array.isArray(j.b) || j.b.length !== base.C) {
    throw new Error('weights do not match this model');
  }
  const W = new Float32Array(base.C * base.D);
  j.W.forEach((row, k) => W.set(row, k * base.D));
  const ra = j.reference_add || { int8: [], scale: [] };
  const refs = ra.int8 && ra.int8.length ? KahawaCore.rowsFromInt8(ra.int8, ra.scale) : [];
  const counts = {};
  (j.labels || []).forEach((l) => { counts[l] = (counts[l] || 0) + 1; });
  const ad = {
    key: 'adapted_head', source: sourceNote || j.source || 'shared file', base_version: base.version, classes: base.classes,
    version: `${base.version}+shared${j.n_labels || 0}`, n_labels: j.n_labels || 0, label_counts: counts, labels: j.labels || [],
    W, b: Float32Array.from(j.b), ref_add: refs, created: Date.now(),
  };
  await DB.put('meta', ad);
  await applyStoredAdaptedHead();
  return ad;
}

// ---------------------------------------------------------------- 7. Co-op statistics
// Uses lib/kahawa-core.js (shared with ml/train_eval.py): maximum-likelihood Beta(a, b) prior across villages
// (beta-binomial; capped so it never counts for more than 50 photos; fallback Beta(1, 4) below 3 villages)
// and the Beta CDF. rows: [{name, n (photos answered), x (rust photos), ...}] -> adds raw, adjusted, pAbove, alert.
function villageStats(rows) {
  const used = rows.filter((r) => r.n > 0);
  const fit = KahawaCore.fitBetaBinomial(used.map((r) => r.x), used.map((r) => r.n));
  const prior = { a: fit.alpha, b: fit.beta, source: fit.fallback ? 'fallback' : 'fitted', capped: !!fit.capped, k: used.length };
  const out = rows.map((r) => {
    if (!r.n) return Object.assign({}, r, { raw: null, adjusted: null, pAbove: null, alert: false });
    const A = prior.a + r.x, B = prior.b + r.n - r.x;
    const pAbove = 1 - KahawaCore.betaCdf(ALERT_RATE, A, B);
    return Object.assign({}, r, { raw: r.x / r.n, adjusted: A / (A + B), pAbove, alert: pAbove > ALERT_PROB });
  });
  out.sort((p, q) => (q.pAbove ?? -1) - (p.pAbove ?? -1) || q.n - p.n);
  return { prior, rows: out };
}

async function villageRows() {
  const [plots, photos] = await Promise.all([DB.all('plots'), DB.all('photos')]);
  const byPlot = new Map();
  photos.forEach((p) => { if (!byPlot.has(p.plot_id)) byPlot.set(p.plot_id, []); byPlot.get(p.plot_id).push(p); });
  const groups = new Map();
  for (const pl of plots) {
    const key = (pl.village || '').trim().toLowerCase() || '(no village)';
    if (!groups.has(key)) groups.set(key, { name: (pl.village || '').trim() || '(no village)', plots: 0, n: 0, x: 0, waiting: 0, synthetic: false, samples: false });
    const g = groups.get(key);
    g.plots += 1;
    if (pl.synthetic) {
      g.synthetic = true;
      g.n += pl.synthetic_counts.answered;
      g.x += pl.synthetic_counts.rust;
      continue;
    }
    if (pl.has_samples) g.samples = true;
    for (const p of byPlot.get(pl.id) || []) {
      const lab = finalLabel(p);
      if (lab) { g.n += 1; if (lab === 'rust') g.x += 1; } else if (!p.officer_label) g.waiting += 1;
    }
  }
  return [...groups.values()];
}

// Synthetic demo villages, clearly labelled. Chosen so a 2-of-3 village is pulled down and does not alert,
// while a 30-of-80 village alerts.
const DEMO_VILLAGES = [
  ['Demo village A (synthetic)', 2, 3], ['Demo village B (synthetic)', 30, 80], ['Demo village C (synthetic)', 9, 70],
  ['Demo village D (synthetic)', 12, 75], ['Demo village E (synthetic)', 8, 60], ['Demo village F (synthetic)', 14, 90],
];

// ---------------------------------------------------------------- 8. Screens
let currentTab = 'visit';
let samples = null; // samples/manifest.json content, if present

function card(cls, ...kids) { return h('div', { class: 'card ' + (cls || '') }, ...kids); }

// ----- 8a. Plot visit
const visit = { step: 'consent', plot: null, photos: [], last: null, retake: null, busy: false, knownVillages: [], unfinished: null,
  farmDraft: {}, confirmDispute: null };

const posOf = (i) => i < PROTOCOL.trees * PROTOCOL.leaves
  ? { tree: Math.floor(i / PROTOCOL.leaves) + 1, leaf: (i % PROTOCOL.leaves) + 1 }
  : { tree: null, leaf: null };

async function refreshVisitContext() {
  try {
    const plots = await DB.all('plots');
    visit.knownVillages = [...new Set(plots.filter((p) => !p.synthetic).map((p) => (p.village || '').trim()).filter(Boolean))].sort();
    const open = plots.filter((p) => p.status === 'in_progress' && !p.synthetic).sort((a, b) => b.updated - a.updated);
    visit.unfinished = (visit.plot && open[0] && open[0].id === visit.plot.id) ? null : (open[0] || null);
  } catch (e) { /* storage unavailable */ }
}

function renderVisit() {
  const root = $('#tab-visit');
  const views = { consent: viewConsent, details: viewDetails, photos: viewPhotos, summary: viewSummary, saved: viewSaved };
  root.replaceChildren(...[].concat(views[visit.step]()));
}

function viewConsent() {
  const out = [];
  if (visit.unfinished) {
    const u = visit.unfinished;
    out.push(card('warn', h('div', { class: 'card-head' }, icon('flag'), 'Unfinished visit'),
      h('p', null, `${u.village}, ${fmtDate(u.created)}: ${plural(u.photo_ids.length, 'photo')}.`),
      h('div', { class: 'stack' },
        h('button', { class: 'btn block', type: 'button', onclick: () => resumeVisit(u) }, 'Continue this visit'),
        h('button', { class: 'btn secondary block', type: 'button', onclick: () => discardVisit(u) }, icon('trash'), 'Discard this visit'))));
  }
  out.push(card('', h('h2', null, 'Plot visit'), h('p', { class: 'small' }, 'Step 1 of 3: ask the farmer first.'),
    answerBlock('consent_photos'),
    h('div', { class: 'stack', style: 'margin-top:14px' },
      h('button', { class: 'btn block', type: 'button', onclick: () => { visit.farmDraft = {}; visit.step = 'details'; renderVisit(); } }, icon('check'), 'Farmer agrees'),
      h('button', { class: 'btn secondary block', type: 'button', onclick: () => toast('No photos taken. Thank the farmer.') }, 'Farmer does not agree'))));
  return out;
}

function viewDetails() {
  const dl = h('datalist', { id: 'villages' }, visit.knownVillages.map((v) => h('option', { value: v })));
  const village = h('input', { type: 'text', list: 'villages', autocomplete: 'off', placeholder: 'Type or pick a village', value: store.get('lastVillage', '') });
  const member = h('input', { type: 'text', inputmode: 'numeric', autocomplete: 'off', placeholder: 'e.g. 1234' });
  const start = async () => {
    const v = village.value.trim();
    if (!v) { village.focus(); toast('Please enter the village.'); return; }
    let hash = null;
    const num = member.value.trim();
    if (num) {
      try { hash = await sha256Hex('kahawa-check|member|' + num); } catch (e) { toast('Cannot scramble the number on this browser; it was not saved.'); }
    }
    store.set('lastVillage', v);
    visit.plot = { id: uid(), created: Date.now(), updated: Date.now(), village: v, member_hash: hash, status: 'in_progress',
      consent: true, photo_ids: [], checklist: {}, has_samples: false, synthetic: false,
      farm: Object.assign({ variety: null, last_spray: null, fruit_load: null }, visit.farmDraft) };
    visit.photos = []; visit.last = null; visit.retake = null; visit.confirmDispute = null;
    await DB.put('plots', visit.plot);
    askPersist();
    visit.step = 'photos';
    renderVisit();
  };
  return card('', h('h2', null, 'Farm details'), h('p', { class: 'small' }, 'Step 2 of 3.'),
    h('div', { class: 'stack' },
      h('label', { class: 'field' }, h('span', null, 'Village'), village, dl),
      h('label', { class: 'field' }, h('span', null, 'Cooperative member number'), member),
      h('p', { class: 'small' }, icon('lock'), ' Only a scrambled code (SHA-256 hash) of the number is saved, not the number. Short numbers can still be guessed by someone who has this phone, so keep the phone private.'),
      farmBlock(visit.farmDraft, null),
      h('button', { class: 'btn block', type: 'button', onclick: start }, 'Start leaf photos', icon('arrow')),
      h('button', { class: 'btn secondary block', type: 'button', onclick: () => { visit.step = 'consent'; renderVisit(); } }, 'Back')));
}

// Three optional taps for the officer (variety, last spray, fruit load). Tapping a chosen answer again clears it.
// The buttons update in place (no re-render), so text typed on the same screen is kept. onChange: save callback.
function farmTaps(target, onChange) {
  return FARM_TAPS.map((t) => {
    const btns = t.options.map(([k, label]) => h('button', { type: 'button', 'aria-pressed': String(target[t.key] === k), 'data-farm': t.key + ':' + k,
      onclick: (e) => {
        target[t.key] = target[t.key] === k ? null : k;
        e.currentTarget.parentNode.querySelectorAll('button').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.farm === t.key + ':' + target[t.key])));
        if (onChange) onChange();
      } }, label));
    return h('div', { class: 'farm-q' }, h('span', { class: 'farm-label' }, t.label),
      h('div', { class: 'seg seg-' + t.cols, role: 'group', 'aria-label': t.label + ' (optional)' }, btns));
  });
}
function farmBlock(target, onChange) {
  return h('div', { class: 'farm' }, h('span', { class: 'label-nonai' }, FARM_NOTE),
    h('p', { class: 'small', style: 'margin-top:6px' }, 'Optional. Tap if you know; leave blank if not.'), farmTaps(target, onChange));
}
// One line for the plot card, the officer screen and the CSV: "Variety: Ruiru 11 · Last spray: Never · ...".
function farmLine(farm) {
  const parts = FARM_TAPS.map((t) => farm && farm[t.key] ? `${t.label}: ${farmValue(t.key, farm[t.key])}` : null).filter(Boolean);
  return parts.length ? parts.join(' · ') : null;
}

function fileButton(text, iconName, capture, cls, disabled) {
  const input = h('input', { type: 'file', accept: 'image/*', capture: capture ? 'environment' : null, disabled });
  input.addEventListener('change', () => {
    const f = input.files && input.files[0];
    input.value = '';
    if (f) handlePhoto(f, null);
  });
  return h('label', { class: 'btn ' + cls, 'aria-disabled': disabled ? 'true' : null }, icon(iconName), text, input);
}

function viewPhotos() {
  const n = visit.photos.length;
  const total = PROTOCOL.trees * PROTOCOL.leaves;
  const pos = posOf(n);
  const ready = Model.ready && !visit.busy;
  const out = [];
  out.push(card('', h('h2', null, visit.plot.village),
    h('p', { class: 'steps' }, n < total ? `Tree ${pos.tree} of ${PROTOCOL.trees} · leaf ${pos.leaf} of ${PROTOCOL.leaves}` : 'All 15 photos taken'),
    h('div', { class: 'progress', role: 'progressbar', 'aria-valuemin': 0, 'aria-valuemax': total, 'aria-valuenow': Math.min(n, total) },
      h('div', { style: `width:${Math.min(100, 100 * n / total)}%` })),
    h('p', { class: 'small' }, `${n} of ${total} photos. Photograph the underside of 3 leaves on each of 5 trees. You can finish early.`)));
  if (!Model.ready) out.push(h('p', { class: 'notice' }, Model.error ? 'The model could not load: ' + Model.error : 'The model is still loading. Photo buttons will work in a moment.'));
  const extra = n >= total ? ' (extra)' : '';
  out.push(h('div', { class: 'btn-grid' },
    fileButton('Take photo' + extra, 'camera', true, 'wide', !ready),
    fileButton('Choose photo', 'image', false, 'secondary', !ready),
    h('button', { class: 'btn secondary', type: 'button', disabled: !ready || !samples, onclick: openSamples, title: samples ? null : 'No sample photos found' }, icon('grid'), 'Try sample photos')));
  if (visit.busy) out.push(card('', h('p', null, h('span', { class: 'busy' }), ' Checking the photo on this phone…')));
  else if (visit.retake) out.push(retakeCard());
  else if (visit.last) out.push(resultCard(visit.last));
  out.push(h('div', { class: 'btn-grid' },
    h('button', { class: 'btn secondary', type: 'button', disabled: !n || visit.busy, onclick: undoLastPhoto }, icon('undo'), 'Undo last'),
    h('button', { class: 'btn ' + (n >= total ? '' : 'secondary'), type: 'button', disabled: !n || visit.busy, onclick: () => { visit.step = 'summary'; renderVisit(); } }, icon('list'), 'Finish plot')));
  return out;
}

function bandText(band) { return band === 'high' ? 'High confidence' : 'Medium confidence'; }
function reasonText(reason) {
  if (reason === 'other_problem') return 'This photo looks like a different problem, not one of the AI\'s answers.';
  return reason === 'unfamiliar'
    ? 'This photo looks unlike the photos the AI learned from.'
    : 'The AI\'s best guess was below its confidence line.';
}
// Dataset label of a sample photo. For a problem outside the AI's answers (the mite sample), say what the
// right result is and, if the AI answered anyway, how such photos are caught.
function truthText(truth, notSure) {
  const t = String(truth).replace(/_/g, ' ');
  const base = String(truth).split('_level')[0];
  const known = answerClasses().includes(base);
  if (known) return t;
  if (notSure) return `${t} (not one of the AI's answers, so sending it to the officer is the right result)`;
  const hasOther = !!(Model.shipped && Model.shipped.toOfficer && Model.shipped.toOfficer.length);
  return `${t}. This problem is not one of the AI's ${answerClasses().length || 5} answers, so the answer above is wrong. ` +
    (hasOther
      ? 'The AI has a "different problem" answer that sends such photos to the officer, but it did not pick it here. The officer\'s 1-in-10 spot check catches some of these photos, and the officer\'s "Different problem" label teaches the AI on this phone.'
      : 'Such photos are found by the officer\'s 1-in-10 spot check and marked "Different problem".');
}

function probBars(r) {
  const classes = (Model.shipped && Model.shipped.classes) || [];
  return h('div', { class: 'bars' }, classes.map((c, k) => [
    h('span', null, className(c)),
    h('div', { class: 'bar' }, h('div', { style: `width:${(100 * (r.probs[k] || 0)).toFixed(1)}%` })),
    h('span', null, pct(r.probs[k], 1))]));
}

function resultCard(r) {
  const head = Model.active;
  const details = h('details', null, h('summary', null, 'Details'),
    h('div', { class: 'stack small' },
      probBars(r),
      h('p', null, `Confidence line: ${pct(head ? head.threshold : null)}. Distance from familiar photos: ${r.ood_distance == null ? '–' : r.ood_distance.toFixed(3)} (limit ${head && isFinite(head.cutoff) ? head.cutoff.toFixed(3) : 'none'}).` +
        (r.local_distance != null && head && head.localCutoff != null ? ` Distance from the nearest officer-labelled photo: ${r.local_distance.toFixed(3)} (limit ${head.localCutoff.toFixed(3)}).` : '')),
      h('p', null, `Model ${r.head_version}. ${r.ms ? r.ms + ' ms on this phone.' : ''}`),
      h('p', null, 'The square shows the part of the photo the AI looked at.')));
  const sample = r.sample_truth ? h('p', { class: 'small' }, h('b', null, 'Dataset label: '), truthText(r.sample_truth, r.not_sure), ' (RoCoLe sample)') : null;
  const where = r.tree ? h('p', { class: 'small' }, `Tree ${r.tree}, leaf ${r.leaf}`) : null;
  const gid = guideIdFor(r);
  const guideBtn = gid ? h('button', { class: 'btn secondary block', type: 'button', 'data-guide': gid, onclick: () => openGuide(gid) }, icon('info'), 'What does this mean?') : null;
  if (r.not_sure) {
    return card('unsure', h('div', { class: 'row' }, h('img', { class: 'thumb', src: r.thumb, alt: 'Leaf photo' }),
      h('div', { class: 'grow' }, h('div', { class: 'card-head' }, icon('question'), 'Not sure'), where)),
    h('div', { class: 'stack', style: 'margin-top:10px' }, answerBlock('result_not_sure'), answerBlock('action_not_sure'),
      h('p', { class: 'small' }, reasonText(r.reason), ' Photo saved for the officer.'), guideBtn, sample, details));
  }
  const healthy = r.label === 'healthy';
  return card(healthy ? 'ok' : 'bad', h('div', { class: 'row' }, h('img', { class: 'thumb', src: r.thumb, alt: 'Leaf photo' }),
    h('div', { class: 'grow' }, h('div', { class: 'card-head' }, icon(healthy ? 'check' : 'alert'), className(r.label)),
      h('div', { class: 'tags' }, h('span', { class: 'tag' }, bandText(r.band)),
        r.disputed ? h('span', { class: 'tag syn' }, 'Sent to the officer') : null), where)),
  h('div', { class: 'stack', style: 'margin-top:10px' }, answerBlock('result_' + r.label), answerBlock('action_' + r.label),
    r.spot_check ? h('p', { class: 'small' }, 'This photo was also picked for an officer spot check (1 in 10 answers are).') : null,
    guideBtn, disputeBlock(r), sample, details));
}

// "I think it's something else" on an answered photo: one confirm step inside the card, then a small
// "sent to the officer" state with Undo (until the plot card is saved or the officer has labelled the photo).
function disputeBlock(r) {
  const saved = !visit.plot || visit.plot.status === 'done';
  if (r.disputed) {
    return h('div', { class: 'sent-box', role: 'status' },
      h('p', null, icon('officer'), h('span', null, h('b', null, 'Sent to the officer'), ` (${DISPUTE_REASON}).`)),
      h('p', { class: 'small' }, r.officer_label
        ? (r.officer_label === 'skip' ? 'The officer could not tell, so this photo is left out of the village numbers.' : `The officer labelled it: ${className(r.officer_label)}. That label counts.`)
        : 'It does not count in the village numbers until the officer labels it.'),
      (!saved && !r.officer_label) ? h('button', { class: 'btn secondary small', type: 'button', onclick: () => setDisputed(r, false) }, icon('undo'), 'Undo') : null);
  }
  if (visit.confirmDispute === r.id) {
    return h('div', { class: 'confirm-box', role: 'group', 'aria-label': 'Send to the officer?' },
      h('p', null, h('b', null, 'Send this photo to the officer?')),
      h('p', { class: 'small' }, `The AI said ${className(r.label)}. The photo will wait for the officer and will not count in the village numbers until the officer labels it.`),
      h('div', { class: 'btn-grid' },
        h('button', { class: 'btn', type: 'button', onclick: () => setDisputed(r, true) }, 'Yes, send'),
        h('button', { class: 'btn secondary', type: 'button', onclick: () => { visit.confirmDispute = null; renderVisit(); } }, 'Cancel')));
  }
  if (saved) return null;
  return h('button', { class: 'btn secondary block', type: 'button', onclick: () => { visit.confirmDispute = r.id; renderVisit(); } },
    icon('question'), 'I think it\'s something else');
}

async function setDisputed(r, on) {
  visit.confirmDispute = null;
  let cur = null;
  try { cur = await DB.get('photos', r.id); } catch (e) { /* storage unavailable */ }
  if (cur && cur.officer_label) { // labelled on the Officer screen meanwhile: keep the officer's label
    Object.assign(r, { officer_label: cur.officer_label, reviewed_at: cur.reviewed_at });
    toast('The officer has already labelled this photo.');
    renderVisit();
    return;
  }
  Object.assign(r, { disputed: on, dispute_reason: on ? DISPUTE_REASON : null, disputed_at: on ? Date.now() : null });
  try { await DB.put('photos', r); } catch (e) { toast('Could not save: ' + (e.message || e)); }
  updateQueueBadge();
  renderVisit();
  toast(on ? 'Sent to the officer. It does not count in the village numbers until the officer labels it.' : 'Undone. The AI answer counts again.');
}

function retakeCard() {
  const r = visit.retake;
  return card('warn', h('div', { class: 'row' }, h('img', { class: 'thumb', src: r.result.thumb, alt: 'Leaf photo' }),
    h('div', { class: 'grow' }, h('div', { class: 'card-head' }, icon('camera'), 'Take again?'), h('p', { class: 'small' }, `Photo looks ${r.result.quality.reason}.`))),
  h('div', { class: 'stack', style: 'margin-top:10px' }, answerBlock('retake_photo'),
    h('div', { class: 'btn-grid' },
      fileButton('Take again', 'camera', true, '', false),
      h('button', { class: 'btn secondary', type: 'button', onclick: async () => { const x = visit.retake; visit.retake = null; await addPhoto(x.result, x.sample); renderVisit(); } }, 'Use anyway'))));
}

async function handlePhoto(blob, sample) {
  if (!visit.plot || visit.busy) return;
  visit.busy = true;
  visit.retake = null;
  renderVisit();
  try {
    const img = await loadImage(blob);
    const r = await classifyImage(img);
    if (r.quality.bad) visit.retake = { result: r, sample };
    else await addPhoto(r, sample);
  } catch (e) {
    toast('Could not check this photo: ' + (e.message || e));
  } finally {
    visit.busy = false;
    renderVisit();
  }
}

async function addPhoto(r, sample) {
  const i = visit.photos.length;
  const pos = posOf(i);
  const rec = {
    id: uid(), plot_id: visit.plot.id, village: visit.plot.village, created: Date.now(), index: i, tree: pos.tree, leaf: pos.leaf,
    thumb: r.thumb, embedding: r.embedding, probs: r.probs, label: r.label, top: r.top, max_prob: r.max_prob, band: r.band,
    not_sure: r.not_sure, reason: r.reason, ood_distance: r.ood_distance, local_distance: r.local_distance,
    familiar_by: r.familiar_by, head_version: r.head_version, ms: r.ms,
    officer_label: null, sample_file: sample ? sample.file : null, sample_truth: sample ? sample.truth : null,
    disputed: false, dispute_reason: null, disputed_at: null, // set by "I think it's something else"
    // Spot check: a random 1 in 10 answered photos also goes to the officer, to catch confident mistakes.
    spot_check: !r.not_sure && Math.random() < SPOT_CHECK_RATE,
  };
  await DB.put('photos', rec);
  visit.photos.push(rec);
  visit.plot.photo_ids.push(rec.id);
  visit.plot.updated = Date.now();
  if (sample) visit.plot.has_samples = true;
  await DB.put('plots', visit.plot);
  visit.last = rec;
  updateQueueBadge();
}

async function undoLastPhoto() {
  const rec = visit.photos.pop();
  if (!rec) return;
  await DB.del('photos', rec.id);
  visit.plot.photo_ids = visit.plot.photo_ids.filter((x) => x !== rec.id);
  visit.plot.has_samples = visit.photos.some((p) => p.sample_file);
  visit.plot.updated = Date.now();
  await DB.put('plots', visit.plot);
  visit.last = visit.photos[visit.photos.length - 1] || null;
  visit.retake = null;
  updateQueueBadge();
  toast('Last photo removed.');
  renderVisit();
}

// The Officer screen saves labels on fresh copies of the photo records; copy them onto the open visit so its
// result card and plot card show the officer's label (and Undo is not offered for a labelled photo).
async function syncVisitPhotos() {
  if (!visit.plot || !visit.photos.length) return;
  try {
    const byId = new Map((await DB.all('photos')).map((p) => [p.id, p]));
    let changed = false;
    for (const p of visit.photos) {
      const q = byId.get(p.id);
      if (q && q.officer_label !== p.officer_label) { p.officer_label = q.officer_label; p.reviewed_at = q.reviewed_at; changed = true; }
    }
    if (changed && currentTab === 'visit') renderVisit();
  } catch (e) { /* storage unavailable */ }
}

async function discardVisit(plot) {
  const n = (plot.photo_ids || []).length;
  if (!confirm(`Discard the unfinished visit (${plot.village || 'no village'}, ${plural(n, 'photo')})? Its photos are deleted from this phone.`)) return;
  try {
    const photos = (await DB.all('photos')).filter((p) => p.plot_id === plot.id);
    for (const p of photos) await DB.del('photos', p.id);
    await DB.del('plots', plot.id);
  } catch (e) {
    toast('Could not discard the visit: ' + (e.message || e));
    await refreshVisitContext();
    renderVisit();
    return;
  }
  visit.unfinished = null;
  await refreshVisitContext();
  updateQueueBadge();
  renderVisit();
  toast('Unfinished visit discarded.');
}

async function resumeVisit(plot) {
  const all = await DB.all('photos');
  visit.plot = plot;
  visit.photos = all.filter((p) => p.plot_id === plot.id).sort((a, b) => a.index - b.index);
  visit.last = visit.photos[visit.photos.length - 1] || null;
  visit.retake = null;
  visit.unfinished = null;
  visit.step = 'photos';
  renderVisit();
}

// Plot card rule (stated on screen): officer alert if a disease answer appears on 2+ trees or in 3+ photos.
function plotVerdict(photos) {
  const answered = photos.filter((p) => finalLabel(p));
  const sick = answered.filter((p) => finalLabel(p) !== 'healthy');
  const trees = new Set(sick.map((p) => p.tree)).size;
  if (sick.length >= 3 || trees >= 2) return 'plot_officer_alert';
  if (sick.length >= 1) return 'plot_some_problem';
  return answered.length ? 'plot_all_healthy' : null;
}

function viewSummary() {
  const ph = visit.photos;
  const counts = {};
  ph.forEach((p) => { const l = finalLabel(p); if (l) counts[l] = (counts[l] || 0) + 1; });
  const waiting = ph.filter((p) => p.not_sure && !p.officer_label).length; // spot checks already have an AI answer
  const disputed = ph.filter((p) => p.disputed && !p.officer_label).length; // relay farmer disagrees: not counted yet
  const verdict = plotVerdict(ph);
  const tone = verdict === 'plot_all_healthy' ? 'ok' : verdict ? 'bad' : 'unsure';
  const classes = [...new Set(((Model.shipped && Model.shipped.classes) || Object.keys(counts)).concat([otherLabel()]))];
  const list = h('ul', null, classes.filter((c) => counts[c]).map((c) => h('li', null, `${className(c)}: ${counts[c]}`)),
    waiting ? h('li', null, `Not sure, waiting for the officer: ${waiting}`) : null,
    disputed ? h('li', null, `You think it is something else, waiting for the officer: ${disputed}`) : null);
  if (!visit.plot.farm) visit.plot.farm = { variety: null, last_spray: null, fruit_load: null };
  const farm = farmLine(visit.plot.farm);
  const plotCard = card(tone,
    h('div', { class: 'card-head' }, icon(tone === 'ok' ? 'check' : tone === 'bad' ? 'alert' : 'question'), 'Plot card'),
    h('p', null, h('b', null, visit.plot.village), ` · ${fmtDate(visit.plot.created)} · ${ph.length} of 15 photos`),
    list,
    verdict ? answerBlock(verdict) : h('p', null, (waiting || disputed) ? 'No photo counts yet. The photos above wait for the officer.' : 'No photo was answered by the AI yet.'),
    h('p', { class: 'small' }, 'Rule: "ask the officer to visit soon" when a possible disease shows on 2 or more trees, or in 3 or more photos.'),
    h('p', { class: 'small farm-line' }, h('b', null, 'Farm details: '), farm || 'none tapped', ' (for the officer; the AI does not use this).'));
  const qs = CHECK_IDS.map((id) => {
    const val = visit.plot.checklist[id];
    const seg = h('div', { class: 'seg', role: 'group' }, [['yes', 'Yes'], ['no', 'No'], ['unknown', 'Don\'t know']].map(([k, label]) =>
      h('button', { type: 'button', 'aria-pressed': String(val === k), onclick: async () => {
        visit.plot.checklist[id] = k;
        visit.plot.updated = Date.now();
        await DB.put('plots', visit.plot);
        renderVisit();
      } }, label)));
    const refer = val === 'yes' && REFER_IDS.includes(id) ? h('p', { class: 'notice' }, 'Tell the officer about this.') : null;
    return h('div', { class: 'q' }, answerBlock(id), seg, refer);
  });
  const checklist = card('', h('h3', null, 'Things a leaf photo cannot show'),
    h('p', { class: 'small' }, 'Fixed questions about other causes of low yield. The AI does not use these answers.'), ...qs);
  const farmCard = card('', h('h3', null, 'Farm details'),
    farmBlock(visit.plot.farm, async () => {
      visit.plot.updated = Date.now();
      try { await DB.put('plots', visit.plot); } catch (e) { /* storage unavailable */ }
      renderVisit();
    }));
  return [plotCard, checklist, farmCard,
    card('warn', answerBlock('disclaimer_final_call')),
    h('button', { class: 'btn block', type: 'button', onclick: savePlot }, icon('check'), 'Save plot card'),
    h('button', { class: 'btn secondary block', type: 'button', onclick: () => { visit.step = 'photos'; renderVisit(); } }, 'Back to photos')];
}

async function savePlot() {
  visit.plot.status = 'done';
  visit.plot.updated = Date.now();
  visit.plot.verdict = plotVerdict(visit.photos);
  visit.plot.model_version = Model.active ? Model.active.version : null;
  await DB.put('plots', visit.plot);
  visit.step = 'saved';
  renderVisit();
}

function viewSaved() {
  return card('ok', h('div', { class: 'card-head' }, icon('check'), 'Plot card saved on this phone'),
    h('p', null, `${visit.plot.village}: ${plural(visit.photos.length, 'photo')}.`),
    h('div', { class: 'stack' },
      h('button', { class: 'btn block', type: 'button', onclick: async () => {
        Object.assign(visit, { step: 'consent', plot: null, photos: [], last: null, retake: null, farmDraft: {}, confirmDispute: null });
        await refreshVisitContext();
        renderVisit();
      } }, 'Start a new plot visit'),
      h('button', { class: 'btn secondary block', type: 'button', onclick: () => setTab('coop') }, icon('chart'), 'Open co-op dashboard')));
}

async function loadSamples() {
  try { samples = await fetchJSON('samples/manifest.json'); if (!samples.samples || !samples.samples.length) samples = null; } catch (e) { samples = null; }
}
function closeSheet() { const s = $('#sheet'); s.hidden = true; s.replaceChildren(); }
function openSamples() {
  const s = $('#sheet');
  const rows = samples.samples.map((x) => h('button', { class: 'sample-row', type: 'button', onclick: async () => {
    closeSheet();
    try {
      const res = await fetch('samples/' + x.file);
      if (!res.ok) throw new Error(res.status);
      await handlePhoto(await res.blob(), x);
    } catch (e) { toast('Could not open the sample photo.'); }
  } }, h('img', { src: 'samples/' + x.file, alt: '' }), h('span', null, h('b', null, 'Dataset label: ' + String(x.truth).replace(/_/g, ' ')), h('br'), h('small', null, `${x.source || ''} · ${x.license || ''}`))));
  s.replaceChildren(h('div', { class: 'sheet-body', role: 'dialog', 'aria-label': 'Sample photos' },
    h('div', { class: 'row' }, h('h3', { class: 'grow', style: 'margin:0' }, 'Sample photos'),
      h('button', { class: 'btn secondary small', type: 'button', onclick: closeSheet }, icon('close'), 'Close')),
    h('p', { class: 'small' }, 'Public field photos (RoCoLe dataset: Ecuador, robusta coffee). They are not from Kenya. The AI was not trained on these photos, so they are a fair check. The dataset label is shown so you can compare. A visit that uses them is marked "sample photos" on the Co-op tab.'),
    rows));
  s.hidden = false;
  s.onclick = (e) => { if (e.target === s) closeSheet(); };
}

// ----- 8a. Officer PIN (demo). The Officer and Co-op tabs open after the officer PIN; the unlock lasts until the app is
// reloaded. Simplification (stated on the lock screen and in About): one fixed demo PIN for every phone, checked on the
// phone. It keeps these screens out of casual reach; it is not real security. A pilot would let each officer set a PIN.
const OFFICER_PIN = '2026';
let officerUnlocked = false;
function officerLock(root, tab) {
  const input = h('input', { type: 'text', inputmode: 'numeric', pattern: '[0-9]*', maxlength: '4', autocomplete: 'off',
    class: 'pin-input', 'aria-label': 'Officer PIN' });
  const msg = h('p', { class: 'small', 'aria-live': 'polite' });
  const tryOpen = () => {
    if (input.value.trim() === OFFICER_PIN) { officerUnlocked = true; renderCurrent(); window.scrollTo(0, 0); return; }
    msg.textContent = 'Wrong PIN. Try again.';
    input.value = '';
    input.focus();
  };
  input.addEventListener('keydown', (e) => { if (e.key === 'Enter') tryOpen(); });
  input.addEventListener('input', () => { if (input.value.length >= 4) tryOpen(); });
  root.replaceChildren(card('', h('h2', null, icon('lock'), ' For the extension officer'),
    h('p', null, tab === 'coop'
      ? 'The co-op dashboard ranks villages from the plot records on this phone. Enter the officer PIN to open it.'
      : 'Photo review, plot records and model updates are for the extension officer. Enter the officer PIN to open them.'),
    h('label', { class: 'field' }, h('span', null, 'Officer PIN'), input),
    h('button', { class: 'btn block', type: 'button', onclick: tryOpen }, 'Open'),
    msg,
    h('p', { class: 'small' }, `Demo PIN: ${OFFICER_PIN}. In a pilot, each officer would set their own PIN.`)));
}
function lockOfficer() { officerUnlocked = false; renderCurrent(); toast('Officer screens locked.'); }

// ----- 8b. Officer review
// Queue: "not sure" photos, spot-check photos and photos the relay farmer disputed, not yet labelled by the officer.
const inQueue = (p) => (p.not_sure || p.spot_check || p.disputed) && !p.officer_label;
async function updateQueueBadge() {
  try {
    const n = (await DB.all('photos')).filter(inQueue).length;
    const b = $('#queue-badge');
    b.textContent = n;
    b.hidden = !n;
  } catch (e) { /* ignore */ }
}

async function setOfficerLabel(p, label) {
  const prev = p.officer_label;
  p.officer_label = label;
  p.reviewed_at = Date.now();
  await DB.put('photos', p);
  updateQueueBadge();
  renderReview();
  toast(label === 'skip' ? 'Skipped.' : `Saved as ${className(label)}.`, { label: 'Undo', fn: async () => {
    p.officer_label = prev;
    p.reviewed_at = null;
    await DB.put('photos', p);
    updateQueueBadge();
    renderReview();
  } });
}

async function renderReview() {
  const root = $('#tab-review');
  if (!officerUnlocked) { officerLock(root, 'review'); return; }
  const [photos, plots] = await Promise.all([DB.all('photos').catch(() => []), DB.all('plots').catch(() => [])]);
  const plotById = new Map(plots.map((pl) => [pl.id, pl]));
  const queue = photos.filter(inQueue).sort((a, b) => a.created - b.created);
  const classes = (Model.shipped && Model.shipped.classes) || [];
  const labelled = photos.filter((p) => classes.includes(p.officer_label) && p.embedding);
  const out = [card('', h('h2', null, 'Officer review'),
    h('p', null, 'Photos the AI was not sure about, photos the relay farmer thinks are something else, plus a random 1 in 10 of the AI\'s answers as a spot check. Tap the correct answer. You make the final call.'),
    h('p', { class: 'small' }, `${queue.length} waiting · ${photos.filter((p) => p.officer_label).length} reviewed so far.`),
    h('button', { class: 'btn secondary small', type: 'button', onclick: lockOfficer }, icon('lock'), 'Lock officer screens'))];
  if (!queue.length) out.push(card('', h('p', null, 'No photos waiting.')));
  for (const p of queue) {
    const farm = farmLine((plotById.get(p.plot_id) || {}).farm);
    out.push(card('', h('div', { class: 'review-item' },
      h('img', { class: 'thumb', src: p.thumb, alt: 'Leaf photo for review' }),
      h('div', null,
        h('b', null, p.village), h('br'),
        h('span', { class: 'small' }, `${fmtDate(p.created)}${p.tree ? ` · tree ${p.tree}, leaf ${p.leaf}` : ''}`),
        p.sample_truth ? h('div', { class: 'small' }, 'Sample photo, dataset label: ' + String(p.sample_truth).replace(/_/g, ' ')) : null,
        p.not_sure
          ? h('details', null, h('summary', { class: 'small' }, 'AI was not sure: see its best guess'),
            h('p', { class: 'small' }, `${className(p.top)} (${pct(p.max_prob)}). ${reasonText(p.reason)}`))
          : h('div', { class: 'tags' },
            p.disputed ? h('span', { class: 'tag warn' }, `Relay farmer disagrees: AI said ${className(p.label)} (${pct(p.max_prob)})`) : null,
            p.spot_check ? h('span', { class: 'tag syn' }, p.disputed ? 'Also a spot check' : `Spot check: AI said ${className(p.label)} (${pct(p.max_prob)})`) : null),
        h('div', { class: 'small farm-line' }, h('b', null, 'Farm details: '), farm || 'none tapped', farm ? ' (the AI does not use these)' : ''))),
    h('div', { class: 'label-btns' },
      answerClasses().map((c) => h('button', { class: 'btn secondary', type: 'button', onclick: () => setOfficerLabel(p, c) }, className(c))),
      h('button', { class: 'btn secondary', type: 'button', onclick: () => setOfficerLabel(p, otherLabel()) }, 'Different problem (not in list)'),
      h('button', { class: 'btn danger', type: 'button', onclick: () => setOfficerLabel(p, 'skip') }, 'Skip (cannot tell)'))));
  }
  out.push(plotsCard(plots, photos));
  out.push(learningCard(labelled));
  out.push(wordingCard(await wordingList()));
  root.replaceChildren(...out);
}

// Plot visits saved on this phone (newest first): the officer sees the farm details and can export every plot.
function plotsCard(plots, photos) {
  const real = plots.filter((pl) => !pl.synthetic).sort((a, b) => b.created - a.created);
  const nPhotos = new Map();
  photos.forEach((p) => nPhotos.set(p.plot_id, (nPhotos.get(p.plot_id) || 0) + 1));
  const SHOW = 10;
  return card('', h('h3', null, icon('list'), ` Plot visits on this phone (${real.length})`),
    real.length
      ? h('ul', { class: 'wc-list' }, real.slice(0, SHOW).map((pl) => h('li', null,
        h('div', null, h('b', null, pl.village || '(no village)'), ` · ${fmtDate(pl.created)} · ${plural(nPhotos.get(pl.id) || 0, 'photo')}`,
          pl.status === 'done' ? '' : ' · not finished'),
        h('div', { class: 'small' }, farmLine(pl.farm) || 'Farm details: none tapped'))),
        real.length > SHOW ? h('li', { class: 'small' }, `${real.length - SHOW} more in the CSV file.`) : null)
      : h('p', null, 'No plot visits yet.'),
    h('p', { class: 'small' }, `Farm details: ${FARM_NOTE.charAt(0).toLowerCase() + FARM_NOTE.slice(1)}. The CSV has one row per plot visit: counts, the plot card result, farm details and checklist answers. No member numbers, member codes or photos.`),
    h('button', { class: 'btn secondary block', type: 'button', id: 'plots-export', disabled: !real.length, onclick: exportPlotsCsv }, icon('download'), 'Export plot records (CSV)'));
}

// CSV cells: a byte-order mark (Excel reads Swahili and Kikuyu letters), and cells that start with = + - @ get a
// leading apostrophe so a spreadsheet does not run them as formulas.
function csvCell(v) {
  let s = v == null ? '' : String(v);
  if (/^[=+\-@\t\r]/.test(s)) s = "'" + s;
  return /[",\r\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
}
async function plotsCsv() {
  const [plots, photos] = await Promise.all([DB.all('plots'), DB.all('photos')]);
  const byPlot = new Map();
  photos.forEach((p) => { if (!byPlot.has(p.plot_id)) byPlot.set(p.plot_id, []); byPlot.get(p.plot_id).push(p); });
  const classes = [...new Set(((Model.shipped && Model.shipped.classes) || ['healthy', 'rust', 'miner', 'cercospora', 'phoma']).concat([otherLabel()]))];
  const head = ['plot_id', 'village', 'visit_date', 'status', 'includes_sample_photos', 'photos', 'answered']
    .concat(classes.map((c) => c === otherLabel() ? 'different_problem' : c))
    .concat(['waiting_for_officer', 'sent_by_relay_farmer', 'plot_card_result', 'variety', 'last_spray', 'fruit_load'])
    .concat(CHECK_IDS).concat(['model_version']);
  const rows = plots.filter((pl) => !pl.synthetic).sort((a, b) => a.created - b.created).map((pl) => {
    const ph = byPlot.get(pl.id) || [];
    const counts = {};
    let answered = 0, waiting = 0;
    ph.forEach((p) => { const l = finalLabel(p); if (l) { answered += 1; counts[l] = (counts[l] || 0) + 1; } else if (!p.officer_label) waiting += 1; });
    const farm = pl.farm || {};
    const d = new Date(pl.created); // local date, as on screen
    const day = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
    return [pl.id, pl.village, day, pl.status, !!pl.has_samples, ph.length, answered]
      .concat(classes.map((c) => counts[c] || 0))
      .concat([waiting, ph.filter((p) => p.disputed).length, plotVerdict(ph) || '',
        farmValue('variety', farm.variety) || '', farmValue('last_spray', farm.last_spray) || '', farmValue('fruit_load', farm.fruit_load) || ''])
      .concat(CHECK_IDS.map((id) => (pl.checklist || {})[id] || '')).concat([pl.model_version || '']);
  });
  return '\ufeff' + [head].concat(rows).map((r) => r.map(csvCell).join(',')).join('\r\n') + '\r\n';
}
async function exportPlotsCsv() {
  try {
    download(`${FILE_PREFIX}-plots-${new Date().toISOString().slice(0, 10)}.csv`, await plotsCsv(), 'text/csv;charset=utf-8');
    toast('Plot records saved as a CSV file.');
  } catch (e) { toast('Could not export: ' + (e.message || e)); }
}

// Wording corrections saved on this phone (newest first), with delete and CSV export.
function wordingCard(items) {
  const list = items.slice().sort((p, q) => String(q.created).localeCompare(String(p.created)));
  const del = async (c) => {
    const k = wcKey(c);
    const all = await wordingList();
    await DB.put('meta', { key: WC_KEY, items: all.filter((x) => wcKey(x) !== k) });
    renderReview();
    toast('Correction deleted.', { label: 'Undo', fn: async () => { await mergeWordingCorrections([c]); renderReview(); } });
  };
  return card('', h('h3', null, icon('list'), ` Wording corrections (${items.length})`),
    list.length
      ? h('ul', { class: 'wc-list' }, list.map((c) => h('li', null,
        h('div', { class: 'small' }, `${c.id} · ${LANG_LABEL[c.lang] || c.lang} · ${WHO[c.who] || c.who || '–'} · ${fmtDate(c.created)}`),
        h('p', { class: 'wc-sugg', lang: HTML_LANG[c.lang] || c.lang }, c.suggestion),
        c.note ? h('p', { class: 'small' }, 'Note: ', c.note) : null,
        h('button', { class: 'btn danger small', type: 'button', onclick: () => del(c) }, icon('trash'), 'Delete'))))
      : h('p', null, 'None yet. Tap "Wording wrong?" under any Swahili or Kikuyu sentence to report one.'),
    h('button', { class: 'btn secondary block', type: 'button', id: 'wc-export', disabled: !items.length, onclick: () => exportWordingCsv(items) }, icon('download'), 'Export corrections (CSV)'),
    h('details', { class: 'more' }, h('summary', null, 'What happens to these reports'),
      h('p', { class: 'small' }, 'Wrong or unnatural phrases reported on this phone. The app\'s text does not change by itself: the team reviews these and ships a corrected answer list. They also go out with the model update file above.')));
}

// CSV with a byte-order mark so Excel reads Swahili and Kikuyu letters (ĩ, ũ) correctly.
// Cells that start with = + - @ get a leading apostrophe so a spreadsheet does not run them as formulas.
function wordingCsv(items) {
  const rows = items.map((c) => WC_FIELDS.map((f) => c[f]));
  return '﻿' + [WC_FIELDS.join(',')].concat(rows.map((r) => r.map(csvCell).join(','))).join('\r\n') + '\r\n';
}
function exportWordingCsv(items) {
  download(`${FILE_PREFIX}-wording-corrections-${new Date().toISOString().slice(0, 10)}.csv`, wordingCsv(items), 'text/csv;charset=utf-8');
  toast(`Saved ${plural(items.length, 'correction')} as a CSV file.`);
}

function learningCard(labelled) {
  const counts = {};
  labelled.forEach((p) => { counts[p.officer_label] = (counts[p.officer_label] || 0) + 1; });
  const ad = Model.adapted;
  const result = h('div', { class: 'small', 'aria-live': 'polite' });
  if (ad && ad.loss_before != null) {
    result.append(h('p', null, `Last update: ${ad.steps_done} steps, training loss ${ad.loss_before.toFixed(3)} → ${ad.loss_after.toFixed(3)}. Officer-labelled photos the head gets right: ${ad.correct_before} → ${ad.correct_after} of ${ad.n_labels}. These are the same photos it learned from, so this is not a test of accuracy.`));
  }
  const importInput = h('input', { type: 'file', accept: 'application/json,.json' });
  importInput.addEventListener('change', async () => {
    const f = importInput.files && importInput.files[0];
    importInput.value = '';
    if (!f) return;
    let j, added = 0;
    try { j = JSON.parse(await f.text()); } catch (e) { toast(`Could not load the update: this is not a ${APP_NAME} update file`); return; }
    // Wording corrections do not depend on the model, so they are kept even if the model part cannot be used.
    if (j && j.kind === 'kahawa-head-update') { try { added = await mergeWordingCorrections(j.wording_corrections); } catch (e) { /* storage problem */ } }
    const wc = Array.isArray(j && j.wording_corrections) ? ` ${plural(added, 'new wording correction')} added.` : '';
    try { const a = await importUpdateJSON(j, 'shared file'); toast(`Update loaded: ${a.version}.${wc}`); } catch (e) { toast('Could not load the update: ' + e.message + '.' + wc); }
    renderReview();
  });
  const ready = Model.ready;
  return card('', h('h3', null, icon('refresh'), ' Update the model on this phone'),
    h('p', null, `Model in use: `, h('b', null, Model.active ? Model.active.version : '–'),
      ad ? ` (shipped model + ${plural(ad.n_labels, 'officer label')}, from ${ad.source})` : ' (shipped model)'),
    Model.adaptedMismatch ? h('p', { class: 'notice' }, `A saved update was made for model ${Model.adaptedMismatch.base_version}; this phone now has ${Model.shipped.version}. The old update is not used. Tap Update to rebuild it from the labels.`) : null,
    h('p', { class: 'small' }, `Officer labels on this phone: ${labelled.length}` + (labelled.length ? ' (' + Object.entries(counts).map(([c, k]) => `${className(c)} ${k}`).join(', ') + ')' : '') + '.'),
    h('div', { class: 'stack' },
      h('button', { class: 'btn block', type: 'button', disabled: !ready || !labelled.length, onclick: async (e) => {
        e.currentTarget.disabled = true;
        e.currentTarget.replaceChildren(h('span', { class: 'busy' }), ' Updating…');
        await new Promise((r) => setTimeout(r, 30)); // let the screen repaint first
        try { const a = await updateModelOnPhone(); toast(`Model updated: ${a.version}.`); } catch (err) { toast('Update failed: ' + err.message); }
        renderReview();
      } }, icon('refresh'), 'Update the model on this phone'),
      result,
      h('button', { class: 'btn secondary block', type: 'button', disabled: !ad, onclick: async () => {
        const r = await exportUpdate();
        toast(`Update file saved (${(r.size / 1024).toFixed(0)} KB${r.corrections ? `, with ${plural(r.corrections, 'wording correction')}` : ''}).`);
      } }, icon('download'), 'Share this update with other relay farmers'),
      h('label', { class: 'btn secondary block', 'aria-disabled': ready ? null : 'true' }, icon('upload'), 'Load an update from another phone', importInput),
      h('button', { class: 'btn danger block', type: 'button', disabled: !ad, onclick: async () => {
        await DB.del('meta', 'adapted_head');
        await applyStoredAdaptedHead();
        toast('Back to the shipped model. Officer labels are kept.');
        renderReview();
      } }, icon('undo'), 'Reset to shipped model')),
    h('details', { class: 'more' }, h('summary', null, 'How the update works'), h('p', { class: 'small' }, `The small last layer of the AI is refitted on this phone from the officer's labels (up to ${REFIT_STEPS} steps of gradient descent). A penalty keeps it close to the shipped model, so a few labels cannot pull it far. The labelled photos also join the AI's set of familiar photos, and a photo close to one labelled photo counts as familiar, so similar photos stop being "not sure". The picture-reading part of the model is not changed. The share file holds the new last layer and the labelled photos as ${(Model.shipped ? Model.shipped.D : 1280).toLocaleString('en')} numbers each (about 5 KB per photo as text); no pictures.`)));
}

// ----- 8c. Co-op dashboard
async function renderCoop() {
  const root = $('#tab-coop');
  if (!officerUnlocked) { officerLock(root, 'coop'); return; }
  let rows = [];
  try { rows = await villageRows(); } catch (e) { /* storage unavailable */ }
  const st = villageStats(rows);
  const P = st.prior;
  const priorMean = P.a / (P.a + P.b);
  const hasDemo = rows.some((r) => r.synthetic);
  const table = h('div', { class: 'table-wrap' }, h('table', { class: 'coop-table' },
    h('colgroup', null, h('col', { class: 'c-village' }), h('col', { class: 'c-raw' }), h('col', { class: 'c-adj' }), h('col', { class: 'c-chance' })),
    h('thead', null, h('tr', null, h('th', null, 'Village'), h('th', null, 'Rust (raw)'), h('th', null, 'Adjusted'), h('th', null, `Chance > ${pct(ALERT_RATE)}`))),
    h('tbody', null, st.rows.length ? st.rows.map((r) => h('tr', { class: r.alert ? 'alert' : null },
      h('td', null, r.synthetic ? String(r.name).replace(/\s*\(synthetic\)$/, '') : r.name, // the tag below says "synthetic"
        r.synthetic ? h('div', null, h('span', { class: 'tag syn' }, 'synthetic')) : null,
        r.samples ? h('div', null, h('span', { class: 'tag' }, 'sample photos')) : null,
        r.waiting ? h('div', { class: 'small' }, `${r.waiting} waiting for officer`) : null),
      h('td', null, `${r.x} / ${r.n}`, h('div', { class: 'small' }, pct(r.raw))),
      h('td', null, h('b', null, pct(r.adjusted))),
      h('td', null, pctP(r.pAbove), r.alert ? h('div', { class: 'alert-flag' }, icon('flag'), ' Alert') : null)))
      : h('tr', null, h('td', { colspan: 4 }, 'No plot records yet. Save a plot visit, or load the demo villages.')))));
  const explain = P.source === 'fitted'
    ? `Villages with few photos are pulled toward the average of all villages (${pct(priorMean)}); villages with many photos stay close to their own share. So 2 rust photos out of 3 do not count as 67%.`
    : `Villages with few photos are pulled toward a starting guess of ${pct(priorMean)} (used until 3 villages have answered photos); villages with many photos stay close to their own share. So 2 rust photos out of 3 do not count as 67%.`;
  root.replaceChildren(
    card('', h('h2', null, 'Co-op: villages to visit first'),
      h('p', null, `Leaf rust per village, from saved plot visits on this phone. Villages most likely above ${pct(ALERT_RATE)} rust come first. This ranks rust already seen in photos; it does not predict outbreaks.`),
      h('p', { class: 'small' }, `Alert when the chance that the rust rate is above ${pct(ALERT_RATE)} is more than ${pct(ALERT_PROB)}. ${plural(rows.length, 'village')}.`)),
    table,
    card('',
      h('details', { class: 'more' }, h('summary', null, 'Why "adjusted" differs from "raw"'), h('p', null, explain)),
      h('details', { class: 'more' }, h('summary', null, 'How the numbers are made'),
      h('ul', { class: 'small' },
        h('li', null, 'Answered = photos with an AI answer or an officer label. "Not sure" photos, and photos the relay farmer sent to the officer ("I think it\'s something else"), count only after the officer labels them; an officer label replaces the AI answer. "Different problem" counts as answered, not rust; "skip" is left out.'),
        h('li', null, `Prior: Beta(${P.a.toFixed(2)}, ${P.b.toFixed(2)}), ${P.source === 'fitted' ? `fitted across ${P.k} villages by maximum likelihood (beta-binomial)${P.capped ? ', capped at the weight of 50 photos' : ''}` : 'fallback starting guess, used until 3 villages have answered photos'}; it counts like ${(P.a + P.b).toFixed(1)} photos.`),
        h('li', null, `Adjusted = posterior mean (Beta-binomial). "Chance > ${pct(ALERT_RATE)}" = P(rust rate > ${pct(ALERT_RATE)}), computed from the posterior Beta distribution.`),
        h('li', null, 'Simplification: photos are counted as independent. Leaves from the same tree or farm are alike, so the true uncertainty is larger than shown.'),
        h('li', null, 'Simplification: the AI\'s answers are used as if correct. AI errors change the counts.')))),
    h('div', { class: 'stack' },
      hasDemo
        ? h('button', { class: 'btn secondary block', type: 'button', onclick: removeDemo }, icon('trash'), 'Remove demo villages')
        : h('button', { class: 'btn secondary block', type: 'button', onclick: loadDemo }, icon('grid'), 'Load demo villages (synthetic)'),
      h('button', { class: 'btn secondary block', type: 'button', disabled: !st.rows.length, onclick: () => exportCsv(st) }, icon('download'), 'Export CSV'),
      h('button', { class: 'btn secondary block', type: 'button', disabled: !rows.some((r) => !r.synthetic), onclick: exportPlotsCsv }, icon('download'), 'Export plot records (CSV)')));
}

async function loadDemo() {
  for (const [name, x, n] of DEMO_VILLAGES) {
    await DB.put('plots', { id: 'demo-' + name, created: Date.now(), updated: Date.now(), village: name, status: 'done', synthetic: true,
      synthetic_counts: { answered: n, rust: x }, photo_ids: [], checklist: {}, note: 'Synthetic record for demonstration only' });
  }
  toast('Demo villages added. They are synthetic, not real data.');
  renderCoop();
}
async function removeDemo() {
  for (const p of await DB.all('plots')) if (p.synthetic) await DB.del('plots', p.id);
  toast('Demo villages removed.');
  renderCoop();
}
function exportCsv(st) {
  const P = st.prior;
  const esc = (v) => { const s = v == null ? '' : String(v); return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; };
  const head = ['rank', 'village', 'synthetic', 'includes_sample_photos', 'plots', 'photos_answered', 'rust_photos', 'waiting_for_officer',
    'raw_share', 'adjusted_share', 'p_rate_above_' + String(ALERT_RATE).replace('.', '_'), 'alert', 'prior_a', 'prior_b', 'prior_source'];
  const lines = [head.join(',')].concat(st.rows.map((r, i) => [i + 1, r.name, r.synthetic, r.samples, r.plots, r.n, r.x, r.waiting,
    r.raw == null ? '' : r.raw.toFixed(4), r.adjusted == null ? '' : r.adjusted.toFixed(4), r.pAbove == null ? '' : r.pAbove.toFixed(4),
    r.alert, P.a.toFixed(4), P.b.toFixed(4), P.source].map(esc).join(',')));
  download(`${FILE_PREFIX}-coop-${new Date().toISOString().slice(0, 10)}.csv`, lines.join('\n') + '\n', 'text/csv');
}

// ----- 8d. About / privacy
function langStatus() {
  return ['sw', 'kik'].map((l) => {
    const ids = ANSWER_IDS.filter((id) => answers[id] && typeof answers[id][l] === 'string' && answers[id][l].trim());
    const ok = ids.filter((id) => isVerified(answers[id], l));
    const all = ids.length === ANSWER_IDS.length && ok.length === ids.length;
    return h('p', null, h('span', { class: 'tag ' + (all ? '' : 'warn') }, LANG_LABEL[l]), ' ',
      !answersLoaded ? 'answers.json not found: English fallback is shown.'
        : `${ids.length} of ${ANSWER_IDS.length} texts written; ${ok.length ? ok.length + ' checked by a native speaker' : 'not yet checked by a native speaker'}.` +
          (ids.length < ANSWER_IDS.length ? (l === 'kik' ? ' Missing texts show in Swahili, then English.' : ' Missing texts show in English.') : ''));
  });
}

async function renderAbout() {
  const root = $('#tab-about');
  const hr = Model.headRaw || {};
  const meta = Model.meta || {};
  const kv = (pairs) => h('dl', { class: 'kv' }, pairs.filter(([, v]) => v != null && v !== '').map(([k, v]) => [h('dt', null, k), h('dd', null, String(v))]));
  const known = new Set(['version', 'classes', 'embed_dim', 'W', 'b', 'temperature', 'threshold', 'ood', 'prior_strength', 'notes',
    'trained_on', 'calibrated_on', 'field_test', 'standardised_in_backbone', 'standardisation', 'role',
    'route_to_officer', 'route_to_officer_note']);
  const toOfficer = Array.isArray(hr.route_to_officer) ? hr.route_to_officer : [];
  const ft = hr.field_test && typeof hr.field_test === 'object' ? hr.field_test : null;
  const ood = hr.ood || {};
  const famText = ood.reference
    ? `distance to the ${ood.k || 10} most similar of ${Number(ood.reference.n).toLocaleString('en')} stored training photos (plus any officer-labelled photos) above ${ood.cutoff} means "not sure"` +
      (Number.isFinite(ood.local_nearest_cutoff) ? `, unless the single nearest officer-labelled photo is within ${ood.local_nearest_cutoff}` : '')
    : (ood.cutoff != null ? `distance to the nearest class centre above ${ood.cutoff} means "not sure"` : null);
  const extra = Object.entries(hr).filter(([k, v]) => !known.has(k) && v != null && (typeof v !== 'object' || JSON.stringify(v).length < 400))
    .map(([k, v]) => [k, typeof v === 'object' ? JSON.stringify(v) : v]);
  let counts = { plots: 0, photos: 0, labels: 0 };
  try {
    const [pl, ph] = await Promise.all([DB.all('plots'), DB.all('photos')]);
    counts = { plots: pl.filter((p) => !p.synthetic).length, photos: ph.length, labels: ph.filter((p) => p.officer_label).length };
  } catch (e) { /* ignore */ }
  const nWc = (await wordingList()).length;
  let usage = '';
  try { if (navigator.storage && navigator.storage.estimate) { const e = await navigator.storage.estimate(); usage = `App files and records use ${e.usage < 1e6 ? 'less than 1' : 'about ' + Math.round(e.usage / 1e6)} MB on this phone.`; } } catch (e) { /* ignore */ }
  root.replaceChildren(
    card('', h('h2', null, `About ${APP_NAME}`),
      h('p', null, `${APP_NAME} helps a relay farmer check coffee leaves on a plot visit, offline on this phone, and passes unclear cases to the extension officer. "Majani" (say mah-JAH-nee) is Swahili for leaves.`),
      h('ol', { class: 'how' },
        h('li', null, h('span', null, h('b', null, 'Photograph. '), 'The relay farmer photographs coffee leaves on a plot visit.')),
        h('li', null, h('span', null, h('b', null, 'Check. '), 'The AI names the leaf problem, or says "not sure".')),
        h('li', null, h('span', null, h('b', null, 'Review. '), 'The extension officer labels the unclear photos. The labels teach the AI on this phone.')),
        h('li', null, h('span', null, h('b', null, 'Plan. '), 'The Co-op tab shows which villages to visit first.'))),
      h('p', { class: 'small' }, 'Tip: use "Add to Home Screen" in the browser menu to open the app like any other app.')),
    card('', h('h2', null, icon('lock'), ' Privacy and your data'),
      h('p', null, 'Plot records, small copies of the leaf photos and officer labels stay on this phone until someone exports them. The app sends nothing anywhere.'),
      h('p', null, 'The member number is saved only as a scrambled code. Short numbers can still be guessed by someone who has this phone.'),
      h('p', null, `The Officer and Co-op tabs open with the officer PIN (demo PIN: ${OFFICER_PIN}).`),
      h('p', { class: 'small' }, `On this phone now: ${plural(counts.plots, 'plot visit')}, ${plural(counts.photos, 'photo')}, ${plural(counts.labels, 'officer label')}. ${usage}`),
      h('button', { class: 'btn danger block', type: 'button', onclick: deleteAll }, icon('trash'), 'Delete all data on this phone'),
      h('p', { class: 'small' }, 'This removes plot records, photos, officer labels, wording corrections and the local model update. The app itself stays saved so it still works offline.')),
    card('', h('h2', null, 'Languages'),
      h('dl', { class: 'langs' },
        h('dt', null, 'Kiswahili'), h('dd', null, 'Answers on screen and as audio'),
        h('dt', null, 'English'), h('dd', null, 'On screen'),
        h('dt', null, 'Gĩkũyũ'), h('dd', null, 'A shorter list of phrases; the rest shows in Swahili')),
      h('p', { class: 'small' }, 'Swahili or Kikuyu wording wrong or unnatural? Tap "Wording wrong?" under the sentence.'),
      h('details', { class: 'more' }, h('summary', null, 'Translation status'),
        ...langStatus(),
        h('p', { class: 'small' }, `${plural(nWc, 'wording correction')} saved on this phone. They go out with the officer's update file or the corrections CSV (Officer screen). The text on screen changes only after the team reviews them and ships a new answer list.`))),
    h('details', { class: 'card tech' }, h('summary', null, 'Technical details (model card, simplifications)'),
      h('p', { class: 'small' }, 'For evaluators and technical staff. Relay farmers and officers do not need this to use the app.'),
      h('h3', null, 'Model card'), h('div', null,
      kv([['Head version', hr.version], ['Model in use', Model.active && Model.active.version], ['Classes', (hr.classes || []).join(', ')],
        ['Sent to the officer, never shown as an answer', toOfficer.length ? toOfficer.map(className).join(', ') : null],
        ['Embedding size', hr.embed_dim], ['Temperature', hr.temperature], ['Confidence line (threshold)', hr.threshold],
        ['"High" confidence from', Model.shipped ? pct(Model.shipped.highCut) : null],
        ['Familiarity check', famText], ['Prior strength (learning loop)', hr.prior_strength],
        ['Trained on', hr.trained_on], ['Calibrated on', hr.calibrated_on],
        ['Field test', ft ? `${ft.dataset || ''}${ft.method ? ', ' + ft.method : ''}: answers ${pct(ft.coverage)} of field photos it did not learn from` +
          (ft.acc_answered != null ? `, ${pct(ft.acc_answered)} of those answers correct` : '') +
          `; if forced to answer every photo, ${pct(ft.acc_all)} correct` : null],
        ['Embedding standardisation', hr.standardisation],
        ['Notes', hr.notes], ...extra,
        ['Backbone', meta.backbone ? `${meta.backbone} (frozen, ImageNet weights, ${meta.license || ''})` : null],
        ['Backbone file', meta.onnx_bytes ? `${(meta.onnx_bytes / 1e6).toFixed(1)} MB` : null],
        ['Input', meta.input_size ? `${meta.input_size}×${meta.input_size} centre crop after resizing the shorter side to ${meta.resize_shorter}` : null],
        ['Runtime', 'onnxruntime-web 1.30.0 (MIT), WebAssembly, 1 thread']]),
      Model.error ? h('p', { class: 'notice' }, 'Model error: ' + Model.error) : null),
      h('h3', null, 'Simplifications'), h('div', null,
      h('ul', { class: 'small' },
        h('li', null, 'Photo resizing copies the Python (PIL) resize used in training. Very large photos are first halved by the browser, so they differ slightly.'),
        h('li', null, 'The photo check (too dark, too bright, no detail) uses rough thresholds, not tuned on data.'),
        h('li', null, '"High" vs "medium" confidence is a fixed cut, halfway between the confidence line and 100%, unless head.json sets it.'),
        h('li', null, 'The plot card rule (2 or more trees, or 3 or more photos with a possible disease) is a simple fixed rule.'),
        h('li', null, 'The learning loop uses gradient descent with a step-size search; the team\'s Python evaluation uses L-BFGS on the same objective. Results should be close, not identical.'),
        h('li', null, 'Spot checks pick a random 1 in 10 answered photos on this phone.'),
        h('li', null, `The officer PIN is one fixed demo PIN (${OFFICER_PIN}) for every phone, checked on the phone. It keeps the officer screens out of casual reach; it is not real security.`),
        h('li', null, 'The co-op dashboard treats photos as independent and AI answers as correct.'))),
    ),
    h('details', { class: 'card tech' }, h('summary', null, 'What the AI can and cannot do'),
      h('h3', null, 'What it does'),
      h('ul', { class: 'small' },
        h('li', null, 'Looks at one photo of the underside of a coffee leaf.'),
        h('li', null, `Picks one of ${(Model.shipped ? answerClasses() : Object.keys(CLASS_NAMES).filter((c) => c !== 'other')).map(className).join(', ')}, or says "not sure".`),
        h('li', null, 'Says "not sure" when its best guess is below a confidence line, when the photo looks unlike the photos it learned from' +
          (toOfficer.length ? ', or when the photo looks like a different problem (one not in the list)' : '') + '. Those photos wait for the officer.'),
        h('li', null, 'If the relay farmer taps "I think it\'s something else", the photo goes to the officer and counts in the village numbers only after the officer labels it.'),
        h('li', null, 'Runs on this phone. No internet is needed after the first visit.'),
        h('li', null, 'Every answer comes from a fixed list of texts. It never writes new text.')),
      h('h3', null, 'What it does not do'),
      h('ul', { class: 'small' },
        h('li', null, 'It does not make the final call. The extension officer does.'),
        h('li', null, 'It does not name any spray, product or dose.'),
        h('li', null, 'It does not check berries, roots or the whole farm. Other causes of low yield are in the checklist, which is not AI.'),
        h('li', null, 'It has not yet seen Kenyan photos taken the way relay farmers take them. It learned from close-up photos of leaf spots (Kenya, Brazil; the Kenyan ones from a farm in Kirinyaga, cropped to the spot) and from on-plant field photos of healthy and rust leaves (Ecuador). Photos that look unlike these get "not sure" and go to the officer, and each officer label teaches the model on this phone.'),
        h('li', null, toOfficer.length
          ? `It can give only the ${answerClasses().length} answers above. Its "different problem" check learned one pest (red spider mite, from field photos in Ecuador); it sends many such photos to the officer, but it still gives some of them a wrong answer, and other problems outside the list can get a wrong answer too. The officer's 1-in-10 spot check finds such photos, and the officer's "Different problem" label teaches the AI on this phone.`
          : `It can give only the ${Model.shipped ? Model.shipped.C : 5} answers above. A pest or problem outside the list (for example red spider mite) can get a wrong answer. The officer's 1-in-10 spot check finds such photos and the officer marks them "Different problem".`))),
    card('', h('h2', null, 'Credits'),
      h('p', null, 'Made by Sidian Lin (Harvard Kennedy School) and Yicong Li (Harvard SEAS) for the World Bank Small AI for Development challenge, 2026.'),
      h('ul', { class: 'small' },
        h('li', null, 'Sample photos: RoCoLe dataset (Parraga-Alava et al. 2019), CC BY 4.0.'),
        h('li', null, 'Swahili and Kikuyu audio: made with Meta MMS text-to-speech, CC BY-NC 4.0.'),
        h('li', null, 'Backbone: MobileNetV3 (timm), Apache-2.0. Runtime: onnxruntime-web, MIT.'),
        h('li', null, 'App code: MIT License.'))));
}

async function deleteAll() {
  if (!confirm('Delete all plot records, photos, officer labels, wording corrections and the local model update from this phone? This cannot be undone.')) return;
  await DB.deleteAll();
  store.clear();
  location.reload();
}

// ---------------------------------------------------------------- 9. Boot
function renderCurrent() {
  ({ visit: renderVisit, review: renderReview, coop: renderCoop, about: renderAbout })[currentTab]();
  document.querySelectorAll('.lang button').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.lang === lang)));
  updateQueueBadge();
}

function setTab(name) {
  currentTab = name;
  document.querySelectorAll('.tab').forEach((s) => { s.hidden = s.id !== 'tab-' + name; });
  // The language choice only changes the farmer-facing answers on the Plot visit screens.
  document.querySelectorAll('.lang').forEach((g) => { g.hidden = name !== 'visit'; });
  document.querySelectorAll('.tabbar button').forEach((b) => {
    if (b.dataset.tab === name) b.setAttribute('aria-current', 'page'); else b.removeAttribute('aria-current');
  });
  try { history.replaceState(null, '', '#' + name); } catch (e) { /* ignore */ }
  closeSheet();
  renderCurrent();
  window.scrollTo(0, 0);
  if (name === 'visit') syncVisitPhotos();
}

function updateNet() {
  const el = $('#net-status');
  el.textContent = navigator.onLine ? 'Online' : 'Offline';
  el.className = 'chip ' + (navigator.onLine ? '' : 'chip-ok');
  el.title = navigator.onLine ? '' : 'Offline: the app still works';
}

// Register the service worker. On the very first visit, wait until it has saved the app for offline use
// before loading the model, so the 31 MB of model + runtime is downloaded once, not twice.
async function setupServiceWorker() {
  if (!('serviceWorker' in navigator)) return 'unsupported';
  try {
    navigator.serviceWorker.addEventListener('message', (e) => {
      if (e.data && e.data.type === 'precache' && !Model.ready) setModelStatus(`Saving for offline ${e.data.done}/${e.data.total}`, 'wait');
      if (e.data && e.data.type === 'precache-done') recheckAudio();
    });
    navigator.serviceWorker.addEventListener('controllerchange', recheckAudio);
    // Some browsers block service workers without rejecting; never let that stop the model from loading.
    const reg = await Promise.race([navigator.serviceWorker.register('sw.js'),
      new Promise((_, rej) => setTimeout(() => rej(new Error('service worker registration timed out')), 15000))]);
    if (navigator.serviceWorker.controller) return 'controlled';
    if (reg.active && !reg.installing && !reg.waiting) return 'bypassed'; // e.g. a hard reload
    await new Promise((resolve) => {
      navigator.serviceWorker.addEventListener('controllerchange', resolve, { once: true });
      const w = reg.installing || reg.waiting;
      if (w) w.addEventListener('statechange', () => { if (w.state === 'redundant' || w.state === 'activated') resolve(); });
      setTimeout(resolve, 60000);
    });
    return navigator.serviceWorker.controller ? 'controlled' : 'failed';
  } catch (e) {
    console.warn('Service worker not registered:', e);
    return 'failed';
  }
}

async function boot() {
  document.querySelectorAll('.lang button').forEach((b) => b.addEventListener('click', () => {
    lang = b.dataset.lang;
    store.set('lang', lang);
    document.documentElement.lang = HTML_LANG[lang];
    renderCurrent();
    if (lang === 'kik') toast('Gĩkũyũ: only a few short phrases are written so far. The rest is shown in Swahili.');
  }));
  document.querySelectorAll('.tabbar button').forEach((b) => b.addEventListener('click', () => setTab(b.dataset.tab)));
  window.addEventListener('online', updateNet);
  window.addEventListener('offline', updateNet);
  updateNet();
  try { await DB.open(); } catch (e) { toast('This browser cannot save records. Results will not be kept.'); }
  const sw = setupServiceWorker();
  swSettled = sw.then(() => {});
  await Promise.all([loadAnswers(), loadGuides(), loadSamples(), refreshVisitContext()]);
  const start = (location.hash || '').slice(1);
  setTab(['visit', 'review', 'coop', 'about'].includes(start) ? start : 'visit');
  // Wait at most 20 s for offline saving before loading the model (it keeps saving in the background).
  window.__kahawa.swState = await Promise.race([sw, new Promise((r) => setTimeout(() => r('still saving'), 20000))]);
  await loadModel();
}

// Test hooks (used by automated checks; harmless for users).
window.__kahawa = {
  ready: () => modelReady.then(() => ({ ready: Model.ready, error: Model.error, head: Model.active && Model.active.version })),
  async classifyUrl(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(url + ': ' + res.status);
    const r = await classifyImage(await loadImage(await res.blob()));
    const classes = Model.active.classes;
    return {
      url, label: r.label, top: r.top, not_sure: r.not_sure, reason: r.reason, band: r.band,
      max_prob: r.max_prob, probs: Object.fromEntries(classes.map((c, k) => [c, r.probs[k]])),
      ood_distance: r.ood_distance, local_distance: r.local_distance, familiar_by: r.familiar_by,
      head_version: r.head_version, quality: r.quality, ms: r.ms,
      embed_dim: r.embedding.length, embedding_head: Array.from(r.embedding.slice(0, 8)),
    };
  },
  async embedUrl(url) {
    const res = await fetch(url);
    const r = await classifyImage(await loadImage(await res.blob()));
    return Array.from(r.embedding);
  },
  stats: { villageStats, villageRows, finalLabel, plotsCsv },
  guides: { get: () => guides, idFor: guideIdFor, open: openGuide },
  wording: { list: wordingList, csv: async () => wordingCsv(await wordingList()), merge: mergeWordingCorrections, buildUpdate },
  refitHead, predictHead,
  model: Model,
};

boot();
})();
