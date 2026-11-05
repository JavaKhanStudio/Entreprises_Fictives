#!/usr/bin/env python3
"""See Au Dernier Prix's 3D coffin in real Safari, on a macOS GitHub runner. On the Mac, standard library only.

    os_check.py --os macos --ref BRANCH --run 'python3 tools/check_configurateur_safari.py' > LOG   # on the runner
    python3 tools/check_configurateur_safari.py --extract LOG OUT                                   # back here

Over http, from a local server, safaridriver makes the choices with real clicks, freezes the sway at its
middle and takes the window, then the same window with the coffin hidden, for the states of
tools/check_configurateur_browsers.py, in a 1280 window and in a 390 iframe (a Safari window does not go
down to 390; its media queries read the iframe). A real pointer presses and drags the coffin, the lid's
checkbox flashes until used, the kit stays inside a 1007 window (frame fit-1007-kit, by eye); the total
is compared, on the Mac, with the same box holding the amount as written text, both PNGs byte for byte.

--extract then draws the same states in Chrome at the width Safari laid out (classic scrollbars take
15 px) and reads the pixels:
- each state's silhouette, by check_configurateur_browsers.judge: side on, end on, lid up, kit apart, oak;
- each state against Chrome, inside the coffin's own box;
- the lid's top closed and the lining open, painted a solid colour and counted against Chrome: what is
  sorted over them, or missing, lowers the count;
- two controls in the same run: the 3D flattened must read as wrong, or the reads above mean nothing, and
  the turned-away faces drawn (hollow, the bug Firefox had) are printed: Safari may sort them right.

Over file://, which no driver may open, the way a student gets it: `open -a Safari` on a scratch copy of the
page. Its script reports by image beacon what loaded and clicks the choices itself; a screen capture takes
each step, read by eye, total included. The scratch copy is removed.

What a green run proves: Safari on a virtual Mac draws the coffin's planes in the right order and sums the
total. What it does NOT prove: a real Mac's card, an iPhone (`hover: none`, a real finger), keyboard use
(Safari skips some controls on Tab by default). A Safari with :has() also has unprefixed
backface-visibility (both 15.4), so an older one fails on :has() first, and that is not tried here.
"""

import base64
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_badge_safari import small_jpeg
from check_trombone_safari import BEGIN, END, call, print_frame, reports, serve

REPO = Path(__file__).resolve().parent.parent
PAGE = "dernier-prix/configurateur.html"
META = "=====META"
SETTLE = 1.1  # the longest transition (.couvercle) and a margin
FREEZE_AT = 6000  # the sway at its middle, as in tools/check_configurateur_browsers.py
# (id of each choice, view, lid open): tests/test_check_configurateur_safari.py holds them to that tool's.
STATES = {
    "ferme": (["m-pin"], "Trois-quarts", False),
    "face": (["m-pin"], "Face", False),
    "bout": (["m-pin"], "Bout", False),
    "ouvert": (["m-pin", "i-satin"], "Trois-quarts", True),
    "chene": (["m-chene", "n6"], "Trois-quarts", False),
    "kit": (["m-peuplier", "i-satin", "k-oui"], "Trois-quarts", False),
    "ferme-occupe": (["m-pin", "o-homme"], "Trois-quarts", False),
    "homme": (["m-pin", "i-satin", "o-homme"], "Trois-quarts", True),
    "femme": (["m-pin", "i-satin", "o-femme"], "Trois-quarts", True),
    "femme-kit": (["m-peuplier", "i-satin", "k-oui", "o-femme"], "Trois-quarts", False),
}
VIEWS = {"Face": ("v6", 0), "Trois-quarts": ("v5", -30), "Bout": ("v9", 90)}
HIDE = ".socle, .fond, .paroi, .couvercle, .corps { visibility: hidden !important; } .paroi *, .couvercle *, .socle *, .corps * { visibility: hidden !important; }"
FLAT = ".camera, .balance, .plateau, .socle, .paroi, .couvercle, .poignee, .h-de { transform-style: flat !important; }"
HOLLOW = ".f { backface-visibility: visible !important; }"
LID = ".h-de { background: #f0f !important; }"
LINING = ".fond, .doublure, .l-de { background: #0ff !important; }"
# name: (state it draws, css). A marker frame is read by its colour, a control must read wrong.
MARKED = {"repere-dessus": ("ferme", LID), "repere-doublure": ("ouvert", LINING)}
CONTROLS = {"plat-repere-dessus": ("ferme", LID + FLAT), "plat-ferme": ("ferme", FLAT),
            "creux-repere-dessus": ("ferme", LID + HOLLOW), "creux-ferme": ("ferme", HOLLOW)}
