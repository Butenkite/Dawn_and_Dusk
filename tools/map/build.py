"""Rebuild one region of the HOI4 map from real geography.

    python tools/map/build.py tools/data/map/southern_africa.json \
        --vanilla "C:/Steam/steamapps/common/Hearts of Iron IV"

What it does, for the countries listed in the spec:
  1. takes every vanilla land province that lies mostly inside them
  2. redraws that area as new provinces built from real district
     boundaries (geoBoundaries), merged or split to a target size that
     follows population density, with metros as their own provinces
  3. groups provinces into states (hand-written groupings in the spec, or
     automatic splits of large first-level regions)
  4. writes provinces.bmp, definition.csv, history/states, strategic region
     membership, buildings.txt, unitstacks.txt, railways.txt,
     supply_nodes.txt and localisation into the mod

It reads the mod's current map files when they exist (so regions can be
built one after another) and vanilla's otherwise. Run tools/map/validate.py
afterwards; it catches the mistakes that crash the game.
"""
import argparse
import collections
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
import core  # noqa: E402
import geo  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RNG = np.random.default_rng(2000)

# Unit-stack slot types the game expects per land province (from vanilla).
STACK_BASE = [0, 1, 2, 3, 4, 5, 9, 10, 21, 22, 23, 24, 25, 26, 38]
STACK_COASTAL = [19, 20]
STATE_BUILDINGS = ["arms_factory"] * 6 + ["industrial_complex"] * 6 + [
    "air_base", "anti_air_building", "anti_air_building", "anti_air_building", "fuel_silo",
    "nuclear_reactor_spawn", "radar_station", "rocket_site_spawn", "stronghold_network",
    "synthetic_refinery"]
PROVINCE_BUILDINGS = ["bunker", "supply_node", "special_project_facility_spawn"]
COASTAL_BUILDINGS = ["coastal_bunker", "naval_base_spawn", "naval_headquarters",
                     "naval_supply_hub", "floating_harbor"]
CATEGORIES = [(150e3, "pastoral", 1), (400e3, "rural", 2), (800e3, "town", 4),
              (1.5e6, "large_town", 5), (3e6, "city", 6), (6e6, "large_city", 8),
              (1e12, "metropolis", 10)]
FOUR = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def log(*a):
    print(*a, flush=True)


# --------------------------------------------------------------------------
# geometry helpers
# --------------------------------------------------------------------------

def bbox(mask, pad=2):
    ys, xs = np.nonzero(mask)
    return (max(ys.min() - pad, 0), min(ys.max() + pad + 1, mask.shape[0]),
            max(xs.min() - pad, 0), min(xs.max() + pad + 1, mask.shape[1]))


def adjacency_pairs(lab):
    """Set of (a, b) label pairs that touch (4-neighbourhood), a < b."""
    pairs = set()
    for a, b in ((lab[:, :-1], lab[:, 1:]), (lab[:-1, :], lab[1:, :])):
        m = a != b
        for x, y in zip(a[m].ravel(), b[m].ravel()):
            pairs.add((min(x, y), max(x, y)))
    return pairs


def interior_point(mask):
    """The pixel deepest inside a mask (pole of inaccessibility)."""
    y0, y1, x0, x1 = bbox(mask)
    sub = mask[y0:y1, x0:x1]
    dt = ndimage.distance_transform_edt(sub)
    iy, ix = np.unravel_index(np.argmax(dt), dt.shape)
    return y0 + iy, x0 + ix


def geodesic_partition(mask, seeds, cost=None, iters=4):
    """Split a mask into len(seeds) contiguous parts (geodesic k-medoids)."""
    from skimage.graph import MCP_Geometric
    y0, y1, x0, x1 = bbox(mask)
    sub = mask[y0:y1, x0:x1]
    c = np.where(sub, 1.0 if cost is None else cost[y0:y1, x0:x1], np.inf)
    pts = [(y - y0, x - x0) for y, x in seeds]
    lab = None
    for _ in range(iters):
        dist = []
        for p in pts:
            m = MCP_Geometric(c)
            d, _ = m.find_costs([p])
            dist.append(d)
        dist = np.stack(dist)
        lab = np.argmin(dist, 0)
        lab[~sub] = -1
        new = []
        for k in range(len(pts)):
            ys, xs = np.nonzero(lab == k)
            if len(ys) == 0:
                new.append(pts[k])
                continue
            cy, cx = ys.mean(), xs.mean()
            j = np.argmin((ys - cy) ** 2 + (xs - cx) ** 2)
            new.append((ys[j], xs[j]))
        if new == pts:
            break
        pts = new
    out = np.full(mask.shape, -1, np.int32)
    out[y0:y1, x0:x1] = lab
    return out


