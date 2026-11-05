#!/usr/bin/env python3
"""See the root list's envelopes in real Safari, on a macOS GitHub runner. On the Mac, standard library only.

    os_check.py --os macos --run 'python3 tools/check_racine_safari.py' > LOG   # on the runner
    python3 tools/check_racine_safari.py --extract LOG OUT                      # back here

Over http, from a local server, safaridriver hovers each card with a real pointer: the flap's matrix,
the letter's rise, the picture, then a screenshot. In the same run the first opened card again with
the 3D flattened: the open flap then covers the letter, so --extract's read of the pixels has to tell
the two apart or its green means nothing. A Safari window does not go down to 390, so the phone width
is the page in a 390 px iframe, which its media queries read as the width.

Over file://, which no driver may open, the way a student gets it: `open -a Safari` on a scratch copy
of index.html holding a script that reports by image beacon what loaded, each picture read below the
page's folder. The mouse is moved by a CGEvent, seen by the page's own :hover and by a screen capture.
If the runner refuses that event, the copy is opened again with its hover rules on a class, and the
log says so: the same CSS, not the same pointer. The scratch copies are removed.

What a green run proves: Safari on a virtual Mac draws the swing and the depth order. What it does NOT
prove: a real Mac's card, or an iPhone. A Mac hovers, so `@media (hover: none)`, the loop a phone gets,
never runs here, and keyboard focus is not driven: Safari skips links on Tab by default. On the screen
captures, "Allow Python to find devices on local networks" is the runner's Python answering the beacon:
a student has no such server. The white band beside the 390 iframe is its classic scrollbar's gutter.
"""

import base64
import ctypes
import ctypes.util
import io
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_badge_safari import small_jpeg
from check_trombone_safari import BEGIN, END, call, print_frame, reports, serve

REPO = Path(__file__).resolve().parent.parent
CARDS = ("merlin", "gobelin", "courtepaille", "inviolia", "dernier-prix", "source-eclat")
META = "=====META"
SETTLE = 1.7
FLAT = ".plaque, .enveloppe, .rabat { transform-style: flat !important; }"
# A runner's Mac may ask for reduced motion: the envelope then opens at once, as it should, and there
# is no swing to read. These beat the page's `*` rule by specificity.
MOVE = """.cible > a .rabat { transition: transform 0.45s ease-in-out !important; }
.cible > a .lettre { transition: transform 0.75s ease 0.45s !important; }"""

PARTS = """
const card = document.querySelector('.cible.' + arguments[0]);
const box = s => { const r = card.querySelector(s).getBoundingClientRect(); return {x: r.x, y: r.y, w: r.width, h: r.height}; };
const img = card.querySelector('.photo');
return {flap: new DOMMatrix(getComputedStyle(card.querySelector('.rabat')).transform).m22,
        letter: box('.lettre'), envelope: box('.poche'), picture: img.complete ? img.naturalWidth : 0,
        hover: card.querySelector('a').matches(':hover'), inner: [innerWidth, innerHeight],
        wide: document.documentElement.scrollWidth - document.documentElement.clientWidth,
        reduced: matchMedia('(prefers-reduced-motion: reduce)').matches, agent: navigator.userAgent};
"""
# Every value the flap takes while it opens: a flap that jumps has no value between the two ends.
WATCH = """
const flap = document.querySelector('.cible.' + arguments[0] + ' .rabat');
const seen = window.__swing = [];
const t0 = performance.now();
(function tick() {
  seen.push(new DOMMatrix(getComputedStyle(flap).transform).m22);
  if (performance.now() - t0 < 1200) requestAnimationFrame(tick);
})();
"""
IN_FRAME = """
const f = document.createElement('iframe');
f.src = location.href;
f.style.cssText = 'position:fixed;left:0;top:0;width:390px;height:800px;border:0;background:#fff;z-index:99999';
document.body.appendChild(f);
return new Promise(done => { f.onload = () => done(f); });
"""
ADD_STYLE = "const s = document.createElement('style'); s.textContent = arguments[0]; document.head.appendChild(s);"

