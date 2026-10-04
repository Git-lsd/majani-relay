// Kahawa Check core maths shared by the app (plain JS, no dependencies). Mirrors ml/train_eval.py.
// - familiarity check: distance to the k nearest stored photos (int8 reference set, see model/head.json), OR, when
//   officer-labelled rows exist and head.ood.local_nearest_cutoff is set, distance to the single nearest officer row
// - head adaptation (learning loop): CE + (lambda/2)||W-W0||^2 pulled toward the shipped head
// - co-op early warning: maximum-likelihood beta-binomial prior + posterior P(share > q*)
(function (root) {
  'use strict';

  function l2normalise(v) {
    let s = 0;
    for (let i = 0; i < v.length; i++) s += v[i] * v[i];
    s = Math.sqrt(s) || 1;
    const out = new Float32Array(v.length);
    for (let i = 0; i < v.length; i++) out[i] = v[i] / s;
    return out;
  }

  // Parse model/reference.bin: n*dim int8 (row-major) then n float32 LE scales. Returns normalised rows.
  function parseReference(buf, n, dim) {
    const q = new Int8Array(buf, 0, n * dim);
    const sc = new Float32Array(buf.slice(n * dim, n * dim + 4 * n));
    const rows = [];
    for (let r = 0; r < n; r++) {
      const v = new Float32Array(dim);
      for (let j = 0; j < dim; j++) v[j] = q[r * dim + j] * sc[r];
      rows.push(l2normalise(v));
    }
    return rows;
  }

  function rowsFromInt8(int8Rows, scales) {
    return int8Rows.map((row, r) => l2normalise(Float32Array.from(row, x => x * scales[r])));
  }

  // distance = 1 - mean of the k largest cosine similarities (rows already L2-normalised)
  function familiarityDistance(embedding, rows, k) {
    const e = l2normalise(embedding);
    const top = [];
    for (const r of rows) {
      let s = 0;
      for (let j = 0; j < e.length; j++) s += e[j] * r[j];
      if (top.length < k) { top.push(s); top.sort((a, b) => a - b); }
      else if (s > top[0]) { top[0] = s; top.sort((a, b) => a - b); }
    }
    return 1 - top.reduce((a, b) => a + b, 0) / top.length;
  }

  // distance to the single nearest row = 1 - max cosine similarity (rows already L2-normalised); Infinity if no rows
  function nearestDistance(embedding, rows) {
    if (!rows || !rows.length) return Infinity;
    const e = l2normalise(embedding);
    let best = -Infinity;
    for (const r of rows) {
      let s = 0;
      for (let j = 0; j < e.length; j++) s += e[j] * r[j];
      if (s > best) best = s;
    }
    return 1 - best;
  }

  // The app's familiarity rule. dist: k-nearest distance to [shipped reference + officer rows]; localDist: distance to
  // the nearest officer row (rows labelled on this phone or received in an officer update; never reference.bin rows).
  // localCutoff missing (older head.json) or no officer rows (localDist = Infinity): the k-nearest rule alone.
  function isFamiliar(dist, cutoff, localDist, localCutoff) {
    if (dist <= cutoff) return true;
    return Number.isFinite(localCutoff) && Number.isFinite(localDist) && localDist <= localCutoff;
  }

  function softmaxT(logits, T) {
    const z = logits.map(v => v / T);
    const m = Math.max(...z);
    const ex = z.map(v => Math.exp(v - m));
    const s = ex.reduce((a, b) => a + b, 0);
    return ex.map(v => v / s);
  }

  function headLogits(W, b, e) {
    return W.map((row, c) => {
      let s = b[c];
      for (let j = 0; j < row.length; j++) s += row[j] * e[j];
      return s;
    });
  }

  // Full decision for one embedding. refRows = shipped reference + locally added rows; localRows (optional) = the
  // locally added (officer) rows alone, for the second familiarity check (head.ood.local_nearest_cutoff).
  // head.route_to_officer (head v3): classes never shown as a diagnosis ('other'); when one is the top class the
  // photo is not answered (reason 'other_problem'), then 'unfamiliar', then 'low_confidence' (as ml/train_eval.py).
  function classify(head, W, b, refRows, e, localRows) {
    const P = softmaxT(headLogits(W, b, e), head.temperature);
    let best = 0;
    for (let c = 1; c < P.length; c++) if (P[c] > P[best]) best = c;
    const dist = familiarityDistance(e, refRows, head.ood.k);
    const localDist = nearestDistance(e, localRows);
    const confident = P[best] >= head.threshold;
    const familiar = isFamiliar(dist, head.ood.cutoff, localDist, head.ood.local_nearest_cutoff);
    const other = (head.route_to_officer || []).includes(head.classes[best]);
    return { label: head.classes[best], prob: P[best], probs: P, distance: dist,
             localDistance: Number.isFinite(localDist) ? localDist : null,
             answered: confident && familiar && !other,
             reason: other ? 'other_problem' : (!familiar ? 'unfamiliar' : (!confident ? 'low_confidence' : null)) };
  }

  // Learning loop: full-batch gradient descent on mean CE((W z + b)/T) + lam/2 (||W-W0||^2 + ||b-b0||^2).
  function adaptHead(W0, b0, Z, y, T, lam, steps, lr) {
    steps = steps || 300; lr = lr || 0.5;
    const C = W0.length, D = W0[0].length, N = Z.length;
    const W = W0.map(r => Float64Array.from(r)), b = Float64Array.from(b0);
    if (!N) return { W: W.map(r => Array.from(r)), b: Array.from(b) };
    for (let it = 0; it < steps; it++) {
      const gW = W.map(() => new Float64Array(D)), gb = new Float64Array(C);
      for (let n = 0; n < N; n++) {
        const z = Z[n];
        const L = W.map((row, c) => { let s = b[c]; for (let j = 0; j < D; j++) s += row[j] * z[j]; return s / T; });
        const m = Math.max(...L); const ex = L.map(v => Math.exp(v - m)); const s = ex.reduce((a, c) => a + c, 0);
        for (let c = 0; c < C; c++) {
          const g = (ex[c] / s - (c === y[n] ? 1 : 0)) / (T * N);
          gb[c] += g;
          const gr = gW[c];
          for (let j = 0; j < D; j++) gr[j] += g * z[j];
        }
      }
      for (let c = 0; c < C; c++) {
        gb[c] += lam * (b[c] - b0[c]);
        b[c] -= lr * gb[c];
        const row = W[c], r0 = W0[c], gr = gW[c];
        for (let j = 0; j < D; j++) row[j] -= lr * (gr[j] + lam * (row[j] - r0[j]));
      }
    }
    return { W: W.map(r => Array.from(r)), b: Array.from(b) };
  }

  // ---- co-op early warning ----
  function lgamma(x) { // Lanczos approximation
    const g = 7, c = [0.99999999999980993, 676.5203681218851, -1259.1392167224028, 771.32342877765313,
      -176.61502916214059, 12.507343278686905, -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7];
    if (x < 0.5) return Math.log(Math.PI / Math.sin(Math.PI * x)) - lgamma(1 - x);
    x -= 1; let a = c[0]; const t = x + g + 0.5;
    for (let i = 1; i < g + 2; i++) a += c[i] / (x + i);
    return 0.5 * Math.log(2 * Math.PI) + (x + 0.5) * Math.log(t) - t + Math.log(a);
  }
  const betaln = (a, b) => lgamma(a) + lgamma(b) - lgamma(a + b);

  // Maximum-likelihood Beta(alpha, beta) prior from flagged counts x out of answered a (grid search in log space)
  function fitBetaBinomial(x, a) {
    if (x.length < 3) return { alpha: 1, beta: 4, fallback: true };
    let best = null;
    for (let la = -3; la <= 6; la += 0.1) {
      for (let lb = -3; lb <= 7; lb += 0.1) {
        const al = Math.exp(la), be = Math.exp(lb);
        let ll = 0;
        for (let i = 0; i < x.length; i++) ll += betaln(x[i] + al, a[i] - x[i] + be) - betaln(al, be);
        if (!best || ll > best.ll) best = { ll, alpha: al, beta: be };
      }
    }
    // cap: the prior never counts for more than 50 photos (avoids pulling every village to the average)
    const k = best.alpha + best.beta, CAP = 50;
    if (k > CAP) return { alpha: best.alpha * CAP / k, beta: best.beta * CAP / k, fallback: false, capped: true };
    return { alpha: best.alpha, beta: best.beta, fallback: false };
  }

  // Regularised incomplete beta I_x(a,b) (continued fraction, Numerical Recipes betacf)
  function betacf(x, a, b) {
    const MAXIT = 200, EPS = 3e-12, FPMIN = 1e-300;
    let qab = a + b, qap = a + 1, qam = a - 1, c = 1, d = 1 - qab * x / qap;
    if (Math.abs(d) < FPMIN) d = FPMIN; d = 1 / d; let h = d;
    for (let m = 1; m <= MAXIT; m++) {
      const m2 = 2 * m;
      let aa = m * (b - m) * x / ((qam + m2) * (a + m2));
      d = 1 + aa * d; if (Math.abs(d) < FPMIN) d = FPMIN; c = 1 + aa / c; if (Math.abs(c) < FPMIN) c = FPMIN;
      d = 1 / d; h *= d * c;
      aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2));
      d = 1 + aa * d; if (Math.abs(d) < FPMIN) d = FPMIN; c = 1 + aa / c; if (Math.abs(c) < FPMIN) c = FPMIN;
      d = 1 / d; const del = d * c; h *= del;
      if (Math.abs(del - 1) < EPS) break;
    }
    return h;
  }
  function betaCdf(x, a, b) {
    if (x <= 0) return 0; if (x >= 1) return 1;
    const bt = Math.exp(lgamma(a + b) - lgamma(a) - lgamma(b) + a * Math.log(x) + b * Math.log(1 - x));
    return x < (a + 1) / (a + b + 2) ? bt * betacf(x, a, b) / a : 1 - bt * betacf(1 - x, b, a) / b;
  }

  // villages: [{name, answered, flagged}] -> adds raw, adjusted (posterior mean), pAbove, alert; sorted by pAbove
  function villageAlerts(villages, qStar) {
    const ok = villages.filter(v => v.answered > 0);
    const prior = fitBetaBinomial(ok.map(v => v.flagged), ok.map(v => v.answered));
    const out = villages.map(v => {
      const A = prior.alpha + v.flagged, B = prior.beta + v.answered - v.flagged;
      const pAbove = 1 - betaCdf(qStar, A, B);
      return Object.assign({}, v, { raw: v.answered ? v.flagged / v.answered : null, adjusted: A / (A + B),
                                    pAbove, alert: pAbove > 0.5 });
    });
    out.sort((p, q) => q.pAbove - p.pAbove);
    return { prior, villages: out };
  }

  root.KahawaCore = { l2normalise, parseReference, rowsFromInt8, familiarityDistance, nearestDistance, isFamiliar,
                      softmaxT, headLogits, classify,
                      adaptHead, fitBetaBinomial, betaCdf, villageAlerts };
})(typeof window !== 'undefined' ? window : globalThis);
