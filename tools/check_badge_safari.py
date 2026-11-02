#!/usr/bin/env python3
"""See Gobelin's 3D badge in real Safari, on a macOS GitHub runner. On the Mac, standard library only.

    os_check.py --os macos --run 'python3 tools/check_badge_safari.py' > LOG   # on the runner
    python3 tools/check_badge_safari.py --extract LOG OUT_DIR                  # back here

The route of r57: safaridriver will not open file:// ("outside the sandbox"), so the frozen states
are driven over http from a local server; file:// the way a student gets it is `open -a Safari`,
seen by screen capture only, and only the top of the page: nothing here can scroll it down to the
badge (a text fragment does not work over file://). A Safari window does not go down to 390, so the phone width is the
page in a 390 px iframe, which its media queries read as the width. --extract reads the driver's
pictures with the reads of tools/check_badge_browsers.py. A runner's graphics are a virtual
machine's: this says nothing of a real Mac's card, and no phone Safari is involved. The runner's
Mac asks for reduced motion, which leaves nothing turning, so it is switched off first.
"""

import base64
import functools
import http.server
import json
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DRIVER = "http://127.0.0.1:4444"
BEGIN, END, META = "=====FRAME", "=====END", "=====META"
TURNED = 20750

STATE = """
const c = document.querySelector('.vitrine').getBoundingClientRect();
const of = s => { const r = document.querySelector(s).getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; };
let m = new DOMMatrix();
const chain = [];
for (let e = document.querySelector('.plaque'); !e.classList.contains('vitrine'); e = e.parentElement) chain.unshift(e);
for (const e of chain) m = m.multiply(new DOMMatrix(getComputedStyle(e).transform));
const s = getComputedStyle(document.querySelector('.crunch span'));
return {facing: m.m11, vitrine: of('.vitrine'), crunch: of('.crunch'), medal: of('.medaille'),
        inner: [innerWidth, innerHeight], hover: document.querySelector('.vitrine').matches(':hover'),
        clip: s.webkitBackgroundClip || s.backgroundClip,
        animations: document.getAnimations().filter(a => a.animationName).length,
        reduced: matchMedia('(prefers-reduced-motion: reduce)').matches,
        wide: document.documentElement.scrollWidth - innerWidth, agent: navigator.userAgent};
"""
FREEZE = """
document.getAnimations().forEach(a => { if (a.animationName) { a.pause(); a.currentTime = arguments[0]; } });
document.querySelector('.vitrine').scrollIntoView({block: 'center'});
"""
# The runner's Mac may ask for reduced motion, and the page rightly stands still then.
MOVE = """
const s = document.createElement('style');
s.textContent = `.balance { animation: balance 11s ease-in-out infinite !important; }
  .tour { animation: tour 26s infinite !important; }
  .ombre { animation: ombre-tour 26s infinite !important; }
  .plaque { transition: transform 0.9s !important; }`;
document.head.appendChild(s);
"""
IN_FRAME = """
const f = document.createElement('iframe');
f.src = location.href;
f.style.cssText = 'position:fixed;left:0;top:0;width:390px;height:800px;border:0;background:#fff;z-index:99999';
document.body.appendChild(f);
return new Promise(done => { f.onload = () => done(f); });
"""


