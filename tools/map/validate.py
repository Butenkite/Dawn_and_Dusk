"""Check the mod's map for the mistakes that crash HOI4 or break it quietly.

    python tools/map/validate.py --vanilla "C:/Steam/steamapps/common/Hearts of Iron IV"

Reads the mod's map files where it has them and vanilla's otherwise, exactly
like the game. Exits non-zero if anything is an ERROR. Run it after
tools/map/build.py and before launching the game.
"""
import argparse
import collections
import re
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
import core  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


class Report:
    def __init__(self):
        self.errors, self.warnings = [], []

    def error(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)

    def show(self, limit=25):
        for kind, items in (("ERROR", self.errors), ("WARNING", self.warnings)):
            c = collections.Counter(m.split(":")[0] for m in items)
            for head, n in c.items():
                print(f"{kind}: {head} ({n})")
                for m in [m for m in items if m.split(":")[0] == head][:limit]:
                    print(f"    {m}")
        print(f"{len(self.errors)} errors, {len(self.warnings)} warnings")
        return not self.errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vanilla", required=True)
    ap.add_argument("--mod", default=str(ROOT))
    ap.add_argument("--all", dest="only_new", action="store_false",
                    help="also check vanilla's own positions and railways (vanilla has a few quirks)")
    a = ap.parse_args()
    van, mod = Path(a.vanilla), Path(a.mod)
    rep = Report()
    mf = lambda rel: core.map_file(van, mod, rel)  # noqa: E731

    defs = core.Definitions.load(mf("map/definition.csv"))
    ids = core.load_province_ids(mf("map/provinces.bmp"), defs)
    n = max(defs.rows) + 1
    print(f"{n - 1} provinces")

    # --- definitions ---------------------------------------------------------
    missing = [i for i in range(n) if i not in defs.rows]
    if missing:
        rep.error(f"definition.csv id gaps: {missing[:10]}")
    colors = collections.Counter(core.rgb_key(d["rgb"]) for d in defs.rows.values())
    dup = [k for k, c in colors.items() if c > 1]
    if dup:
        rep.error(f"duplicate province colours: {len(dup)}")
    present = np.bincount(ids.ravel(), minlength=n)
    for i in range(1, n):
        if present[i] == 0:
            rep.error(f"province not on the map: {i}")
    ptype = np.array([defs.rows[i]["type"] if i in defs.rows else "" for i in range(n)])

    registry_path = mod / "tools/data/map/built.json"
    import json
    registry = json.loads(registry_path.read_text()) if registry_path.exists() else {}
    new_provs = sorted({p for r in registry.values() for p in r["provinces"]})
    new_states = {s for r in registry.values() for s in r["states"]}

    # --- province shape ------------------------------------------------------
    sea = ptype == "sea"
    slices = ndimage.find_objects(ids)
    for pid in new_provs:
        sl = slices[pid - 1] if pid - 1 < len(slices) else None
        if sl is None:
            continue
        sl = tuple(slice(max(x.start - 1, 0), x.stop + 1) for x in sl)
        sub = ids[sl]
        m = sub == pid
        _, k = ndimage.label(m)
        if k > 1:
            rep.warn(f"province in several pieces: {pid} ({k})")
        if m.sum() < 8:
            rep.error(f"province too small: {pid} ({m.sum()} px)")
        if ptype[pid] == "land":
            ring = ndimage.binary_dilation(m) & ~m
            coastal = bool(sea[sub[ring]].any())
            if coastal != defs.rows[pid]["coastal"]:
                rep.error(f"coastal flag wrong: {pid}")

    # --- states --------------------------------------------------------------
    states = core.load_states(van, mod)
    sids = sorted(states)
    gaps = sorted(set(range(1, max(sids) + 1)) - set(sids))
    if gaps:
        rep.error(f"state id gaps: {gaps[:10]}")
    owner = {}
    prov_state = collections.defaultdict(list)
    for sid, s in states.items():
        if not s.provinces:
            rep.error(f"state without provinces: {sid}")
        for p in s.provinces:
            if p >= n:
                rep.error(f"state lists unknown province: state {sid} province {p}")
            else:
                prov_state[p].append(sid)
        m = re.search(r"owner\s*=\s*(\w+)", s.text)
        owner[sid] = m.group(1) if m else None
        clean = core.strip_comments(s.text)
        vp = re.search(r"victory_points\s*=\s*\{([^}]*)\}", clean)
        if vp:
            nums = vp.group(1).split()
            for p in nums[0::2]:
                if int(p) not in s.provinces:
                    rep.error(f"victory point outside its state: state {sid} province {p}")
        for pid in re.findall(r"\b(\d+)\s*=\s*\{\s*naval_base", clean):
            if int(pid) not in s.provinces:
                rep.error(f"naval base outside its state: state {sid} province {pid}")
            elif not defs.rows[int(pid)]["coastal"]:
                rep.error(f"naval base in an inland province: state {sid} province {pid}")
    for p, ss in prov_state.items():
        if len(ss) > 1:
            rep.error(f"province in several states: {p} {ss}")
    for pid in new_provs:
        if ptype[pid] == "land" and pid not in prov_state:
            rep.error(f"new land province in no state: {pid}")
    unowned_land = [i for i in range(1, n) if ptype[i] == "land" and i not in prov_state]
    if unowned_land:
        rep.warn(f"land provinces in no state (vanilla has some): {len(unowned_land)}")

    # --- strategic regions ---------------------------------------------------
    regions = core.load_regions(van, mod)
    prov_reg = collections.defaultdict(list)
    for rid, r in regions.items():
        for p in r.provinces:
            prov_reg[p].append(rid)
    for p, rr in prov_reg.items():
        if len(rr) > 1:
            rep.error(f"province in several strategic regions: {p} {rr}")
    for pid in new_provs:
        if pid not in prov_reg:
            rep.error(f"new province in no strategic region: {pid}")
    if len(regions) < 300:
        rep.warn(f"only {len(regions)} strategic region files available; region checks are partial")

    # --- positions -----------------------------------------------------------
    p2s = {p: ss[0] for p, ss in prov_state.items()}

    def at(x, z):
        xi, yi = int(round(float(x))), int(round(core.MAP_H - 1 - float(z)))
        if not (0 <= xi < core.MAP_W and 0 <= yi < core.MAP_H):
            return -1
        return int(ids[yi, xi])

    def near(pid, x, z, r=1):
        xi, yi = int(round(float(x))), int(round(core.MAP_H - 1 - float(z)))
        win = ids[max(yi - r, 0):yi + r + 1, max(xi - r, 0):xi + r + 1]
        return pid in win

    per_state = collections.defaultdict(collections.Counter)
    for line in core.load_lines(mf("map/buildings.txt")):
        f = line.split(";")
        if len(f) < 7 or not f[0].isdigit():
            continue
        sid, kind = int(f[0]), f[1]
        per_state[sid][kind] += 1
        if a.only_new and sid not in new_states:
            continue
        if sid not in states:
            rep.error(f"buildings.txt unknown state: {line}")
            continue
        pid = at(f[2], f[4])
        if pid < 0 or p2s.get(pid) != sid:
            if not any(p2s.get(q) == sid for q in np.unique(
                    ids[max(int(core.MAP_H - 1 - float(f[4])) - 1, 0):int(core.MAP_H - float(f[4])) + 1,
                        max(int(float(f[2])) - 1, 0):int(float(f[2])) + 2])):
                rep.error(f"building position outside its state: {line}")
        sea_id = int(f[6])
        if sea_id and (sea_id >= n or ptype[sea_id] != "sea"):
            rep.error(f"building faces a non-sea province: {line}")
    for sid in new_states:
        if per_state[sid]["industrial_complex"] == 0:
            rep.error(f"state has no building positions: {sid}")

    stacks = collections.defaultdict(set)
    for line in core.load_lines(mf("map/unitstacks.txt")):
        f = line.split(";")
        if len(f) < 7 or not f[0].isdigit():
            continue
        pid = int(f[0])
        stacks[pid].add(int(f[1]))
        if a.only_new and pid not in new_provs:
            continue
        if pid >= n:
            rep.error(f"unitstacks.txt unknown province: {line}")
        elif not near(pid, f[2], f[4]):
            rep.error(f"unit stack outside its province: {line}")
    for pid in new_provs:
        if ptype[pid] == "land" and 0 not in stacks[pid]:
            rep.error(f"province has no unit stack positions: {pid}")

    # --- railways and supply -------------------------------------------------
    pairs = set()
    for x, y in ((ids[:, :-1], ids[:, 1:]), (ids[:-1, :], ids[1:, :])):
        m = x != y
        e = np.stack([x[m], y[m]], 1)
        e.sort(1)
        pairs |= set(map(tuple, np.unique(e, axis=0)))
    for line in core.load_lines(mf("map/railways.txt")):
        f = line.split()
        if len(f) < 3:
            continue
        cnt, provs = int(f[1]), [int(x) for x in f[2:]]
        if a.only_new and not set(provs) & set(new_provs):
            continue
        if cnt != len(provs):
            rep.error(f"railway count wrong: {line[:60]}")
        for p, q in zip(provs, provs[1:]):
            if (min(p, q), max(p, q)) not in pairs:
                rep.error(f"railway joins provinces that do not touch: {p}-{q}")
            if ptype[p] != "land" or ptype[q] != "land":
                rep.error(f"railway through water: {p}-{q}")
    for line in core.load_lines(mf("map/supply_nodes.txt")):
        f = line.split()
        if len(f) == 2 and (int(f[1]) >= n or ptype[int(f[1])] != "land"):
            rep.error(f"supply node not on land: {line}")

    # --- adjacencies -----------------------------------------------------------
    for line in core.load_lines(mf("map/adjacencies.csv"))[1:]:
        f = line.split(";")
        if len(f) > 3 and f[0].lstrip("-").isdigit() and int(f[0]) >= 0:
            for v in (f[0], f[1]):
                if int(v) >= n:
                    rep.error(f"adjacency unknown province: {line}")

    # --- country capitals --------------------------------------------------------
    hist = mod / "history/countries"
    if hist.exists():
        for p in hist.glob("*.txt"):
            t = core.read_text(p)
            tag = p.name[:3]
            m = re.search(r"^capital\s*=\s*(\d+)", t, re.M)
            if m:
                cap = int(m.group(1))
                if cap not in states:
                    rep.error(f"capital is not a state: {tag} {cap}")
                elif owner.get(cap) != tag and tag in {owner.get(s) for s in new_states}:
                    rep.warn(f"capital owned by someone else: {tag} {cap} ({owner.get(cap)})")

    ok = rep.show()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
