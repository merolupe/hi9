/* ==========================================================================
   Compassos 5–6 · SISTEMA — o drop: a marca no centro, oito ferramentas em
   órbita, câmera 3D que inclina do topo para o plano oblíquo e mergulha
   ========================================================================== */
'use strict';
(function () {
  const { C, E, B, clamp, lerp, prog, TAU } = R;
  const T = B(16), END = B(24);
  const RADII = [430, 640, 860];
  const PR = [34, 30, 27];
  const TOP = { tx: 0, ty: 0, tz: 0, dist: 3000, yaw: 0, pitch: R.deg(89), roll: 0, fov: 34, px: 0, py: 0 };
  const OBL = { tx: 0, ty: 0, tz: 0, dist: 2250, yaw: R.deg(-16), pitch: R.deg(24), roll: R.deg(-7), fov: 34, px: 190, py: -70 };
  const DRIFT = { tx: 0, ty: 0, tz: 0, dist: 2050, yaw: R.deg(12), pitch: R.deg(19), roll: R.deg(-4), fov: 34, px: 180, py: -60 };
  function cam(t) {
    let p;
    if (t < T + 0.1) p = TOP;
    else if (t < B(18.6)) p = R.camLerp(TOP, OBL, E.io(prog(t, T + 0.1, B(18.6))));
    else p = R.camLerp(OBL, DRIFT, E.sineIO(prog(t, B(18.6), END)));
    return R.camera(p);
  }
  R.planetAngle = (i, t) => {
    const tl = R.TOOLS[i], dt = Math.max(0, t - T);
    return tl.a0 + (0.22 * dt + 2.6 * (1 - Math.exp(-dt * 1.4))) / (tl.ring + 1);
  };
  const popAt = i => B(17) + i * B(0.5);

  R.S2 = function (ctx, t) {
    if (t < T - 0.02 || t > END + 0.05) return;
    const cm = cam(t);
    // mergulho: o Fiscalbot cresce até cobrir a tela
    const dv = prog(t, B(22.3), B(23.85));
    ctx.save();
    const a0 = R.planetAngle(0, t), r0 = RADII[0];
    const P0 = cm.project(Math.cos(a0) * r0, 0, Math.sin(a0) * r0);
    if (dv > 0) {
      const k = Math.exp(E.expoIn(dv) * Math.log(420)), m = E.io(dv);
      ctx.translate(lerp(P0.x, 960, m), lerp(P0.y, 540, m));
      ctx.scale(k, k);
      ctx.translate(-P0.x, -P0.y);
    }
    // órbitas
    RADII.forEach((rad, ri) => {
      const g = E.out(prog(t, T + ri * B(0.25), T + ri * B(0.25) + 0.9));
      if (g <= 0) return;
      ctx.beginPath();
      for (let k = 0; k <= 120; k++) {
        const a = (k / 120) * TAU, p = cm.project(Math.cos(a) * rad * g, 0, Math.sin(a) * rad * g);
        k ? ctx.lineTo(p.x, p.y) : ctx.moveTo(p.x, p.y);
      }
      ctx.strokeStyle = R.rgba(C.b1, 0.28); ctx.lineWidth = 1.2;
      if (ri === 1) ctx.setLineDash([3, 9]);
      ctx.stroke(); ctx.setLineDash([]);
      // marcas de régua na órbita de fora
      if (ri === 2) for (let k = 0; k < 72; k++) {
        const a = (k / 72) * TAU, q1 = cm.project(Math.cos(a) * (rad + 22) * g, 0, Math.sin(a) * (rad + 22) * g),
          q2 = cm.project(Math.cos(a) * (rad + (k % 6 ? 36 : 54)) * g, 0, Math.sin(a) * (rad + (k % 6 ? 36 : 54)) * g);
        R.line(ctx, q1.x, q1.y, q2.x, q2.y, C.b1, 1, 0.3 * g);
      }
    });
    // planetas atrás, marca, planetas na frente
    const Pl = R.TOOLS.map((tl, i) => {
      const a = R.planetAngle(i, t), rad = RADII[tl.ring];
      const p = cm.project(Math.cos(a) * rad, 0, Math.sin(a) * rad);
      return { tl, i, p, pop: R.spring(t - popAt(i), 2.3, 0.4) };
    });
    const O = cm.project(0, 0, 0);
    const drawP = q => {
      if (q.pop <= 0) return;
      const r = PR[q.tl.ring] * q.p.s * q.pop;
      R.disc(ctx, q.p.x, q.p.y, r * 2.6, q.tl.c, 0.07);
      R.disc(ctx, q.p.x, q.p.y, r, q.tl.c, 1);
      R.disc(ctx, q.p.x - r * 0.35, q.p.y - r * 0.35, r * 0.36, '#fff', 0.2);
      // flash de nascimento
      const f = prog(t, popAt(q.i), popAt(q.i) + 0.5);
      if (f > 0 && f < 1) R.ring(ctx, q.p.x, q.p.y, r * (1 + E.out(f) * 3), q.tl.c, 1.5, 1 - f);
      // nome, digitado
      const n = Math.floor(clamp((t - popAt(q.i) - 0.08) / 0.3) * q.tl.name.length);
      if (n > 0) {
        R.text(ctx, q.tl.name.slice(0, n).toUpperCase(), q.p.x + r + 14, q.p.y + 6,
          { font: R.font(500, 17, R.MONO), color: C.ink, ls: 3, alpha: (1 - dv * 3) * (q.p.z > 0 ? 1 : 0) });
      }
    };
    Pl.filter(q => q.p.z > cm.project(0, 0, 0).z).forEach(drawP);
    const core = R.spring(t - T, 1.8, 0.45);
    R.ring(ctx, O.x, O.y, 150 * O.s * (1 + R.pulse(t, T, 3) * 1.4), C.acc, 1.2, 0.6 * core);
    R.logo(ctx, O.x, O.y, 118 * O.s * core, { alpha: 1, spread: 1 });
    Pl.filter(q => q.p.z <= cm.project(0, 0, 0).z).forEach(drawP);
    ctx.restore();
    if (dv >= 1) R.rect(ctx, -40, -40, 2000, 1160, R.TOOLS[0].c, 1);
    // título do drop
    const L = R.layout(ctx, 'Oito ferramentas.', R.font(700, 108), -5);
    R.rise(ctx, L, 130, 880, t, { t0: B(19.6), size: 108, stagger: 0.02, out: { t0: B(22.1), stagger: 0.01 } });
    const L2 = R.layout(ctx, 'UMA TELA · DOIS CLIQUES · NADA INSTALADO', R.font(500, 20, R.MONO), 6);
    R.rise(ctx, L2, 136, 936, t, { t0: B(20.4), size: 22, stagger: 0.008, color: C.acc, out: { t0: B(22.1), stagger: 0.004 } });
  };
})();