# Goes first in <head>, so that it hears a stylesheet's error event too. The first card is brought to
# the middle of the window, then the page keeps saying what it is: nothing can ask it over file://.
SONDE = """<script>(function () {
  var failed = [];
  document.addEventListener('error', function (e) { var t = e.target; if (t && t.tagName) failed.push(t.href || t.src); }, true);
  function send(n, d) { new Image().src = 'http://127.0.0.1:PORT/sonde?n=' + n + '&d=' + encodeURIComponent(JSON.stringify(d)); }
  addEventListener('load', function () { setTimeout(function () {
    var card = document.querySelector('.cible.merlin'), a = card.querySelector('a');
    FORCE
    a.scrollIntoView({block: 'center'});
    var e = document.documentElement, r = a.getBoundingClientRect();
    send('NAME-load', {url: location.href, failed: failed, wide: e.scrollWidth - e.clientWidth,
      images: [].map.call(document.images, function (i) { return [i.getAttribute('src'), i.complete ? i.naturalWidth : 0]; }),
      sheets: [].map.call(document.querySelectorAll('link[rel=stylesheet]'), function (l) { return [l.getAttribute('href'), !!l.sheet]; }),
      reduced: matchMedia('(prefers-reduced-motion: reduce)').matches, agent: navigator.userAgent,
      centre: [screenX + r.left + r.width / 2, screenY + (outerHeight - innerHeight) + r.top + r.height / 2]});
    setInterval(function () {
      var q = function (s) { var b = card.querySelector(s).getBoundingClientRect(); return b.top; };
      send('NAME-state', {hover: a.matches(':hover'), flap: new DOMMatrix(getComputedStyle(card.querySelector('.rabat')).transform).m22,
        risen: q('.poche') - q('.lettre'), force: a.classList.contains('sonde-force')});
    }, 400);
  }, 1500); });
})();</script>"""


def closed_problems(card, state):
    problems = []
    if not state["picture"]:
        problems.append(f"{card}: its picture did not load")
    if state["flap"] < 0.9 or state["letter"]["y"] < state["envelope"]["y"] - 1:
        problems.append(f"{card}: not closed at rest")
    return problems


def open_problems(card, state):
    risen = state["envelope"]["y"] - state["letter"]["y"]
    problems = []
    if not state["hover"]:
        problems.append(f"{card}: the pointer did not reach it")
    if state["flap"] > -0.9:
        problems.append(f"{card}: the flap did not swing over (m22 {state['flap']:.2f})")
    if risen < 20:
        problems.append(f"{card}: the letter rose only {risen:.0f} px above the envelope")
    if state["wide"] > 0:
        problems.append(f"{card}: the page is {state['wide']} px wider than its window")
    return problems


def over_http(failed):
    """A real pointer on each card, from safaridriver."""
    subprocess.run(["sudo", "safaridriver", "--enable"], capture_output=True, text=True)
    driver = subprocess.Popen(["safaridriver", "-p", "4444"])
    try:
        for _ in range(40):
            try:
                call("GET", "/status", timeout=2)
                break
            except (OSError, RuntimeError):
                time.sleep(0.5)
        session = call("POST", "/session", {"capabilities": {"alwaysMatch": {"browserName": "safari"}}}, timeout=120)
        here = f"/session/{session['sessionId']}"
        print("Safari", session["capabilities"].get("browserVersion"), flush=True)

        def script(source, *args):
            return call("POST", f"{here}/execute/sync", {"script": source, "args": list(args)}, timeout=30)

        def shot(name, state):
            print(f"{META} {name} {json.dumps(state)}", flush=True)
            print_frame(name, small_jpeg(base64.b64decode(call("GET", f"{here}/screenshot")), 1400))

        def hover(card):
            script(f"document.querySelector('.cible.{card}').scrollIntoView({{block: 'center'}});")
            time.sleep(0.3)
            element = call("POST", f"{here}/element", {"using": "css selector", "value": f".cible.{card} > a"})
            key = next(iter(element))
            script(WATCH, card)
            call("POST", f"{here}/actions", {"actions": [{"type": "pointer", "id": "m", "parameters": {"pointerType": "mouse"},
                 "actions": [{"type": "pointerMove", "duration": 100, "origin": {key: element[key]}, "x": 0, "y": 0}]}]})
            time.sleep(SETTLE)
            return script(PARTS, card)

        def swing(card):
            values = script("return window.__swing;")
            between = sum(-0.8 < v < 0.8 for v in values)
            print(f"swing {card}: {len(values)} frames, {between} part-way", flush=True)
            if not between:
                failed.append(f"{card}: the flap jumps instead of swinging")

        call("POST", f"{here}/window/rect", {"width": 1280, "height": 1000, "x": 0, "y": 0})
        port = serve()
        call("POST", f"{here}/url", {"url": f"http://127.0.0.1:{port}/index.html"})
        time.sleep(SETTLE + 0.5)
        if script(PARTS, CARDS[0])["reduced"]:
            print("this Mac asks for reduced motion: the swing is forced on", flush=True)
            script(ADD_STYLE, MOVE)
        for card in CARDS:
            failed.extend(closed_problems(card, script(PARTS, card)))
        shot("repos", script(PARTS, CARDS[0]))
        for card in CARDS:
            state = hover(card)
            failed.extend(open_problems(card, state))
            swing(card)
            shot(f"ouvert-{card}", state)
        call("POST", f"{here}/url", {"url": f"http://127.0.0.1:{port}/index.html"})
        time.sleep(SETTLE + 0.5)
        script(ADD_STYLE, FLAT)
        shot(f"plat-{CARDS[3]}", hover(CARDS[3]))
        frame = script(IN_FRAME)
        call("POST", f"{here}/frame", {"id": frame})
        time.sleep(SETTLE)
        if script(PARTS, CARDS[0])["reduced"]:
            script(ADD_STYLE, MOVE)
        state = hover(CARDS[3])
        failed.extend(f"at 390, {problem}" for problem in open_problems(CARDS[3], state))
        shot(f"tel-{CARDS[3]}", state)
        call("DELETE", here)
    finally:
        driver.terminate()


