#!/usr/bin/env python3
"""Starting armies for the armed standoffs of 1 January 2000.

Only the sides of the conflicts set up on the map have troops so far:

  - the Second Congo War (tools/data/map/central_africa.json, "control"):
    Kinshasa (COG) against RCD-Goma (RCD), the MLC (MLC) and RCD-ML (RML),
    already at war (declared in their country history files)
  - Sierra Leone (tools/data/map/west_africa.json): the government (SIE) and
    the RUF facing each other across the Lomé ceasefire line, at peace until
    content breaks it
  - the Second Sudanese Civil War (tools/data/map/east_africa.json): Khartoum
    (SUD) against the SPLA (SPL)
  - the Eritrean-Ethiopian War: ETH against ERI along the whole border, with
    Eritrea still holding Zalambessa

Divisions are placed from the built map, so re-run this after rebuilding a
region:

    python tools/countries/generate_armies.py --vanilla "C:/Steam/steamapps/common/Hearts of Iron IV"

Most divisions stand on the front line (provinces touching an enemy), spread
along it; a few guard each capital. Foreign armies that fought in these wars
are not on the map.
"""
import argparse
import collections
import json
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import REPO, MOD, DATA  # noqa: E402
sys.path.insert(0, str(REPO / "tools/map"))
import core  # noqa: E402

# tag: (army, template name, divisions, capital garrison, stockpile of rifles, language)
SIDES = {
    "COG": ("FAC", "Brigade d'infanterie", 16, 2, 2500, "fr"),
    "RCD": ("ANC", "Brigade d'infanterie", 12, 1, 1500, "fr"),
    "MLC": ("ALC", "Brigade d'infanterie", 7, 1, 1000, "fr"),
    "RML": ("APC", "Brigade d'infanterie", 4, 1, 600, "fr"),
    "SIE": ("SLA", "Infantry Brigade", 6, 2, 900, "en"),
    "RUF": ("RUF", "Combat Group", 6, 1, 900, "en"),
    "SUD": ("SAF", "Infantry Brigade", 18, 3, 2500, "en"),
    "SPL": ("SPLA", "Infantry Brigade", 12, 1, 1500, "en"),
    "ETH": ("ENDF", "Infantry Division", 24, 3, 4000, "en"),
    "ERI": ("EDF", "Infantry Division", 18, 2, 3000, "en"),
}
# Who each side expects to fight: its divisions stand along that line.
ENEMIES = {
    "COG": {"RCD", "MLC", "RML"},
    "RCD": {"COG", "RML"},
    "MLC": {"COG"},
    "RML": {"COG", "RCD"},
    "SIE": {"RUF"},
    "RUF": {"SIE"},
    "SUD": {"SPL"},
    "SPL": {"SUD"},
    "ETH": {"ERI"},
    "ERI": {"ETH"},
}
def ordinal(n, lang):
    if lang == "fr":
        return f"{n}re" if n == 1 else f"{n}e"
    return f"{n}" + ("th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th"))


def load(vanilla, mod):
    defs = core.Definitions.load(core.map_file(vanilla, mod, "map/definition.csv"))
    ids = core.load_province_ids(core.map_file(vanilla, mod, "map/provinces.bmp"), defs)
    owner, vps, state_of = {}, {}, {}
    for sid, s in core.load_states(vanilla, mod).items():
        t = core.strip_comments(s.text)
        m = re.search(r"\bowner\s*=\s*(\w+)", t)
        if not m:
            continue
        for p in s.provinces:
            owner[p] = m.group(1)
            state_of[p] = sid
        for occ, body in re.findall(r"\b([A-Z][A-Z0-9]{2})\s*=\s*\{([^{}]*set_province_controller[^{}]*)\}", t):
            for p in re.findall(r"set_province_controller\s*=\s*(\d+)", body):
                owner[int(p)] = occ          # who holds it on the day, for placing troops
        v = re.search(r"victory_points\s*=\s*\{([^}]*)\}", t)
        if v:
            nums = v.group(1).split()
            for i in range(0, len(nums) - 1, 2):
                vps[int(nums[i])] = float(nums[i + 1])
    return defs, ids, owner, vps, state_of


