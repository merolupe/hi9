/* ==========================================================================
   Central Fiscal · reel — regente
   Fundo (campo de estrelas em voo), impactos, composição do quadro, pós
   (bloom, aberração, vinheta, grão) e a API que o render.mjs usa.
   A técnica veio do showreel do órbita (horbita/showreel): tudo é função
   pura do tempo, então qualquer quadro sai igual em qualquer processo.
   ========================================================================== */
'use strict';
(function () {
  const { C, E, B, clamp, lerp, prog } = R;

  /* ---------- viagem: distância percorrida, com arrancadas nas transições ---------- */
  const WARPS = [[B(15.2), 900, 0.8], [B(22.5), 1400, 1.5]];
  for (let i = 1; i < 8; i++) WARPS.push([R.T0 + i * R.TLEN - 0.3, 420, 0.55]);
  WARPS.push([B(71.4), 700, 0.7], [B(79.2), 1300, 0.9], [B(87.4), 600, 0.8]);
  R.travel = t => 60 * t + WARPS.reduce((a, w) => a + w[1] * R.smooth(prog(t, w[0], w[0] + w[2])), 0);

  const STARS = (() => {
    const g = R.rng(7), out = [];
    for (let i = 0; i < 520; i++) {
      const warm = g();
      out.push({
        x: (g() - 0.5) * 3600, y: (g() - 0.5) * 2200, z: g() * 2400, r: 0.5 + g() * 1.3,
        c: warm < 0.08 ? C.b1 : warm < 0.13 ? C.acc : warm < 0.16 ? '#8C98EA' : null,
      });
    }
    return out;
  })();
  const Z = 2400, F = 700;
  const starA = t => prog(t, 0.2, 1.8) * (1 - prog(t, 44.3, 45));
  function stars(ctx, t, sub) {
    const a = starA(t);
    if (a <= 0) return;
    const D1 = R.travel(t), D0 = R.travel(t - Math.max(sub, 1 / 60) * 1.4);
    const dx = R.noise(t * 0.15, 3) * 60, dy = R.noise(t * 0.13, 4) * 40;
    ctx.save();
    ctx.lineCap = 'round';
    for (const s of STARS) {
      let z1 = ((s.z - D1) % Z + Z) % Z + 40;
      let z0 = z1 + (D1 - D0);
      if (z0 > Z + 40) z0 = z1;
      const x1 = 960 + (s.x + dx) * F / z1, y1 = 540 + (s.y + dy) * F / z1;
      if (x1 < -40 || x1 > 1960 || y1 < -40 || y1 > 1120) continue;
      const x0 = 960 + (s.x + dx) * F / z0, y0 = 540 + (s.y + dy) * F / z0;
      const near = clamp(1 - z1 / Z);
      const al = a * (0.18 + 0.7 * near * near);
      ctx.strokeStyle = s.c ? R.rgba(s.c, al) : 'rgba(170,190,215,' + al.toFixed(3) + ')';
      ctx.lineWidth = s.r * (0.6 + near * 1.6);
      ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1 + 0.01, y1); ctx.stroke();
    }
    ctx.restore();
  }

  /* ---------- impactos: tremor, flash e aberração ---------- */
  const HITS = [[B(2), 0.45], [B(8), 0.3], [B(12), 0.35], [B(16), 1], [B(80), 0.6], [B(82), 0.45], [B(84), 0.45], [B(86), 0.6], [B(88), 0.5], [B(93), 0.35]];
  for (let i = 0; i < 8; i++) HITS.push([R.T0 + i * R.TLEN, i ? 0.4 : 0.7]);
  HITS.push([R.T0 + 7 * R.TLEN + B(4), 0.35]);          /* o carimbo do Faturabot */
  R.impact = t => HITS.reduce((a, h) => a + h[1] * R.pulse(t, h[0], 6), 0);
  function shake(t) {
    const k = HITS.reduce((a, h) => a + h[1] * R.pulse(t, h[0], 11), 0);
    return [R.noise(t * 40, 1) * 12 * k, R.noise(t * 40, 2) * 12 * k];
  }
  const FLASH = [[B(16), 0.3], [B(80), 0.14], [B(88), 0.12], [R.T0, 0.1]];
  const flash = t => FLASH.reduce((a, f) => a + f[1] * R.pulse(t, f[0], 14), 0);

  R.S = 1;
  let bgGrad = null;
  R.draw = function (ctx, t, sub) {
    ctx.setTransform(R.S, 0, 0, R.S, 0, 0);
    ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over'; ctx.filter = 'none';
    ctx.fillStyle = C.bg; ctx.fillRect(0, 0, R.W, R.H);
    if (!bgGrad) {
      bgGrad = ctx.createRadialGradient(960, 540, 0, 960, 540, 1150);
      bgGrad.addColorStop(0, 'rgba(20,26,38,.9)'); bgGrad.addColorStop(1, 'rgba(20,26,38,0)');
    }
    ctx.fillStyle = bgGrad; ctx.fillRect(0, 0, R.W, R.H);
    const sh = shake(t);
    ctx.translate(sh[0], sh[1]);
    stars(ctx, t, sub);
    R.S0(ctx, t);
    R.S1(ctx, t);
    R.S2(ctx, t);
    R.Tools(ctx, t);
    R.S4(ctx, t);
    R.S5(ctx, t);
    R.S6(ctx, t);
    R.HUD(ctx, t);
    ctx.setTransform(R.S, 0, 0, R.S, 0, 0);
    const fl = flash(t);
    if (fl > 0.002) {
      ctx.globalCompositeOperation = 'lighter';
      ctx.fillStyle = 'rgba(150,235,195,' + clamp(fl).toFixed(3) + ')'; ctx.fillRect(0, 0, R.W, R.H);
      ctx.globalCompositeOperation = 'source-over';
    }
    const fb = E.sineIO(prog(t, 44.35, 45)) + (1 - E.sineIO(prog(t, 0, 0.12)));
    if (fb > 0) { ctx.fillStyle = 'rgba(0,0,0,' + clamp(fb).toFixed(3) + ')'; ctx.fillRect(0, 0, R.W, R.H); }
  };

  /* ---------- pós ---------- */
  let B1, B2, b1, b2;
  R.bloom = function (ctx, cv, k = 1) {
    if (!B1) {
      B1 = document.createElement('canvas'); B2 = document.createElement('canvas');
      b1 = B1.getContext('2d'); b2 = B2.getContext('2d');
    }
    const w = cv.width, h = cv.height;
    if (B1.width !== Math.round(w / 4)) { B1.width = Math.round(w / 4); B1.height = Math.round(h / 4); B2.width = Math.round(w / 8); B2.height = Math.round(h / 8); }
    b1.setTransform(1, 0, 0, 1, 0, 0); b1.filter = 'url(#thr) blur(' + (3 * R.S).toFixed(1) + 'px)';
    b1.clearRect(0, 0, B1.width, B1.height);
    b1.drawImage(cv, 0, 0, B1.width, B1.height);
    b1.filter = 'none';
    b2.filter = 'blur(' + (5 * R.S).toFixed(1) + 'px)';
    b2.clearRect(0, 0, B2.width, B2.height);
    b2.drawImage(B1, 0, 0, B2.width, B2.height);
    b2.filter = 'none';
    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.globalCompositeOperation = 'lighter';
    ctx.imageSmoothingQuality = 'high';
    ctx.globalAlpha = 0.24 * k; ctx.drawImage(B1, 0, 0, w, h);
    ctx.globalAlpha = 0.32 * k; ctx.drawImage(B2, 0, 0, w, h);
    ctx.restore();
  };

  let VIG = null, GR = null;
  function grade(src, w, h, t, frame) {
    if (!VIG || VIG.length !== w * h) {
      VIG = new Float32Array(w * h);
      for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
        const dx = (x / w - 0.5) * 1.78, dy = y / h - 0.5, r = Math.hypot(dx, dy) / 0.9;
        VIG[y * w + x] = 1 - 0.32 * R.smooth(clamp((r - 0.45) / 0.75));
      }
      const g = R.rng(9); GR = new Float32Array(512 * 512);
      for (let i = 0; i < GR.length; i++) GR[i] = (g() + g() + g() - 1.5) * 2.4;
    }
    const out = new Uint8ClampedArray(src.length);
    const k = (0.0008 + clamp(R.impact(t)) * 0.005), cx = w / 2, cy = h / 2;
    const ox = (frame * 173) % 512, oy = (frame * 311) % 512;
    for (let y = 0; y < h; y++) {
      const yr = Math.round(cy + (y - cy) * (1 + k)), yb = Math.round(cy + (y - cy) * (1 - k));
      const rowR = clamp(yr, 0, h - 1) * w, rowB = clamp(yb, 0, h - 1) * w, gy = ((y + oy) & 511) * 512;
      for (let x = 0; x < w; x++) {
        const i = y * w + x, o = i * 4;
        const xr = clamp(Math.round(cx + (x - cx) * (1 + k)), 0, w - 1), xb = clamp(Math.round(cx + (x - cx) * (1 - k)), 0, w - 1);
        const v = VIG[i], n = GR[gy + ((x + ox) & 511)];
        out[o] = src[(rowR + xr) * 4] * v + n;
        out[o + 1] = src[o + 1] * v + n;
        out[o + 2] = src[(rowB + xb) * 4 + 2] * v + n;
        out[o + 3] = 255;
      }
    }
    return out;
  }

  /* ---------- quadro final com motion blur por subamostragem ---------- */
  const FAST = [[B(1.8), B(3)], [B(6), B(8.2)], [B(12.3), B(14.2)], [B(15.2), B(17.5)], [B(22.3), B(24.8)], [B(71.2), B(72.6)], [B(78.8), B(80.6)], [B(86.8), B(88.8)], [B(91.8), B(93)]];
  for (let i = 1; i < 8; i++) FAST.push([R.T0 + i * R.TLEN - 0.45, R.T0 + i * R.TLEN + 0.5]);
  R.samplesAt = T => (FAST.some(f => T >= f[0] && T <= f[1]) ? 10 : 5);
  let ACC = null;
  R.renderFrame = function (cv, ctx, frame, o = {}) {
    const T = frame / R.FPS;
    const n = o.samples || R.samplesAt(T);
    const shutter = (o.shutter == null ? 0.5 : o.shutter) / R.FPS;
    const w = cv.width, h = cv.height;
    if (n > 1) {
      if (!ACC || ACC.length !== w * h * 4) ACC = new Uint16Array(w * h * 4);
      ACC.fill(0);
      for (let s = 0; s < n; s++) {
        const t = T - shutter / 2 + ((s + 0.5) * shutter) / n;
        R.draw(ctx, t, shutter / n);
        const d = ctx.getImageData(0, 0, w, h).data;
        for (let i = 0; i < d.length; i++) ACC[i] += d[i];
      }
      const img = ctx.createImageData(w, h), a = img.data, inv = 1 / n;
      for (let i = 0; i < a.length; i++) a[i] = ACC[i] * inv + 0.5;
      ctx.putImageData(img, 0, 0);
    } else R.draw(ctx, T, shutter);
    R.bloom(ctx, cv, 1);
    const src = ctx.getImageData(0, 0, w, h).data;
    return o.grade === false ? src : grade(src, w, h, T, frame);
  };

  /* ---------- fontes e API do render.mjs ---------- */
  const FACES = [
    ['Inter', 'inter-latin-400-normal', '400'], ['Inter', 'inter-latin-500-normal', '500'],
    ['Inter', 'inter-latin-600-normal', '600'], ['Inter', 'inter-latin-700-normal', '700'],
    ['JetBrains Mono', 'jetbrains-mono-latin-400-normal', '400'], ['JetBrains Mono', 'jetbrains-mono-latin-500-normal', '500'],
  ];
  const SRC = f => 'url(' + ((window.REEL_FONTS && window.REEL_FONTS[f]) || '../fontes/' + f + '.woff2') + ')';
  R.ready = Promise.all(FACES.map(f => new FontFace(f[0], SRC(f[1]), { weight: f[2] }).load().then(ff => document.fonts.add(ff))))
    .then(() => R.prepare && R.prepare());

  window.REEL = {
    ready: R.ready,
    setup(scale) {
      R.S = scale;
      const cv = document.getElementById('c');
      cv.width = Math.round(R.W * scale); cv.height = Math.round(R.H * scale);
      return cv;
    },
    async renderRange(o) {
      const cv = this.setup(o.scale || 1), ctx = cv.getContext('2d', { willReadFrequently: true });
      for (let i = o.from + o.offset; i < o.to; i += o.step) {
        const px = R.renderFrame(cv, ctx, i, o);
        await fetch(o.url + '?i=' + i, { method: 'POST', body: px });
      }
      return true;
    },
    async stills(o) {
      const cv = this.setup(o.scale || 0.5), ctx = cv.getContext('2d', { willReadFrequently: true });
      for (const t of o.times) {
        const px = R.renderFrame(cv, ctx, Math.round(t * R.FPS), o);
        ctx.putImageData(new ImageData(px, cv.width, cv.height), 0, 0);
        const blob = await new Promise(r => cv.toBlob(r, 'image/png'));
        await fetch(o.url + '?name=' + encodeURIComponent(o.prefix + t.toFixed(3)), { method: 'POST', body: blob });
      }
      return true;
    },
  };

  /* ---------- reprodução ao vivo ---------- */
  if (/render/.test(location.search)) return;
  R.ready.then(() => {
    const stage = document.getElementById('stage');
    const box = stage.getBoundingClientRect();
    const shown = Math.min(box.width, (box.height * 16) / 9) * (devicePixelRatio || 1);
    const cv = window.REEL.setup(clamp(shown / R.W, 0.5, 1));
    const ctx = cv.getContext('2d');
    const au = document.getElementById('au'), gate = document.getElementById('gate');
    const POSTER = 43.2;
    let state = 'idle', t0 = 0, tp = 0;
    const clock = () => (performance.now() - t0) / 1000;
    function play() {
      if (state !== 'paused') tp = 0;
      t0 = performance.now() - tp * 1000;
      if (au) { try { au.currentTime = tp; } catch (e) {} au.play().catch(() => {}); }
      state = 'playing'; gate.hidden = true;
    }
    function pause() { tp = clamp(clock(), 0, R.DUR - 0.001); state = 'paused'; if (au) au.pause(); gate.hidden = false; }
    gate.addEventListener('click', play);
    cv.addEventListener('click', () => (state === 'playing' ? pause() : play()));
    addEventListener('keydown', e => { if (e.key === ' ') { e.preventDefault(); state === 'playing' ? pause() : play(); } });
    (function loop() {
      let t = state === 'playing' ? clock() : state === 'paused' ? tp : POSTER;
      if (state === 'playing' && t >= R.DUR) { state = 'idle'; gate.hidden = false; t = POSTER; if (au) au.pause(); }
      R.draw(ctx, t, 1 / R.FPS);
      R.bloom(ctx, cv, 1);
      requestAnimationFrame(loop);
    })();
  });
})();
