// node render.mjs [--still t1,t2,...] [--out dir]   renders frames with headless Chromium (Playwright)
import { createRequire } from 'module'; import { execSync } from 'child_process'; const { chromium } = createRequire(execSync('npm root -g').toString().trim() + '/')('playwright'); import http from 'http'; import fs from 'fs'; import path from 'path'; import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
const dir = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2); const opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
const FPS = 24, still = opt('--still', null), out = path.resolve(opt('--out', path.join(dir, 'out')));
fs.mkdirSync(out, { recursive: true });
const types = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json' };
const srv = http.createServer((q, r) => { const f = path.join(dir, q.url.split('?')[0] === '/' ? 'index.html' : q.url.split('?')[0]); fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); } else { r.writeHead(200, { 'content-type': types[path.extname(f)] || 'application/octet-stream' }); r.end(d); } }); }).listen(0);
const port = srv.address().port;
const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 1920, height: 1080 } });
pg.on('pageerror', e => { console.error('PAGE ERROR', e.message); process.exit(1); });
await pg.goto(`http://localhost:${port}/`); await pg.waitForFunction('window.READY === true', null, { timeout: 60000 });
const DUR = await pg.evaluate('window.DUR');
if (still) {
  for (const t of still.split(',')) { await pg.evaluate(t => window.render(t), +t); await pg.screenshot({ path: path.join(out, `s_${(+t).toFixed(2)}.jpg`), type: 'jpeg', quality: 88 }); }
} else {
  const N = Math.round(DUR * FPS), mp4 = path.join(out, 'video_silent.mp4');
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', '-r', String(FPS), mp4], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let f = 0; f < N; f++) {
    await pg.evaluate(t => window.render(t), f / FPS);
    const buf = await pg.screenshot({ type: 'jpeg', quality: 95 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r)); console.log('frames', N, '->', mp4);
}
await b.close(); srv.close();
