/* ==========================================================================
   Compassos 7–18 · FERRAMENTAS — oito capítulos de 6 tempos
   Cada capítulo: disco da cor da ferramenta cobre a tela e se recolhe no
   orbe do nome; à esquerda, nome e três números; à direita, o instrumento
   que reproduz a regra dela. Tudo em função do tempo local u.
   ========================================================================== */
'use strict';
(function () {
  const { C, E, B, clamp, lerp, prog, TAU } = R;
  const PX = 840, PY = 170, PW = 940, PH = 740;          /* painel do instrumento */
  const ORB = [174, 318];                                 /* orbe ao lado do índice */
  const KPI = {
    fiscalbot: [[7, 0, '', 'camadas'], [6, 0, '', 'dimensões'], [3, 0, '', 'veredictos']],
    apurabot: [[99.87, 2, '%', 'equalização'], [7, 0, '', 'filiais · dif. 0,00'], [239, 0, '', 'testes']],
    dixml: [[8, 0, '', 'níveis de .zip'], [44, 0, '', 'dígitos, texto'], [0, 0, '', 'colunas a manter']],
    gerarpendentes: [[5, 0, '', 'portas de saída'], [2, 0, '', 'abas no e-mail'], [370, 0, '', 'testes']],
    gerarservpend: [[4, 0, '', 'passos'], [1, 0, '', 'casamento por lado'], [127, 0, '', 'sem contraparte']],
    conhecimento: [[44, 0, '/44', 'categoria'], [18, 0, '/18', 'operação'], [77, 0, '%', 'guardião']],
    resumoexecutivo: [[141, 0, '', 'notas'], [3, 0, '', 'categorias'], [6, 0, '/6', 'blocos iguais']],
    faturabot: [[4, 0, '', 'relatórios'], [24, 0, '/24', 'autoteste da OC'], [0.5, 2, '%', 'tolerância']],
  };
  const mono = (px, w = 500) => R.font(w, px, R.MONO);

  /* ---------- o quadro comum ---------- */
  function chapter(ctx, i, u) {
    const tl = R.TOOLS[i];
    // índice e subtítulo
    const L0 = R.layout(ctx, 'T·0' + (i + 1), mono(20), 4);
    R.rise(ctx, L0, 210, 327, u, { t0: 0.18, size: 22, stagger: 0.03, color: tl.c });
    const Lq = R.layout(ctx, tl.q.toUpperCase(), mono(20), 5);
    R.rise(ctx, Lq, 300, 327, u, { t0: 0.26, size: 22, stagger: 0.008, color: C.ink3 });
    // nome: grande, reduzido até caber em 640 px
    let size = 150;
    let L = R.layout(ctx, tl.name, R.font(700, size), -6);
    if (L.w > 640) { size = Math.floor(150 * 640 / L.w); L = R.layout(ctx, tl.name, R.font(700, size), -size / 25); }
    const lines = L.w > 640 ? null : [L];
    R.rise(ctx, (lines || [L])[0], 146, 470, u, { t0: 0.24, size, stagger: 0.028, dur: 0.55, ease: E.quintOut });
    // os três números
    let nx = 150;
    KPI[tl.id].forEach((k, j) => {
      const x = nx, y = 690;
      const full = R.layout(ctx, R.fmt(k[0], k[1]), R.font(600, 76), -3).w + (k[2] ? R.layout(ctx, k[2], R.font(600, 34), 0).w + 10 : 0);
      nx += Math.max(222, full + 70);
      const c = E.quartOut(prog(u, 0.55 + j * 0.08, 1.35 + j * 0.08));
      const a = prog(u, 0.5 + j * 0.08, 0.7 + j * 0.08);
      if (a <= 0) return;
      R.line(ctx, x, 590, x, 760, C.line2, 1, a);
      const v = k[0] * c;
      R.text(ctx, R.fmt(v, k[1]), x + 22, y, { font: R.font(600, 76), ls: -3, alpha: a });
      const w = R.layout(ctx, R.fmt(k[0], k[1]), R.font(600, 76), -3).w;
      if (k[2]) R.text(ctx, k[2], x + 26 + w, y, { font: R.font(600, 34), color: tl.c, alpha: a * prog(u, 1.2, 1.4) });
      R.text(ctx, k[3].toUpperCase(), x + 24, y + 44, { font: mono(15), color: C.ink3, ls: 2, alpha: a });
    });
    // painel
    const pa = E.out(prog(u, 0.15, 0.6));
    R.rect(ctx, PX, PY, PW, PH, C.bg2, 0.82 * pa);
    R.frame(ctx, PX, PY, PW, PH, C.line2, pa);
    R.ticks(ctx, PX - 12, PY - 12, PW + 24, PH + 24, tl.c, pa, 22);
    R.text(ctx, '● AO VIVO', PX + PW - 20, PY - 22, { font: mono(14), color: tl.c, align: 'right', ls: 3, alpha: pa * (0.6 + 0.4 * Math.sin(u * 9)) });
    ctx.save();
    ctx.beginPath(); ctx.rect(PX, PY, PW, PH); ctx.clip();
    ctx.translate(PX, PY);
    INST[tl.id](ctx, u, tl);
    ctx.restore();
  }

  /* ---------- T·01 Fiscalbot: sete camadas, três veredictos ---------- */
  const FB = (() => {
    const g = R.rng(11), out = [];
    for (let i = 0; i < 96; i++) {
      const o = g(), res = o < 0.78 ? 'conf' : o < 0.92 ? 'adv' : 'man';
      out.push({ s: 0.55 + i * 0.0205 + g() * 0.05, x: 390 + g() * 190, v: 520 + g() * 180, res,
        cancel: res === 'conf' && g() < 0.09, advAt: g() < 0.6 ? 4 : 5 });
    }
    return out;
  })();
  const FB_L = ['CANCELADA', 'FRETE SIMPLES NAC.', 'CAVACO', 'IDENTIFICAÇÃO', 'SEIS DIMENSÕES', 'CAMADA 0', 'CAMADA IND'];
  const FB_BIN = [['CONFORME', C.acc, 40], ['ADVERTÊNCIA', C.warn, 330], ['VALID. MANUAL', C.manual, 620]];
  function fbPos(p, u) {
    const y0 = 40, bottom = 40 + 6 * 68 + 58, by = 640;
    const exitY = p.cancel ? y0 + 34 : bottom;
    const te = p.s + (exitY + 10) / p.v;
    if (u < te) return { x: p.x, y: -10 + (u - p.s) * p.v, landed: false };
    const bin = FB_BIN[p.res === 'conf' ? 0 : p.res === 'adv' ? 1 : 2];
    const f = E.io(prog(u, te, te + 0.32));
    return { x: lerp(p.x, bin[2] + 140 + (p.x - 480) * 0.3, f), y: lerp(exitY, by, f), landed: f >= 1 };
  }
  function fiscal(ctx, u, tl) {
    const lit = new Array(7).fill(0);
    const pos = FB.map(p => (u >= p.s ? fbPos(p, u) : null));
    pos.forEach((q, k) => {
      if (!q || q.landed || q.y > 506) return;
      const li = Math.floor((q.y - 40) / 68);
      if (li >= 0 && li < 7) lit[li] = 1;
    });
    FB_L.forEach((l, i) => {
      const y = 40 + i * 68, w = 860 * E.out(prog(u, 0.25 + i * 0.05, 0.7 + i * 0.05));
      R.rect(ctx, 40, y, w, 58, lit[i] ? R.rgba(tl.c, 0.16) : 'rgba(255,255,255,.03)', 1);
      R.frame(ctx, 40, y, w, 58, C.line2, w > 0 ? 1 : 0);
      R.text(ctx, (i + 1) + ' · ' + l, 62, y + 36, { font: mono(17), color: lit[i] ? C.ink : C.ink3, ls: 3, alpha: prog(u, 0.4 + i * 0.05, 0.6 + i * 0.05) });
    });
    const cnt = [0, 0, 0];
    FB.forEach((p, k) => {
      const q = pos[k];
      if (!q) return;
      if (q.landed) { cnt[p.res === 'conf' ? 0 : p.res === 'adv' ? 1 : 2]++; return; }
      let c = C.ink2;
      if (p.res === 'man' && q.y > 40 + 3 * 68) c = C.manual;
      if (p.res === 'adv' && q.y > 40 + p.advAt * 68) c = C.warn;
      if (p.res === 'conf' && (q.y > 506 || p.cancel && q.y > 60)) c = C.acc;
      R.disc(ctx, q.x, q.y, 5, c, 1);
    });
    FB_BIN.forEach(([n, c, x], j) => {
      const a = prog(u, 0.5 + j * 0.06, 0.8 + j * 0.06);
      R.rect(ctx, x, 560, 280, 150, 'rgba(255,255,255,.03)', a);
      R.rect(ctx, x, 560, 280, 4, c, a);
      R.text(ctx, n, x + 20, 596, { font: mono(16), color: C.ink2, ls: 3, alpha: a });
      R.text(ctx, String(cnt[j]), x + 20, 684, { font: R.font(600, 64), color: C.ink, ls: -2, alpha: a });
    });
  }

  /* ---------- T·02 Apurabot: a carga bruta se encaixa na nominal ---------- */
  const AP_N = [4, 7, 12, 17, 18, 20.5];
  const AP = (() => {
    const g = R.rng(22), out = [];
    const W = [[4, 40], [7, 10], [12, 20], [17, 8], [18, 14], [20.5, 8]];
    for (let i = 0; i < 230; i++) {
      let r = g() * 100, n = 4;
      for (const [k, w] of W) { if ((r -= w) <= 0) { n = k; break; } }
      out.push({ n, raw: n * (0.84 + g() * 0.145), x: 70 + g() * 740, sp: false });
    }
    for (let i = 0; i < 3; i++) out.push({ n: 4, raw: 7 * (0.95 + g() * 0.035), x: 200 + g() * 480, sp: true });
    return out;
  })();
  function apura(ctx, u, tl) {
    const yOf = c => 560 - c * 23;
    AP_N.forEach((n, i) => {
      const a = prog(u, 0.3 + i * 0.04, 0.5 + i * 0.04), snapped = u > 1.3;
      ctx.save(); ctx.setLineDash([4, 8]);
      R.line(ctx, 60, yOf(n), 840, yOf(n), snapped ? tl.c : C.line2, 1.2, a);
      ctx.restore();
      R.text(ctx, R.fmt(n, n % 1 ? 1 : 0) + '%', 856, yOf(n) + 6, { font: mono(16), color: snapped ? C.ink : C.ink3, alpha: a });
    });
    const sw = prog(u, 1.15, 1.6);
    if (sw > 0 && sw < 1) R.line(ctx, lerp(60, 840, sw), 50, lerp(60, 840, sw), 580, tl.c, 2, 0.9);
    AP.forEach(p => {
      const xn = (p.x - 60) / 780;
      const a = prog(u, 0.25 + xn * 0.3, 0.45 + xn * 0.3);
      const k = E.snap(prog(u, 1.15 + xn * 0.45, 1.15 + xn * 0.45 + 0.28));
      const y = lerp(yOf(p.raw), yOf(p.n), k);
      R.disc(ctx, p.x, y, p.sp ? 7 : 4, p.sp ? C.warn : k > 0.9 ? tl.c : C.ink3, a);
    });
    const c = E.quartOut(prog(u, 1.2, 1.9));
    R.text(ctx, R.fmt(99.87 * c, 2) + '%', 60, 680, { font: R.font(700, 76), ls: -3, alpha: prog(u, 1.1, 1.3) });
    R.text(ctx, '2.333 / 2.336 LINHAS', 64, 716, { font: mono(15), color: C.ink3, ls: 3, alpha: prog(u, 1.2, 1.4) });
    ['SP', 'SP', 'SP', 'MT', 'PR', 'MS', 'MS'].forEach((uf, j) => {
      const x = 470 + j * 62, on = u > 1.75 + j * B(0.25) * 0.8, a = prog(u, 1.4, 1.6);
      R.ring(ctx, x, 660, 18, on ? C.acc : C.line2, 2, a);
      if (on) R.disc(ctx, x, 660, 10 * R.spring(u - (1.75 + j * B(0.25) * 0.8), 3, 0.4), C.acc, a);
      R.text(ctx, uf, x, 712, { font: mono(14), color: on ? C.ink : C.ink3, align: 'center', alpha: a });
    });
    R.text(ctx, 'DIFERENÇA 0,00', 900, 632, { font: mono(14), color: C.acc, align: 'right', ls: 3, alpha: prog(u, 2.5, 2.7) });
  }

  /* ---------- T·03 DiXML: oito pacotes, um dentro do outro ---------- */
  const KEY = '3526 0712 3456 7800 0190 5500 1000 0123 4510 0001 2345';
  const CF = ['5101', '6101', '1101', '2102', '5905', '6118'];
  function dixml(ctx, u, tl) {
    const z = E.io(prog(u, 0.2, 1.35)) * 8.2;
    const cx = lerp(470, 150, E.io(prog(u, 1.3, 1.7))), cy = 340;
    for (let i = 7; i >= 0; i--) {
      const s = 560 * Math.pow(1.42, z - i) * (1 - E.io(prog(u, 1.3, 1.7)) * 0.9);
      if (s > 2200) continue;
      const a = clamp(1 - (s - 700) / 900) * prog(u, 0.1 + (7 - i) * 0.02, 0.3 + (7 - i) * 0.02);
      ctx.save(); ctx.globalAlpha = a;
      ctx.strokeStyle = z - i > 0.2 ? R.rgba(tl.c, 0.4) : tl.c; ctx.lineWidth = 1.5;
      if (z - i > 0.2) ctx.setLineDash([4, 6]);
      ctx.strokeRect(cx - s / 2, cy - s / 2, s, s);
      ctx.restore();
    }
    const lvl = Math.min(8, Math.floor(z));
    R.text(ctx, 'NÍVEL ' + lvl + ' / 8', 30, 44, { font: mono(18), color: tl.c, ls: 4, alpha: prog(u, 0.2, 0.3) * (1 - prog(u, 1.3, 1.5)) });
    // o arquivo que estava no fundo
    const fa = prog(u, 1.2, 1.4);
    if (fa > 0) {
      ctx.save(); ctx.globalAlpha = fa; ctx.translate(cx, cy);
      ctx.fillStyle = C.bg3; ctx.strokeStyle = tl.c; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.moveTo(-34, -44); ctx.lineTo(14, -44); ctx.lineTo(34, -24); ctx.lineTo(34, 44); ctx.lineTo(-34, 44); ctx.closePath(); ctx.fill(); ctx.stroke();
      ctx.restore();
      R.text(ctx, 'XML', cx, cy + 8, { font: mono(18), color: tl.c, align: 'center', alpha: fa });
    }
    // a planilha: uma linha por item, uma a cada semicolcheia
    const X = [330, 560, 650, 760];
    ['CHAVE', 'ITEM', 'CFOP', 'VPROD'].forEach((h, j) => R.text(ctx, h, X[j], 70, { font: mono(15), color: C.ink3, ls: 3, alpha: prog(u, 1.4, 1.6) }));
    R.line(ctx, 320, 84, 910, 84, C.line2, 1, prog(u, 1.4, 1.6));
    const g = R.rng(33);
    for (let j = 0; j < 12; j++) {
      const t0 = 1.45 + j * B(0.25) * 0.8, f = E.quintOut(prog(u, t0, t0 + 0.25));
      const vp = R.fmt(800 + g() * 47000, 2);
      if (f <= 0) continue;
      const y = 120 + j * 36;
      // partícula voando do arquivo até a linha
      const fl = prog(u, t0 - 0.2, t0);
      if (fl > 0 && fl < 1) R.disc(ctx, lerp(cx + 40, 330, E.io(fl)), lerp(cy, y - 6, E.io(fl)) - Math.sin(fl * Math.PI) * 40, 5, tl.c, 1);
      ctx.save(); ctx.translate((1 - f) * 60, 0); ctx.globalAlpha = f;
      R.rect(ctx, 320, y - 24, 590, 32, j % 2 ? 'rgba(255,255,255,.025)' : 'rgba(255,255,255,.05)', 1);
      R.text(ctx, '3526…' + (1240 + (j / 3 | 0)), X[0], y, { font: mono(17), color: C.ink2 });
      R.text(ctx, String(j % 3 + 1), X[1], y, { font: mono(17), color: C.ink2 });
      R.text(ctx, CF[j % CF.length], X[2], y, { font: mono(17), color: C.ink });
      R.text(ctx, vp, X[3], y, { font: mono(17), color: C.ink });
      ctx.restore();
    }
    // a chave: notação científica riscada, texto de 44 dígitos
    const ka = prog(u, 1.5, 1.7);
    R.line(ctx, 30, 600, 910, 600, C.line2, 1, ka);
    R.text(ctx, 'EXCEL', 30, 650, { font: mono(15), color: C.ink3, ls: 3, alpha: ka });
    R.text(ctx, '3,52604E+43', 160, 652, { font: mono(26), color: C.bad, alpha: ka });
    const st = E.snap(prog(u, 1.65, 1.85));
    R.rect(ctx, 156, 642, 190 * st, 3, C.bad, ka);
    R.text(ctx, 'DIXML', 30, 700, { font: mono(15), color: C.ink3, ls: 3, alpha: ka });
    const n = Math.floor(clamp((u - 1.8) / 0.85) * KEY.length);
    R.text(ctx, KEY.slice(0, n) + (n < KEY.length && n > 0 ? '▍' : ''), 160, 702, { font: mono(24), color: C.acc, alpha: ka });
  }

  /* ---------- T·04 GerarPendentes: a esteira de portas ---------- */
  const GP_G = [['DESCARTE', 110, 6, C.ink3], ['CT-E', 245, 13, '#8C98EA'], ['MANIFEST.', 380, 8, C.manual], ['3OS', 515, 10, C.b1], ['LANÇADOS', 650, 44, C.acc], ['PENDENTES', 820, 19, null]];
  const GP = (() => {
    const g = R.rng(44), ps = [], tot = GP_G.reduce((a, x) => a + x[2], 0);
    for (let i = 0; i < 140; i++) {
      let r = g() * tot, d = 0;
      for (let k = 0; k < GP_G.length; k++) { if ((r -= GP_G[k][2]) <= 0) { d = k; break; } }
      const s = 0.35 + i * 0.0145, tg = s + (GP_G[d][1] - 30) / 640;
      const fr = g();
      ps.push({ s, d, tg, farol: fr < 0.4 ? C.acc : fr < 0.75 ? C.warn : C.bad });
    }
    const cnt = GP_G.map(() => 0);
    ps.slice().sort((a, b) => a.tg - b.tg).forEach(p => { p.k = cnt[p.d]++; });
    ps.forEach(p => {
      const cols = p.d === 5 ? 8 : 6, bw = p.d === 5 ? 130 : 96;
      p.col = p.k % cols; p.row = Math.floor(p.k / cols);
      p.fx = GP_G[p.d][1] - bw / 2 + 10 + p.col * ((bw - 20) / (cols - 1));
      p.fy = 596 - p.row * 15;
      p.fall = Math.sqrt(2 * (p.fy - 150) / 3400);
    });
    return ps;
  })();
  function pend(ctx, u, tl) {
    const ba = prog(u, 0.2, 0.4);
    R.rect(ctx, 30, 140, 880, 20, 'rgba(255,255,255,.04)', ba);
    ctx.save(); ctx.globalAlpha = ba; ctx.setLineDash([3, 13]); ctx.lineDashOffset = -u * 180;
    ctx.strokeStyle = C.line2; ctx.lineWidth = 8; ctx.beginPath(); ctx.moveTo(30, 150); ctx.lineTo(910, 150); ctx.stroke(); ctx.restore();
    R.text(ctx, 'XML EMITIDO →', 30, 110, { font: mono(15), color: C.ink3, ls: 3, alpha: ba });
    const cnt = GP_G.map(() => 0);
    GP_G.forEach(([n, x, , c], k) => {
      const a = prog(u, 0.3 + k * 0.05, 0.5 + k * 0.05), bw = k === 5 ? 130 : 96;
      R.line(ctx, x, 128, x, 172, k === 5 ? tl.c : C.ink3, 2, a);
      R.text(ctx, k === 5 ? '→' : String(k), x, 118, { font: mono(15), color: C.ink3, align: 'center', alpha: a });
      R.rect(ctx, x - bw / 2, 250, bw, 360, 'rgba(255,255,255,.025)', a);
      R.frame(ctx, x - bw / 2, 250, bw, 360, k === 5 ? R.rgba(tl.c, 0.6) : C.line2, a);
      R.text(ctx, n, x, 648, { font: mono(14), color: k === 5 ? tl.c : C.ink3, align: 'center', ls: 1, alpha: a });
    });
    GP.forEach(p => {
      if (u < p.s) return;
      const color = p.d === 5 ? p.farol : GP_G[p.d][3];
      if (u < p.tg) { R.disc(ctx, 30 + (u - p.s) * 640, 150, 5, C.ink2, 1); return; }
      const f = u - p.tg;
      if (f < p.fall) {
        const y = 150 + 0.5 * 3400 * f * f;
        R.disc(ctx, lerp(GP_G[p.d][1], p.fx, f / p.fall), y, 5, color, 1);
        return;
      }
      cnt[p.d]++;
      R.disc(ctx, p.fx, p.fy, 5, color, 0.95);
    });
    GP_G.forEach(([, x], k) => R.text(ctx, String(cnt[k]), x, 232, { font: R.font(600, 30), align: 'center', color: k === 5 ? tl.c : C.ink, alpha: prog(u, 0.4, 0.6) }));
    const so = prog(u, 2.2, 2.4);
    R.text(ctx, 'O QUE SOBRA É A COBRANÇA', 910, 700, { font: mono(16), color: tl.c, align: 'right', ls: 3, alpha: so });
  }

  /* ---------- T·05 GerarServPend: quatro peneiras ---------- */
  const SV_ST = [['1 · NOTA + CNPJ', C.acc, false], ['2 · RPS + CNPJ', C.acc, false], ['3 · CNPJ + VALOR', C.b1, false], ['4 · NOTA + VALOR', C.warn, true]];
  const SV = (() => {
    const g = R.rng(55), sh = n => { const a = [...Array(n).keys()]; for (let i = n - 1; i > 0; i--) { const j = Math.floor(g() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
    const L = sh(12), Rr = sh(12), M = []; let k = 0;
    [5, 2, 2, 1].forEach((c, s) => { for (let j = 0; j < c; j++, k++) M.push({ l: L[k], r: Rr[k], s, j }); });
    return { M, uL: L.slice(k), uR: Rr.slice(k) };
  })();
  function serv(ctx, u, tl) {
    const LX = 230, RX = 710, Y = i => 110 + i * 40;
    const ha = prog(u, 0.2, 0.4);
    R.text(ctx, 'ASIS', LX, 60, { font: mono(18), color: C.ink2, align: 'center', ls: 4, alpha: ha });
    R.text(ctx, 'SANKHYA', RX, 60, { font: mono(18), color: C.ink2, align: 'center', ls: 4, alpha: ha });
    const W = [0.45, 0.92, 1.39, 1.86];
    const colL = new Array(12).fill(C.ink3), colR = new Array(12).fill(C.ink3);
    SV.M.forEach(m => {
      const t0 = W[m.s] + m.j * 0.05, f = E.snap(prog(u, t0, t0 + 0.28));
      if (f <= 0) return;
      const st = SV_ST[m.s];
      ctx.save();
      if (st[2]) ctx.setLineDash([8, 7]);
      R.line(ctx, LX, Y(m.l), lerp(LX, RX, f), lerp(Y(m.l), Y(m.r), f), st[1], m.s < 2 ? 2.4 : 1.8, 0.95);
      ctx.restore();
      if (f >= 1) { colL[m.l] = st[1]; colR[m.r] = st[1]; }
      if (m.s === 3 && f >= 1) R.text(ctx, 'REVISÃO', LX - 30, Y(m.l) + 6, { font: mono(15), color: C.warn, align: 'right', ls: 2 });
    });
    const end = u > 2.3;
    SV.uL.forEach(l => { if (end) { colL[l] = C.bad; R.text(ctx, 'PENDENTE', LX - 30, Y(l) + 6, { font: mono(15), color: C.bad, align: 'right', ls: 2, alpha: prog(u, 2.3, 2.4) }); } });
    SV.uR.forEach(r => { if (end) { colR[r] = C.b1; R.text(ctx, 'SEM CORRESP.', RX + 30, Y(r) + 6, { font: mono(15), color: C.b1, ls: 2, alpha: prog(u, 2.3, 2.4) }); } });
    for (let i = 0; i < 12; i++) {
      const a = prog(u, 0.15 + i * 0.015, 0.3 + i * 0.015);
      const pl = end && SV.uL.includes(i) ? R.pulse(u % 0.47, 0, 6) * 5 : 0;
      R.disc(ctx, LX, Y(i), 9 + pl, colL[i], a);
      R.disc(ctx, RX, Y(i), 9, colR[i], a);
    }
    SV_ST.forEach(([n, c], k) => {
      const x = 30 + k * 222, on = u > W[k] && u < (W[k + 1] || 2.3), a = prog(u, 0.3, 0.5);
      R.rect(ctx, x, 630, 210, 70, on ? R.rgba(c, 0.18) : 'rgba(255,255,255,.03)', a);
      R.rect(ctx, x, 630, 210, 3, c, a);
      R.text(ctx, n, x + 16, 673, { font: mono(15), color: on ? C.ink : C.ink3, ls: 2, alpha: a });
    });
  }

  /* ---------- T·06 Base de conhecimento: medidores e a célula âmbar ---------- */
  const BK_G = [[1, '100%', '44 DE 44', 'CATEGORIA · FIRME', null], [0.77, '77%', '40 DE 52', 'GUARDIÃO · SUGESTÃO', C.warn], [1, '100%', '18 DE 18', 'OPERAÇÃO · FIRME', null]];
  const BK_R = [
    ['NF 18.204', ['Diretos', 'amb'], ['Suprimentos', 'sug'], ['Compra p/ Industrialização', 'amb']],
    ['NF 18.211', ['Indiretos', 'hum'], ['Manutenção', 'hum'], ['Compra Uso e Consumo', 'amb']],
    ['NF 18.230', ['Diretos', 'amb'], ['Faturamento', 'sug'], ['', '']],
    ['NF 18.245', ['Indiretos', 'amb'], ['', ''], ['Compra Uso e Consumo', 'amb']],
    ['NF 18.262', ['Diretos', 'hum'], ['Logística', 'sug'], ['Remessa p/ Armazém', 'hum']],
  ];
  function base(ctx, u, tl) {
    BK_G.forEach(([p, v, s, k, c], j) => {
      const x = 160 + j * 310, y = 190, a = prog(u, 0.2 + j * 0.06, 0.4 + j * 0.06);
      const f = E.quartOut(prog(u, 0.35 + j * 0.1, 1.35 + j * 0.1));
      R.ring(ctx, x, y, 110, C.line2, 14, a);
      ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = c || tl.c; ctx.lineWidth = 14;
      ctx.beginPath(); ctx.arc(x, y, 110, -Math.PI / 2, -Math.PI / 2 + TAU * p * f); ctx.stroke(); ctx.restore();
      R.text(ctx, Math.round(p * 100 * f) + '%', x, y + 14, { font: R.font(600, 46), align: 'center', ls: -2, alpha: a });
      R.text(ctx, s, x, y + 46, { font: mono(14), color: C.ink3, align: 'center', ls: 2, alpha: a });
      R.text(ctx, k, x, y + 150, { font: mono(15), color: C.ink2, align: 'center', ls: 2, alpha: a });
    });
    const X = [30, 200, 410, 620, 910], y0 = 400, rh = 56;
    const ha = prog(u, 0.9, 1.1);
    ['NOTA', 'CATEGORIA', 'GUARDIÃO', 'TIPO DE OPERAÇÃO'].forEach((h, j) => R.text(ctx, h, X[j] + 14, y0 + 30, { font: mono(14), color: C.ink3, ls: 2, alpha: ha }));
    R.rect(ctx, 30, y0, 880, 44, 'rgba(255,255,255,.04)', ha);
    let n = 0;
    BK_R.forEach((r, i) => {
      const y = y0 + 44 + i * rh;
      R.line(ctx, 30, y + rh, 910, y + rh, C.line2, 1, ha);
      R.text(ctx, r[0], X[0] + 14, y + 36, { font: mono(16), color: C.ink3, alpha: ha });
      r.slice(1).forEach(([v, k], j) => {
        const x = X[j + 1], w = X[j + 2] - x;
        R.line(ctx, x, y, x, y + rh, C.line2, 1, ha);
        if (k === 'hum') { R.text(ctx, v, x + 14, y + 36, { font: R.font(500, 20), color: C.ink2, alpha: ha }); return; }
        if (!k) return;
        const t0 = 1.15 + (n++) * B(0.25) * 0.85, f = prog(u, t0, t0 + 0.08);
        if (f <= 0) return;
        R.rect(ctx, x + 2, y + 2, w - 4, rh - 4, k === 'amb' ? 'rgba(242,195,91,.3)' : 'rgba(242,195,91,.12)', f);
        if (k === 'sug') { ctx.save(); ctx.setLineDash([5, 4]); R.frame(ctx, x + 5, y + 5, w - 11, rh - 11, '#F2C35B', f); ctx.restore(); }
        const ch = Math.floor(clamp((u - t0) / 0.3) * v.length);
        ctx.save(); ctx.beginPath(); ctx.rect(x, y, w, rh); ctx.clip();
        R.text(ctx, v.slice(0, ch), x + 14, y + 36, { font: R.font(500, 20), color: C.ink });
        ctx.restore();
      });
    });
  }

  /* ---------- T·07 Resumo Executivo: o painel se monta e se confere ---------- */
  function resumo(ctx, u, tl) {
    const cx = 230, cy = 290, r = 170, A = 67 / 141;
    R.ring(ctx, cx, cy, r, C.line2, 46, prog(u, 0.2, 0.4));
    const k1 = E.io(prog(u, 0.3, 1.0)), k2 = E.io(prog(u, 0.8, 1.4));
    ctx.save(); ctx.lineWidth = 46;
    ctx.strokeStyle = '#E3B04B'; ctx.beginPath(); ctx.arc(cx, cy, r, -Math.PI / 2, -Math.PI / 2 + TAU * A * k1); ctx.stroke();
    ctx.strokeStyle = '#E0795E'; ctx.beginPath(); ctx.arc(cx, cy, r, -Math.PI / 2 + TAU * A + 0.02, -Math.PI / 2 + TAU * A + 0.02 + (TAU * (1 - A) - 0.04) * k2); ctx.stroke();
    ctx.restore();
    R.text(ctx, String(Math.round(141 * E.quartOut(prog(u, 0.3, 1.4)))), cx, cy + 20, { font: R.font(700, 72), align: 'center', ls: -3, alpha: prog(u, 0.3, 0.5) });
    R.text(ctx, 'NOTAS', cx, cy + 56, { font: mono(15), color: C.ink3, align: 'center', ls: 4, alpha: prog(u, 0.3, 0.5) });
    [['MERCADORIA 67', '#E3B04B'], ['SERVIÇO 74', '#E0795E']].forEach(([n, c], j) => {
      const a = prog(u, 1.0 + j * 0.1, 1.2 + j * 0.1);
      R.rect(ctx, 70 + j * 230, 520, 14, 14, c, a);
      R.text(ctx, n, 94 + j * 230, 533, { font: mono(15), color: C.ink2, ls: 2, alpha: a });
    });
    const H = [[180, 70, 90], [110, 120, 60], [250, 50, 130], [70, 90, 80]], SER = ['#E3B04B', '#8FAFCB', '#E0795E'];
    H.forEach((hs, j) => {
      let acc = 0; const x = 520 + j * 96;
      hs.forEach((h, s) => {
        const f = E.out(prog(u, 0.6 + j * 0.08 + s * 0.12, 1.2 + j * 0.08 + s * 0.12)), hh = h * f;
        R.rect(ctx, x, 520 - acc - hh, 62, hh, SER[s], 0.85);
        acc += hh;
      });
      R.text(ctx, 'U' + (j + 1), x + 31, 556, { font: mono(14), color: C.ink3, align: 'center', alpha: prog(u, 0.6, 0.8) });
    });
    R.line(ctx, 505, 520, 905, 520, C.line2, 1, prog(u, 0.5, 0.7));
    const CK = ['TABELA POR CATEGORIA', 'TOTAL DAS TRÊS', 'TOP 5 · TEMPO', 'TOP 5 · VALOR', 'VALOR POR UNIDADE', 'POR GUARDIÃO'];
    CK.forEach((n, j) => {
      const x = 30 + (j % 3) * 295, y = 620 + Math.floor(j / 3) * 56, t0 = 1.5 + j * B(0.25) * 0.8, on = u > t0;
      R.ring(ctx, x + 12, y, 11, on ? C.acc : C.line2, 2, prog(u, 1.3, 1.5));
      if (on) R.disc(ctx, x + 12, y, 6 * R.spring(u - t0, 3, 0.4), C.acc, 1);
      R.text(ctx, n, x + 34, y + 6, { font: mono(14), color: on ? C.ink : C.ink3, ls: 1, alpha: prog(u, 1.3, 1.5) });
    });
  }

  /* ---------- T·08 Faturabot: o caminhão, a balança e a nota ---------- */
  const OBS = 'CARREG. LIBERADO — ORDEM DE CARREGAMENTO: 71.145 / MOTORISTA CIENTE';
  function fatura(ctx, u, tl) {
    const GY = 470;
    R.line(ctx, 0, GY, PW, GY, C.line2, 1, 1);
    R.rect(ctx, 180, GY, 480, 26, C.bg3, 1);
    for (let i = 0; i < 26; i++) R.line(ctx, 186 + i * 18, GY + 26, 198 + i * 18, GY + 6, C.line2, 1, 1);
    const on = u > 0.85;
    R.rect(ctx, 180, on ? GY - 7 : GY - 10, 480, 10, C.line2, 1);
    // caminhão
    const x = lerp(-520, 205, E.out(prog(u, 0, 0.95))), yb = GY - (on ? 7 : 10);
    ctx.save(); ctx.translate(x, on ? 2 : 0);
    const S = 1.95;
    ctx.fillStyle = C.bg3; ctx.strokeStyle = C.ink3; ctx.lineWidth = 2;
    ctx.fillRect(0, yb - 66 * S, 166 * S, 52 * S); ctx.strokeRect(0, yb - 66 * S, 166 * S, 52 * S);
    R.rect(ctx, 0, yb - 18 * S, 166 * S, 4 * S, tl.c, 1);
    [['#8FAFCB', 10], ['#343F73', 62], ['#2A9165', 114]].forEach(([c, bx]) => {
      ctx.fillStyle = c; ctx.beginPath(); ctx.roundRect(bx * S, yb - 62 * S, 44 * S, 40 * S, 8); ctx.fill();
    });
    ctx.fillStyle = C.bg3; ctx.beginPath();
    ctx.moveTo(172 * S, yb - 14 * S); ctx.lineTo(172 * S, yb - 52 * S); ctx.lineTo(204 * S, yb - 52 * S); ctx.lineTo(222 * S, yb - 34 * S); ctx.lineTo(222 * S, yb - 14 * S); ctx.closePath(); ctx.fill(); ctx.stroke();
    ctx.fillStyle = R.rgba(tl.c, 0.4); ctx.beginPath();
    ctx.moveTo(178 * S, yb - 46 * S); ctx.lineTo(202 * S, yb - 46 * S); ctx.lineTo(214 * S, yb - 34 * S); ctx.lineTo(178 * S, yb - 34 * S); ctx.closePath(); ctx.fill();
    [26, 56, 138, 196].forEach(wx => {
      ctx.save(); ctx.translate(wx * S, yb - 6 * S);
      ctx.fillStyle = C.bg; ctx.strokeStyle = C.ink2; ctx.lineWidth = 3;
      ctx.beginPath(); ctx.arc(0, 0, 10 * S, 0, TAU); ctx.fill(); ctx.stroke();
      ctx.rotate(x * 0.05);
      ctx.strokeStyle = C.ink3; ctx.beginPath(); ctx.moveTo(-6 * S, 0); ctx.lineTo(6 * S, 0); ctx.moveTo(0, -6 * S); ctx.lineTo(0, 6 * S); ctx.stroke();
      ctx.restore();
    });
    ctx.restore();
    // mostrador
    const da = prog(u, 0.3, 0.5), DX = 560, DY = 30;
    R.rect(ctx, DX, DY, 350, 230, C.bg, da);
    R.frame(ctx, DX, DY, 350, 230, C.line2, da);
    R.text(ctx, 'PLACA SFE-5B10 · COLETA', DX + 20, DY + 32, { font: mono(14), color: C.ink3, ls: 2, alpha: da });
    const F = 34540, Hn = 34620, Lv = (Hn / F - 1) * 100;
    const fF = E.quartOut(prog(u, 0.9, 1.35)), fH = E.quartOut(prog(u, 1.2, 1.6));
    [['BALANÇA', u > 0.9 ? R.fmt(Math.round(F * fF)) + ' kg' : '—'], ['NOTA', u > 1.2 ? R.fmt(Math.round(Hn * fH)) + ' kg' : '—'], ['DESVIO', u > 1.62 ? '+' + R.fmt(Lv, 2) + '%' : '—']].forEach(([k, v], j) => {
      const y = DY + 80 + j * 44;
      R.text(ctx, k, DX + 20, y, { font: mono(14), color: C.ink3, ls: 2, alpha: da });
      R.text(ctx, v, DX + 330, y + 2, { font: R.font(600, 30), align: 'right', color: j === 2 && u > 1.62 ? C.acc : C.ink, alpha: da });
      R.line(ctx, DX + 20, y + 14, DX + 330, y + 14, C.line, 1, da);
    });
    const stp = R.spring(u - B(4), 2.6, 0.45);
    if (u > B(4)) {
      ctx.save(); ctx.translate(DX + 175, DY + 205); ctx.scale(1.6 - 0.6 * stp, 1.6 - 0.6 * stp); ctx.rotate(-0.04 * (1 - stp));
      R.rect(ctx, -155, -18, 310, 36, C.acc, 0.25 + 0.2 * R.pulse(u, B(4), 5));
      R.frame(ctx, -155, -18, 310, 36, C.acc, 1);
      R.text(ctx, 'CONFORME', 0, 8, { font: mono(18), color: C.acc, align: 'center', ls: 6 });
      ctx.restore();
    }
    // régua de tolerância
    const gx = v => lerp(40, 500, (clamp(v, -3, 3) + 3) / 6), GYy = 110, ga = prog(u, 0.4, 0.6);
    R.rect(ctx, gx(-0.5), GYy - 16, gx(0.5) - gx(-0.5), 32, C.acc, 0.2 * ga);
    R.line(ctx, 40, GYy, 500, GYy, C.line2, 1, ga);
    [-3, -2, -1, 0, 1, 2, 3].forEach(v => {
      R.line(ctx, gx(v), GYy - (v ? 7 : 12), gx(v), GYy + (v ? 7 : 12), C.ink3, 1, ga);
      R.text(ctx, (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v) + '%', gx(v), GYy + 36, { font: mono(13), color: C.ink3, align: 'center', alpha: ga });
    });
    R.text(ctx, '±0,50%', gx(0), GYy - 26, { font: mono(14), color: C.acc, align: 'center', alpha: ga });
    const nx = lerp(gx(0) - 60, gx(Lv), R.spring(u - 1.62, 2.2, 0.35));
    if (u > 1.62) {
      ctx.save(); ctx.fillStyle = C.ink; ctx.beginPath(); ctx.moveTo(nx, GYy - 4); ctx.lineTo(nx - 9, GYy - 20); ctx.lineTo(nx + 9, GYy - 20); ctx.closePath(); ctx.fill(); ctx.restore();
    }
    // a OC lida da observação
    const oa = prog(u, 0.5, 0.7);
    R.line(ctx, 30, 560, 910, 560, C.line2, 1, oa);
    R.text(ctx, 'OBSERVAÇÃO → OC', 30, 596, { font: mono(14), color: C.ink3, ls: 3, alpha: oa });
    const f17 = mono(19), La = R.layout(ctx, OBS, f17, 0);
    const i0 = OBS.indexOf('ORDEM DE CARREGAMENTO'), i1 = i0 + 21, d0 = OBS.indexOf('71.145'), d1 = d0 + 6;
    const hlA = E.out(prog(u, 1.0, 1.2)), hlD = E.out(prog(u, 1.3, 1.45));
    const xa0 = 30 + La.xs[i0], xa1 = 30 + La.xs[i1], xd0 = 30 + La.xs[d0], xd1 = 30 + (La.xs[d1] || La.w);
    R.rect(ctx, xa0 - 3, 616, (xa1 - xa0 + 6) * hlA, 32, R.rgba(tl.c, 0.35), oa);
    R.rect(ctx, xd0 - 3, 616, (xd1 - xd0 + 6) * hlD, 32, C.acc, oa);
    R.text(ctx, OBS, 30, 640, { font: f17, color: C.ink2, alpha: oa });
    if (hlD > 0.5) R.text(ctx, '71.145', xd0, 640, { font: f17, color: C.bg, alpha: oa });
    const ra = prog(u, 1.6, 1.75);
    R.frame(ctx, 30, 672, 150, 40, C.ink2, ra);
    R.text(ctx, 'OC 71145', 105, 699, { font: mono(18), color: C.ink, align: 'center', alpha: ra });
    R.text(ctx, 'ANCORA_OC · CONFIANÇA ALTA', 200, 699, { font: mono(15), color: C.ink3, ls: 2, alpha: ra });
  }

  const INST = { fiscalbot: fiscal, apurabot: apura, dixml, gerarpendentes: pend, gerarservpend: serv, conhecimento: base, resumoexecutivo: resumo, faturabot: fatura };

  /* ---------- regência dos oito capítulos e das passagens ---------- */
  const IN = 0.5, OUT = 0.42;
  R.toolAt = t => Math.floor((t - R.T0) / R.TLEN);
  R.Tools = function (ctx, t) {
    const i = R.toolAt(t);
    if (i < 0 || i > 7) {
      // saída do último: disco verde cobre e vira o ponto do fluxo
      const u = t - (R.T0 + 8 * R.TLEN);
      if (u >= 0 && u < 0.5) {
        const f = E.expoIn(1 - prog(u, 0, 0.5));
        R.disc(ctx, 960, 540, 2300 * f, C.acc, 1);
      }
      return;
    }
    const tl = R.TOOLS[i], u = t - (R.T0 + i * R.TLEN);
    chapter(ctx, i, u);
    // entrada: o disco da cor da ferramenta se recolhe no orbe
    const fin = E.expoOut(prog(u, 0, IN));
    const rr = lerp(2300, 20, fin), ox = lerp(960, ORB[0], fin), oy = lerp(540, ORB[1], fin);
    R.disc(ctx, ox, oy, rr, tl.c, 1);
    R.disc(ctx, ORB[0], ORB[1], 20, tl.c, prog(u, IN - 0.05, IN));
    R.ring(ctx, ORB[0], ORB[1], 20 + R.pulse(u, IN, 3) * 30, tl.c, 1.5, R.pulse(u, IN, 3));
    // saída: o disco da próxima cobre a tela
    const fo = E.expoIn(prog(u, R.TLEN - OUT, R.TLEN));
    if (fo > 0) {
      const nc = i < 7 ? R.TOOLS[i + 1].c : C.acc;
      R.disc(ctx, 1310, 540, 2300 * fo, nc, 1);
      R.ring(ctx, 1310, 540, 2300 * fo * 1.02, nc, 2, 0.6 * prog(fo, 0.02, 0.1));
    }
  };
})();
