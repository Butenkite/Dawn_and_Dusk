"""Where things live, for every tool in this folder.

    <repo>/mod/          what HOI4 loads (the launcher's .mod points here)
    <repo>/tools/        generators, map builder, setup helpers
    <repo>/tools/data/   the hand-edited sources the generators read
    <repo>/docs/         conventions, testing, credits

A tool in a subfolder of tools/ finds this module by adding tools/ to its
import path, then imports REPO, MOD and DATA from it.
"""
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MOD = REPO / "mod"
DATA = REPO / "tools" / "data"