class Point(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]


def move_mouse(x, y):
    """A real mouse move, by CGEvent. A runner may drop it: the page's :hover says if it arrived."""
    quartz = ctypes.CDLL(ctypes.util.find_library("CoreGraphics") or
                         "/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics")
    quartz.CGEventCreateMouseEvent.restype = ctypes.c_void_p
    quartz.CGEventCreateMouseEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint32, Point, ctypes.c_uint32]
    quartz.CGEventPost.argtypes = [ctypes.c_uint32, ctypes.c_void_p]
    for dx in (-3, -1, 0):
        quartz.CGEventPost(0, quartz.CGEventCreateMouseEvent(None, 5, Point(x + dx, y), 0))   # 5: mouse moved
        time.sleep(0.1)


def screen(name):
    with tempfile.TemporaryDirectory() as d:
        picture = Path(d) / "s.png"
        done = subprocess.run(["screencapture", "-x", str(picture)], capture_output=True, text=True)
        if picture.exists():
            print_frame(name, small_jpeg(picture.read_bytes(), 1400))
        else:
            print("screencapture took nothing:", name, done.returncode, done.stderr.strip(), flush=True)


def wait_for(name, seconds=20, ready=lambda said: True):
    for _ in range(seconds * 4):
        if name in reports and ready(reports[name]):
            return reports[name]
        time.sleep(0.25)
    return reports.get(name)


def scratch_page(port, name, force=False):
    """index.html with the probe in its head, beside the real one, so that its links read the same."""
    html = (REPO / "index.html").read_text(encoding="utf-8")
    sonde = SONDE.replace("PORT", str(port)).replace("NAME", name)
    sonde = sonde.replace("FORCE", "a.classList.add('sonde-force');" if force else "")
    head = "<head>" + sonde
    if force:
        rules = (REPO / "index.css").read_text(encoding="utf-8").replace("a:hover", "a.sonde-force")
        html = html.replace("</head>", f"<style>{rules}</style></head>", 1)
    return html.replace("<head>", head, 1)


