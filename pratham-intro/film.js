// "Pratham Nawal — 10 s intro", drawn entirely in code in the Dark Tech Keynote style (lemo-opuscar).
// Content comes from Pratham_Nawal_Resume_Updated.pdf. 24 fps, 1920×1080, tempo 120 bpm (beat = 0.5 s).
import { W, H, PAL, FONT, font, rgba, rr, bg, glow, grid, vignette, panel, caret, lightReveal, scramble, buf, flyPose, setAccent, clamp, lerp, seg, ss, eo, ei, eio, back } from './engine.js';

FONT.disp = 'Inter'; FONT.mono = 'DejaVu Sans Mono';   // InterTight / JetBrains Mono are not installed here
setAccent('#B7F34A');                                    // one accent: lime
export const DUR = 20;
const CX = W / 2;

// ───────────────────────── content ─────────────────────────
const NAME = 'Pratham Nawal';
const ROLE = 'SENIOR PRODUCT MANAGER  ·  AI / ML PLATFORMS';
const TILES = [
  { num: '50B+', label: 'DAILY DECISIONS', sub: 'PayPal experimentation platform', accent: true },
  { num: '400M+', label: 'CONSUMERS SERVED', sub: 'Checkout, Venmo, merchants' },
  { num: '5x', label: 'EXPERIMENT VELOCITY', sub: 'Governance + self-serve' },
  { num: '$5M', label: 'INFRA COST SAVED', sub: 'Simulation platform, cloud migration' },
];
const CHIPS = [
  { yr: '2019', co: 'Quantiphi', role: 'Data Scientist', stat: 'Augmented analytics' },
  { yr: '2020', co: 'Niyo', role: 'Product Manager', stat: 'Video KYC  +26% adoption' },
  { yr: '2022', co: 'GoKwik', role: 'Senior PM', stat: 'KwikFlows  $1M ARR' },
  { yr: '2025 →', co: 'PayPal', role: 'Senior PM · AI/ML', stat: '15K+ users  ·  5x velocity', accent: true },
];

// ───────────────────────── timing (shared with the score) ─────────────────────────
const TYPE0 = 0.4, TYPE_DT = 0.075;                 // typing the name
const ROLE0 = 1.6, ROLE1 = 2.4;                     // role label light reveal
const HDR0 = 4.1, HDR1 = 4.7;                       // name collapses to header
const LANDS = [5.3, 8.55, 10.3, 12.7];              // tiles land as each number is spoken
const FLY0 = i => LANDS[i] - 0.5, FLY_D = 0.5;
const LAND = i => LANDS[i];
const LOCK = (i, n) => 0.18 + 0.08 * n;             // digit lock offsets after landing
const DIS0 = i => 14.1 + i * 0.08, DIS_D = 0.5;     // tiles put away
const CHIP0 = i => [14.95, 15.4, 15.85, 16.3][i];   // chips arrive as each company is spoken
const OUT0 = i => 16.95 + i * 0.06;                 // chips put away
const END0 = 16.9, ICON0 = 17.1, NAME2 = 17.3, URL0 = 18.7;
export const VO = { l1: 1.3, a1: 4.75, a2: 7.95, b: 10.15, c: 12.5, d: 14.2, e: 17.2 };   // voice-over clip start times

