/* ==========================================================================
   órbita · reel — núcleo
   Tudo é função pura do tempo t (segundos). Nada de estado entre quadros:
   qualquer quadro pode ser renderizado em qualquer ordem, em qualquer
   processo — é o que permite motion blur por subamostragem e render paralelo.
   ========================================================================== */
'use strict';
const R = (window.R = {});

R.W = 1920; R.H = 1080; R.FPS = 60; R.DUR = 45;
/* 128 BPM: 24 compassos de 4 tempos = 96 tempos = exatamente 45 s */
R.BPM = 128; R.BEAT = 60 / R.BPM; R.BAR = 4 * R.BEAT;
const B = (R.B = n => n * R.BEAT);               /* tempo → segundos */

/* ---------- matemática ---------- */
const clamp = (R.clamp = (x, a = 0, b = 1) => (x < a ? a : x > b ? b : x));
const lerp = (R.lerp = (a, b, t) => a + (b - a) * t);
const prog = (R.prog = (t, a, b) => clamp((t - a) / (b - a)));
const TAU = (R.TAU = Math.PI * 2);
R.smooth = t => t * t * (3 - 2 * t);
R.mix2 = (a, b, t) => [lerp(a[0], b[0], t), lerp(a[1], b[1], t)];
R.deg = d => (d * Math.PI) / 180;

/* cubic-bezier idêntica à do CSS (UnitBezier do WebKit) */
function bezier(p1x, p1y, p2x, p2y) {
  const cx = 3 * p1x, bx = 3 * (p2x - p1x) - cx, ax = 1 - cx - bx;
  const cy = 3 * p1y, by = 3 * (p2y - p1y) - cy, ay = 1 - cy - by;
  const sx = t => ((ax * t + bx) * t + cx) * t;
  const sy = t => ((ay * t + by) * t + cy) * t;
  const dx = t => (3 * ax * t + 2 * bx) * t + cx;
  function solve(x) {
    let t = x;
    for (let i = 0; i < 8; i++) {
      const e = sx(t) - x;
      if (Math.abs(e) < 1e-6) return t;
      const d = dx(t);
      if (Math.abs(d) < 1e-6) break;
      t -= e / d;
    }
    let lo = 0, hi = 1; t = x;
    for (let i = 0; i < 40; i++) {
      const v = sx(t);
      if (Math.abs(v - x) < 1e-6) break;
      if (x > v) lo = t; else hi = t;
      t = (lo + hi) / 2;
    }
    return t;
  }
  return x => (x <= 0 ? 0 : x >= 1 ? 1 : sy(solve(x)));
}
R.bezier = bezier;

/* as duas curvas do site, mais o vocabulário de sempre */
const E = (R.E = {
  out: bezier(0.22, 0.9, 0.24, 1),        /* --ease    */
  io: bezier(0.6, 0.02, 0.16, 1),         /* --ease-io */
  snap: bezier(0.7, 0, 0.1, 1),
  whip: bezier(0.85, 0, 0.15, 1),
  lin: t => t,
  cubicOut: t => 1 - Math.pow(1 - t, 3),
  quartOut: t => 1 - Math.pow(1 - t, 4),
  quintOut: t => 1 - Math.pow(1 - t, 5),
  cubicIn: t => t * t * t,
  quartIn: t => t * t * t * t,
  sineIO: t => 0.5 - 0.5 * Math.cos(Math.PI * t),
  expoOut: t => (t >= 1 ? 1 : 1 - Math.pow(2, -10 * t)),
  expoIn: t => (t <= 0 ? 0 : Math.pow(2, 10 * (t - 1))),
  expoIO: t => (t <= 0 ? 0 : t >= 1 ? 1 : t < 0.5 ? Math.pow(2, 20 * t - 10) / 2 : (2 - Math.pow(2, -20 * t + 10)) / 2),
  backOut: (t, s = 1.9) => 1 + (s + 1) * Math.pow(t - 1, 3) + s * Math.pow(t - 1, 2),
  backIn: (t, s = 1.7) => (s + 1) * t * t * t - s * t * t,
});