def over_file(failed):
    """Double-clicked, as a student does."""
    port = serve()
    scratch = REPO / "_sonde_racine.html"
    forced = REPO / "_sonde_racine_force.html"
    try:
        scratch.write_text(scratch_page(port, "file"), encoding="utf-8")
        subprocess.run(["open", "-a", "Safari", str(scratch)], check=True)
        load = wait_for("file-load")
        print("REPORT file-load", json.dumps(load), flush=True)
        if not load:
            failed.append("file://: the page reported nothing")
            screen("file-rien")
            return
        if load["failed"]:
            failed.append(f"file://: refused {load['failed']}")
        unread = [src for src, width in load["images"] if not width]
        if unread:
            failed.append(f"file://: pictures not loaded: {unread}")
        unapplied = [href for href, sheet in load["sheets"] if not sheet]
        if unapplied:
            failed.append(f"file://: stylesheets not applied: {unapplied}")
        if load["wide"] > 0:
            failed.append(f"file://: {load['wide']} px wider than its window")
        print(f"file://: {len(load['images']) - len(unread)} of {len(load['images'])} pictures loaded", flush=True)
        time.sleep(SETTLE)
        screen("file-repos")
        rest = wait_for("file-state")
        print("REPORT file rest", json.dumps(rest), flush=True)
        if not rest or rest["flap"] < 0.9:
            failed.append(f"file://: not closed at rest: {rest}")
        try:
            move_mouse(*load["centre"])
        except OSError as e:
            print("the mouse could not be moved:", e, flush=True)
        reports.pop("file-state", None)
        hovered = wait_for("file-state", 5, lambda said: said["hover"])
        time.sleep(SETTLE)
        said = reports.get("file-state")
        print("REPORT file hover", json.dumps(said), flush=True)
        if hovered and hovered["hover"]:
            print("file://: a real mouse hovers the card", flush=True)
            screen("file-ouvert")
        else:
            print("file://: this runner's mouse never reached the page: the same rules on a class", flush=True)
            forced.write_text(scratch_page(port, "force", force=True), encoding="utf-8")
            subprocess.run(["open", "-a", "Safari", str(forced)], check=True)
            wait_for("force-load")
            time.sleep(SETTLE + 1)
            said = wait_for("force-state")
            print("REPORT force", json.dumps(said), flush=True)
            screen("file-ouvert-force")
        if not said or said["flap"] > -0.9 or said["risen"] < 20:
            failed.append(f"file://: the envelope did not open: {said}")
    finally:
        scratch.unlink(missing_ok=True)
        forced.unlink(missing_ok=True)


def on_the_mac():
    print(subprocess.run(["sw_vers"], capture_output=True, text=True).stdout)
    motion = subprocess.run(["defaults", "write", "com.apple.universalaccess", "reduceMotion", "-bool", "false"],
                            capture_output=True, text=True)
    print("reduceMotion off:", motion.returncode, motion.stderr.strip())
    failed = []
    try:
        over_http(failed)
    except Exception as e:     # file:// is still worth a look: it is what the ticket is for
        failed.append(f"http: {e}")
    over_file(failed)
    print("FAILED: " + "; ".join(failed) if failed else "ALL OK", flush=True)
    return 1 if failed else 0


def extract(log, out):
    """Write the frames, and read the paper in them the way tools/check_racine.py does."""
    from PIL import Image
    from check_racine import PAPER_AT_LEAST, paper_share

    out.mkdir(parents=True, exist_ok=True)
    name, parts, metas, wrote = None, [], {}, 0
    for line in log.read_text(errors="replace").splitlines():
        if META in line:
            key, state = line.split(META, 1)[1].strip().split(" ", 1)
            metas[key] = json.loads(state)
        elif BEGIN in line:
            name, parts = line.split(BEGIN, 1)[1].strip(), []
        elif END in line and name:
            (out / f"safari-{name}.jpg").write_bytes(base64.b64decode("".join(parts)))
            name, wrote = None, wrote + 1
        elif name:
            parts.append(line.split()[-1] if line.strip() else "")
    print(f"{wrote} frames in {out}")
    problems = []
    for key, state in metas.items():
        if key == "repos" or key.startswith("tel-"):     # the phone's rects are the iframe's: by eye
            print(key, {k: state[k] for k in ("flap", "hover", "wide", "reduced", "inner")})
            continue
        picture = Image.open(out / f"safari-{key}.jpg").convert("RGB")
        css = picture.resize((state["inner"][0], round(picture.height * state["inner"][0] / picture.width)))
        png = io.BytesIO()
        css.save(png, "PNG")
        share = paper_share(png.getvalue(), (state["letter"], state["envelope"]))
        print(f"{key}: {share:.0%} paper where the letter stands, flap m22 {state['flap']:.2f}, hover {state['hover']}")
        if key.startswith("plat-"):
            if share >= PAPER_AT_LEAST:
                problems.append(f"{key}: the flat control still reads {share:.0%} paper: this read proves nothing")
        elif share < PAPER_AT_LEAST:
            problems.append(f"{key}: {share:.0%} paper where the letter stands: something is over it")
    for problem in problems:
        print(f"FAILED: {problem}")
    print("OK" if wrote and not problems else "NOT OK")
    return 0 if wrote and not problems else 1


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--extract":
        sys.exit(extract(Path(sys.argv[2]), Path(sys.argv[3])))
    sys.exit(on_the_mac())
