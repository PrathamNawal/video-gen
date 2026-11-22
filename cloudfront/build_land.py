"""Rasterise Natural Earth countries (world-atlas 110m TopoJSON, public domain) into an equirectangular land mask."""
import json, pathlib
from PIL import Image, ImageDraw

HERE = pathlib.Path(__file__).parent
topo = json.loads((HERE / "assets/data/countries-110m.json").read_text())
sx, sy = topo["transform"]["scale"]; tx, ty = topo["transform"]["translate"]
arcs = []
for arc in topo["arcs"]:
    x = y = 0; pts = []
    for dx, dy in arc:
        x += dx; y += dy; pts.append((x * sx + tx, y * sy + ty))
    arcs.append(pts)

def ring(idxs):
    out = []
    for i in idxs:
        a = arcs[i] if i >= 0 else arcs[~i][::-1]
        out.extend(a if not out else a[1:])
    return out

W, H = 4096, 2048
im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im)
def px(p): return ((p[0] + 180) / 360 * W, (90 - p[1]) / 180 * H)
for g in topo["objects"]["countries"]["geometries"]:
    if g.get("id") == "010" or g.get("properties", {}).get("name") == "Antarctica":
        continue
    polys = g["arcs"] if g["type"] == "MultiPolygon" else [g["arcs"]] if g["type"] == "Polygon" else []
    for poly in polys:
        for k, r in enumerate(poly):
            d.polygon([px(p) for p in ring(r)], fill=255 if k == 0 else 0)
out = HERE / "assets/prep"; out.mkdir(parents=True, exist_ok=True)
im.save(out / "land_mask.png")
print("land mask", im.size, "land fraction", round(sum(1 for v in im.resize((512, 256)).getdata() if v) / (512 * 256), 3))