RESETS = ("n0", "i-brut", "o-non", "q-non", "k-non", "g-0", "m-pin")
# Every option once at least; the full list is on Chrome and Firefox: a macOS minute counts ten times.
TOTALS = [(["m-pin"], 449), (["m-peuplier"], 519), (["m-chene"], 833),
          (["m-chene", "n6", "i-satin", "o-homme", "q-oui", "g-10"], 1068),
          (["m-peuplier", "n6", "i-satin", "o-femme", "q-oui", "k-oui", "g-10"], 714),
          (["m-pin", "n2", "i-poly", "k-oui", "g-5"], 501),
          (["m-chene", "n4", "i-poly", "q-oui", "k-oui", "g-5"], 934)]

STATE = """
const q = s => document.querySelector(s), e = document.documentElement;
const r = q('.scene').getBoundingClientRect();
const m = new DOMMatrix(getComputedStyle(q('.plateau')).transform);
return {scene: {x: r.x, y: r.y, w: r.width, h: r.height},
        angle: Math.round(Math.atan2(-m.m13, m.m11) * 180 / Math.PI),
        client: e.clientWidth,
        top: [parent.innerWidth, parent.innerHeight], wide: e.scrollWidth - e.clientWidth, ratio: devicePixelRatio,
        reduced: matchMedia('(prefers-reduced-motion: reduce)').matches,
        animations: document.getAnimations().length, agent: navigator.userAgent};
"""
SWAY = "return new DOMMatrix(getComputedStyle(document.querySelector('.balance')).transform).m13;"
FREEZE = "document.getAnimations().forEach(a => { if (a.animationName) { a.pause(); a.currentTime = arguments[0]; } });"
ADD_STYLE = "const s = document.createElement('style'); s.textContent = arguments[0]; document.head.appendChild(s); window.__ajout = s;"
DROP_STYLE = "window.__ajout.remove();"
TO_SCENE = "document.querySelector('.scene').scrollIntoView({block: 'center'});"
IN_FRAME = """
const f = document.createElement('iframe');
f.src = location.href;
f.style.cssText = 'position:fixed;left:0;top:0;width:WIDTHpx;height:800px;border:0;background:#fff;z-index:99999';
document.body.appendChild(f);
return new Promise(done => { f.onload = () => done(f); });
"""
ECLAT = """const l = document.querySelector('label.ouvrir');
return [document.getAnimations().filter(a => a.animationName === 'eclat').length, getComputedStyle(l, '::after').opacity];"""
STILL = ".balance { animation: none !important; } .camera, .plateau, .paroi, .couvercle { transition: none !important; }"
# tests/test_check_configurateur_safari.py holds its selector to tools/check_configurateur.py's LEAST.
PLANES = ".paroi .f, .couvercle .f, .socle .f, .poignee i, .plaque-laiton"
FIT = """const s = document.querySelector('.scene').getBoundingClientRect();
let least = [Infinity, ''];
for (let i = 0; i < 13; i++) {
  document.querySelector('#v' + i).checked = true;
  for (const e of document.querySelectorAll('PLANES')) {
    if (!e.getClientRects().length) continue;
    const r = e.getBoundingClientRect();
    const m = Math.min(r.left - s.left, s.right - r.right, r.top - s.top, s.bottom - r.bottom);
    if (m < least[0]) least = [m, e.parentElement.className + ' ' + e.className];
  }
}
return least;""".replace("PLANES", PLANES)
# A Mac that asks for reduced motion has no sway to read: this puts it back, for that read only.
MOVE = ".balance { animation: balance3d 12s ease-in-out infinite alternate !important; }"