export const EVENTS = (() => {
  const ev = [];
  for (let i = 0; i < NAME.length; i++) ev.push({ t: TYPE0 + i * TYPE_DT, type: 'key', i });
  ev.push({ t: ROLE0 + 0.2, type: 'shimmer' });
  ev.push({ t: HDR0, type: 'whoosh' });
  TILES.forEach((tl, i) => {
    ev.push({ t: FLY0(i), type: 'whoosh_s' });
    ev.push({ t: LAND(i), type: 'note', n: [64, 67, 69, 72][i] });
    for (let n = 0; n < tl.num.length; n++) if (/[0-9]/.test(tl.num[n])) ev.push({ t: LAND(i) + LOCK(i, n), type: 'digit', n });
    ev.push({ t: LAND(i) + LOCK(i, tl.num.length - 1), type: 'lock' });
  });
  for (let i = 0; i < 4; i++) ev.push({ t: DIS0(i), type: 'crt' });
  CHIPS.forEach((c, i) => ev.push({ t: CHIP0(i), type: c.accent ? 'chord' : 'note', n: [60, 64, 67, 72][i] }));
  for (let i = 0; i < 4; i++) ev.push({ t: OUT0(i), type: 'crt' });
  ev.push({ t: ICON0, type: 'note', n: 72 });
  ev.push({ t: NAME2, type: 'chord', big: 1 });
  ev.push({ t: URL0, type: 'shimmer' });
  for (let k = 0; k < 26; k++) { const t = 4.5 + k * 0.5; if (t < 16.9) ev.push({ t, type: 'pulse' }); }
  return ev.sort((a, b) => a.t - b.t);
})();

// ───────────────────────── helpers ─────────────────────────
function text(g, s, x, y, px, wt, color, o = {}) {
  const { align = 'left', fam = 'ui', track = 0, alpha = 1 } = o;
  g.save(); g.globalAlpha *= alpha; g.font = font(px, wt, fam); g.fillStyle = color; g.textAlign = align; g.textBaseline = 'alphabetic';
  if (g.letterSpacing !== undefined) g.letterSpacing = `${track * px}px`;
  g.fillText(s, x, y); g.restore();
}
const blink = t => (Math.floor(t / 0.25) % 2 === 0 ? 1 : 0);   // on/off every eighth note
/** CRT-off put-away: collapse vertically to a line, then the line to a point. Returns null when gone. */
function crt(p) { if (p >= 1) return null; const a = ei(seg(p, 0, 0.62)), b = ei(seg(p, 0.62, 1)); return { sx: 1 - b * 0.98, sy: Math.max(0.012, 1 - a), glint: ss(seg(p, 0.4, 0.8)) * (1 - b) }; }

// ───────────────────────── scene pieces ─────────────────────────
function nameAndRole(g, t) {
  const hp = eio(seg(t, HDR0, HDR1));
  const out = 1 - seg(t, 16.9, 17.2);                         // header leaves before the end card
  // measure at 150 px
  g.save(); g.font = font(150, 600); if (g.letterSpacing !== undefined) g.letterSpacing = `${-0.03 * 150}px`;
  const tw = g.measureText(NAME).width; g.restore();
  const sc = lerp(1, 44 / 150, hp);
  const cx = lerp(CX, 96 + tw * (44 / 150) / 2, hp), by = lerp(560, 128, hp);   // baseline
  g.save(); g.globalAlpha *= out; g.translate(cx, by); g.scale(sc, sc);
  const n = clamp(Math.floor((t - TYPE0) / TYPE_DT) + 1, 0, NAME.length);
  g.font = font(150, 600); g.fillStyle = PAL.text; g.textAlign = 'left'; g.textBaseline = 'alphabetic';
  if (g.letterSpacing !== undefined) g.letterSpacing = `${-0.03 * 150}px`;
  g.fillText(NAME.slice(0, n), -tw / 2, 0);
  // caret rides the typing, then blinks, then dies as the header forms
  const typedW = n ? g.measureText(NAME.slice(0, n)).width : 0;
  const cOn = t < TYPE0 + NAME.length * TYPE_DT + 0.05 ? (t < TYPE0 ? blink(t) : 1) : blink(t);
  const cA = 1 - seg(t, HDR0 - 0.2, HDR0 + 0.1);
  caret(g, -tw / 2 + typedW + 14, -52, 138, { on: cOn, alpha: cA * ss(seg(t, 0, 0.12)), wr: 1 / 11 });
  g.restore();
  // role label: light reveal in the centre, then it rides the header
  const lsc = lerp(1, 0.62, hp), ly = lerp(618, 162, hp);
  g.save(); g.font = font(26, 500, 'mono'); if (g.letterSpacing !== undefined) g.letterSpacing = '3.6px';
  const lwd = g.measureText(ROLE).width; g.restore();
  const lcx = lerp(CX, 96 + lwd * 0.62 / 2, hp);
  g.save(); g.globalAlpha *= out;
  if (t < HDR0) {
    const [lc, lg] = buf('role', 1240, 64);
    lg.clearRect(0, 0, 1240, 64); lg.font = font(26, 500, 'mono'); lg.fillStyle = PAL.dim; lg.textAlign = 'center'; lg.textBaseline = 'middle';
    if (lg.letterSpacing !== undefined) lg.letterSpacing = '3.6px';
    lg.fillText(ROLE, 620 + 2, 33);
    lightReveal(g, lc, CX - 620, 618 - 33, 1240, 64, seg(t, ROLE0, ROLE1), { base: 0.0, soft: 220, band: 70 });
  } else {
    g.translate(lcx, ly); g.scale(lsc, lsc); g.font = font(26, 500, 'mono'); g.fillStyle = PAL.dim; g.textAlign = 'center'; g.textBaseline = 'middle';
    if (g.letterSpacing !== undefined) g.letterSpacing = '3.6px';
    g.fillText(ROLE, 2, 0);
  }
  g.restore();
}

