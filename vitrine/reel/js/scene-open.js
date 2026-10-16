/* ==========================================================================
   Compassos 1–4 · IGNIÇÃO e MANIFESTO
   ========================================================================== */
'use strict';
(function () {
  const { C, E, B, clamp, lerp, prog, TAU } = R;
  const CX = 960, CY = 520;

  /* ---------- compassos 1–2: um ponto vira régua, a régua vira a marca ---------- */
  R.S0 = function (ctx, t) {
    if (t > B(8.2)) return;
    // o ponto: bate no tempo 0 e no tempo 1
    const dotA = prog(t, 0.08, 0.3) * (1 - prog(t, B(2) - 0.03, B(2)));
    const beat = R.pulse(t, 0.12, 7) + R.pulse(t, B(1), 7);
    R.disc(ctx, CX, CY, 5 + beat * 7, C.acc, dotA);
    R.ring(ctx, CX, CY, 10 + prog(t, 0.12, 0.9) * 80, C.acc, 1, dotA * (1 - prog(t, 0.12, 0.9)) * 0.8);
    // régua: nasce do ponto nos dois sentidos e volta
    const out = E.expoOut(prog(t, B(1), B(1) + 0.38)), back = E.io(prog(t, B(1.55), B(2)));
    const half = 860 * out * (1 - back);
    if (half > 1) {
      R.line(ctx, CX - half, CY, CX + half, CY, C.ink2, 1, 0.8);
      for (let i = 1; i <= 43; i++) {
        const dx = i * 20;
        if (dx > half) break;
        const major = i % 5 === 0, h = major ? 14 : 6;
        const a = 0.35 + (major ? 0.5 : 0);
        R.line(ctx, CX - dx, CY - h, CX - dx, CY + h * 0.3, C.ink2, 1, a);
        R.line(ctx, CX + dx, CY - h, CX + dx, CY + h * 0.3, C.ink2, 1, a);
        if (major && i % 10 === 0) {
          R.text(ctx, String(i / 10), CX + dx, CY + 30, { font: R.font(500, 12, R.MONO), color: C.ink3, align: 'center', alpha: 0.8 });
          R.text(ctx, String(-i / 10), CX - dx, CY + 30, { font: R.font(500, 12, R.MONO), color: C.ink3, align: 'center', alpha: 0.8 });
        }
      }
    }
    // a marca: três estouros, três notas
    if (t < B(2)) return;
    const pop = [0, 1, 2].map(i => R.spring(t - (B(2) + i * B(0.25)), 2.1, 0.36));
    const spread = R.spring(t - B(2), 1.6, 0.5);
    const fly = E.whip(prog(t, B(6.4), B(7.6)));
    const s = lerp(150, 13, fly), x = lerp(CX, 118, fly), y = lerp(CY - 40, 84, fly);
    const rot = (1 - fly) * (t - B(2)) * 0.12;
    ctx.save();
    ctx.translate(x, y); ctx.rotate(rot); ctx.translate(-x, -y);
    R.logo(ctx, x, y, s, { pop, spread: 0.2 + 0.8 * spread, alpha: 1 - prog(t, B(7.6), B(7.9)) });
    ctx.restore();
    // ondas a cada batida da marca
    for (const [tb, a] of [[B(2), 0.7], [B(4), 0.5], [B(5), 0.35]]) {
      const p = prog(t, tb, tb + 1.1);
      if (p > 0 && p < 1) R.ring(ctx, CX, CY - 40, 200 + E.out(p) * 420, C.acc, 1.2, (1 - p) * a * (1 - fly));
    }
    // palavra-marca
    const L1 = R.layout(ctx, 'Hinove', R.font(700, 120), -4);
    R.rise(ctx, L1, CX - L1.w / 2, CY + 250, t, { t0: B(3.3), size: 120, stagger: 0.04, out: { t0: B(6.1), stagger: 0.02 } });
    const L2 = R.layout(ctx, 'CENTRAL FISCAL', R.font(500, 24, R.MONO), 14);
    R.rise(ctx, L2, CX - L2.w / 2, CY + 310, t, { t0: B(4.4), size: 26, stagger: 0.025, color: C.acc, out: { t0: B(6.1), stagger: 0.01 } });
  };

  /* ---------- compassos 3–4: de onde se vem, e para onde se vai ---------- */
  const WORDS = [
    { w: 'Macros.', at: B(8), x: 150, y: 330, size: 190 },
    { w: 'Planilhas.', at: B(8.75), x: 640, y: 560, size: 190 },
    { w: 'Scripts', at: B(9.5), x: 230, y: 800, size: 190 },
    { w: 'soltos.', at: B(10), x: 1030, y: 800, size: 190 },
  ];
  const FINAL = { a: 'Uma ', b: 'tela.', size: 300, y: 640 };
  let PTS = null, N = 0;
  function sample(draw, step) {
    const cv = document.createElement('canvas'); cv.width = 1920; cv.height = 1080;
    const c = cv.getContext('2d', { willReadFrequently: true });
    draw(c);
    const d = c.getImageData(0, 0, 1920, 1080).data, out = [];
    for (let y = 0; y < 1080; y += step) for (let x = 0; x < 1920; x += step) {
      if (d[(y * 1920 + x) * 4 + 3] > 140) out.push([x, y, d[(y * 1920 + x) * 4] > 128 ? 0 : 1]);
    }
    return out;
  }
  R.prepare = function () {
    const src = sample(c => {
      c.fillStyle = '#fff';
      for (const w of WORDS) { c.font = R.font(700, w.size); c.letterSpacing = '-8px'; c.fillText(w.w, w.x, w.y); }
    }, 4);
    const dst = sample(c => {
      c.font = R.font(700, FINAL.size); c.letterSpacing = '-12px';
      const wa = c.measureText(FINAL.a).width, wb = c.measureText(FINAL.b).width, x0 = 960 - (wa + wb) / 2;
      c.fillStyle = '#fff'; c.fillText(FINAL.a, x0, FINAL.y);
      c.fillStyle = '#00ff00'; c.fillText(FINAL.b, x0 + wa, FINAL.y);   /* canal R zero marca "tela." */
    }, 4);
    const g = R.rng(31);
    N = Math.min(7000, src.length, dst.length);
    const pick = (arr) => { const a = arr.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(g() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a.slice(0, N); };
    const S = pick(src).sort((p, q) => p[0] - q[0]), D = pick(dst).sort((p, q) => p[0] - q[0]);
    PTS = S.map((s, i) => ({ sx: s[0], sy: s[1], dx: D[i][0], dy: D[i][1], green: D[i][2] === 1, d: g() * 0.22, sw: (g() - 0.5) * 2, r: 2.2 + g() * 1.6 }));
  };

  R.S1 = function (ctx, t) {
    if (t < B(7.8) || t > B(16.3)) return;
    const dissolve = B(11.25);
    if (t < dissolve + 0.02) {
      WORDS.forEach((w, i) => {
        const L = R.layout(ctx, w.w, R.font(700, w.size), -8);
        const dim = i < WORDS.length - 1 ? prog(t, WORDS[i + 1].at, WORDS[i + 1].at + 0.3) : 0;
        ctx.save();
        ctx.globalAlpha = 1 - dim * 0.55;
        R.rise(ctx, L, w.x, w.y, t, { t0: w.at, size: w.size, stagger: 0.022, dur: 0.42, ease: E.quintOut });
        ctx.restore();
        // o risco: cada palavra é cortada por um fio verde
        const st = E.snap(prog(t, B(10.6) + i * 0.06, B(10.6) + i * 0.06 + 0.26));
        if (st > 0) R.rect(ctx, w.x - 10, w.y - w.size * 0.33, (L.w + 20) * st, 10, C.acc, 1);
        // rótulo técnico ao lado, em mono
        const la = prog(t, w.at + 0.15, w.at + 0.35) * (1 - dim * 0.6);
        R.text(ctx, ['.xlsm', '.xlsx', '.py', '.bas'][i], w.x + L.w + 18, w.y - w.size * 0.62, { font: R.font(500, 22, R.MONO), color: C.ink3, alpha: la });
      });
      return;
    }
    if (!PTS) return;
    // partículas: das palavras para "Uma tela.", depois tudo num ponto
    const col = E.expoIn(prog(t, B(15.25), B(16)));
    const spin = col * 2.4;
    const hold = prog(t, B(13.9), B(15.25));
    for (let i = 0; i < N; i++) {
      const p = PTS[i];
      const k = E.io(prog(t, dissolve + p.d, dissolve + p.d + B(2.2)));
      let x = lerp(p.sx, p.dx, k), y = lerp(p.sy, p.dy, k);
      const bump = Math.sin(k * Math.PI);
      x += p.sw * bump * 260; y += Math.cos(p.sw * 9) * bump * 180;
      x += R.noise(t * 3 + i, 5) * 1.2 * hold; y += R.noise(t * 3 + i, 6) * 1.2 * hold;
      if (col > 0) {
        const ang = Math.atan2(y - 540, x - 960) + spin, rad = Math.hypot(x - 960, y - 540) * (1 - col);
        x = 960 + Math.cos(ang) * rad; y = 540 + Math.sin(ang) * rad;
      }
      const c = k > 0.6 && p.green ? C.acc : C.ink;
      ctx.fillStyle = c;
      ctx.globalAlpha = 0.9;
      const r = p.r * (1 - col * 0.6);
      ctx.fillRect(x - r / 2, y - r / 2, r, r);
    }
    ctx.globalAlpha = 1;
    // ponto que sobra antes do drop
    R.disc(ctx, 960, 540, 6 + col * 10, C.acc, col);
  };
})();
