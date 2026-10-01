/* ==========================================================================
   Compassos 19–24 · FLUXO, NÚMEROS e ASSINATURA, mais o HUD
   ========================================================================== */
'use strict';
(function () {
  const { C, E, B, clamp, lerp, prog, TAU } = R;
  const mono = (px, w = 500) => R.font(w, px, R.MONO);

  /* ---------- compassos 19–20 · FLUXO: de onde vem, por onde passa, o que sai ---------- */
  const SRC = ['LIVRO FISCAL', 'LOTE DE XML', 'IMPORTAÇÃO XML', 'CONF. ENTRADAS', 'ASIS', 'PORTAL COMPRAS', 'PESAGENS', 'AGENDAS · MIC'];
  const OUT = ['LIVRO AUDITADO', 'APURAÇÃO ICMS', 'NFE + CTE', 'PENDENTES', 'PROPOSTAS', 'SERVIÇOS', 'PAINEL', 'DESVIOS'];
  const TOOL_ORDER = [0, 1, 2, 3, 5, 4, 6, 7];            /* índice em R.TOOLS por linha */
  const EDGES = [[0, 0], [0, 1], [1, 2], [2, 3], [3, 3], [4, 5], [5, 5], [6, 7], [7, 7]];
  const INNER = [[0, 1], [3, 6], [5, 6], [4, 3]];         /* entre ferramentas (linha → linha) */
  const rowY = k => 170 + k * 102;
  const bez = (x1, y1, x2, y2, s) => {
    const dx = (x2 - x1) * 0.5, u = 1 - s;
    return [u * u * u * x1 + 3 * u * u * s * (x1 + dx) + 3 * u * s * s * (x2 - dx) + s * s * s * x2,
      u * u * u * y1 + 3 * u * u * s * y1 + 3 * u * s * s * y2 + s * s * s * y2];
  };
  function curve(ctx, x1, y1, x2, y2, f, col, w, a, dash) {
    if (f <= 0) return;
    ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = col; ctx.lineWidth = w;
    if (dash) ctx.setLineDash([6, 8]);
    ctx.beginPath(); ctx.moveTo(x1, y1);
    const n = 40;
    for (let i = 1; i <= Math.ceil(n * f); i++) { const p = bez(x1, y1, x2, y2, Math.min(i / n, f)); ctx.lineTo(p[0], p[1]); }
    ctx.stroke(); ctx.restore();
  }
  R.S4 = function (ctx, t) {
    const T = B(72), END = B(80);
    if (t < T || t > END + 0.05) return;
    const u = t - T;
    const col = E.expoIn(prog(t, B(78.6), END));
    const zoom = 1 + 0.06 * E.sineIO(prog(u, 0, 3.2));
    ctx.save();
    ctx.translate(960, 540); ctx.scale(zoom * (1 - col * 0.98), zoom * (1 - col * 0.2)); ctx.translate(-960, -540);
    const XS = 330, XT = 960, XO = 1590;
    // arestas
    EDGES.forEach(([s, r], k) => {
      const tl = R.TOOLS[TOOL_ORDER[r]], f = E.io(prog(u, 0.7 + k * 0.05, 1.3 + k * 0.05));
      curve(ctx, XS, rowY(s), XT - 34, rowY(r), f, tl.c, 1.6, 0.55);
    });
    OUT.forEach((o, r) => {
      const tl = R.TOOLS[TOOL_ORDER[r]], f = E.io(prog(u, 1.1 + r * 0.05, 1.7 + r * 0.05));
      curve(ctx, XT + 34, rowY(r), XO, rowY(r), f, tl.c, 1.6, 0.55);
    });
    INNER.forEach(([a, b], k) => {
      const f = E.io(prog(u, 1.5 + k * 0.08, 2.0 + k * 0.08));
      if (f <= 0) return;
      ctx.save(); ctx.globalAlpha = 0.7; ctx.strokeStyle = C.ink2; ctx.lineWidth = 1.4; if (k === 3) ctx.setLineDash([5, 7]);
      const x = XT + (k % 2 ? 60 : -60);
      ctx.beginPath(); ctx.moveTo(XT, rowY(a)); ctx.quadraticCurveTo(x, (rowY(a) + rowY(b)) / 2, XT, lerp(rowY(a), rowY(b), f)); ctx.stroke();
      ctx.restore();
    });
    // pacotes em trânsito
    if (u > 1.4) {
      const g = R.rng(77);
      for (let k = 0; k < 90; k++) {
        const lane = Math.floor(g() * 17), sp = 0.45 + g() * 0.5, off = g();
        const s = ((u - 1.4) * sp + off) % 1, a = prog(u, 1.4, 1.8);
        let p, tl;
        if (lane < 9) { const [si, r] = EDGES[lane]; tl = R.TOOLS[TOOL_ORDER[r]]; p = bez(XS, rowY(si), XT - 34, rowY(r), s); }
        else { const r = lane - 9; tl = R.TOOLS[TOOL_ORDER[r]]; p = bez(XT + 34, rowY(r), XO, rowY(r), s); }
        R.disc(ctx, p[0], p[1], 4, tl.c, a);
      }
    }
    // nós
    SRC.forEach((s, k) => {
      const a = prog(u, 0.2 + k * B(0.125), 0.4 + k * B(0.125));
      R.disc(ctx, XS, rowY(k), 6, C.ink2, a);
      R.text(ctx, s, XS - 24, rowY(k) + 6, { font: mono(17), color: C.ink2, align: 'right', ls: 2, alpha: a });
    });
    OUT.forEach((o, k) => {
      const a = prog(u, 1.2 + k * B(0.125), 1.4 + k * B(0.125));
      R.disc(ctx, XO, rowY(k), 6, C.ink2, a);
      R.text(ctx, o, XO + 24, rowY(k) + 6, { font: mono(17), color: C.ink, ls: 2, alpha: a });
    });
    TOOL_ORDER.forEach((ti, k) => {
      const tl = R.TOOLS[ti], p = R.spring(u - (0.1 + k * B(0.25)), 2.4, 0.4);
      R.disc(ctx, XT, rowY(k), 34 * p, tl.c, 1);
      R.disc(ctx, XT, rowY(k), 34 * p * 1.9, tl.c, 0.08);
      R.text(ctx, tl.name.toUpperCase(), XT, rowY(k) + 58, { font: mono(13), color: C.ink3, align: 'center', ls: 2, alpha: prog(u, 0.4 + k * 0.05, 0.6 + k * 0.05) * (1 - col * 4) });
    });
    ctx.restore();
    // título
    const L = R.layout(ctx, 'Nenhuma ferramenta importa outra.', R.font(700, 54), -2);
    R.rise(ctx, L, 960 - L.w / 2, 1010, t, { t0: B(74), size: 54, stagger: 0.012, out: { t0: B(78.2), stagger: 0.006 } });
    R.disc(ctx, 960, 540, 10 + col * 14, C.acc, col);
  };

  /* ---------- compassos 21–22 · NÚMEROS: quatro batidas ---------- */
  const NUMS = [
    [8, 0, '', 'FERRAMENTAS', C.acc],
    [742, 0, '', 'TESTES AUTOMÁTICOS', C.b1],
    [19.5, 1, 'mil', 'LINHAS DE MOTOR', '#8C98EA'],
    [0, 0, '', 'INSTALAÇÕES', C.acc],
  ];
  R.S5 = function (ctx, t) {
    const T = B(80), END = B(88);
    if (t < T - 0.02 || t > END + 0.6) return;
    NUMS.forEach(([v, d, suf, lbl, c], k) => {
      const t0 = T + k * B(2), t1 = t0 + B(2);
      if (t < t0 - 0.02 || t > t1 + (k === 3 ? 0.6 : 0.3)) return;
      const inn = E.quintOut(prog(t, t0, t0 + 0.35)), out = k < 3 ? E.whip(prog(t, t1 - 0.12, t1 + 0.18)) : 0;
      const cnt = k === 3 ? Math.round(lerp(99, 0, E.quartOut(prog(t, t0, t0 + 0.55)))) : v * E.quartOut(prog(t, t0, t0 + 0.6));
      const str = R.fmt(cnt, d);
      const size = 400;
      ctx.save();
      ctx.translate(960, 560 - out * 700 + (1 - inn) * 260);
      const sc = 1.25 - 0.25 * inn;
      ctx.scale(sc, sc);
      ctx.globalAlpha = inn * (1 - out);
      const L = R.layout(ctx, str, R.font(700, size), -18);
      const Ls = suf ? R.layout(ctx, suf, R.font(700, 150), -4) : null;
      const W = L.w + (Ls ? Ls.w + 20 : 0);
      R.text(ctx, str, -W / 2, 120, { font: R.font(700, size), ls: -18 });
      if (Ls) R.text(ctx, suf, -W / 2 + L.w + 20, 120, { font: R.font(700, 150), color: c, ls: -4 });
      const Ll = R.layout(ctx, lbl, mono(30), 12);
      R.text(ctx, lbl, -Ll.w / 2, 210, { font: mono(30), color: c, ls: 12 });
      ctx.restore();
      // anel que pulsa a cada batida
      const rp = prog(t, t0, t0 + 0.9);
      if (rp > 0 && rp < 1) R.ring(ctx, 960, 470, 300 + E.out(rp) * 600, c, 2, (1 - rp) * 0.6);
    });
    // o zero vira o horizonte: um anel que se abre
    const z = E.expoIn(prog(t, B(87.2), B(88)));
    if (z > 0) R.ring(ctx, 960, 470 + z * 2900, 160 + z * 2800, C.acc, 2 + z * 2, 0.9);
  };

  /* ---------- compassos 23–24 · ASSINATURA ---------- */
  R.S6 = function (ctx, t) {
    const T = B(88);
    if (t < T) return;
    // horizonte: o limbo de um planeta, com luz
    const rise = E.out(prog(t, T, T + 1.3)), sink = E.io(prog(t, B(92), B(93.5)));
    const R0 = 3000, cy = 1080 + R0 - 150 * rise + 400 * sink;
    const glow = ctx.createRadialGradient(960, cy - R0, 0, 960, cy - R0, 900);
    glow.addColorStop(0, R.rgba(C.acc, 0.28 * rise * (1 - sink))); glow.addColorStop(1, R.rgba(C.acc, 0));
    ctx.fillStyle = glow; ctx.fillRect(0, 0, 1920, 1080);
    // os três círculos nascem atrás do limbo
    const sun = [0, 1, 2].map(i => R.spring(t - (B(88.6) + i * B(0.33)), 1.1, 0.55));
    const up = E.whip(prog(t, B(92), B(93.4)));
    const lx = 960, ly = lerp(cy - R0 + 60 - 160 * sun[0], 450, up), ls = lerp(128, 150, up);
    ctx.save();
    if (up < 1) { ctx.beginPath(); ctx.rect(0, 0, 1920, 1080); ctx.arc(960, cy, R0, 0, TAU, true); ctx.clip('evenodd'); }
    const pulse = [0, 1, 2].map(i => 1 + 0.12 * R.pulse(t, B(95) + i * B(0.25), 5));
    R.logo(ctx, lx, ly, ls, { pop: sun.map((s, i) => Math.min(1, 0.4 + 0.6 * s) * pulse[i]), spread: lerp(1.05, 1, up) });
    ctx.restore();
    ctx.save(); ctx.beginPath(); ctx.arc(960, cy, R0, 0, TAU);
    ctx.fillStyle = C.bg2; ctx.globalAlpha = 1 - sink; ctx.fill();
    ctx.strokeStyle = C.acc; ctx.lineWidth = 2; ctx.globalAlpha = 0.8 * (1 - sink); ctx.stroke(); ctx.restore();
    // a frase
    const L1 = R.layout(ctx, 'Menos procurar erro.', R.font(700, 112), -5);
    R.rise(ctx, L1, 960 - L1.w / 2, 300, t, { t0: B(89), size: 112, stagger: 0.02, out: { t0: B(91.7), stagger: 0.01 } });
    const L2 = R.layout(ctx, 'Mais analisar número.', R.font(700, 112), -5);
    R.rise(ctx, L2, 960 - L2.w / 2, 430, t, { t0: B(90), size: 112, stagger: 0.02, color: C.acc, out: { t0: B(91.8), stagger: 0.01 } });
    // assinatura
    const Lw = R.layout(ctx, 'Hinove', R.font(700, 140), -5);
    R.rise(ctx, Lw, 960 - Lw.w / 2, 820, t, { t0: B(92.6), size: 140, stagger: 0.04 });
    const Lc = R.layout(ctx, 'CENTRAL FISCAL', mono(26), 16);
    R.rise(ctx, Lc, 960 - Lc.w / 2, 880, t, { t0: B(93.2), size: 28, stagger: 0.02, color: C.acc });
    const orb = E.io(prog(t, B(93), B(94.4)));
    if (orb > 0) {
      ctx.save(); ctx.strokeStyle = C.acc; ctx.lineWidth = 1.5; ctx.globalAlpha = 0.8;
      ctx.beginPath(); ctx.ellipse(960, 450, 232, 232, 0, -Math.PI / 2, -Math.PI / 2 + TAU * orb); ctx.stroke(); ctx.restore();
      const a = -Math.PI / 2 + TAU * orb;
      R.disc(ctx, 960 + Math.cos(a) * 232, 450 + Math.sin(a) * 232, 7, C.acc, 1);
    }
    const Lf = R.layout(ctx, 'OITO FERRAMENTAS · UMA TELA · HINOVE AGROCIÊNCIA S.A.', mono(15), 5);
    R.rise(ctx, Lf, 960 - Lf.w / 2, 960, t, { t0: B(94), size: 16, stagger: 0.004, color: C.ink3 });
  };

  /* ---------- HUD: moldura, relógio, compasso e a trilha das ferramentas ---------- */
  const SECT = t => {
    if (t < B(16)) return '01 · MANIFESTO';
    if (t < B(24)) return '02 · SISTEMA';
    if (t < B(72)) { const i = R.toolAt(t); return '03 · ' + R.TOOLS[i].name.toUpperCase(); }
    if (t < B(80)) return '04 · FLUXO';
    if (t < B(88)) return '05 · NÚMEROS';
    return '06 · ASSINATURA';
  };
  R.HUD = function (ctx, t) {
    const a = prog(t, B(7.6), B(8.4)) * (1 - prog(t, B(91.8), B(92.6)));
    if (a <= 0) return;
    ctx.save(); ctx.globalAlpha = a;
    R.logo(ctx, 118, 84, 13);
    R.text(ctx, 'HINOVE · CENTRAL FISCAL', 150, 91, { font: mono(14), color: C.ink2, ls: 4 });
    const fr = Math.floor(t * 60), s = Math.floor(t), ff = fr % 60;
    const tc = '00:' + String(s).padStart(2, '0') + ':' + String(ff).padStart(2, '0');
    R.text(ctx, tc, 1802, 91, { font: mono(14), color: C.ink2, align: 'right', ls: 3 });
    const bar = Math.floor(t / R.BAR) + 1, beat = Math.floor(t / R.BEAT) % 4;
    R.text(ctx, 'BAR ' + String(bar).padStart(2, '0') + '/24', 1640, 91, { font: mono(14), color: C.ink3, align: 'right', ls: 3 });
    for (let k = 0; k < 4; k++) R.rect(ctx, 1662 + k * 12, 82, 7, 7, k === beat ? C.acc : C.line2, 1);
    R.text(ctx, SECT(t), 118, 1004, { font: mono(14), color: C.ink2, ls: 4 });
    // trilha: oito marcas, uma por ferramenta, acendendo
    for (let k = 0; k < 8; k++) {
      const x = 1478 + k * 42, t0 = R.T0 + k * R.TLEN;
      const on = t >= t0, cur = R.toolAt(t) === k;
      R.rect(ctx, x, 996, 30, cur ? 6 : 3, on ? R.TOOLS[k].c : C.line2, cur ? 1 : on ? 0.7 : 1);
    }
    // cantos da moldura
    R.ticks(ctx, 60, 50, 1800, 980, C.line2, 1, 26);
    ctx.restore();
  };
})();