function tile(g, i, t) {
  const tl = TILES[i];
  const x0 = 326, y0 = 240, tw = 620, th = 270, gap = 28;
  const to = { x: x0 + (i % 2) * (tw + gap) + tw / 2, y: y0 + Math.floor(i / 2) * (th + gap) + th / 2, rot: 0, s: 1 };
  const fr = [{ x: -300, y: -200, rot: -0.25 }, { x: W + 300, y: -200, rot: 0.25 }, { x: -300, y: H + 200, rot: 0.2 }, { x: W + 300, y: H + 200, rot: -0.2 }][i];
  const p = seg(t, FLY0(i), FLY0(i) + FLY_D);
  if (p <= 0) {
    if (t > HDR1 && t < DIS0(i)) { g.save(); g.globalAlpha = ss(seg(t, HDR1, HDR1 + 0.4)); g.strokeStyle = 'rgba(255,255,255,.07)'; g.lineWidth = 1.5; g.setLineDash([10, 10]); rr(g, to.x - tw / 2, to.y - th / 2, tw, th, 24); g.stroke(); g.restore(); }
    return;
  }
  const pose = flyPose({ ...fr, s: 1.1 }, to, p);
  const cr = crt(seg(t, DIS0(i), DIS0(i) + DIS_D));
  if (seg(t, DIS0(i), DIS0(i) + DIS_D) >= 1) return;
  g.save(); g.translate(pose.x, pose.y); g.rotate(pose.rot); g.scale(pose.s, pose.s);
  if (cr) g.scale(cr.sx, cr.sy);
  const sq = cr ? cr.sy : 1;
  g.globalAlpha *= clamp(p * 4);
  panel(g, -tw / 2, -th / 2, tw, th, { r: 24, fill: PAL.surf2, stroke: tl.accent ? rgba(PAL.accent, 0.45) : PAL.line });
  if (sq > 0.5) {
    const tt = t - LAND(i);
    g.save(); g.globalAlpha *= clamp((sq - 0.5) * 2);
    text(g, tl.label, -tw / 2 + 46, -th / 2 + 52, 20, 500, PAL.dim, { fam: 'mono', track: 0.16 });
    if (tl.accent) { g.fillStyle = PAL.accent; g.shadowColor = rgba(PAL.accent, 0.9); g.shadowBlur = 14; g.beginPath(); g.arc(tw / 2 - 52, -th / 2 + 44, 7, 0, 7); g.fill(); g.shadowColor = 'transparent'; }
    const locks = [...tl.num].map((_, n) => LOCK(i, n));
    if (tl.accent) glow(g, -tw / 2 + 200, 20, 260, PAL.accent, 0.10 * ss(seg(tt, 0.2, 0.8)));
    scramble(g, tl.num, -tw / 2 + 42, 52, tt, locks, { px: 128, wt: 700, color: tl.accent ? PAL.accent : PAL.text, start: 0, tracking: -0.045 });
    text(g, tl.sub, -tw / 2 + 46, th / 2 - 40, 25, 400, PAL.dim);
    g.restore();
  }
  if (cr && cr.glint > 0) { g.globalCompositeOperation = 'lighter'; g.fillStyle = `rgba(210,215,255,${0.55 * cr.glint})`; rr(g, -tw / 2, -3, tw, 6, 3); g.fill(); }
  g.restore();
}

