"""Read and write HOI4 map data (provinces, definitions, states, regions, positions).

Everything works on the full 5632x2048 map in numpy arrays. Image row 0 is
the top of the map; HOI4 position files (buildings.txt, unitstacks.txt...)
measure their z coordinate from the bottom, so z = MAP_H - 1 - row.
"""
import csv
import re
from pathlib import Path

import numpy as np
from PIL import Image

MAP_W, MAP_H = 5632, 2048
CONTINENTS = ["europe", "north_america", "south_america", "australia", "africa", "asia", "middle_east"]


def continent_index(name):
    return CONTINENTS.index(name) + 1


# --- provinces --------------------------------------------------------------

def rgb_key(rgb):
    r, g, b = rgb
    return (int(r) << 16) | (int(g) << 8) | int(b)


class Definitions:
    """definition.csv: id;r;g;b;type;coastal;terrain;continent"""

    def __init__(self, rows):
        self.rows = rows  # dict id -> dict

    @classmethod
    def load(cls, path):
        rows = {}
        with open(path, encoding="latin-1") as f:
            for r in csv.reader(f, delimiter=";"):
                if not r or not r[0].strip().lstrip("-").isdigit():
                    continue
                pid = int(r[0])
                rows[pid] = dict(id=pid, rgb=(int(r[1]), int(r[2]), int(r[3])), type=r[4],
                                 coastal=r[5] == "true", terrain=r[6], continent=int(r[7]))
        return cls(rows)

    def save(self, path):
        with open(path, "w", encoding="latin-1", newline="") as f:
            for pid in sorted(self.rows):
                d = self.rows[pid]
                r, g, b = d["rgb"]
                f.write(f"{pid};{r};{g};{b};{d['type']};{'true' if d['coastal'] else 'false'};"
                        f"{d['terrain']};{d['continent']}\n")

    def max_id(self):
        return max(self.rows)

    def used_colors(self):
        return {rgb_key(d["rgb"]) for d in self.rows.values()}


def load_province_ids(bmp_path, defs):
    """Return an int32 array of province ids, one per pixel."""
    im = np.asarray(Image.open(bmp_path).convert("RGB"))
    key = (im[:, :, 0].astype(np.int64) << 16) | (im[:, :, 1].astype(np.int64) << 8) | im[:, :, 2]
    lut = {rgb_key(d["rgb"]): pid for pid, d in defs.rows.items()}
    uniq, inv = np.unique(key, return_inverse=True)
    ids = np.array([lut.get(int(u), -1) for u in uniq], dtype=np.int32)[inv].reshape(key.shape)
    if (ids < 0).any():
        raise ValueError(f"{(ids < 0).sum()} pixels have colours missing from definition.csv")
    return ids


def save_province_bmp(ids, defs, path):
    n = ids.max() + 1
    lut = np.zeros((n, 3), np.uint8)
    for pid, d in defs.rows.items():
        if pid < n:
            lut[pid] = d["rgb"]
    Image.fromarray(lut[ids], "RGB").save(path)


def save_8bit_bmp_like(arr, template, path):
    """Write an 8-bit bitmap with the template's exact header and palette
    (the game checks the palette of rivers.bmp and terrain.bmp), replacing
    only the pixels. Rows are stored bottom-up, padded to 4 bytes."""
    raw = Path(template).read_bytes()
    offset = int.from_bytes(raw[10:14], "little")
    w = int.from_bytes(raw[18:22], "little", signed=True)
    h = int.from_bytes(raw[22:26], "little", signed=True)
    bpp = int.from_bytes(raw[28:30], "little")
    if bpp != 8 or (w, abs(h)) != (arr.shape[1], arr.shape[0]):
        raise SystemExit(f"{template}: not an 8-bit {arr.shape[1]}x{arr.shape[0]} bitmap")
    stride = (w + 3) // 4 * 4
    rows = np.zeros((abs(h), stride), np.uint8)
    rows[:, :w] = arr if h < 0 else arr[::-1]
    data = rows.tobytes()
    Path(path).write_bytes(raw[:offset] + data + raw[offset + len(data):])


def new_colors(defs, count, seed=1):
    """Unique, not-yet-used province colours."""
    rng = np.random.default_rng(seed)
    used = defs.used_colors()
    out = []
    while len(out) < count:
        c = tuple(int(x) for x in rng.integers(1, 255, 3))
        k = rgb_key(c)
        if k not in used:
            used.add(k)
            out.append(c)
    return out


# --- Clausewitz text --------------------------------------------------------

def read_text(path):
    return Path(path).read_text(encoding="utf-8-sig", errors="replace")


def strip_comments(text):
    return re.sub(r"#[^\n]*", "", text)


def block_ints(text, key):
    m = re.search(r"\b" + key + r"\s*=\s*\{([^}]*)\}", strip_comments(text))
    return [int(x) for x in m.group(1).split()] if m else []


def replace_block_ints(text, key, values, per_line=20):
    vals = [str(v) for v in values]
    lines = ["\t\t" + " ".join(vals[i:i + per_line]) + " " for i in range(0, len(vals), per_line)]
    new = key + "={\n" + "\n".join(lines) + "\n\t}"
    return re.sub(r"\b" + key + r"\s*=\s*\{[^}]*\}", lambda _: new, text, count=1)


# --- states -----------------------------------------------------------------

class StateFile:
    def __init__(self, path, text):
        self.path = Path(path)
        self.text = text
        self.id = int(re.search(r"\bid\s*=\s*(\d+)", text).group(1))
        self.provinces = block_ints(text, "provinces")


def load_states(vanilla_dir, mod_dir):
    """Vanilla history/states, with same-named files in the mod taking precedence."""
    files = {p.name: p for p in sorted((Path(vanilla_dir) / "history/states").glob("*.txt"))}
    mod_states = Path(mod_dir) / "history/states"
    if mod_states.exists():
        for p in sorted(mod_states.glob("*.txt")):
            files[p.name] = p
    states = {}
    for name, p in files.items():
        s = StateFile(p, read_text(p))
        states[s.id] = s
    return states


# --- strategic regions ------------------------------------------------------

class RegionFile:
    def __init__(self, path, text):
        self.path = Path(path)
        self.text = text
        self.id = int(re.search(r"\bid\s*=\s*(\d+)", text).group(1))
        self.provinces = block_ints(text, "provinces")


def load_regions(vanilla_dir, mod_dir):
    files = {p.name: p for p in sorted((Path(vanilla_dir) / "map/strategicregions").glob("*.txt"))}
    mod_reg = Path(mod_dir) / "map/strategicregions"
    if mod_reg.exists():
        for p in sorted(mod_reg.glob("*.txt")):
            files[p.name] = p
    return {r.id: r for r in (RegionFile(p, read_text(p)) for p in files.values())}


# --- position files ---------------------------------------------------------

def load_lines(path):
    return Path(path).read_text(encoding="utf-8-sig", errors="replace").splitlines()


def map_file(vanilla_dir, mod_dir, rel):
    """The mod's copy of a map file if it has one, else vanilla's."""
    p = Path(mod_dir) / rel
    return p if p.exists() else Path(vanilla_dir) / rel