/* mola amortecida: resposta de 0 a 1 em função do tempo decorrido (s) */
R.spring = function (dt, f = 2.4, z = 0.42) {
  if (dt <= 0) return 0;
  const w = TAU * f, wd = w * Math.sqrt(1 - z * z);
  return 1 - Math.exp(-z * w * dt) * (Math.cos(wd * dt) + ((z * w) / wd) * Math.sin(wd * dt));
};
/* pulso: sobe rápido, decai exponencial — para acentos de batida */
R.pulse = (t, at, decay = 9) => (t < at ? 0 : Math.exp(-(t - at) * decay));

/* ---------- aleatório determinístico ---------- */
R.rng = function (seed) {
  let a = seed >>> 0;
  return function () {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
};
R.hash = function (n) {
  n = (n << 13) ^ n;
  return 1 - ((n * (n * n * 15731 + 789221) + 1376312589) & 0x7fffffff) / 1073741824;
};
/* ruído de valor 1D suave, -1..1 */
R.noise = function (x, seed = 0) {
  const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f);
  return lerp(R.hash(i + seed * 131), R.hash(i + 1 + seed * 131), u);
};

/* ---------- paleta (a da vitrine, tema escuro) ---------- */
R.C = {
  bg: '#07090E', bg2: '#0B0E15', bg3: '#10141D',
  ink: '#F3F5F9', ink2: '#9AA3B3', ink3: '#5C6474',
  line: '#1A1F29', line2: '#2B323F',
  acc: '#35C285', warn: '#E3B04B', bad: '#E0795E', manual: '#A78BFA',
  b1: '#8FAFCB', b2: '#343F73', b3: '#2A9165',
};
R.rgba = (hex, a) => {
  const n = parseInt(hex.slice(1), 16);
  return 'rgba(' + (n >> 16) + ',' + ((n >> 8) & 255) + ',' + (n & 255) + ',' + a.toFixed(4) + ')';
};

/* as oito ferramentas da Central, na ordem do filme (6 tempos cada) */
R.TOOLS = [
  { id: 'fiscalbot', name: 'Fiscalbot', c: '#35C285', ring: 0, a0: 0.5, note: 76, q: 'auditoria do Livro Fiscal' },
  { id: 'apurabot', name: 'Apurabot', c: '#8FAFCB', ring: 0, a0: 3.6, note: 79, q: 'apuração de ICMS' },
  { id: 'dixml', name: 'DiXML', c: '#8C98EA', ring: 1, a0: 1.1, note: 81, q: 'lote de XML em planilha' },
  { id: 'gerarpendentes', name: 'GerarPendentes', c: '#E3B04B', ring: 1, a0: 3.2, note: 83, q: 'mercadoria sem entrada' },
  { id: 'gerarservpend', name: 'GerarServPend', c: '#E0795E', ring: 1, a0: 5.2, note: 84, q: 'serviço sem lançamento' },
  { id: 'conhecimento', name: 'Base de conhecimento', c: '#4EC3C7', ring: 2, a0: 0.15, note: 86, q: 'propõe, nunca decide' },
  { id: 'resumoexecutivo', name: 'Resumo Executivo', c: '#B98CE0', ring: 2, a0: 2.25, note: 88, q: 'o painel da semana' },
  { id: 'faturabot', name: 'Faturabot', c: '#F29BB5', ring: 2, a0: 4.3, note: 91, q: 'a balança, caminhão a caminhão' },
];
R.T0 = B(24); R.TLEN = B(6);                     /* ferramentas: tempo 24 a 72 */