# Goes first in <head>, to hear a stylesheet's error event. Each step clicks what a student clicks,
# then reports; the Mac takes the screen on that report.
STEP_MS = 7000
STEPS = [("ferme", [], -30, 449), ("ouvert", ["i-satin", "o-homme", "ouvert"], -30, 538), ("kit", ["ouvert", "k-oui"], -30, 498),
         ("bout", ["k-non", "v9"], 90, 538), ("chene", ["v5", "m-chene", "n6", "i-brut"], -30, 905)]
SONDE = """<script>(function () {
  var failed = [], woods = {}, steps = STEPS, q = function (s) { return document.querySelector(s); };
  document.addEventListener('error', function (e) { var t = e.target; if (t && t.tagName) failed.push(t.href || t.src); }, true);
  function send(n, d) { new Image().src = 'http://127.0.0.1:PORT/sonde?n=' + n + '&d=' + encodeURIComponent(JSON.stringify(d)); }
  function report(i) {
    var m = new DOMMatrix(getComputedStyle(q('.plateau')).transform), l = new DOMMatrix(getComputedStyle(q('.couvercle')).transform);
    send('NAME-' + steps[i][0], {angle: Math.round(Math.atan2(-m.m13, m.m11) * 180 / Math.PI),
      lid: Math.round(Math.atan2(l.m23, l.m22) * 180 / Math.PI), kit: Math.round(new DOMMatrix(getComputedStyle(q('.avant')).transform).m43),
      wood: getComputedStyle(q('.avant .bois')).backgroundImage.split('/').pop(), handles: [].filter.call(document.querySelectorAll('.poignee'), function (e) { return getComputedStyle(e).display !== 'none'; }).length,
      wide: document.documentElement.scrollWidth - document.documentElement.clientWidth});
  }
  function step(i) {
    steps[i][1].forEach(function (id) { document.getElementById(id).click(); });
    setTimeout(function () { report(i); }, 1400);
    if (i + 1 < steps.length) setTimeout(function () { step(i + 1); }, STEP_MS);
  }
  addEventListener('load', function () {
    ['pin', 'peuplier', 'chene'].forEach(function (w) { var i = new Image(); i.onload = function () { woods[w] = i.naturalWidth; }; i.onerror = function () { woods[w] = 0; }; i.src = 'img/bois-' + w + '.webp'; });
    setTimeout(function () {
      q('.scene').scrollIntoView({block: 'center'});
      var e = document.documentElement;
      send('NAME-load', {url: location.href, failed: failed, saisie: q('.scene').classList.contains('saisie'), woods: woods, wide: e.scrollWidth - e.clientWidth, client: e.clientWidth,
        sheets: [].map.call(document.querySelectorAll('link[rel=stylesheet]'), function (l) { return [l.getAttribute('href'), !!l.sheet]; }),
        reduced: matchMedia('(prefers-reduced-motion: reduce)').matches, agent: navigator.userAgent});
      step(0);
    }, 1500);
  });
})();</script>"""


def as_expected(name, state, angle):
    """What the page itself says, before any picture is read."""
    problems = []
    if abs((state["angle"] - angle + 180) % 360 - 180) > 1:
        problems.append(f"{name}: at {state['angle']} degrees, not {angle}")
    if state["wide"] > 0:
        problems.append(f"{name}: the page is {state['wide']} px wider than its window")
    return problems


