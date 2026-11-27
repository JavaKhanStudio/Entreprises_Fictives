#!/usr/bin/env python3
"""r113: the server the Safari tools now share, tried here. Trombone's Merlin handler still serves
merlin.js with reduced motion read as off once told to, and every tool's server keeps a beacon's
report. Also each of the five tools imports.

    python3 tools/r113/serve_same.py
"""

import importlib
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import safari_driver

tools = {n: importlib.import_module(f"check_{n}_safari") for n in ("trombone", "badge", "inviolia", "configurateur", "racine")}
trombone = tools["trombone"]
failed = []
for handler in (safari_driver.Quiet, trombone.Merlin):
    port = safari_driver.serve(handler)
    get = lambda path, port=port: urllib.request.urlopen(f"http://127.0.0.1:{port}{path}").read().decode()
    beacon = f"/sonde?n={handler.__name__}&d=" + urllib.parse.quote(json.dumps({"wide": 0}))
    get(beacon)
    if safari_driver.wait_for(handler.__name__, 2) != {"wide": 0}:
        failed.append(f"{handler.__name__}: the beacon was not kept")
    trombone.patched["motion"] = handler is trombone.Merlin
    body = get("/merlin/merlin.js")
    patched = trombone.CALME not in body
    print(handler.__name__, "merlin.js patched:", patched, "reports:", sorted(safari_driver.reports))
    if patched != (handler is trombone.Merlin):
        failed.append(f"{handler.__name__}: merlin.js patched is {patched}")
if any(t.reports is not safari_driver.reports for t in (trombone, tools["racine"])):
    failed.append("a tool holds its own reports")
print("FAILED: " + "; ".join(failed) if failed else "OK")
sys.exit(1 if failed else 0)
