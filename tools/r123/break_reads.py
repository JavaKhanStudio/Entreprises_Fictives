#!/usr/bin/env python3
"""r123's proof: the two Safari tests still fail when one read of their tool is broken.

    python3 tools/r123/break_reads.py TREE        # each break, run on TREE's tool and TREE's test

Each break replaces one line of the tool in memory only (the file is untouched), loads that source
as the tool's module, then runs the test in its own process. "none" is the control: it must pass.
Run it on the tree before the split and after it: the verdicts must be the same, each break FAIL.
"""

import subprocess
import sys
from pathlib import Path

RUN = r'''
import importlib.util, runpy, sys
tree, name, old, new = sys.argv[1:5]
sys.path.insert(0, tree + "/tools")
path = f"{tree}/tools/{name}.py"
source = open(path, encoding="utf-8").read()
if old:
    assert source.count(old) == 1, (old, source.count(old))
    source = source.replace(old, new)
spec = importlib.util.spec_from_file_location(name, path)
module = importlib.util.module_from_spec(spec)
sys.modules[name] = module
exec(compile(source, path, "exec"), module.__dict__)
sys.argv = [f"{tree}/tests/test_{name}.py"]
runpy.run_path(sys.argv[0], run_name="__main__")
'''

BREAKS = {
    "check_racine_safari": [
        ("none", "", ""),
        ("an unloaded picture let through", "    if unread:\n", "    if False:\n"),
        ("a blank shot never retaken", "if len(jpeg) < BLANK_JPEG_UNDER:", "if False:"),
        ("a black window not named", "<= BLACK_AT_MOST:", "< 0:"),
        ("paper under the letter not read", "elif share < PAPER_AT_LEAST:", "elif False:"),
    ],
    "check_configurateur_safari": [
        ("none", "", ""),
        ("a total read as right always", "return drawn == written", "return True"),
        ("the lid's marker not counted", "theirs > 500 and 0.93 < ours / theirs < 1.07", "True"),
    ],
}


def main():
    tree = str(Path(sys.argv[1]).resolve())
    for name, breaks in BREAKS.items():
        for label, old, new in breaks:
            run = subprocess.run([sys.executable, "-c", RUN, tree, name, old, new], capture_output=True, text=True,
                                 cwd=tree, check=False)
            said = [line for line in run.stdout.splitlines() if line.startswith("FAILED:")]
            verdict = "pass" if run.returncode == 0 else "FAIL"
            print(f"{name} / {label}: {verdict}")
            for line in said:
                print("   ", line)
            if run.returncode not in (0, 1):
                print("    crashed:", run.stderr.strip().splitlines()[-1:])


if __name__ == "__main__":
    main()