def run_states(d, emit, failed):
    """Every state at both widths, through d, the driver: Safari here, Chrome in the test."""
    for width in (1280, 390):
        narrow = width == 390
        drawn = {name: (*STATES[name], "") for name in STATES}
        for name, (state, css) in MARKED.items():
            drawn[name] = (*STATES[state], css)
        if not narrow:
            for name, (state, css) in CONTROLS.items():
                drawn[name] = (*STATES[state], css)
        for name, (combo, view, lid, css) in drawn.items():
            d.open(narrow)
            if css:
                d.script(ADD_STYLE, css)
            d.choose(combo, view, lid)
            d.script(TO_SCENE)
            d.away()
            d.script(FREEZE, FREEZE_AT)
            time.sleep(SETTLE)
            state = d.script(STATE)
            key = f"{width}-{name}"
            if name in STATES:
                failed.extend(as_expected(key, state, VIEWS[view][1]))
            d.frame(key, state)
            if name == "chene":    # after the frame: the read writes its amount over the total
                state["total_right"] = d.price_is(".prix-scene", 905) and not d.price_is(".prix-scene", 906)
            emit(f"{META} {key} {json.dumps(state)}")
            d.script(ADD_STYLE, HIDE)
            time.sleep(0.2)
            d.frame(f"{key}-vide", state)


def run_turn(d, failed):
    """The sway, a real pointer on the strips, a click that stays."""
    d.open(False)
    if d.script(STATE)["reduced"]:
        print("this Mac asks for reduced motion: the sway is forced on, for this read", flush=True)
        d.script(ADD_STYLE, MOVE)
    d.script(TO_SCENE)
    d.script(FREEZE, 0)
    a = d.script(SWAY)
    d.script(FREEZE, 12000)
    b = d.script(SWAY)
    print(f"sway: {a:.2f}, {b:.2f}", flush=True)
    if abs(a - b) < 0.1:
        failed.append(f"it does not sway ({a:.2f}, {b:.2f})")
    d.away()
    running = d.script(ECLAT)
    print(f"flash, before use: {running}", flush=True)
    if running[0] != 1 or running[1] != "1":
        failed.append(f"the lid's checkbox does not flash before use ({running})")
    scene = d.script(STATE)["scene"]
    middle = round(scene["y"] + scene["h"] / 2)
    at = lambda share: round(scene["x"] + scene["w"] * share)
    d.place(at(1 / 26), middle)
    d.place(at(25 / 26), middle)
    time.sleep(0.8)
    failed.extend(as_expected("the pointer alone", d.script(STATE), -30))
    d.place(at(0.5), middle)
    d.press()
    failed.extend(as_expected("a press", d.script(STATE), -30))
    d.place(at(0.5 + 4 / 12), middle)
    state = d.script(STATE)
    print(f"held, a third of the scene along: {state['angle']} degrees", flush=True)
    failed.extend(as_expected("the drag", state, 90))
    d.lift()
    d.place(at(0.1), middle)
    time.sleep(0.8)
    failed.extend(as_expected("after the release", d.script(STATE), 90))
    d.place(at(0.8), middle)
    d.press()
    d.lift()
    time.sleep(0.8)
    failed.extend(as_expected("a click without a drag", d.script(STATE), 90))
    a = d.script(SWAY)
    time.sleep(0.7)
    if abs(a - d.script(SWAY)) > 0.001:
        failed.append("the first press did not stop the sway")
    d.click("label[for=v5]")
    d.away()
    time.sleep(0.8)
    failed.extend(as_expected("the view already chosen, after a drag", d.script(STATE), -30))
    d.click("label.ouvrir")
    time.sleep(0.2)
    running = d.script(ECLAT)
    print(f"flash, after use: {running}", flush=True)
    if running[1] != "0":
        failed.append(f"using the lid's checkbox does not stop its flash ({running})")


def run_fit(d, failed):
    """r93, the kit against the scene's edge, in a 1007 window: planes' rects at each angle, and a frame."""
    d.open(1007)
    d.script(ADD_STYLE, STILL)
    d.pick(["n6", "q-oui", "k-oui"])
    for lid in ("shut", "open"):
        least = d.script(FIT)
        print(f"1007, kit, lid {lid}: least {least[0]:.1f} px, {least[1]}", flush=True)
        if least[0] < 0:
            failed.append(f"1007, kit, lid {lid}: {least[1]} passes the scene's edge by {-least[0]:.1f} px")
        d.click("label.ouvrir")
    d.script("document.querySelector('#v5').checked = true;")
    d.script(TO_SCENE)
    d.away()
    time.sleep(SETTLE)
    d.frame("fit-1007-kit", d.script(STATE))


