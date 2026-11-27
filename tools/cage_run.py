"""Run a browsers check headed inside cage, and read what it left: the launcher the *_browsers tools share.

cage is a Wayland compositor of its own; with WLR_BACKENDS=headless it shows nothing on screen and
renders on the card named (/dev/dri/<card>). The tool re-runs itself inside it with --inside,
writes its results as JSON to a file, and the outer run reads that file.

    found = cage_run.run([__file__, "--inside", ...], results_file, card, timeout)
    sys.exit(cage_run.control_main(__doc__, CONTROLS, inside, judge, sheets, timeout=540))

control_main is the whole main() of a tool whose --control breaks the page in Firefox only
(check_badge_browsers.py, check_configurateur_browsers.py): exit 1 is red on the read the control
names, exit 2 is green or red elsewhere.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def env_for(card):
    """The environment of a headless cage on /dev/dri/<card>, without the desktop's display."""
    env = {**os.environ, "WLR_BACKENDS": "headless", "WLR_RENDER_DRM_DEVICE": f"/dev/dri/{card}",
           "WLR_LIBINPUT_NO_DEVICES": "1", "XDG_CURRENT_DESKTOP": "cage", "WLR_LOG": "error"}
    env.pop("DISPLAY", None)
    env.pop("WAYLAND_DISPLAY", None)
    return env


def run(argv, results_file, card, timeout):
    """Run `python3 argv...` inside cage; the JSON it wrote to results_file, or None if it wrote none."""
    results_file = Path(results_file)
    results_file.unlink(missing_ok=True)
    subprocess.run(["cage", "--", sys.executable, *map(str, argv)], env=env_for(card), timeout=timeout, check=False)
    if not results_file.exists():
        print("FAILED: the run inside cage left no results")
        return None
    return json.loads(results_file.read_text())


def control_main(doc, controls, inside, judge, sheets, timeout, describe=None):
    """main() of a browsers tool with --control: inside(out, results_file, control) runs in cage and
    writes {"frames": [...], "behaviour": [...]}; judge(frame, out) gives (what, ok) pairs; sheets(out)
    draws the contact sheets; describe(frame), if given, prints a frame's raw figures."""
    script = sys.modules[inside.__module__].__file__
    parser = argparse.ArgumentParser(description=doc.splitlines()[0])
    parser.add_argument("out")
    parser.add_argument("--control", choices=controls)
    parser.add_argument("--card", default="renderD128")
    parser.add_argument("--inside", help=argparse.SUPPRESS)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    if args.inside:
        inside(out, Path(args.inside), args.control)
        return 0
    out.mkdir(parents=True, exist_ok=True)
    results_file = out / "results.json"
    argv = [script, out, "--inside", results_file] + (["--control", args.control] if args.control else [])
    found = run(argv, results_file, args.card, timeout)
    if found is None:
        return 2 if args.control else 1
    failed = list(found["behaviour"])
    for r in found["frames"]:
        label = f"{r['browser']} at {r['width']}"
        if describe:
            describe(r)
        for what, ok in judge(r, out):
            print(f"{'OK  ' if ok else 'FAIL'} {label}: {what}")
            if not ok:
                failed.append(f"{label}: {what}")
    for what in found["behaviour"]:
        print(f"FAIL firefox behaviour: {what}")
    sheets(out)
    if args.control:
        named = controls[args.control][1]
        chrome_red = [f for f in failed if f.startswith("chrome")]
        right = any(f.startswith("firefox") and named in f for f in failed) and not chrome_red
        print(f"CONTROL {args.control}: " + ("red on the read it names" if right else f"did NOT go red on {named!r}"))
        return 1 if right else 2
    print("FAILED" if failed else "ALL OK")
    return 1 if failed else 0