def adjacency(ids):
    nbr = collections.defaultdict(set)
    for a, b in ((ids[:, :-1], ids[:, 1:]), (ids[:-1, :], ids[1:, :])):
        m = a != b
        for x, y in set(zip(a[m].ravel().tolist(), b[m].ravel().tolist())):
            nbr[x].add(y)
            nbr[y].add(x)
    return nbr


def spread(cands, centre, k):
    """k provinces spread evenly along a front (farthest-point sampling)."""
    if not cands:
        return []
    pts = np.array([centre[c] for c in cands])
    chosen = [int(np.argmin(pts[:, 0]))]          # start at the northern end
    d = np.full(len(cands), np.inf)
    while len(chosen) < min(k, len(cands)):
        d = np.minimum(d, ((pts - pts[chosen[-1]]) ** 2).sum(1))
        chosen.append(int(np.argmax(d)))
    out = [cands[i] for i in chosen]
    while len(out) < k:                           # short front: double up
        out.append(out[len(out) % len(chosen)])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vanilla", required=True)
    ap.add_argument("--mod", default=str(MOD))
    a = ap.parse_args()
    defs, ids, owner, vps, state_of = load(a.vanilla, a.mod)
    land = {i for i, r in defs.rows.items() if r["type"] == "land"}
    nbr = adjacency(ids)
    present = np.unique(ids)
    ys, xs = np.indices(ids.shape)
    flat = ids.ravel()
    cnt = np.bincount(flat, minlength=present.max() + 1)
    cy = np.bincount(flat, ys.ravel(), minlength=len(cnt)) / np.maximum(cnt, 1)
    cx = np.bincount(flat, xs.ravel(), minlength=len(cnt)) / np.maximum(cnt, 1)
    centre = {int(p): (cy[p], cx[p]) for p in present}
    caps = {}
    for region in json.loads((DATA / "map/built.json").read_text()).values():
        caps.update(region.get("capitals", {}))

    out_dir = Path(a.mod) / "history/units"
    out_dir.mkdir(parents=True, exist_ok=True)
    for tag, (army, template, n, garrison, rifles, lang) in SIDES.items():
        mine = [p for p, t in owner.items() if t == tag and p in land]
        front = sorted(p for p in mine if any(owner.get(q) in ENEMIES[tag] for q in nbr[p]))
        cap_state = caps[tag]
        cap_provs = [p for p in mine if state_of[p] == cap_state]
        cap = max(cap_provs, key=lambda p: (vps.get(p, 0), p))
        spots = [cap] * garrison + spread(front, centre, n - garrison)
        lines = [
            f"# {tag}: order of battle on 1 January 2000",
            "# GENERATED by tools/countries/generate_armies.py - re-run after rebuilding the map.",
            "",
            "division_template = {",
            f"\tname = \"{template}\"",
            "\tregiments = {",
            "\t\tinfantry = { x = 0 y = 0 }",
            "\t\tinfantry = { x = 0 y = 1 }",
            "\t\tinfantry = { x = 0 y = 2 }",
            "\t}",
            "}",
            "",
            "units = {",
        ]
        for i, prov in enumerate(spots, start=1):
            lines += [
                "\tdivision = {",
                (f"\t\tname = \"{ordinal(i, lang)} Brigade {army}\"" if lang == "fr" else
                 f"\t\tname = \"{ordinal(i, lang)} {template.replace('Infantry ', '')} {army}\""),
                f"\t\tlocation = {prov}",
                f"\t\tdivision_template = \"{template}\"",
                "\t\tstart_experience_factor = 0.2",
                "\t\tstart_equipment_factor = 0.7",
                "\t}",
            ]
        lines += [
            "}",
            "",
            "instant_effect = {",
            "\tadd_equipment_to_stockpile = {",
            "\t\ttype = infantry_equipment_1",
            f"\t\tamount = {rifles}",
            f"\t\tproducer = {tag}",
            "\t}",
            "}",
            "",
        ]
        path = out_dir / f"{tag}_2000.txt"
        path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
        print(f"{tag}: {len(spots)} divisions, {len(front)} front provinces, capital province {cap}")


if __name__ == "__main__":
    main()