def run_totals(d, failed):
    """The drawn total against the same box holding it as text, on the ticket and over the coffin."""
    d.open(False)
    d.script(FREEZE, FREEZE_AT)
    for combo, amount in TOTALS:
        d.pick(RESETS)
        d.pick(combo)
        right = d.price_is(".ticket .prixf", amount) and d.price_is(".prix-scene", amount)
        print(f"{' + '.join(combo)} = {amount}: {'OK' if right else 'FAIL'}", flush=True)
        if not right:
            failed.append(f"{' + '.join(combo)} does not draw {amount} €")
    d.pick(RESETS)
    if d.price_is(".ticket .prixf", 450):
        failed.append("the read cannot tell 449 € from 450 €")


class Safari:
    """The moves run_states asks for, through safaridriver."""

    def __init__(self, here, port):
        self.here, self.url, self.narrow = here, f"http://127.0.0.1:{port}/{PAGE}", False

    def script(self, source, *args):
        return call("POST", f"{self.here}/execute/sync", {"script": source, "args": list(args)}, timeout=30)

    def open(self, narrow):
        call("POST", f"{self.here}/url", {"url": self.url})
        time.sleep(0.8)
        self.narrow = narrow
        if narrow:
            frame = self.script(IN_FRAME.replace("WIDTH", str(390 if narrow is True else narrow)))
            self.script(FREEZE, FREEZE_AT)    # the page around the iframe sways in the window's shot too
            call("POST", f"{self.here}/frame", {"id": frame})
            time.sleep(0.8)

    def element(self, selector):
        found = call("POST", f"{self.here}/element", {"using": "css selector", "value": selector})
        return next(iter(found)), next(iter(found.values()))

    def click(self, selector):
        call("POST", f"{self.here}/element/{self.element(selector)[1]}/click", {})

    def pick(self, ids):
        for i in ids:
            self.click(f"label:has(#{i})")

    def choose(self, combo, view, lid):
        self.pick(combo)
        self.click(f"label[for={VIEWS[view][0]}]")
        if lid:
            self.click("label.ouvrir")

    def move(self, origin, x=0, y=0):
        call("POST", f"{self.here}/actions", {"actions": [{"type": "pointer", "id": "m", "parameters": {"pointerType": "mouse"},
             "actions": [{"type": "pointerMove", "duration": 100, "origin": origin, "x": x, "y": y}]}]})

    def away(self):
        """Twice: this input source remembers where it was, and a click moved another one, so a move to where it already is sends nothing."""
        self.move("viewport", 6, 6)
        self.move("viewport")

    def place(self, x, y):
        self.move("viewport", x, y)

    def button(self, kind):
        call("POST", f"{self.here}/actions", {"actions": [{"type": "pointer", "id": "m", "parameters": {"pointerType": "mouse"},
             "actions": [{"type": kind, "button": 0}]}]})

    def press(self):
        self.button("pointerDown")

    def lift(self):
        self.button("pointerUp")

    def shot(self, selector):
        """Good for text only. An element's shot flattens the 3D (seen on Safari 26.6, the screen capture
        had it right), and inside an iframe it answers 500: there the whole window, the selector in view."""
        if self.narrow:
            return call("GET", f"{self.here}/screenshot")
        return call("GET", f"{self.here}/element/{self.element(selector)[1]}/screenshot")

    def frame(self, name, state):
        """The window, which the compositor drew; --extract crops the scene out of it."""
        print_frame(name, small_jpeg(base64.b64decode(call("GET", f"{self.here}/screenshot")), round(state["top"][0])))

    def price_is(self, selector, amount):
        """Digits only, as in tools/check_configurateur.py: a counter and the string after it are two runs."""
        self.script(ADD_STYLE, ".total::after { content: counter(total) !important; }")
        time.sleep(0.25)    # a window's shot is the last paint: a change just made may not be in it
        drawn = self.shot(selector)
        self.script(DROP_STYLE)
        self.script(ADD_STYLE, f'.total::after {{ content: "{amount}" !important; }}')
        time.sleep(0.25)
        written = self.shot(selector)
        self.script(DROP_STYLE)
        time.sleep(0.25)
        return drawn == written