def farthest_points(mask, k, first=None):
    ys, xs = np.nonzero(mask)
    pts = np.stack([ys, xs], 1)
    chosen = [first] if first is not None else [tuple(pts[len(pts) // 2])]
    d = np.full(len(pts), np.inf)
    while len(chosen) < k:
        cy, cx = chosen[-1]
        d = np.minimum(d, (pts[:, 0] - cy) ** 2 + (pts[:, 1] - cx) ** 2)
        chosen.append(tuple(pts[np.argmax(d)]))
    return chosen


# --------------------------------------------------------------------------
# the build
# --------------------------------------------------------------------------

class Builder:
    def __init__(self, spec_path, vanilla, mod):
        self.spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
        self.vanilla = Path(vanilla)
        self.mod = Path(mod)
        self.proj = geo.Projection(ROOT / self.spec["projection"])
        self.registry_path = self.mod / "tools/data/map/built.json"
        self.registry = json.loads(self.registry_path.read_text()) if self.registry_path.exists() else {}

    # ---- inputs -----------------------------------------------------------

    def load_map(self):
        log("loading map")
        mf = lambda rel: core.map_file(self.vanilla, self.mod, rel)  # noqa: E731
        self.defs = core.Definitions.load(mf("map/definition.csv"))
        self.ids = core.load_province_ids(mf("map/provinces.bmp"), self.defs)
        self.states = core.load_states(self.vanilla, self.mod)
        self.regions = core.load_regions(self.vanilla, self.mod)
        self.img_height = core.Image.open(mf("map/heightmap.bmp"))
        self.img_rivers = core.Image.open(mf("map/rivers.bmp"))
        self.img_terrain = core.Image.open(mf("map/terrain.bmp"))
        self.heightmap = np.array(self.img_height)
        self.rivers = np.array(self.img_rivers)
        self.terrain_px = np.array(self.img_terrain)
        self.buildings = core.load_lines(mf("map/buildings.txt"))
        self.unitstacks = core.load_lines(mf("map/unitstacks.txt"))
        self.railways = core.load_lines(mf("map/railways.txt"))
        self.supply_nodes = core.load_lines(mf("map/supply_nodes.txt"))
        self.adjacencies = core.load_lines(mf("map/adjacencies.csv"))
        n = self.ids.max() + 1
        self.ptype = np.array([self.defs.rows[i]["type"] if i in self.defs.rows else "" for i in range(n)])
        self.pterrain = np.array([self.defs.rows[i]["terrain"] if i in self.defs.rows else "" for i in range(n)])

    def load_geo(self):
        log("loading geography")
        self.countries = self.spec["countries"]
        self.adm1_names, self.unit_names = [], []
        f1, f2 = [], []
        for iso, c in self.countries.items():
            for f in geo.geoboundaries(iso, "ADM1")["features"]:
                f["properties"]["_l"] = len(self.adm1_names) + 1
                self.adm1_names.append((iso, f["properties"]["shapeName"]))
                f1.append(f)
            for f in geo.geoboundaries(iso, c.get("unit_level", "ADM2"))["features"]:
                f["properties"]["_l"] = len(self.unit_names) + 1
                self.unit_names.append((iso, f["properties"]["shapeName"]))
                f2.append(f)
        lab = lambda f: f["properties"]["_l"]  # noqa: E731
        self.r_adm1 = geo.rasterize(f1, lab, self.proj)
        self.r_unit = geo.rasterize(f2, lab, self.proj)
        # second-level (districts) only where states are grouped from them
        self.r_adm2, self.adm2_names = None, []
        f3 = []
        for iso, c in self.countries.items():
            if c.get("unit_level", "ADM2") != "ADM2" and iso in self.spec.get("states", {}):
                for f in geo.geoboundaries(iso, "ADM2")["features"]:
                    f["properties"]["_l"] = len(self.adm2_names) + 1
                    self.adm2_names.append((iso, f["properties"]["shapeName"]))
                    f3.append(f)
        if f3:
            self.r_adm2 = geo.rasterize(f3, lab, self.proj)
        want = set(self.spec.get("lakes", []))
        lakes = [f for f in geo.natural_earth("ne_10m_lakes")["features"] if f["properties"].get("name") in want]
        self.lake_names = [f["properties"]["name"] for f in lakes]
        missing = want - set(self.lake_names)
        if missing:
            raise SystemExit(f"spec: lakes not found in Natural Earth: {missing}")
        for i, f in enumerate(lakes, start=1):
            f["properties"]["_l"] = i
        self.r_lakes = geo.rasterize(lakes, lab, self.proj) if lakes else np.zeros_like(self.r_adm1)
        self.places = []
        for f in geo.natural_earth("ne_10m_populated_places")["features"]:
            p = f["properties"]
            x, y = self.proj(p["LONGITUDE"], p["LATITUDE"])
            self.places.append(dict(name=p["NAME"], x=float(x), y=float(y),
                                    pop=float(p.get("POP_MAX") or 0), a3=p.get("ADM0_A3")))

    # ---- region -----------------------------------------------------------

    def select_region(self):
        built = {p for name, r in self.registry.items() if name != self.spec["name"] for p in r["provinces"]}
        n = len(self.ptype)
        cover = np.bincount(self.ids[self.r_adm1 > 0], minlength=n)
        total = np.bincount(self.ids.ravel(), minlength=n)
        sel = (self.ptype == "land") & (cover > 0.5 * total)
        for p in built:
            sel[p] = False
        self.freed = np.nonzero(sel)[0].tolist()
        self.R = sel[self.ids]
        # new reservoirs (built after 1936) become lake provinces
        self.lake_mask = (self.r_lakes > 0) & self.R
        cc, k = ndimage.label(self.lake_mask)
        for j in range(1, k + 1):
            if (cc == j).sum() < 15:
                self.lake_mask[cc == j] = False
        self.lake_labels = np.where(self.lake_mask, self.r_lakes, 0)
        self.R &= ~self.lake_mask
        log(f"region: {len(self.freed)} old provinces, {self.R.sum()} pixels")

        def fill(r):
            _, (iy, ix) = ndimage.distance_transform_edt(r == 0, return_indices=True)
            out = r[iy, ix]
            out[~self.R] = 0
            return out
        self.f_adm1 = fill(self.r_adm1)
        self.f_unit = fill(self.r_unit)
        self.f_adm2 = fill(self.r_adm2) if self.r_adm2 is not None else None
        self.crop()

    def crop(self):
        """Work in a window around the region from here on (memory)."""
        y0, y1, x0, x1 = bbox(self.R, pad=24)
        self.off = (y0, x0)
        self.h, self.w = y1 - y0, x1 - x0
        self.ids_full = self.ids
        self.ids = self.ids_full[y0:y1, x0:x1]          # a view: edits reach the full map
        self.heightmap_full, self.rivers_full, self.terrain_full = self.heightmap, self.rivers, self.terrain_px
        for name in ("R", "f_adm1", "f_unit", "f_adm2", "heightmap", "rivers", "terrain_px",
                     "lake_mask", "lake_labels"):
            a = getattr(self, name)
            if a is not None:
                setattr(self, name, np.ascontiguousarray(a[y0:y1, x0:x1]))
        del self.r_adm1, self.r_unit, self.r_adm2, self.r_lakes
        for pl in self.places:
            pl["x"] -= x0
            pl["y"] -= y0

    def projw(self, lon, lat):
        x, y = self.proj(lon, lat)
        return x - self.off[1], y - self.off[0]

    def inside(self, y, x):
        return 0 <= y < self.h and 0 <= x < self.w

    # ---- population -------------------------------------------------------

    def population(self):
        """A population raster: each ADM1's 2000 total spread over its pixels,
        45% evenly and 55% towards Natural Earth towns."""
        log("population")
        pop = np.zeros(self.ids.shape, np.float64)
        weights = np.zeros(self.ids.shape, np.float64)
        for pl in self.places:
            x, y = int(round(pl["x"])), int(round(pl["y"]))
            if self.inside(y, x) and self.R[y, x] and pl["pop"] > 0:
                weights[y, x] += pl["pop"]
        weights = ndimage.gaussian_filter(weights, 2.0)
        for li, (iso, name) in enumerate(self.adm1_names, start=1):
            total = self.countries[iso]["pop2000"].get(name)
            m = self.f_adm1 == li
            if not m.any():
                continue
            if total is None:
                raise SystemExit(f"spec: no pop2000 for {iso} / {name}")
            w = weights[m]
            even = 0.45 * total / m.sum()
            towns = 0.55 * total * (w / w.sum() if w.sum() > 0 else np.full(w.shape, 1 / m.sum()))
            pop[m] = even + towns
        self.pop = pop

    # ---- states -----------------------------------------------------------

    def plan_states(self):
        """Returns list of dict(key, name, tag, iso, mask)."""
        log("planning states")
        plans = []
        curated = self.spec.get("states", {})
        assigned = np.zeros(self.ids.shape, bool)
        for iso, cfg in self.countries.items():
            tag = cfg["tag"]
            cmask = np.isin(self.f_adm1, [i + 1 for i, (c, _) in enumerate(self.adm1_names) if c == iso])
            if iso in curated:
                names = self.adm2_names if self.f_adm2 is not None else self.unit_names
                rast = self.f_adm2 if self.f_adm2 is not None else self.f_unit
                lookup = collections.defaultdict(list)
                for i, (c, n) in enumerate(names, start=1):
                    if c == iso:
                        lookup[n].append(i)
                for st in curated[iso]:
                    labs = []
                    for d in st["districts"]:
                        if d not in lookup:
                            raise SystemExit(f"spec: unknown district {iso} / {d}")
                        labs += lookup[d]
                    m = np.isin(rast, labs) & cmask & ~assigned
                    assigned |= m
                    plans.append(dict(key=st["key"], name=st["name"], tag=tag, iso=iso, mask=m,
                                      metros=st.get("metros", {})))
                left = cmask & ~assigned
                if left.sum() > 20:
                    log(f"  WARNING {iso}: {left.sum()} px not in any curated state")
            else:
                plans += self.auto_states(iso, tag, cfg)
        self.plans = plans

    def auto_states(self, iso, tag, cfg):
        """One state per first-level region, large ones split around their
        biggest towns. cfg["groups"] merges several regions into one state."""
        out = []
        max_px = cfg.get("state_max_px", 2200)
        units = []
        grouped = set()
        for gname, members in cfg.get("groups", {}).items():
            labs = [li for li, (c, n) in enumerate(self.adm1_names, start=1) if c == iso and n in members]
            missing = set(members) - {self.adm1_names[li - 1][1] for li in labs}
            if missing:
                raise SystemExit(f"spec: unknown regions in group {gname}: {missing}")
            grouped.update(members)
            units.append((gname, np.isin(self.f_adm1, labs)))
        for li, (c, name) in enumerate(self.adm1_names, start=1):
            if c == iso and name not in grouped:
                units.append((name, self.f_adm1 == li))
        for name, m in units:
            if m.sum() == 0:
                continue
            area = m.sum()
            pop = self.pop[m].sum()
            k = max(1, math.ceil(area / max_px))
            if pop > 2.5e6 and area > 0.5 * max_px:     # big and crowded: one more
                k += 1
            k = min(k, 4)
            k = cfg.get("split", {}).get(name, k)
            base = cfg.get("names", {}).get(name, name)
            if k == 1:
                out.append(dict(key=f"{iso}_{name}", name=base, tag=tag, iso=iso, mask=m, metros={}))
                continue
            seeds = self.town_seeds(m, k, iso)
            part = geodesic_partition(m, seeds, iters=6)
            for j in range(k):
                pm = part == j
                town = self.largest_town(pm, iso)
                nm = cfg.get("part_names", {}).get(f"{name}/{town}", town or f"{base} {j + 1}")
                out.append(dict(key=f"{iso}_{name}_{j}", name=nm, tag=tag, iso=iso, mask=pm, metros={}))
        return out

    def town_seeds(self, mask, k, iso=None):
        towns = sorted((p for p in self.places if self.in_mask(mask, p) and (iso is None or p["a3"] == iso)),
                       key=lambda p: -p["pop"])
        seeds = []
        for t in towns:
            y, x = int(round(t["y"])), int(round(t["x"]))
            if all((y - a) ** 2 + (x - b) ** 2 > 400 for a, b in seeds):
                seeds.append((y, x))
            if len(seeds) == k:
                break
        if len(seeds) < k:
            seeds = farthest_points(mask, k, seeds[0] if seeds else None)[:k]
        return seeds

    @staticmethod
    def in_mask(mask, p):
        x, y = int(round(p["x"])), int(round(p["y"]))
        return 0 <= y < mask.shape[0] and 0 <= x < mask.shape[1] and mask[y, x]

    def largest_town(self, mask, iso=None):
        best = max((p for p in self.places if self.in_mask(mask, p) and (iso is None or p["a3"] == iso)),
                   key=lambda p: p["pop"], default=None)
        return best["name"] if best else None

    # ---- provinces --------------------------------------------------------

    def target_size(self, plan):
        m = plan["mask"]
        dens = self.pop[m].sum() / max(m.sum(), 1)
        s = self.spec["province_size"]
        return float(np.clip(s["base"] * (dens / s["reference_density"]) ** -s["exponent"], s["min"], s["max"]))

    def build_provinces(self):
        log("building provinces")
        cost = 1.0 + (self.rivers < 254).astype(float) * 0  # rivers.bmp: 254/255 = land/water, below = river
        river = (self.rivers < 254) & self.R
        cost = np.where(river, 6.0, 1.0)
        noise = ndimage.gaussian_filter(RNG.random(self.ids.shape), 6)
        noise = (noise - noise.min()) / (noise.max() - noise.min())
        cost = cost * (0.7 + 0.6 * noise)
        self.cost = cost
        self.provs = []  # dict(mask, plan_index, kind, name)
        cities = self.spec.get("cities", [])
        for pi, plan in enumerate(self.plans):
            m = plan["mask"].copy()
            tsz = self.target_size(plan)
            # metros: named units, each its own province(s)
            for unit_name, n_split in plan.get("metros", {}).items():
                labs = [i for i, (c, n) in enumerate(self.unit_names, start=1) if c == plan["iso"] and n == unit_name]
                um = np.isin(self.f_unit, labs) & m
                if self.f_adm2 is not None and not um.any():
                    labs = [i for i, (c, n) in enumerate(self.adm2_names, start=1) if c == plan["iso"] and n == unit_name]
                    um = np.isin(self.f_adm2, labs) & m
                if not um.any():
                    log(f"  WARNING metro {unit_name} not found in {plan['name']}")
                    continue
                m &= ~um
                parts = [um] if n_split <= 1 else self.split(um, n_split)
                for part in parts:
                    self.provs.append(dict(mask=part, plan=pi, kind="metro"))
            # city provinces carved around a point
            for c in cities:
                if not c.get("city_province"):
                    continue
                x, y = self.projw(c["lon"], c["lat"])
                yi, xi = int(round(float(y))), int(round(float(x)))
                if not self.inside(yi, xi) or not m[yi, xi]:
                    continue
                r = c.get("radius", 3.5)
                yy, xx = np.ogrid[:self.h, :self.w]
                disc = ((yy - yi) ** 2 + (xx - xi) ** 2 <= r * r) & m
                if disc.sum() >= 12:
                    m &= ~disc
                    self.provs.append(dict(mask=disc, plan=pi, kind="metro"))
            # the rest: merge small district units, split big ones
            for part in self.agglomerate(m, tsz):
                self.provs.append(dict(mask=part, plan=pi, kind="rural"))
        self.fix_fragments()
        for li in np.unique(self.lake_labels[self.lake_labels > 0]):
            cc, k = ndimage.label(self.lake_labels == li)
            for j in range(1, k + 1):
                self.provs.append(dict(mask=cc == j, plan=None, kind="lake", name=self.lake_names[li - 1]))
        log(f"  {len(self.provs)} provinces ({sum(p['kind'] == 'lake' for p in self.provs)} lakes)")

    def split(self, mask, k):
        seeds = farthest_points(mask, k)
        part = geodesic_partition(mask, seeds, self.cost, iters=6)
        return [part == j for j in range(k) if (part == j).any()]

    def agglomerate(self, mask, tsz):
        if not mask.any():
            return []
        y0, y1, x0, x1 = bbox(mask)
        sub = mask[y0:y1, x0:x1]
        units = np.where(sub, self.f_unit[y0:y1, x0:x1], 0)
        # split each unit into connected pieces so clusters stay contiguous
        lab = np.zeros(units.shape, np.int64)
        n = 0
        for u in np.unique(units[units > 0]):
            cc, k = ndimage.label(units == u)
            lab[cc > 0] = cc[cc > 0] + n
            n += k
        size = dict(zip(*np.unique(lab[lab > 0], return_counts=True)))
        parent = {u: u for u in size}

        def find(u):
            while parent[u] != u:
                parent[u] = parent[parent[u]]
                u = parent[u]
            return u
        border = collections.Counter()
        for a, b in ((lab[:, :-1], lab[:, 1:]), (lab[:-1, :], lab[1:, :])):
            mm = (a != b) & (a > 0) & (b > 0)
            for x, y in zip(a[mm].ravel(), b[mm].ravel()):
                border[(min(x, y), max(x, y))] += 1
        csize = dict(size)
        cborder = collections.defaultdict(collections.Counter)
        for (a, b), c in border.items():
            cborder[a][b] += c
            cborder[b][a] += c
        lo = 0.6 * tsz
        changed = True
        while changed:
            changed = False
            for u in sorted(csize, key=lambda u: csize[u]):
                if u not in csize or csize[u] >= lo:
                    continue
                nbrs = cborder[u]
                if not nbrs:
                    continue
                # prefer a long shared border and a small partner
                v = max(nbrs, key=lambda v: nbrs[v] / (csize[v] + csize[u]) ** 0.5)
                if csize[u] + csize[v] > 1.8 * tsz and csize[u] > 0.3 * tsz:
                    continue
                parent[u] = v
                csize[v] += csize.pop(u)
                for w, c in cborder.pop(u).items():
                    if w == v:
                        cborder[v].pop(u, None)
                        continue
                    cborder[w].pop(u, None)
                    cborder[w][v] += c
                    cborder[v][w] += c
                changed = True
        roots = np.zeros(lab.max() + 1, np.int64)
        for u in size:
            roots[u] = find(u)
        clus = roots[lab]
        out = []
        for r in np.unique(clus[lab > 0]):
            cm = np.zeros(mask.shape, bool)
            cm[y0:y1, x0:x1] = clus == r
            k = int(round(cm.sum() / tsz))
            if k >= 2 and cm.sum() > 1.5 * tsz:
                out += self.split(cm, min(k, 12))
            else:
                out.append(cm)
        return out

    def fix_fragments(self):
        """Every province must be one connected piece of at least a few pixels."""
        lab = np.full(self.ids.shape, -1, np.int32)
        for i, p in enumerate(self.provs):
            lab[p["mask"]] = i
        keep = []
        for i, p in enumerate(self.provs):
            cc, k = ndimage.label(lab == i)
            if k == 0:
                continue
            sizes = ndimage.sum(np.ones_like(cc), cc, range(1, k + 1))
            main = int(np.argmax(sizes)) + 1
            for j in range(1, k + 1):
                if j == main:
                    continue
                frag = cc == j
                if sizes[j - 1] >= 30:          # a real island: its own province
                    self.provs.append(dict(mask=frag, plan=p["plan"], kind="rural"))
                    lab[frag] = len(self.provs) - 1
                    continue
                ring = ndimage.binary_dilation(frag) & ~frag & (lab >= 0)
                vals = lab[ring]
                lab[frag] = np.bincount(vals).argmax() if len(vals) else i
        # tiny provinces fold into a neighbour of the same state; tiny islets
        # with no land neighbour join the nearest province of their state
        for i, p in enumerate(self.provs):
            m = lab == i
            if 0 < m.sum() < 12:
                ring = ndimage.binary_dilation(m) & ~m & (lab >= 0)
                vals = [v for v in lab[ring] if self.provs[v]["plan"] == p["plan"]] or list(lab[ring])
                if vals:
                    lab[m] = collections.Counter(vals).most_common(1)[0][0]
                else:
                    same = np.isin(lab, [j for j, q in enumerate(self.provs) if q["plan"] == p["plan"] and j != i])
                    if same.any():
                        _, (iy, ix) = ndimage.distance_transform_edt(~same, return_indices=True)
                        ys, xs = np.nonzero(m)
                        lab[m] = lab[iy[ys[0], xs[0]], ix[ys[0], xs[0]]]
        for i, p in enumerate(self.provs):
            p["mask"] = lab == i
            if p["mask"].any():
                keep.append(p)
        self.provs = keep

    # ---- ids, definitions, bitmap ------------------------------------------

    def assign_ids(self):
        log("assigning ids")
        free = sorted(self.freed)
        nxt = self.defs.max_id() + 1
        colors = core.new_colors(self.defs, len(self.provs), seed=len(self.provs))
        sea = self.ptype == "sea"
        old_ids = self.ids.copy()
        for i, p in enumerate(self.provs):
            pid = free.pop(0) if free else nxt
            if pid == nxt:
                nxt += 1
            p["id"] = pid
            self.ids[p["mask"]] = pid
        if free:
            raise SystemExit(f"{len(free)} old ids left unused; the map would have id gaps")
        n = self.ids.max() + 1
        ptype = np.concatenate([self.ptype, np.full(max(0, n - len(self.ptype)), "land")]).astype(object)
        for i, p in enumerate(self.provs):
            m = p["mask"]
            olds = old_ids[m]
            terr = collections.Counter(t for t in self.pterrain[olds] if t not in ("", "unknown", "lakes"))
            terrain = "urban" if p["kind"] == "metro" else (terr.most_common(1)[0][0] if terr else "plains")
            ring = ndimage.binary_dilation(m) & ~m
            coastal = bool(sea[np.clip(old_ids[ring], 0, len(sea) - 1)].any())
            kind = "land"
            if p["kind"] == "lake":
                kind, terrain, coastal = "lake", "lakes", False
            p["coastal"] = coastal
            p["terrain"] = terrain
            self.defs.rows[p["id"]] = dict(id=p["id"], rgb=colors[i], type=kind, coastal=coastal,
                                           terrain=terrain, continent=core.continent_index(self.spec["continent"]))
            p["old"] = collections.Counter(olds.tolist())
        for p in self.provs:
            ptype[p["id"]] = "lake" if p["kind"] == "lake" else "land"
        self.ptype = np.array(ptype, dtype=str)
        self.land_provs = [p for p in self.provs if p["kind"] != "lake"]

    # ---- states -------------------------------------------------------------

    def write_states(self):
        log("writing states")
        freed = set(self.freed)
        touched = {sid for sid, s in self.states.items() if freed & set(s.provinces)}
        reuse = sorted(touched)
        partial = {}
        for sid in touched:
            rest = [p for p in self.states[sid].provinces if p not in freed]
            if rest:
                partial[sid] = rest
        reuse = [s for s in reuse if s not in partial]
        nxt = max(self.states) + 1
        self.state_ids = []
        for plan in self.plans:
            sid = reuse.pop(0) if reuse else nxt
            if sid == nxt:
                nxt += 1
            plan["id"] = sid
            self.state_ids.append(sid)
        if reuse:
            raise SystemExit(f"{len(reuse)} old state ids unused; state ids would have gaps")
        for sid, rest in partial.items():
            s = self.states[sid]
            s.text = core.replace_block_ints(s.text, "provinces", rest)
            s.text = self.drop_province_refs(s.text, set(rest))
            self.write_state_file(s.path.name, s.text)
            log(f"  trimmed partial state {sid}: {len(rest)} provinces left")
        by_plan = collections.defaultdict(list)
        for p in self.land_provs:
            by_plan[p["plan"]].append(p)
        self.capitals = {}
        econ = self.spec.get("economy", {})
        city_vps = self.city_victory_points()
        for pi, plan in enumerate(self.plans):
            provs = by_plan[pi]
            pop = float(sum(self.pop[p["mask"]].sum() for p in provs))
            plan["pop"] = pop
            plan["provinces"] = [p["id"] for p in provs]
        self.distribute_factories()
        loc = {}
        for pi, plan in enumerate(self.plans):
            provs = by_plan[pi]
            pop = plan["pop"]
            slots_needed = plan["civ"] + plan["mil"] + plan["dock"]
            cat = next(c for c in CATEGORIES if pop < c[0])
            ci = CATEGORIES.index(cat)
            while CATEGORIES[ci][2] < slots_needed and ci < len(CATEGORIES) - 1:
                ci += 1
            category = CATEGORIES[ci][1]
            vps = city_vps.get(pi, [])
            if not vps:
                big = max(provs, key=lambda p: self.pop[p["mask"]].sum())
                town = self.largest_town(big["mask"], plan["iso"]) or plan["name"]
                vps = [(big["id"], 1, town)]
            cfg = self.countries[plan["iso"]]
            infra = cfg.get("infrastructure", 2) + (1 if pop / max(sum(p["mask"].sum() for p in provs), 1) > 4000 else 0)
            infra = int(min(infra, 5))
            res = {k: v for k, v in self.spec.get("resources", {}).get(plan["key"], {}).items()}
            lines = [
                "state={",
                f"\tid={plan['id']}",
                f"\tname=\"STATE_{plan['id']}\" # {plan['name']}",
                f"\tmanpower = {int(pop)}",
                f"\tstate_category = {category}",
                "",
            ]
            if res:
                lines.append("\tresources={")
                lines += [f"\t\t{k}={v}" for k, v in res.items()]
                lines += ["\t}", ""]
            lines += ["\thistory={", f"\t\towner = {plan['tag']}", "\t\tbuildings = {",
                      f"\t\t\tinfrastructure = {infra}"]
            if plan["civ"]:
                lines.append(f"\t\t\tindustrial_complex = {plan['civ']}")
            if plan["mil"]:
                lines.append(f"\t\t\tarms_factory = {plan['mil']}")
            if plan["dock"]:
                lines.append(f"\t\t\tdockyard = {plan['dock']}")
            if plan.get("air"):
                lines.append(f"\t\t\tair_base = {plan['air']}")
            for pid, lvl in plan.get("naval", []):
                lines.append(f"\t\t\t{pid} = {{ naval_base = {lvl} }}")
            lines.append("\t\t}")
            lines.append("\t\tvictory_points = {")
            lines += [f"\t\t\t{pid} {v}" for pid, v, _ in vps]
            lines.append("\t\t}")
            lines += [f"\t\tadd_core_of = {plan['tag']}", "\t}", ""]
            lines.append("\tprovinces={")
            ids = sorted(plan["provinces"])
            for i in range(0, len(ids), 20):
                lines.append("\t\t" + " ".join(map(str, ids[i:i + 20])) + " ")
            lines += ["\t}", "", "\tlocal_supplies=0.0", "}", ""]
            fname = (self.states[plan["id"]].path.name if plan["id"] in self.states
                     else f"{plan['id']}-{re.sub(r'[^A-Za-z0-9 ]', '', plan['name'])}.txt")
            self.write_state_file(fname, "\n".join(lines))
            loc[f"STATE_{plan['id']}"] = plan["name"]
            for pid, _, name in vps:
                loc[f"VICTORY_POINTS_{pid}"] = name
            plan["vps"] = vps
        self.loc = loc

    @staticmethod
    def drop_province_refs(text, keep):
        """Remove victory points and province buildings for provinces a state lost."""
        def vp(m):
            nums = core.strip_comments(m.group(1)).split()
            pairs = [(nums[i], nums[i + 1]) for i in range(0, len(nums) - 1, 2) if int(nums[i]) in keep]
            return "victory_points = { " + " ".join(f"{a} {b}" for a, b in pairs) + " }" if pairs else ""
        text = re.sub(r"victory_points\s*=\s*\{([^}]*)\}", vp, text)
        text = re.sub(r"\b(\d+)\s*=\s*\{[^{}]*\}",
                      lambda m: m.group(0) if int(m.group(1)) in keep else "", text)
        return text

    def write_state_file(self, name, text):
        d = self.mod / "history/states"
        d.mkdir(parents=True, exist_ok=True)
        (d / name).write_text(text, encoding="utf-8", newline="\n")

    def city_victory_points(self):
        out = collections.defaultdict(list)
        lab = np.full(self.ids.shape, -1, np.int32)
        for i, p in enumerate(self.provs):
            if p["kind"] != "lake":
                lab[p["mask"]] = i
        for c in self.spec.get("cities", []):
            x, y = self.projw(c["lon"], c["lat"])
            yi, xi = int(round(float(y))), int(round(float(x)))
            i = lab[yi, xi] if self.inside(yi, xi) else -1
            if i < 0:
                ring = lab[max(yi - 3, 0):yi + 4, max(xi - 3, 0):xi + 4]
                vals = ring[ring >= 0]
                if not len(vals):
                    log(f"  WARNING city {c['name']} is outside the region")
                    continue
                i = np.bincount(vals).argmax()
            p = self.provs[i]
            if any(pid == p["id"] for pid, _, _ in out[p["plan"]]):
                continue
            out[p["plan"]].append((p["id"], c["vp"], c["name"]))
            if c.get("capital"):
                self.capitals[self.plans[p["plan"]]["tag"]] = p["plan"]
            if c.get("port"):
                port = p
                if not p["coastal"]:   # a carved city province can be inland: use the nearest coast
                    coast = [q for q in self.land_provs if q["plan"] == p["plan"] and q["coastal"]]
                    if coast:
                        cy, cx = np.argwhere(p["mask"]).mean(0)
                        port = min(coast, key=lambda q: ((np.argwhere(q["mask"]).mean(0) - (cy, cx)) ** 2).sum())
                if port["coastal"]:
                    self.plans[p["plan"]].setdefault("naval", []).append((port["id"], c["port"]))
            if c.get("air"):
                self.plans[p["plan"]]["air"] = c["air"]
        return out

    def distribute_factories(self):
        for plan in self.plans:
            plan.update(civ=0, mil=0, dock=0)
        for iso, cfg in self.countries.items():
            tot = cfg.get("factories", {})
            plans = [p for p in self.plans if p["iso"] == iso]
            if not plans:
                continue
            w = np.array([p["pop"] ** 1.3 for p in plans])
            for kind in ("civ", "mil", "dock"):
                n = tot.get(kind, 0)
                if not n:
                    continue
                cand = [i for i, p in enumerate(plans) if kind != "dock" or p.get("naval")]
                if not cand:
                    continue
                ww = w[cand] / w[cand].sum()
                alloc = np.floor(ww * n).astype(int)
                for j in np.argsort(-(ww * n - alloc))[: n - alloc.sum()]:
                    alloc[j] += 1
                for j, a in zip(cand, alloc):
                    plans[j][kind] += int(a)

    # ---- strategic regions -------------------------------------------------

    def write_regions(self):
        log("strategic regions")
        region_of = {}
        for rid, r in self.regions.items():
            for p in r.provinces:
                region_of[p] = rid
        freed = set(self.freed)
        changed = set()
        for rid, r in self.regions.items():
            if freed & set(r.provinces):
                r.provinces = [p for p in r.provinces if p not in freed]
                changed.add(rid)
        for p in self.provs:
            votes = collections.Counter()
            for old, n in p["old"].items():
                if old in region_of:
                    votes[region_of[old]] += n
            rid = votes.most_common(1)[0][0]
            self.regions[rid].provinces.append(p["id"])
            changed.add(rid)
        d = self.mod / "map/strategicregions"
        d.mkdir(parents=True, exist_ok=True)
        for rid in changed:
            r = self.regions[rid]
            text = core.replace_block_ints(r.text, "provinces", sorted(r.provinces))
            (d / r.path.name).write_text(text, encoding="utf-8", newline="\n")

    # ---- positions ----------------------------------------------------------

    def height(self, y, x):
        return max(9.5, round(float(self.heightmap[y, x]) / 10.0, 2))

    def points_in(self, mask, k, spread=0.6):
        y0, y1, x0, x1 = bbox(mask)
        sub = mask[y0:y1, x0:x1]
        dt = ndimage.distance_transform_edt(sub)
        ys, xs = np.nonzero(dt >= max(1.0, dt.max() * (1 - spread)))
        idx = RNG.integers(0, len(ys), k)
        return [(y0 + ys[i], x0 + xs[i]) for i in idx]

    def pos(self, y, x):
        fy, fx = y + self.off[0], x + self.off[1]
        return f"{fx:.2f};{self.height(y, x):.2f};{core.MAP_H - 1 - fy:.2f}"

    def write_positions(self):
        log("positions")
        freed = set(self.freed)
        sids = set(self.state_ids)
        keep_b = [l for l in self.buildings if l.split(";")[0].isdigit() and int(l.split(";")[0]) not in sids]
        sea_ids = self.ptype == "sea"
        new_b = []
        by_plan = collections.defaultdict(list)
        for p in self.land_provs:
            by_plan[p["plan"]].append(p)
        for pi, plan in enumerate(self.plans):
            sid = plan["id"]
            smask = plan["mask"]
            core_prov = max(by_plan[pi], key=lambda p: self.pop[p["mask"]].sum())
            pts = self.points_in(core_prov["mask"], len(STATE_BUILDINGS) + 1, 0.8)
            for b, (y, x) in zip(STATE_BUILDINGS, pts):
                new_b.append(f"{sid};{b};{self.pos(y, x)};{RNG.uniform(-3.14, 3.14):.2f};0")
            coastal_any = False
            for p in by_plan[pi]:
                for b, (y, x) in zip(PROVINCE_BUILDINGS, self.points_in(p["mask"], len(PROVINCE_BUILDINGS))):
                    new_b.append(f"{sid};{b};{self.pos(y, x)};{RNG.uniform(-3.14, 3.14):.2f};0")
                if p["coastal"]:
                    m = p["mask"]
                    ring = ndimage.binary_dilation(m) & ~m
                    seas = [s for s in self.ids[ring] if s < len(sea_ids) and sea_ids[s]]
                    if not seas:
                        continue
                    sea = collections.Counter(seas).most_common(1)[0][0]
                    edge = m & ndimage.binary_dilation(self.ids == sea)
                    ys, xs = np.nonzero(edge)
                    for b in COASTAL_BUILDINGS:
                        j = RNG.integers(0, len(ys))
                        new_b.append(f"{sid};{b};{self.pos(ys[j], xs[j])};{RNG.uniform(-3.14, 3.14):.2f};{sea}")
                    coastal_any = True
            if coastal_any:
                y, x = self.points_in(core_prov["mask"], 1, 0.9)[0]
                new_b.append(f"{sid};dockyard;{self.pos(y, x)};{RNG.uniform(-3.14, 3.14):.2f};0")
        self.write_lines("map/buildings.txt", keep_b + new_b)

        new_ids = {p["id"] for p in self.provs}
        keep_u = [l for l in self.unitstacks if l.split(";")[0].isdigit() and int(l.split(";")[0]) not in new_ids]
        new_u = []
        for p in self.land_provs:
            types = list(STACK_BASE)
            size = p["mask"].sum()
            if size > 300:
                types += [6, 27]
            if size > 700:
                types += [7, 28]
            if p["coastal"]:
                types += STACK_COASTAL
            for t, (y, x) in zip(sorted(types), self.points_in(p["mask"], len(types), 0.7)):
                new_u.append(f"{p['id']};{t};{self.pos(y, x)};0.00;{RNG.uniform(0.2, 0.9):.2f}")
        self.write_lines("map/unitstacks.txt", keep_u + new_u)

    def write_lines(self, rel, lines):
        p = self.mod / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    # ---- railways and supply ----------------------------------------------

    def write_rails(self):
        log("railways")
        freed = set(self.freed)
        keep = []
        for l in self.railways:
            parts = l.split()
            if len(parts) < 3:
                continue
            level, provs = parts[0], [int(x) for x in parts[2:]]
            run = []
            for pr in provs + [None]:
                if pr is not None and pr not in freed:
                    run.append(pr)
                    continue
                if len(run) >= 2:
                    keep.append((int(level), run))
                run = []
        adj = adjacency_pairs(self.ids)
        nbr = collections.defaultdict(set)
        for a, b in adj:
            nbr[a].add(b)
            nbr[b].add(a)
        land = set(np.nonzero(self.ptype == "land")[0].tolist())
        new_ids = {p["id"] for p in self.land_provs}
        new = []
        rails = geo.natural_earth("ne_10m_railroads")["features"]
        y0, y1, x0, x1 = bbox(self.R, pad=20)
        for f in rails:
            g = f["geometry"]
            lines = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
            for ln in lines:
                a = np.asarray(ln, float)
                if len(a) < 2:
                    continue
                x, y = self.projw(a[:, 0], a[:, 1])
                if x.max() < x0 or x.min() > x1 or y.max() < y0 or y.min() > y1:
                    continue
                seq = []
                for k in range(len(x) - 1):
                    steps = int(max(abs(x[k + 1] - x[k]), abs(y[k + 1] - y[k]))) + 1
                    for t in np.linspace(0, 1, steps, endpoint=False):
                        xi = int(round(x[k] + (x[k + 1] - x[k]) * t))
                        yi = int(round(y[k] + (y[k + 1] - y[k]) * t))
                        if self.inside(yi, xi):
                            pid = int(self.ids[yi, xi])
                            if pid in land and (not seq or seq[-1] != pid):
                                seq.append(pid)
                if not any(p in new_ids for p in seq):
                    continue
                path = [seq[0]]
                for pid in seq[1:]:
                    if pid in nbr[path[-1]]:
                        path.append(pid)
                    else:
                        bridge = self.bfs(path[-1], pid, nbr, land, 6)
                        if bridge:
                            path += bridge[1:]
                        else:
                            if len(path) >= 2:
                                new.append(path)
                            path = [pid]
                if len(path) >= 2:
                    new.append(path)
        level = self.spec.get("rail_level", {})
        seen = set()
        out_lines = []
        for lvl, run in keep:
            out_lines.append(f"{lvl} {len(run)} " + " ".join(map(str, run)))
        owner_iso = {}
        for p in self.land_provs:
            owner_iso[p["id"]] = self.plans[p["plan"]]["iso"]
        for path in new:
            # drop repeated edges so overlapping rail features do not stack
            edges = [(min(a, b), max(a, b)) for a, b in zip(path, path[1:])]
            if all(e in seen for e in edges):
                continue
            seen.update(edges)
            isos = [owner_iso[p] for p in path if p in owner_iso]
            lvl = max((level.get(i, 1) for i in isos), default=1)
            out_lines.append(f"{lvl} {len(path)} " + " ".join(map(str, path)))
        self.write_lines("map/railways.txt", out_lines)
        log(f"  {len(new)} new rail runs")

        keep_s = [l for l in self.supply_nodes if l.split() and int(l.split()[1]) not in freed]
        for pi, plan in enumerate(self.plans):
            for pid, v, _ in plan.get("vps", []):
                if v >= self.spec.get("supply_hub_min_vp", 10):
                    keep_s.append(f"1 {pid}")
        self.write_lines("map/supply_nodes.txt", keep_s)

    @staticmethod
    def bfs(a, b, nbr, land, limit):
        prev = {a: None}
        frontier = [a]
        for _ in range(limit):
            nxt = []
            for u in frontier:
                for v in nbr[u]:
                    if v in prev or v not in land:
                        continue
                    prev[v] = u
                    if v == b:
                        path = [b]
                        while prev[path[-1]] is not None:
                            path.append(prev[path[-1]])
                        return path[::-1]
                    nxt.append(v)
            frontier = nxt
        return None

    # ---- the rest -----------------------------------------------------------

    def write_adjacencies(self):
        freed = set(self.freed)
        new_ids = {p["id"] for p in self.provs}
        out = []
        for l in self.adjacencies:
            parts = l.split(";")
            if parts[0].lstrip("-").isdigit() and len(parts) > 3:
                ids = [int(parts[0]), int(parts[1]), int(parts[3]) if parts[3].lstrip("-").isdigit() else -1]
                if any(i in freed for i in ids) and not any(i in new_ids for i in ids):
                    log(f"  dropping adjacency {l}")
                    continue
                if any(i in freed for i in ids):
                    log(f"  WARNING adjacency references a rebuilt province, check it: {l}")
            out.append(l)
        self.write_lines("map/adjacencies.csv", out)

    def write_map(self):
        log("writing provinces.bmp and definition.csv")
        d = self.mod / "map"
        d.mkdir(parents=True, exist_ok=True)
        core.save_province_bmp(self.ids_full, self.defs, d / "provinces.bmp")
        self.defs.save(d / "definition.csv")
        if any(p["kind"] == "lake" for p in self.provs):
            self.write_lakes(d)

    def write_lakes(self, d):
        """Lower the ground under new lakes below water level and clear rivers."""
        y0, x0 = self.off
        lake = np.zeros(self.heightmap_full.shape, bool)
        lake[y0:y0 + self.h, x0:x0 + self.w] = self.lake_mask
        hm = self.heightmap_full.copy()
        hm[lake] = np.minimum(hm[lake], 88)
        shore = ndimage.binary_dilation(lake, iterations=2) & ~lake
        hm[shore] = np.maximum(hm[shore], 96)     # keep the new shoreline dry
        rv = self.rivers_full.copy()
        rv[lake] = 254
        tr = self.terrain_full.copy()
        tr[lake] = 0
        for arr, img, name in ((hm, self.img_height, "heightmap.bmp"), (rv, self.img_rivers, "rivers.bmp"),
                               (tr, self.img_terrain, "terrain.bmp")):
            out = core.Image.fromarray(arr, img.mode)
            if img.mode == "P":
                out.putpalette(img.getpalette())
            out.save(d / name)
        log(f"  lakes: {lake.sum()} px written to heightmap, rivers, terrain")

    def write_loc(self):
        name = self.spec["name"]
        p = self.mod / f"localisation/english/replace/dnd_map_{name}_l_english.yml"
        p.parent.mkdir(parents=True, exist_ok=True)
        lines = ["l_english:", f" # GENERATED by tools/map/build.py from tools/data/map/{name}.json"]
        for k, v in sorted(self.loc.items()):
            lines.append(f' {k}: "{v}"')
        p.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")

    def write_outputs(self):
        caps = {}
        for tag, pi in self.capitals.items():
            caps[tag] = self.plans[pi]["id"]
        for iso, cfg in self.countries.items():
            if cfg["tag"] not in caps:
                own = [p for p in self.plans if p["iso"] == iso]
                caps[cfg["tag"]] = max(own, key=lambda p: p["pop"])["id"]
        self.registry[self.spec["name"]] = dict(
            provinces=sorted(p["id"] for p in self.provs),
            states=sorted(self.state_ids),
            capitals=caps,
            states_detail=[dict(id=p["id"], key=p["key"], name=p["name"], tag=p["tag"],
                                pop=int(p["pop"]), provinces=len(p["provinces"]),
                                civ=p["civ"], mil=p["mil"], dock=p["dock"]) for p in self.plans])
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.registry_path.write_text(json.dumps(self.registry, indent=1))
        log("capitals: " + ", ".join(f"{t}={s}" for t, s in caps.items()))

    def run(self):
        self.load_map()
        self.load_geo()
        self.select_region()
        self.population()
        self.plan_states()
        self.build_provinces()
        self.assign_ids()
        self.write_map()
        self.write_states()
        self.write_regions()
        self.write_positions()
        self.write_rails()
        self.write_adjacencies()
        self.write_loc()
        self.write_outputs()
        log("done")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--vanilla", required=True)
    ap.add_argument("--mod", default=str(ROOT))
    a = ap.parse_args()
    Builder(a.spec, a.vanilla, a.mod).run()


if __name__ == "__main__":
    main()
