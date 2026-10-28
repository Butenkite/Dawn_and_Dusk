"""Fit the longitude/latitude -> HOI4 pixel projection for a region.

HOI4's map is not a standard projection, so we fit one: a degree-4
polynomial, first roughly from vanilla victory-point cities matched to
Natural Earth places, then refined so the real coastline lands on the
HOI4 coastline (least squares on a distance field).

    python tools/map/fit_projection.py --vanilla "C:/Steam/steamapps/common/Hearts of Iron IV" \
        --region -25 60 -40 40 --out tools/data/map/projection_africa.json
"""
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
from scipy import ndimage, optimize

sys.path.insert(0, str(Path(__file__).resolve().parent))
import core  # noqa: E402
import geo  # noqa: E402

DEG = 4


def feats(lon, lat):
    lon = np.asarray(lon, float) / 100.0
    lat = np.asarray(lat, float) / 100.0
    return np.stack([lon ** i * lat ** j for i in range(DEG + 1) for j in range(DEG + 1 - i)], -1)


def norm(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower().strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vanilla", required=True)
    ap.add_argument("--region", nargs=4, type=float, default=[-25, 60, -40, 40],
                    metavar=("LON0", "LON1", "LAT0", "LAT1"))
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    van = Path(a.vanilla)
    defs = core.Definitions.load(van / "map/definition.csv")
    ids = core.load_province_ids(van / "map/provinces.bmp", defs)
    n = ids.max() + 1
    ys, xs = np.indices(ids.shape)
    cnt = np.bincount(ids.ravel(), minlength=n)
    cx = np.bincount(ids.ravel(), xs.ravel(), n) / np.maximum(cnt, 1)
    cy = np.bincount(ids.ravel(), ys.ravel(), n) / np.maximum(cnt, 1)

    # 1. rough fit: victory-point cities
    vp = {}
    for f in (van / "history/states").glob("*.txt"):
        t = core.strip_comments(core.read_text(f))
        for m in re.finditer(r"victory_points\s*=\s*\{\s*(\d+)", t):
            vp[int(m.group(1))] = True
    names = {}
    for f in (van / "localisation/english").glob("victory_points_l_english.yml"):
        for line in f.read_text(encoding="utf-8-sig").splitlines():
            m = re.match(r"\s*VICTORY_POINTS_(\d+):\d*\s*\"(.*)\"", line)
            if m:
                names[int(m.group(1))] = m.group(2)
    places = {}
    for f in geo.natural_earth("ne_10m_populated_places")["features"]:
        p = f["properties"]
        for k in ("NAME", "NAMEASCII", "NAME_EN"):
            if p.get(k):
                places.setdefault(norm(p[k]), []).append((p["LONGITUDE"], p["LATITUDE"], p.get("POP_MAX") or 0))
    pairs = []
    for pid in vp:
        c = places.get(norm(names.get(pid, "")))
        if c:
            lon, lat, _ = max(c, key=lambda t: t[2])
            pairs.append((lon, lat, cx[pid], cy[pid]))
    A = np.array(pairs)
    lo0, lo1, la0, la1 = a.region
    sel = (A[:, 0] > lo0 - 10) & (A[:, 0] < lo1 + 10) & (A[:, 1] > la0 - 10) & (A[:, 1] < la1 + 10)
    A = A[sel]
    mask = np.ones(len(A), bool)
    for _ in range(6):
        F = feats(A[mask, 0], A[mask, 1])
        px, *_ = np.linalg.lstsq(F, A[mask, 2], rcond=None)
        py, *_ = np.linalg.lstsq(F, A[mask, 3], rcond=None)
        Fa = feats(A[:, 0], A[:, 1])
        res = np.hypot(Fa @ px - A[:, 2], Fa @ py - A[:, 3])
        mask = res < max(np.percentile(res[mask], 90) * 2, 8)

    # 2. refine on the coastline
    ptype = np.array([defs.rows[i]["type"] if i in defs.rows else "" for i in range(n)])
    land = ptype[ids] == "land"
    sea = ptype[ids] == "sea"
    coast = land & ndimage.binary_dilation(sea)
    dt = ndimage.distance_transform_edt(~coast)
    pts = []
    for f in geo.natural_earth("ne_10m_coastline")["features"]:
        g = f["geometry"]
        for ln in (g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]):
            q = np.asarray(ln, float)
            for k in range(len(q) - 1):
                steps = max(1, int(np.hypot(*(q[k + 1] - q[k])) / 0.05))
                for t in np.linspace(0, 1, steps, endpoint=False):
                    pts.append(q[k] * (1 - t) + q[k + 1] * t)
    pts = np.array(pts)
    pts = pts[(pts[:, 0] > lo0) & (pts[:, 0] < lo1) & (pts[:, 1] > la0) & (pts[:, 1] < la1)][::3]
    F = feats(pts[:, 0], pts[:, 1])
    Fc = feats(A[mask, 0], A[mask, 1])
    k = F.shape[1]
    H, W = dt.shape

    def resid(p):
        x, y = F @ p[:k], F @ p[k:]
        v = ndimage.map_coordinates(dt, [np.clip(y, 0, H - 1), np.clip(x, 0, W - 1)], order=1)
        anchor = np.concatenate([Fc @ p[:k] - A[mask, 2], Fc @ p[k:] - A[mask, 3]]) * 0.15
        return np.concatenate([np.minimum(v, 40.0), anchor])

    sol = optimize.least_squares(resid, np.concatenate([px, py]), loss="soft_l1", f_scale=3.0, max_nfev=300)
    r = resid(sol.x)[:len(pts)]
    print(f"coastline distance: median {np.median(r):.2f} px, p90 {np.percentile(r, 90):.2f} px")
    Path(a.out).write_text(json.dumps(dict(
        note=("lon/lat -> HOI4 pixel (x right, y down from top). Polynomial of degree 4 in (lon/100, lat/100); "
              f"fitted by tools/map/fit_projection.py: median {np.median(r):.1f} px."),
        degree=DEG, region=a.region, cx=sol.x[:k].tolist(), cy=sol.x[k:].tolist()), indent=1))


if __name__ == "__main__":
    main()