function chips(g, t) {
  const cw = 390, chh = 250, gap = 36, x0 = 126, cy = 490, lineY = 710, x1 = x0 + 4 * cw + 3 * gap;
  if (t < CHIP0(0) - 0.3 || t > 17.9) return;
  // timeline hairline with an accent-lit progress segment
  const lineA = ss(seg(t, CHIP0(0) - 0.2, CHIP0(0) + 0.1)) * (1 - seg(t, OUT0(0), OUT0(0) + 0.4));
  const prog = ss(seg(t, CHIP0(0), CHIP0(3) + 0.3));
  g.save(); g.globalAlpha *= lineA;
  g.fillStyle = 'rgba(255,255,255,.10)'; g.fillRect(x0, lineY, x1 - x0, 2);
  g.fillStyle = PAL.accent; g.shadowColor = rgba(PAL.accent, 0.8); g.shadowBlur = 14; g.fillRect(x0, lineY, (x1 - x0) * prog, 2); g.shadowColor = 'transparent';
  g.restore();
  CHIPS.forEach((c, i) => {
    const p = seg(t, CHIP0(i), CHIP0(i) + 0.4), bx = x0 + i * (cw + gap);
    const cr = crt(seg(t, OUT0(i), OUT0(i) + 0.55));
    if (p <= 0 || seg(t, OUT0(i), OUT0(i) + 0.55) >= 1) return;
    const k = back(p, 1.5), cyy = cy + (1 - k) * 60, cxx = bx + cw / 2;
    // dot on the timeline
    g.save(); g.globalAlpha *= lineA; g.fillStyle = c.accent ? PAL.accent : PAL.text; g.shadowColor = rgba(PAL.accent, c.accent ? 0.9 : 0); g.shadowBlur = 16;
    g.beginPath(); g.arc(cxx, lineY + 1, c.accent ? 9 : 6, 0, 7); g.fill(); g.restore();
    g.save(); g.translate(cxx, cyy); if (cr) g.scale(cr.sx, cr.sy); g.globalAlpha *= clamp(p * 3);
    const sq = cr ? cr.sy : 1;
    panel(g, -cw / 2, -chh / 2, cw, chh, { r: 22, fill: PAL.surf2, stroke: c.accent ? rgba(PAL.accent, 0.5) : PAL.line });
    if (c.accent) glow(g, 0, 0, 340, PAL.accent, 0.07 * ss(seg(t, CHIP0(i), CHIP0(i) + 0.5)));
    if (sq > 0.5) {
      g.save(); g.globalAlpha *= clamp((sq - 0.5) * 2);
      text(g, c.yr, -cw / 2 + 34, -chh / 2 + 50, 19, 500, c.accent ? PAL.accent : PAL.mute, { fam: 'mono', track: 0.14 });
      text(g, c.co, -cw / 2 + 34, -4, 58, 600, PAL.text, { track: -0.03 });
      text(g, c.role, -cw / 2 + 34, 40, 24, 500, PAL.dim);
      text(g, c.stat, -cw / 2 + 34, chh / 2 - 34, 20, 500, c.accent ? PAL.text : PAL.dim, { fam: 'mono', track: 0.02 });
      g.restore();
    }
    if (cr && cr.glint > 0) { g.globalCompositeOperation = 'lighter'; g.fillStyle = `rgba(210,215,255,${0.55 * cr.glint})`; rr(g, -cw / 2, -3, cw, 6, 3); g.fill(); }
    g.restore();
  });
  // caption under the line
  const ca = ss(seg(t, CHIP0(3), CHIP0(3) + 0.3)) * (1 - seg(t, OUT0(0), OUT0(0) + 0.3));
  text(g, '7+ YEARS  ·  PAYMENTS  ·  FINTECH  ·  E-COMMERCE', CX, 810, 22, 500, PAL.dim, { align: 'center', fam: 'mono', track: 0.18, alpha: ca });
}

