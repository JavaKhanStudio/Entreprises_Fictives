"""r109: each pack's lines as shown, by atelier's own counter (db.pack_lines). Run with
atelier's venv python: ~/Documents/GitHub/atelier/.venv/bin/python tools/r109/measure.py"""
import sys, tomllib, pathlib
sys.path.insert(0, str(pathlib.Path.home() / "Documents/GitHub/atelier"))
from atelier import db
tags = tomllib.load(open(pathlib.Path(__file__).resolve().parents[2] / ".atelier/packs.toml", "rb"))["tags"]
bad = 0
for slug, t in tags.items():
    n = db.pack_lines(t["context"])
    bad += n > db.PACK_CAP
    print(f"{slug:14} {n:3}{'  OVER' if n > db.PACK_CAP else ''}")
sys.exit(1 if bad else 0)