def call(method, path, body=None, timeout=60):
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(DRIVER + path, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as answer:
            return json.load(answer)["value"]
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {path}: {e.code} {e.read()[:400]!r}") from None


def small_jpeg(png, size=1000):
    """A retina PNG is too much for a log: sips, which every Mac has, makes it a small JPEG."""
    with tempfile.TemporaryDirectory() as d:
        source, target = Path(d) / "s.png", Path(d) / "t.jpg"
        source.write_bytes(png)
        subprocess.run(["sips", "-Z", str(size), "-s", "format", "jpeg", "-s", "formatOptions", "80",
                        str(source), "--out", str(target)], check=True, capture_output=True)
        return target.read_bytes()


def print_frame(name, jpeg):
    print(f"{BEGIN} {name}")
    text = base64.b64encode(jpeg).decode()
    for i in range(0, len(text), 100):
        print(text[i:i + 100])
    print(END, flush=True)


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve():
    handler = functools.partial(Quiet, directory=str(REPO))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server.server_address[1]


def screen(name):
    with tempfile.TemporaryDirectory() as d:
        shot = Path(d) / "s.png"
        done = subprocess.run(["screencapture", "-x", str(shot)], capture_output=True, text=True)
        if shot.exists():
            print_frame(name, small_jpeg(shot.read_bytes()))
        else:
            print("screencapture took nothing:", name, done.returncode, done.stderr.strip())


def double_click():
    """file://, opened as a student opens it, moving. Only the screen can say what it drew."""
    subprocess.run(["open", "-a", "Safari", str(REPO / "gobelin/a-propos.html")], check=True)
    time.sleep(5)
    screen("file-top")


def on_the_mac():
    print(subprocess.run(["sw_vers"], capture_output=True, text=True).stdout)
    motion = subprocess.run(["defaults", "write", "com.apple.universalaccess", "reduceMotion", "-bool", "false"],
                            capture_output=True, text=True)
    print("reduceMotion off:", motion.returncode, motion.stderr.strip())
    enable = subprocess.run(["sudo", "safaridriver", "--enable"], capture_output=True, text=True)
    print("safaridriver --enable:", enable.returncode, enable.stderr.strip())
    driver = subprocess.Popen(["safaridriver", "-p", "4444"])
    failed = []
    try:
        for _ in range(40):
            try:
                call("GET", "/status", timeout=2)
                break
            except (OSError, RuntimeError):
                time.sleep(0.5)
        session = call("POST", "/session", {"capabilities": {"alwaysMatch": {"browserName": "safari"}}}, timeout=120)
        sid = session["sessionId"]
        print("Safari", session["capabilities"].get("browserVersion"), flush=True)
        here = f"/session/{sid}"

        def script(source, *args):
            return call("POST", f"{here}/execute/sync", {"script": source, "args": list(args)}, timeout=30)

        def take(width, label):
            state = script(STATE)
            print(f"{META} {width}-{label} {json.dumps(state)}", flush=True)
            print_frame(f"{width}-{label}", small_jpeg(base64.b64decode(call("GET", f"{here}/screenshot")), 1400))
            return state

        call("POST", f"{here}/window/rect", {"width": 1280, "height": 1000, "x": 0, "y": 0})
        call("POST", f"{here}/url", {"url": f"http://127.0.0.1:{serve()}/gobelin/a-propos.html"})
        time.sleep(2)
        for width in (1280, 390):
            if width == 390:
                frame = script(IN_FRAME)
                call("POST", f"{here}/frame", {"id": frame})
                time.sleep(1)
            if script("return matchMedia('(prefers-reduced-motion: reduce)').matches"):
                print(f"at {width} the Mac asks for reduced motion: animations forced on", flush=True)
                script(MOVE)
            script(FREEZE, 0)
            time.sleep(0.5)
            state = take(width, "front")
            if state["animations"] < 5:
                failed.append(f"{width}: {state['animations']} animations")
            if width == 1280:
                screen("screen-1280-front")
            best = min((abs(script(FREEZE + STATE, t)["facing"]), t)
                       for t in range(19500, 20100, 50))
            script(FREEZE, best[1])
            time.sleep(0.5)
            take(width, "edge")
            script(FREEZE, TURNED)
            time.sleep(0.5)
            take(width, "turned")
            if width == 1280:
                screen("screen-1280-turned")
            script(FREEZE, 0)
            # Hover by a real pointer. In the iframe its origin is the element all the same.
            element = call("POST", f"{here}/element", {"using": "css selector", "value": ".vitrine"})
            key = next(iter(element))
            call("POST", f"{here}/actions", {"actions": [{"type": "pointer", "id": "m", "parameters": {"pointerType": "mouse"},
                 "actions": [{"type": "pointerMove", "duration": 100, "origin": {key: element[key]}, "x": 0, "y": 0}]}]})
            time.sleep(1.3)
            state = take(width, "back")
            if state["facing"] > -0.8:
                failed.append(f"{width}: the hover did not turn it ({state['facing']:.2f}, hover {state['hover']})")
        call("DELETE", here)
    finally:
        driver.terminate()
    double_click()
    print("FAILED: " + "; ".join(failed) if failed else "ALL OK")
    return 1 if failed else 0


def extract(log, out):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from PIL import Image
    import check_badge_browsers as reads

    out.mkdir(parents=True, exist_ok=True)
    name, parts, metas, wrote = None, [], {}, 0
    for line in log.read_text(errors="replace").splitlines():
        if META in line:
            _, key, state = line.split(META, 1)[1].split(" ", 2)
            metas[key] = json.loads(state)
        elif BEGIN in line:
            name, parts = line.split(BEGIN, 1)[1].strip(), []
        elif END in line and name:
            (out / f"safari-{name}.jpg").write_bytes(base64.b64decode("".join(parts)))
            name, wrote = None, wrote + 1
        elif name:
            parts.append(line.split()[-1] if line.strip() else "")
    print(f"{wrote} frames in {out}")
    for key, state in metas.items():
        picture = Image.open(out / f"safari-{key}.jpg").convert("RGB")
        # The driver shoots the whole window; in the iframe, rects are the iframe's, at the corner.
        width, label = key.split("-")
        scale = picture.width / state["inner"][0] if width != "390" else None  # in the iframe: by eye
        print(key, {k: state[k] for k in ("facing", "hover", "clip", "animations", "reduced", "wide", "inner")})
        if scale is None:
            continue
        box = lambda r: tuple(round(v * scale) for v in r)
        case = picture.crop(box(state["vitrine"]))
        if label == "front":
            print(" ", key, "gold", round(reads.share(picture, box(state["crunch"]), reads.GOLD), 3),
                  "crimson", round(reads.share(picture, box(state["crunch"]), reads.CRIMSON), 3),
                  "medal green", round(reads.share(picture, box(state["medal"]), reads.GREEN), 3))
        elif label in ("turned", "back"):
            print(" ", key, reads.back_read(case))
        else:
            b = reads.card_box(case)
            print(" ", key, "edge width", round((b[2] - b[0]) / scale), "css px")
    return 0 if wrote else 1


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--extract":
        sys.exit(extract(Path(sys.argv[2]), Path(sys.argv[3])))
    sys.exit(on_the_mac())