def over_http(failed):
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
        call("POST", f"{here}/window/rect", {"width": 1280, "height": 1000, "x": 0, "y": 0})
        d = Safari(here, serve())
        run_turn(d, failed)
        run_totals(d, failed)
        run_fit(d, failed)
        run_states(d, lambda line: print(line, flush=True), failed)
        call("DELETE", here)
    finally:
        driver.terminate()


def screen(name):
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as d:
        picture = Path(d) / "s.png"
        done = subprocess.run(["screencapture", "-x", str(picture)], capture_output=True, text=True)
        if picture.exists():
            print_frame(name, small_jpeg(picture.read_bytes(), 1400))
        else:
            print("screencapture took nothing:", name, done.returncode, done.stderr.strip(), flush=True)


def wait_for(name, seconds=20):
    for _ in range(seconds * 4):
        if name in reports:
            return reports[name]
        time.sleep(0.25)
    return None


def scratch_page(port, name):
    """The page with the probe in its head, beside the real one, so that its links read the same."""
    html = (REPO / PAGE).read_text(encoding="utf-8")
    steps = json.dumps([[n, ids] for n, ids, _, _ in STEPS])
    sonde = SONDE.replace("PORT", str(port)).replace("NAME", name).replace("STEP_MS", str(STEP_MS)).replace("STEPS", steps)
    return html.replace("<head>", "<head>" + sonde, 1)


def load_problems(load):
    if not load:
        return ["file://: the page reported nothing"]
    problems = []
    if not load.get("saisie"):
        problems.append("file://: configurateur.js did not run")
    if load["failed"]:
        problems.append(f"file://: refused {load['failed']}")
    unapplied = [href for href, sheet in load["sheets"] if not sheet]
    if unapplied:
        problems.append(f"file://: stylesheets not applied: {unapplied}")
    if sorted(w for w, width in load["woods"].items() if width) != ["chene", "peuplier", "pin"]:
        problems.append(f"file://: woods not loaded: {load['woods']}")
    if load["wide"] > 0:
        problems.append(f"file://: {load['wide']} px wider than its window")
    return problems


def step_problems(name, angle, said):
    if not said:
        return [f"file://, {name}: no report"]
    problems = []
    if abs((said["angle"] - angle + 180) % 360 - 180) > 1:
        problems.append(f"file://, {name}: at {said['angle']} degrees, not {angle}")
    if said["wide"] > 0:
        problems.append(f"file://, {name}: {said['wide']} px wider than its window")
    return problems


def over_file(failed):
    """Double-clicked, as a student does. The totals on the captures are read by eye."""
    port = serve()
    scratch = REPO / "dernier-prix/_sonde_configurateur.html"
    try:
        scratch.write_text(scratch_page(port, "file"), encoding="utf-8")
        subprocess.run(["open", "-a", "Safari", str(scratch)], check=True)
        load = wait_for("file-load", 30)
        print("REPORT file-load", json.dumps(load), flush=True)
        failed.extend(load_problems(load))
        if not load:
            screen("file-rien")
            return
        for name, _, angle, amount in STEPS:
            said = wait_for(f"file-{name}", 15)
            print(f"REPORT file-{name}, its total should read {amount}:", json.dumps(said), flush=True)
            failed.extend(step_problems(name, angle, said))
            screen(f"file-{name}")
    finally:
        scratch.unlink(missing_ok=True)