function sectionTag(g, t) {
  const a = ss(seg(t, HDR1, HDR1 + 0.3)) * (1 - seg(t, 14.0, 14.2));
  text(g, 'PAYPAL  ·  AI/ML PLATFORM', W - 96, 120, 20, 500, PAL.mute, { align: 'right', fam: 'mono', track: 0.16, alpha: a });
  const b = ss(seg(t, 14.6, 14.9)) * (1 - seg(t, 16.9, 17.2));
  text(g, 'CAREER', W - 96, 120, 20, 500, PAL.mute, { align: 'right', fam: 'mono', track: 0.16, alpha: b });
}

function endCard(g, t) {
  if (t < END0) return;
  // lone caret first, then it becomes the mark
  const s = 150, cxm = CX, cym = 380;
  const pi = seg(t, ICON0, ICON0 + 0.4), k = back(pi, 1.6);
  const c0 = t < ICON0 ? ss(seg(t, END0, END0 + 0.1)) * blink(t) : 0;
  if (c0 > 0) caret(g, cxm, cym, 96, { on: c0, wr: 1 / 11 });
  if (pi > 0) {
    g.save(); g.translate(cxm, cym); g.scale(k, k);
    panel(g, -s / 2, -s / 2, s, s, { r: s * 0.28, fill: PAL.surf3, shadow: 0.8, stroke: rgba(PAL.accent, 0.25) });
    caret(g, 0, 0, s * 0.52, { on: 1, glow: 0.8, wr: 1 / 6.5 });
    g.restore();
    glow(g, cxm, cym, 420, PAL.accent, 0.08 * ss(seg(t, ICON0, ICON0 + 0.8)));
  }
  // name reveals with the light
  const [nc, ng] = buf('endname', 1400, 170);
  ng.clearRect(0, 0, 1400, 170); ng.font = font(124, 600); ng.fillStyle = PAL.text; ng.textAlign = 'center'; ng.textBaseline = 'alphabetic';
  if (ng.letterSpacing !== undefined) ng.letterSpacing = `${-0.03 * 124}px`;
  ng.fillText(NAME, 700, 124);
  if (t >= NAME2) lightReveal(g, nc, CX - 700, 560, 1400, 170, seg(t, NAME2, NAME2 + 0.7), { base: 0, soft: 240, band: 80 });
  text(g, 'SENIOR PRODUCT MANAGER  ·  BENGALURU', CX, 748, 24, 500, PAL.dim, { align: 'center', fam: 'mono', track: 0.16, alpha: ss(seg(t, NAME2 + 0.45, NAME2 + 0.8)) });
  text(g, 'linkedin.com/in/prathamnawal', CX, 808, 28, 500, PAL.accent, { align: 'center', fam: 'mono', track: 0.04, alpha: ss(seg(t, URL0, URL0 + 0.3)) });
}

// ───────────────────────── film ─────────────────────────
export function renderFilm(g, t) {
  g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over'; g.shadowColor = 'transparent';
  bg(g, { lift: 1, cool: 1 });
  grid(g, { alpha: 1 });
  nameAndRole(g, t);
  sectionTag(g, t);
  TILES.forEach((_, i) => tile(g, i, t));
  chips(g, t);
  endCard(g, t);
  vignette(g, 0.5);
  // open from black / close into black on the very last frames
  const fade = Math.max(1 - seg(t, 0, 0.12), seg(t, DUR - 0.12, DUR));
  if (fade > 0) { g.fillStyle = `rgba(0,0,0,${fade})`; g.fillRect(0, 0, W, H); }
}