/* a marca: três círculos, centro em (0,0), tamanho s = raio do maior */
R.LOGO = [[40 - 56, 38 - 54, 38, '#8FAFCB', 1], [74 - 56, 52 - 54, 34, '#343F73', 0.92], [45 - 56, 72 - 54, 26, '#2A9165', 0.92]];
R.logo = function (ctx, x, y, s, o = {}) {
  const k = s / 38, sp = o.spread == null ? 1 : o.spread;
  ctx.save();
  ctx.globalAlpha *= o.alpha == null ? 1 : o.alpha;
  R.LOGO.forEach((c, i) => {
    const pop = o.pop ? o.pop[i] : 1;
    if (pop <= 0) return;
    ctx.globalAlpha = (o.alpha == null ? 1 : o.alpha) * c[4];
    ctx.fillStyle = c[3];
    ctx.beginPath();
    ctx.arc(x + c[0] * k * sp, y + c[1] * k * sp, Math.max(0, c[2] * k * pop), 0, TAU);
    ctx.fill();
  });
  ctx.restore();
};
R.disc = (ctx, x, y, r, fill, a = 1) => {
  if (r <= 0 || a <= 0) return;
  ctx.save(); ctx.globalAlpha *= a; ctx.fillStyle = fill; ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill(); ctx.restore();
};
R.ring = (ctx, x, y, r, stroke, w = 1, a = 1) => {
  if (r <= 0 || a <= 0) return;
  ctx.save(); ctx.globalAlpha *= a; ctx.strokeStyle = stroke; ctx.lineWidth = w; ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.stroke(); ctx.restore();
};
R.line = (ctx, x1, y1, x2, y2, stroke, w = 1, a = 1) => {
  if (a <= 0) return;
  ctx.save(); ctx.globalAlpha *= a; ctx.strokeStyle = stroke; ctx.lineWidth = w; ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke(); ctx.restore();
};
R.rect = (ctx, x, y, w, h, fill, a = 1) => {
  if (a <= 0 || w <= 0 || h <= 0) return;
  ctx.save(); ctx.globalAlpha *= a; ctx.fillStyle = fill; ctx.fillRect(x, y, w, h); ctx.restore();
};
R.frame = (ctx, x, y, w, h, stroke, a = 1) => {
  if (a <= 0) return;
  ctx.save(); ctx.globalAlpha *= a; ctx.strokeStyle = stroke; ctx.lineWidth = 1; ctx.strokeRect(x + .5, y + .5, w, h); ctx.restore();
};
/* cantos de mira, a assinatura dos painéis do site */
R.ticks = (ctx, x, y, w, h, stroke, a = 1, L = 18) => {
  if (a <= 0) return;
  ctx.save(); ctx.globalAlpha *= a; ctx.strokeStyle = stroke; ctx.lineWidth = 1.5; ctx.beginPath();
  ctx.moveTo(x, y + L); ctx.lineTo(x, y); ctx.lineTo(x + L, y);
  ctx.moveTo(x + w - L, y + h); ctx.lineTo(x + w, y + h); ctx.lineTo(x + w, y + h - L);
  ctx.stroke(); ctx.restore();
};
R.fmt = (v, d = 0) => v.toLocaleString('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d });

/* ---------- tipografia ---------- */
R.SANS = 'Inter';
R.MONO = 'JetBrains Mono';
R.font = (w, px, fam = R.SANS) => w + ' ' + px + 'px "' + fam + '"';

const LAYOUTS = new Map();
/* posição x de cada caractere (com kerning e tracking), em cache */
R.layout = function (ctx, str, font, ls = 0) {
  const k = font + '|' + ls + '|' + str;
  let L = LAYOUTS.get(k);
  if (L) return L;
  ctx.save();
  ctx.font = font; ctx.letterSpacing = ls + 'px';
  const xs = [], chars = [...str];
  let acc = '';
  for (const ch of chars) { xs.push(ctx.measureText(acc).width); acc += ch; }
  const m = ctx.measureText(str);
  L = { chars, xs, w: m.width - ls, font, ls };
  ctx.restore();
  LAYOUTS.set(k, L);
  return L;
};

/* texto simples */
R.text = function (ctx, str, x, y, o = {}) {
  ctx.save();
  ctx.font = o.font || R.font(500, 16);
  ctx.letterSpacing = (o.ls || 0) + 'px';
  ctx.fillStyle = o.color || R.C.ink;
  ctx.globalAlpha *= o.alpha == null ? 1 : o.alpha;
  ctx.textAlign = o.align || 'left';
  ctx.textBaseline = o.base || 'alphabetic';
  ctx.fillText(str, x, y);
  ctx.restore();
};

/* texto caractere a caractere: fn(i, ch) → {dx, dy, a, s, rot, color} ou null */
R.chars = function (ctx, L, x, y, fn, color) {
  ctx.save();
  ctx.font = L.font; ctx.letterSpacing = '0px';
  ctx.textBaseline = 'alphabetic';
  const ga = ctx.globalAlpha;
  for (let i = 0; i < L.chars.length; i++) {
    const ch = L.chars[i];
    if (ch === ' ') continue;
    const g = fn(i, ch);
    if (!g || g.a <= 0.001) continue;
    ctx.globalAlpha = ga * clamp(g.a == null ? 1 : g.a);
    ctx.fillStyle = g.color || color || R.C.ink;
    const px = x + L.xs[i] + (g.dx || 0), py = y + (g.dy || 0);
    if (g.s != null || g.rot) {
      ctx.save();
      ctx.translate(px, py);
      if (g.rot) ctx.rotate(g.rot);
      if (g.s != null) ctx.scale(g.s, g.sy == null ? g.s : g.sy);
      ctx.fillText(ch, 0, 0);
      ctx.restore();
    } else ctx.fillText(ch, px, py);
  }
  ctx.restore();
};

/* revelação por máscara: cada letra sobe de baixo de uma linha de corte.
   o = {t0, stagger, dur, size, out:{t0,stagger,dur}, color, ease} */
R.rise = function (ctx, L, x, y, t, o) {
  const size = o.size, st = o.stagger == null ? 0.022 : o.stagger, dur = o.dur || 0.62;
  const ease = o.ease || E.out;
  ctx.save();
  ctx.beginPath();
  ctx.rect(x - size, y - size * 1.08, L.w + size * 2, size * 1.4);
  ctx.clip();
  R.chars(ctx, L, x, y, i => {
    const p = ease(prog(t, o.t0 + i * st, o.t0 + i * st + dur));
    if (p <= 0) return null;
    let dy = (1 - p) * size * 1.15;
    if (o.out) {
      const q = E.io(prog(t, o.out.t0 + i * (o.out.stagger || 0.012), o.out.t0 + i * (o.out.stagger || 0.012) + (o.out.dur || 0.4)));
      dy -= q * size * 1.2;
    }
    return { dy, a: 1 };
  }, o.color);
  ctx.restore();
};

/* ---------- câmera 3D ----------
   alvo (tx,ty,tz), distância, yaw (azimute), pitch (elevação), roll,
   fov vertical em graus, px/py desloca o ponto principal na tela */
R.camera = function (o) {
  const tx = o.tx || 0, ty = o.ty || 0, tz = o.tz || 0;
  const cp = Math.cos(o.pitch), sp = Math.sin(o.pitch);
  const cy = Math.cos(o.yaw), sy = Math.sin(o.yaw);
  const pos = [tx + o.dist * cp * sy, ty + o.dist * sp, tz + o.dist * cp * cy];
  const f = [-cp * sy, -sp, -cp * cy];
  const r0 = [cy, 0, -sy];
  const u0 = [r0[1] * f[2] - r0[2] * f[1], r0[2] * f[0] - r0[0] * f[2], r0[0] * f[1] - r0[1] * f[0]];
  const cr = Math.cos(o.roll || 0), sr = Math.sin(o.roll || 0);
  const r = [r0[0] * cr + u0[0] * sr, r0[1] * cr + u0[1] * sr, r0[2] * cr + u0[2] * sr];
  const u = [u0[0] * cr - r0[0] * sr, u0[1] * cr - r0[1] * sr, u0[2] * cr - r0[2] * sr];
  const F = R.H / 2 / Math.tan((o.fov * Math.PI) / 360);
  const cx = R.W / 2 + (o.px || 0), cyy = R.H / 2 + (o.py || 0);
  return {
    pos, f, r, u, F, o,
    project(x, y, z) {
      const dx = x - pos[0], dy = y - pos[1], dz = z - pos[2];
      const zc = dx * f[0] + dy * f[1] + dz * f[2];
      const xc = dx * r[0] + dy * r[1] + dz * r[2];
      const yc = dx * u[0] + dy * u[1] + dz * u[2];
      const s = F / zc;
      return { x: cx + xc * s, y: cyy - yc * s, z: zc, s };
    },
  };
};
/* interpola parâmetros de câmera (ângulos e distância em escala log) */
R.camLerp = function (a, b, t) {
  const o = {};
  for (const k in a) o[k] = k === 'dist' ? Math.exp(lerp(Math.log(a[k]), Math.log(b[k]), t)) : lerp(a[k], b[k] == null ? a[k] : b[k], t);
  return o;
};
