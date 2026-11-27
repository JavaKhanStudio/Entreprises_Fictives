"""r110: prove a formatting-only fix changed no code. Before the fix:
    python3 tools/r110/same_ast.py --save SNAP FILE...
after it:
    python3 tools/r110/same_ast.py --check SNAP FILE...
Parentheses and line breaks leave no trace in the AST, so equal dumps mean equal programs."""
import ast
import json
import pathlib
import sys

mode, snap, files = sys.argv[1], pathlib.Path(sys.argv[2]), sys.argv[3:]
dumps = {f: ast.dump(ast.parse(pathlib.Path(f).read_text(encoding="utf-8"))) for f in files}
if mode == "--save":
    snap.write_text(json.dumps(dumps))
    print(f"saved {len(dumps)} files")
else:
    before = json.loads(snap.read_text())
    bad = [f for f in files if before[f] != dumps[f]]
    for f in files:
        print("same" if f not in bad else "DIFFERS", f)
    sys.exit(1 if bad else 0)
