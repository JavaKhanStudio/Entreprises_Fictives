#!/usr/bin/env python3
"""See Inviolia's scroll camera in real Safari, on a macOS GitHub runner. On the Mac, standard library only.

    os_check.py --os macos --run 'python3 tools/check_inviolia_safari.py' > LOG   # on the runner
    python3 tools/check_inviolia_safari.py --extract LOG OUT                     # the frames, back here

Over http from a local server, because safaridriver will not open file:// (tools/check_badge_safari.py
says why): the home at its key scroll positions, then a-propos and equipe swept to the end. It fails
if the hero is not held under the header, the camera does not push in, the page scrolls sideways, or
anything stays faded at the end. What it does NOT prove: a real Mac's card, an iPhone, or a wheel:
the driver scrolls by script, so the gentle stops are Chrome's and Firefox's proof, in
tools/check_inviolia.py.
"""

import base64
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from safari_driver import (
    call,
    print_frame,
    read_frames,
    safari_session,
    serve,
    small_jpeg,
)

STATE = """
const of = s => document.querySelector(s);
const m = of('.hero-img') && getComputedStyle(of('.hero-img')).transform.match(/matrix\\(([-\\d.]+)/);
return {y: scrollY, wide: document.documentElement.scrollWidth - innerWidth, vivant: document.documentElement.classList.contains('vivant'),
        scale: m ? +m[1] : 1, cadre: of('.cadre') ? of('.cadre').getBoundingClientRect().top : null,
        bar: of('.haut').getBoundingClientRect().bottom,
        faded: [...document.querySelectorAll('main *')].filter(e => getComputedStyle(e).opacity !== '1' && !e.matches('.suite')).length,
        inner: [innerWidth, innerHeight]};
"""


def script(here, source):
    return call("POST", f"{here}/execute/sync", {"script": source, "args": []}, timeout=30)


def take(here, failed, name, y):
    """Scroll to y, print the state and the frame into the log: a page wider than its window or with
    no html.vivant goes into failed."""
    script(here, f"scrollTo(0, {y})")
    time.sleep(1.0)  # past the glide: it may rest on a stop nearby
    state = script(here, STATE)
    print(f"{name} {json.dumps(state)}", flush=True)
    print_frame(name, small_jpeg(base64.b64decode(call("GET", f"{here}/screenshot")), 1400))
    if state["wide"] > 0:
        failed.append(f"{name}: {state['wide']} px sideways")
    if not state["vivant"]:
        failed.append(f"{name}: no html.vivant")
    return state


def home(here, port, failed):
    """The home at its key positions: the camera wide at the top, pushed in and held at the end of
    its course, then the globe, the cards and the end, where nothing stays faded."""
    call("POST", f"{here}/url", {"url": f"http://127.0.0.1:{port}/inviolia/index.html"})
    time.sleep(2)
    start = take(here, failed, "home-top", 0)
    if abs(start["scale"] - 1) > .01:
        failed.append(f"camera starts at {start['scale']}")
    course = script(here, "return document.querySelector('.scene-hero').offsetHeight - document.querySelector('.cadre').offsetHeight")
    end = take(here, failed, "home-pinned-end", course)
    if abs(end["scale"] - 1.55) > .01:
        failed.append(f"camera ends at {end['scale']}")
    if abs(end["cadre"] - end["bar"]) > 2:
        failed.append(f"hero not held: {end['cadre']} against {end['bar']}")
    last = script(here, "return document.documentElement.scrollHeight - innerHeight")
    take(here, failed, "home-globe", course + (last - course) // 3)
    take(here, failed, "home-cards", course + 2 * (last - course) // 3)
    if take(here, failed, "home-end", last)["faded"]:
        failed.append("home: faded at the end")


def swept(here, port, failed, one):
    """Another page at its top, middle and end, where nothing stays faded."""
    call("POST", f"{here}/url", {"url": f"http://127.0.0.1:{port}/inviolia/{one}.html"})
    time.sleep(2)
    last = script(here, "return document.documentElement.scrollHeight - innerHeight")
    take(here, failed, f"{one}-top", 0)
    take(here, failed, f"{one}-middle", last // 2)
    if take(here, failed, f"{one}-end", last)["faded"]:
        failed.append(f"{one}: faded at the end")


def on_the_mac():
    print(subprocess.run(["sw_vers"], capture_output=True, text=True, check=False).stdout)
    subprocess.run(["defaults", "write", "com.apple.universalaccess", "reduceMotion", "-bool", "false"], check=False)
    failed = []
    with safari_session() as here:
        port = serve()
        call("POST", f"{here}/window/rect", {"width": 1280, "height": 900, "x": 0, "y": 0})
        home(here, port, failed)
        for one in ("a-propos", "equipe"):
            swept(here, port, failed, one)
    print("FAILED: " + "; ".join(failed) if failed else "OK")
    return 1 if failed else 0


def extract(log, out):
    read_frames(log, out)


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--extract":
        extract(Path(sys.argv[2]), Path(sys.argv[3]))
    else:
        sys.exit(on_the_mac())
