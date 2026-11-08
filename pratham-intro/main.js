import { renderFilm, DUR } from './film.js';
const g = document.getElementById('c').getContext('2d');
await Promise.all([500, 600, 700].flatMap(w => [`${w} 40px Inter`, `${w} 20px "DejaVu Sans Mono"`]).map(f => document.fonts.load(f)));
window.DUR = DUR;
const t0 = +(new URLSearchParams(location.search).get('t') ?? -1);
window.render = t => renderFilm(g, t);
window.READY = true;