def on_the_mac():
    print(subprocess.run(["sw_vers"], capture_output=True, text=True).stdout)
    motion = subprocess.run(["defaults", "write", "com.apple.universalaccess", "reduceMotion", "-bool", "false"],
                            capture_output=True, text=True)
    print("reduceMotion off:", motion.returncode, motion.stderr.strip())
    failed = []
    try:
        over_http(failed)
    except Exception as e:     # file:// is still worth a look
        failed.append(f"http: {e}")
    over_file(failed)
    print("FAILED: " + "; ".join(failed) if failed else "ALL OK", flush=True)
    return 1 if failed else 0


def read_log(log, out):
    """The frames as files, and what the page said of each."""
    name, parts, metas, wrote = None, [], {}, 0
    for line in log.read_text(errors="replace").splitlines():
        if META in line:
            key, state = line.split(META, 1)[1].strip().split(" ", 1)
            metas[key] = json.loads(state)
        elif BEGIN in line:
            name, parts = line.split(BEGIN, 1)[1].strip(), []
        elif END in line and name:
            (out / f"mac-{name}.jpg").write_bytes(base64.b64decode("".join(parts)))
            name, wrote = None, wrote + 1
        elif name:
            parts.append(line.split()[-1] if line.strip() else "")
    print(f"{wrote} frames in {out}")
    return metas


