"""Real-world geography: download, project onto the HOI4 map, rasterise.

Sources (fetched into tools/map/cache/, which git ignores):
  - Natural Earth 1:10m (public domain): countries, places, rivers, lakes,
    railways, coastline. https://www.naturalearthdata.com
  - geoBoundaries gbOpen (CC BY / public domain / ODbL, per country, see
    docs/CREDITS.md): first and second level administrative boundaries.
    https://www.geoboundaries.org

The projection from longitude/latitude to HOI4 pixels is a polynomial fitted
by tools/map/fit_projection.py against the HOI4 coastline.
"""
import json
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from core import MAP_W, MAP_H

ROOT = Path(__file__).resolve().parents[2]   # the repository
CACHE = ROOT / "tools/map/cache"
NE_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/{name}.geojson"
GB_URL = ("https://media.githubusercontent.com/media/wmgeolab/geoBoundaries/main/releaseData/"
          "gbOpen/{iso}/{level}/geoBoundaries-{iso}-{level}_simplified.geojson")


def _fetch(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        print(f"downloading {url}")
        urllib.request.urlretrieve(url, dest)
    return json.loads(dest.read_text(encoding="utf-8"))


def natural_earth(name):
    return _fetch(NE_URL.format(name=name), CACHE / "ne" / f"{name}.geojson")


def geoboundaries(iso, level):
    return _fetch(GB_URL.format(iso=iso, level=level), CACHE / "gb" / f"{iso}-{level}.geojson")


class Projection:
    def __init__(self, path):
        d = json.loads(Path(path).read_text())
        self.deg = d["degree"]
        self.cx = np.array(d["cx"])
        self.cy = np.array(d["cy"])
        self.region = d.get("region", [-180, 180, -90, 90])

    def _feats(self, lon, lat):
        lon = np.asarray(lon, float) / 100.0
        lat = np.asarray(lat, float) / 100.0
        cols = []
        for i in range(self.deg + 1):
            for j in range(self.deg + 1 - i):
                cols.append(lon ** i * lat ** j)
        return np.stack(cols, -1)

    def __call__(self, lon, lat):
        f = self._feats(lon, lat)
        return f @ self.cx, f @ self.cy


def polygons(feature):
    g = feature["geometry"]
    if g is None:
        return []
    return g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]


def rasterize(features, label_of, proj):
    """Paint polygons (largest first, so enclaves win) into an int32 label map."""
    img = Image.new("I", (MAP_W, MAP_H), 0)
    draw = ImageDraw.Draw(img)
    items = []
    for f in features:
        lab = label_of(f)
        for poly in polygons(f):
            ring = np.asarray(poly[0], float)
            if len(ring) < 3:
                continue
            x, y = proj(ring[:, 0], ring[:, 1])
            area = abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1))) / 2
            items.append((area, lab, list(zip(x.tolist(), y.tolist()))))
    for _, lab, pts in sorted(items, key=lambda t: -t[0]):
        draw.polygon(pts, fill=int(lab))
    return np.asarray(img, dtype=np.int32)
