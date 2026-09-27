#!/usr/bin/env node
/* ==========================================================================
   Renderiza o reel.html quadro a quadro (adaptado do showreel do órbita).

     node render.mjs video  [--scale 1] [--workers 4] [--out central-fiscal-reel.mp4]
                            [--audio soundtrack.wav] [--from 0] [--to 900] [--samples N]
     node render.mjs stills --times 0.5,3.9,7.6 [--scale 0.5] [--dir stills]

   Cada worker é um Chromium headless (canvas em software, determinístico)
   que renderiza os quadros i ≡ w (mod workers) e envia RGBA cru por POST.
   O servidor reordena e entrega ao ffmpeg em sequência.
   ========================================================================== */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { spawn, execSync } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.dirname(HERE);                  /* vitrine/: serve também ../fontes */
const argv = process.argv.slice(2);
const mode = argv[0] || 'video';
const opt = (k, d) => { const i = argv.indexOf('--' + k); return i >= 0 ? argv[i + 1] : d; };

async function loadPlaywright() {
  try { return await import('playwright'); } catch {}
  const g = execSync('npm root -g').toString().trim();
  return import(pathToFileURL(path.join(g, 'playwright', 'index.mjs')).href);
}
function ffmpegPath() {
  if (process.env.FFMPEG) return process.env.FFMPEG;
  try { execSync('ffmpeg -version', { stdio: 'ignore' }); return 'ffmpeg'; } catch {}
  return execSync('python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"').toString().trim();
}

const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.woff2': 'font/woff2', '.mp3': 'audio/mpeg', '.wav': 'audio/wav' };
function serve(onPost) {
  const srv = http.createServer((req, res) => {
    const u = new URL(req.url, 'http://x');
    if (req.method === 'POST') {
      const chunks = [];
      req.on('data', c => chunks.push(c));
      req.on('end', async () => { await onPost(u, Buffer.concat(chunks)); res.end('ok'); });
      return;
    }
    const f = path.join(ROOT, decodeURIComponent(u.pathname));
    if (!f.startsWith(ROOT) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.statusCode = 404; return res.end(); }
    res.setHeader('Content-Type', MIME[path.extname(f)] || 'application/octet-stream');
    fs.createReadStream(f).pipe(res);
  });
  return new Promise(r => srv.listen(0, '127.0.0.1', () => r(srv)));
}

async function launch(pw, port, n) {
  const out = [];
  for (let i = 0; i < n; i++) {
    const browser = await pw.chromium.launch({ args: ['--disable-gpu', '--disable-accelerated-2d-canvas', '--disable-gpu-compositing'] });
    const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
    page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') console.log('[page]', m.text()); });
    page.on('pageerror', e => console.log('[pageerror]', e.message));
    await page.goto(`http://127.0.0.1:${port}/reel/reel.html?render=1`);
    await page.evaluate(() => window.REEL.ready);
    out.push({ browser, page });
  }
  return out;
}

const pw = await loadPlaywright();
const scale = +opt('scale', mode === 'stills' ? 0.5 : 1);
const W = Math.round(1920 * scale), H = Math.round(1080 * scale);
const samples = opt('samples') ? +opt('samples') : undefined;

if (mode === 'stills') {
  const dir = path.resolve(opt('dir', path.join(HERE, 'stills')));
  fs.mkdirSync(dir, { recursive: true });
  const times = opt('times', '0.5').split(',').map(Number);
  const srv = await serve((u, buf) => fs.writeFileSync(path.join(dir, u.searchParams.get('name') + '.png'), buf));
  const nw = Math.min(+opt('workers', 4), times.length);
  const ws = await launch(pw, srv.address().port, nw);
  await Promise.all(ws.map((w, k) => w.page.evaluate(o => window.REEL.stills(o), {
    times: times.filter((_, i) => i % nw === k), scale, samples, url: '/still', prefix: opt('prefix', 't'),
  })));
  for (const w of ws) await w.browser.close();
  srv.close();
  console.log('stills →', dir);
} else {
  const from = +opt('from', 0), to = +opt('to', 2700), nw = +opt('workers', 4);
  const out = path.resolve(opt('out', path.join(HERE, 'central-fiscal-reel.mp4')));
  const audio = opt('audio');
  const args = ['-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', `${W}x${H}`, '-r', '60', '-i', '-'];
  if (audio) args.push('-i', path.resolve(audio));
  args.push('-vf', 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p',
    '-c:v', 'libx264', '-preset', opt('preset', 'slow'), '-crf', opt('crf', '17'), '-tune', 'film',
    '-profile:v', 'high', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709');
  if (audio) args.push('-c:a', 'aac', '-b:a', '256k', '-shortest');
  args.push('-movflags', '+faststart', out);
  const ff = spawn(ffmpegPath(), args, { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise(r => ff.on('close', r));

  /* fila de reordenação: responde ao POST só quando o quadro foi escrito
     (ou quando está perto da vez), para os workers não correrem demais */
  const buf = new Map(); let next = from; const waiters = new Map();
  const t0 = Date.now();
  async function flush() {
    while (buf.has(next)) {
      const b = buf.get(next); buf.delete(next);
      if (!ff.stdin.write(b)) await new Promise(r => ff.stdin.once('drain', r));
      next++;
      if ((next - from) % 30 === 0 || next === to) {
        const el = (Date.now() - t0) / 1000, fps = (next - from) / el;
        console.log(`frame ${next}/${to}  ${fps.toFixed(2)} f/s  eta ${((to - next) / fps).toFixed(0)}s`);
      }
      for (const [i, r] of waiters) if (i < next + 3 * nw) { waiters.delete(i); r(); }
    }
  }
  const srv = await serve(async (u, b) => {
    const i = +u.searchParams.get('i');
    if (b.length !== W * H * 4) throw new Error('frame size ' + b.length);
    buf.set(i, b);
    await flush();
    if (i >= next + 3 * nw) await new Promise(r => waiters.set(i, r));
  });
  const ws = await launch(pw, srv.address().port, nw);
  await Promise.all(ws.map((w, k) => w.page.evaluate(o => window.REEL.renderRange(o), {
    from, to, step: nw, offset: k, scale, samples, url: '/frame',
  })));
  ff.stdin.end();
  await done;
  for (const w of ws) await w.browser.close();
  srv.close();
  console.log('video →', out, `(${((Date.now() - t0) / 1000).toFixed(0)}s)`);
}