def extract(log, out):
    """Write the frames, draw the same states in Chrome, read the pixels."""
    from PIL import Image, ImageChops, ImageFilter
    from playwright.sync_api import sync_playwright
    import check_configurateur as cc
    import check_configurateur_browsers as ccb

    magenta = lambda r, g, b: r > 200 and g < 70 and b > 200
    cyan = lambda r, g, b: r < 70 and g > 200 and b > 200
    colour = {"repere-dessus": magenta, "repere-doublure": cyan, "plat-repere-dessus": magenta, "creux-repere-dessus": magenta}

    def count(path, kind):
        rgb = Image.open(path).convert("RGB").tobytes()
        return sum(1 for i in range(0, len(rgb), 3) if kind(rgb[i], rgb[i + 1], rgb[i + 2]))

    out.mkdir(parents=True, exist_ok=True)
    metas = read_log(log, out)
    problems = []
    widths = sorted({key.split("-", 1)[0] for key in metas}, key=int, reverse=True)
    if not widths:
        print("NOT OK: no state in this log")
        return 1

    def far_from_chrome(client, state, box, other):
        """check_configurateur_browsers.apart for a frame that came through a JPEG and a crop: softened,
        and at its best alignment within a pixel, or wood grain alone reads as far apart (5 to 7 % on
        Chrome against itself)."""
        if box[2] <= box[0] or box[3] <= box[1]:
            return 1.0
        soft = ImageFilter.GaussianBlur(1.5)
        a = Image.open(out / f"chrome-{client}-{state}.png").convert("RGB").filter(soft).crop(box)
        b = Image.open(out / f"{other}-{client}-{state}.png").convert("RGB").filter(soft)
        best = 1.0
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                moved = b.crop((box[0] + dx, box[1] + dy, box[2] + dx, box[3] + dy))
                d = ImageChops.difference(a, moved).convert("L")
                best = min(best, sum(d.histogram()[25:]) / (d.width * d.height))
        return best

    def load(asked, name):
        """The scene cut out of the Mac's frames, on Chrome's pixel grid. By the height: a window's shot
        may or may not count its classic scrollbar in its width."""
        state = metas[f"{asked}-{name}"]
        scene, cut = state["scene"], []
        for suffix in ("", "-vide"):
            picture = Image.open(out / f"mac-{asked}-{name}{suffix}.jpg").convert("RGB")
            scale = picture.height / state["top"][1]
            box = [round(v * scale) for v in (scene["x"], scene["y"], scene["x"] + scene["w"], scene["y"] + scene["h"])]
            cut.append(picture.crop(box).resize((round(scene["w"]), round(scene["h"]))))
        return cut

    missing = [f"{asked}-{name}" for asked in widths for name in STATES if f"{asked}-{name}" not in metas]
    if missing:
        print(f"FAILED: the run left no frame of {missing}")
        print("NOT OK")
        return 1

    steps = {}
    with sync_playwright() as playwright:
        chrome = playwright.chromium.launch(channel="chrome", args=["--hide-scrollbars"])
        print("reference: chrome", chrome.version)
        for asked in widths:
            client = metas[f"{asked}-ferme"]["client"]
            steps[client] = ccb.frames(chrome, "chrome", client, out, "")["step"]
            for name, (state, css) in MARKED.items():
                combo, view, lid = STATES[state]
                context, page = cc.opened(chrome, [], client)
                page.add_style_tag(content=css)
                page.locator(".scene").scroll_into_view_if_needed()
                cc.choose(page, *combo)
                page.locator(".vues label", has_text=view).click()
                if lid:
                    page.locator("label.ouvrir").click()
                page.mouse.move(0, 0)
                page.evaluate(cc.FREEZE, FREEZE_AT)
                page.wait_for_timeout(cc.SETTLE)
                page.evaluate(ccb.SETTLE)
                page.locator(".scene").screenshot(path=out / f"chrome-{client}-{name}.png")
                context.close()
        chrome.close()

    for asked in widths:
        client = metas[f"{asked}-ferme"]["client"]
        r = {"browser": "safari", "width": client, "errors": [], "step": steps[client],
             "total_right": metas[f"{asked}-chene"].get("total_right", False)}
        for state in STATES:
            picture, empty = load(asked, state)
            picture.save(out / f"safari-{client}-{state}.png")
            mask = ccb.silhouette(picture, empty)
            r[state] = {"box": ccb.box_of(mask), "oak": ccb.share(picture, mask, ccb.OAK), "gold": ccb.share(picture, mask, ccb.GOLD)}
        checks = ccb.judge(r, out)
        for state in STATES:
            far = far_from_chrome(client, state, r[state]["box"], "safari")
            checks.append((f"{state} is drawn as in Chrome ({far:.1%} of its box far apart)", far < ccb.LIMIT))
        for name in MARKED:
            picture, _ = load(asked, name)
            picture.save(out / f"safari-{client}-{name}.png")
            ours, theirs = count(out / f"safari-{client}-{name}.png", colour[name]), count(out / f"chrome-{client}-{name}.png", colour[name])
            checks.append((f"{name}: {ours} px of the marker against Chrome's {theirs}", theirs > 500 and 0.93 < ours / theirs < 1.07))
        for what, ok in checks:
            print(f"{'OK  ' if ok else 'FAIL'} safari at {client}: {what}")
            if not ok:
                problems.append(f"safari at {client}: {what}")
        if asked == "1280":
            for name, (state, _css) in CONTROLS.items():
                picture, _ = load(asked, name)
                if "repere" in name:
                    path = out / f"safari-{client}-{name}.png"
                    picture.save(path)
                    ours = count(path, colour[name])
                    ratio = ours / max(1, count(out / f"chrome-{client}-repere-dessus.png", colour[name]))
                    print(f"CONTROL {name}: {ours} px of the marker, {ratio:.0%} of Chrome's")
                    wrong = not 0.93 < ratio < 1.07
                else:
                    picture.save(out / f"{name}-{client}-{state}.png")
                    far = far_from_chrome(client, state, r[state]["box"], name)
                    print(f"CONTROL {name}: {far:.1%} of the coffin's box far from Chrome")
                    wrong = far >= ccb.LIMIT
                if name.startswith("plat-") and not wrong:
                    problems.append(f"{name}: the flat control still reads as right: this read proves nothing")
    for problem in problems:
        print(f"FAILED: {problem}")
    print("OK" if not problems else "NOT OK")
    return 0 if not problems else 1


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--extract":
        sys.exit(extract(Path(sys.argv[2]), Path(sys.argv[3])))
    sys.exit(on_the_mac())
