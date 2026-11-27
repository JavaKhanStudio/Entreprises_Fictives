#!/usr/bin/env python3
"""See the turning clip in real Safari, on a macOS GitHub runner. Standard library only.

    os_check.py --os macos --run 'python3 tools/check_trombone_safari.py' > LOG   # on the runner
    python3 tools/check_trombone_safari.py --extract LOG OUT_DIR                  # back here

On the Mac: drives Safari through safaridriver and fails if #trombone-repli shows, because a green
run on the fallback proves the fallback. safaridriver will not open file:// ("outside the
sandbox"), so that run is over http from a local server. Then file:// the way a student gets it,
`open -a Safari`, seen by screen capture only: no driver can read that page, so those pictures are
judged by eye. Frames come back as base64 in the log, since a runner hands back nothing else
through os_check.py.

What a green run proves: Safari's WebGL compiles merlin.js's shaders, draws the clip and turns it,
read from the page's own buffer. What it does NOT prove: that a Mac shows it. On macos-latest (26.6,
2026-11-02) no WebGL canvas reached a screenshot or a screen capture, not even a control that only
clears red, and the runner is a virtual machine asking for reduced motion, so merlin.js's motion
is switched back on by the server below. Only a look on a real Mac settles the screen.

    os_check.py --os macos --run 'python3 tools/check_trombone_safari.py --file-probe' > LOG

--file-probe answers what a screen capture cannot: what Safari really loaded over file://. It writes
scratch copies of the pages holding a little script that reports to a local server by image beacon,
opens each with `open -a Safari` as a student does, prints what each said, and removes the copies.
It fails on a resource refused or a page wider than its window: Safari refuses over file:// what is
above the opened page's folder (r61), which left each site without shared/base.css.
"""

import base64
import json
import subprocess
import sys
import time
from pathlib import Path

from safari_driver import (
    Quiet,
    call,
    print_frame,
    read_frames,
    reports,
    safari_session,
    screen,
    serve,
    small_jpeg,
)

REPO = Path(__file__).resolve().parent.parent

LOOK = """
const c = document.getElementById('trombone'), r = document.getElementById('trombone-repli');
const seen = e => !!e && !e.hidden && getComputedStyle(e).display !== 'none' && e.getBoundingClientRect().width > 0;
const gl = document.createElement('canvas').getContext('webgl');
const info = gl && gl.getExtension('WEBGL_debug_renderer_info');
return {
  canvas: seen(c), drawn: seen(r), url: location.href, agent: navigator.userAgent,
  inner: [innerWidth, innerHeight], ratio: devicePixelRatio,
  reduced: matchMedia('(prefers-reduced-motion: reduce)').matches,
  webgl: !!gl,
  renderer: gl ? gl.getParameter(info ? info.UNMASKED_RENDERER_WEBGL : gl.RENDERER) : null,
  vendor: gl ? gl.getParameter(info ? info.UNMASKED_VENDOR_WEBGL : gl.VENDOR) : null,
};
"""
FPS = """
const done = arguments[arguments.length - 1];
let n = 0; const t0 = performance.now();
(function tick() { n++; performance.now() - t0 < 2000 ? requestAnimationFrame(tick) : done(Math.round(n / 2)); })();
"""


# Inside rAF, right after the page's own callback in the same frame, its drawing buffer is still
# valid. What the page really drew, whatever the compositor then shows of it: an element screenshot
# here froze on a first frame while the screen showed nothing. And a control: a canvas that only
# clears red, to tell a runner that shows no WebGL from a page that draws none.
BUFFER = """
const done = arguments[arguments.length - 1];
const c = document.getElementById('trombone'), gl = c.getContext('webgl');
requestAnimationFrame(() => {
  const w = c.width, h = c.height, px = new Uint8Array(w * h * 4);
  gl.readPixels(0, 0, w, h, gl.RGBA, gl.UNSIGNED_BYTE, px);
  let solid = 0; for (let i = 3; i < px.length; i += 4) if (px[i]) solid++;
  done({size: [w, h], client: [c.clientWidth, c.clientHeight], share: solid / (w * h), lost: gl.isContextLost(),
        error: gl.getError(), shot: c.toDataURL('image/jpeg', 0.7).split(',')[1], rect: JSON.stringify(c.getBoundingClientRect())});
});
"""
CONTROL = """
const k = document.createElement('canvas');
k.width = k.height = 160;
k.style.cssText = 'position:fixed;left:10px;top:120px;width:160px;height:160px;z-index:99;';
document.body.appendChild(k);
const g = k.getContext('webgl');
(function red() { g.clearColor(1, 0, 0, 1); g.clear(g.COLOR_BUFFER_BIT); requestAnimationFrame(red); })();

"""


CALME = 'window.matchMedia("(prefers-reduced-motion: reduce)").matches'
patched = {"motion": False}


class Merlin(Quiet):
    """Serves the page, and once told to, merlin.js with reduced motion read as off."""

    def do_GET(self):
        if patched["motion"] and self.path.startswith("/merlin/merlin.js"):
            body = (REPO / "merlin/merlin.js").read_text(encoding="utf-8")
            assert CALME in body
            data = body.replace(CALME, "false").encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/javascript")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)
            return
        super().do_GET()


def double_click():
    """file://, opened as a student opens it. Only the screen can say what it drew."""
    subprocess.run(["open", "-a", "Safari", str(REPO / "merlin/index.html")], check=True)
    for i in range(3):
        time.sleep(6 if i == 0 else 2)
        if not screen(f"file-{i}", 700, 70):
            return


def on_the_mac():
    print(subprocess.run(["sw_vers"], capture_output=True, text=True, check=False).stdout)
    failed = []
    with safari_session() as here:

        def script(source, kind="sync"):
            return call("POST", f"{here}/execute/{kind}", {"script": source, "args": []}, timeout=30)

        page = f"http://127.0.0.1:{serve(Merlin)}/merlin/index.html"
        call("POST", f"{here}/url", {"url": page})
        if script(LOOK)["reduced"]:
            # A runner's Mac may ask for reduced motion: merlin.js then draws once and stands still,
            # as it should, and there is no turn to see. Look at the turn all the same.
            print("this Mac asks for reduced motion: first the page as it is, still", flush=True)
            still = call("GET", f"{here}/screenshot")
            print_frame("still", small_jpeg(base64.b64decode(still), 700, 70))
            patched["motion"] = True
            call("POST", f"{here}/url", {"url": f"{page}?turning"})
            print("reduced motion read as off in merlin.js from here on", flush=True)
        script(CONTROL)
        for width in (1280, 390):
            call("POST", f"{here}/window/rect", {"width": width, "height": 1000, "x": 0, "y": 0})
            time.sleep(1.5)
            look = script(LOOK)
            look["asked_width"] = width
            look["fps"] = script(FPS, "async")
            print("LOOK", json.dumps(look), flush=True)
            if not look["canvas"] or look["drawn"]:
                failed.append(f"at {width} the canvas does not show")
            print_frame(f"page-{width}", small_jpeg(base64.b64decode(call("GET", f"{here}/screenshot")), 700, 70))
            screen(f"http-screen-{width}", 700, 70)
            shots = []
            for i in range(3):
                time.sleep(1.5)
                buffer = script(BUFFER, "async")
                shots.append(buffer.pop("shot"))
                print("BUFFER", width, i, json.dumps(buffer), flush=True)
                print_frame(f"buffer-{width}-{i}", base64.b64decode(shots[-1]))
                if not buffer["share"]:
                    failed.append(f"at {width} frame {i}: the page's buffer is empty")
            if len(set(shots)) != len(shots):
                failed.append(f"at {width} the page's buffer does not turn")
    double_click()
    print("FAILED: " + "; ".join(failed) if failed else "ALL OK")
    return 1 if failed else 0


# Goes first in <head>, so that it hears a stylesheet's error event too.
SONDE = """<script>(function () {
  var failed = [];
  document.addEventListener('error', function (e) { var t = e.target; if (t && t.tagName) failed.push(t.href || t.src); }, true);
  addEventListener('load', function () { setTimeout(function () {
    var e = document.documentElement, q = function (s) { var r = document.querySelector(s); r = r && r.getBoundingClientRect(); return r ? [r.left, r.right] : null; };
    var d = {scrollWidth: e.scrollWidth, inner: innerWidth, client: e.clientWidth, failed: failed, url: location.href,
             margin: getComputedStyle(document.body).marginLeft, sizing: getComputedStyle(document.body).boxSizing,
             footer: getComputedStyle(document.querySelector('.site-fictif')).backgroundColor,
             main: q('main'), sheets: [].map.call(document.querySelectorAll('link[rel=stylesheet]'), function (l) { return [l.getAttribute('href'), !!l.sheet]; })};
    new Image().src = 'http://127.0.0.1:PORT/sonde?n=NAME&d=' + encodeURIComponent(JSON.stringify(d));
  }, 1500); });
})();</script>"""


def file_probe():
    """What real Safari loads over file://, read from inside the page."""
    print(subprocess.run(["sw_vers"], capture_output=True, text=True, check=False).stdout)
    port = serve()
    scratch = []

    def copy(name, source, target):
        html = (REPO / source).read_text(encoding="utf-8")
        html = html.replace("<head>", "<head>" + SONDE.replace("PORT", str(port)).replace("NAME", name), 1)
        scratch.append(REPO / target)
        (REPO / target).write_text(html, encoding="utf-8")
        return REPO / target

    # The root last: opening it may widen what this Safari may read, which would hide a refusal.
    steps = [(site, f"{site}/index.html", f"{site}/_sonde.html") for site in ("merlin", "gobelin", "courtepaille")]
    steps.append(("root", "index.html", "_sonde.html"))
    failed = False
    try:
        for name, source, target in steps:
            subprocess.run(["open", "-a", "Safari", str(copy(name, source, target))], check=True)
            for _ in range(40):
                if name in reports:
                    break
                time.sleep(0.5)
            print("REPORT", name, json.dumps(reports.get(name, "nothing came back")), flush=True)
            said = reports.get(name)
            failed = failed or not said or bool(said["failed"]) or said["scrollWidth"] > said["client"]
            screen(f"probe-{name}", 700, 70)
    finally:
        for path in scratch:
            path.unlink(missing_ok=True)
    return 1 if failed else 0


def extract(log, out):
    return 0 if read_frames(log, out)[1] else 1


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--extract":
        sys.exit(extract(Path(sys.argv[2]), Path(sys.argv[3])))
    if sys.argv[1:] == ["--file-probe"]:
        sys.exit(file_probe())
    sys.exit(on_the_mac())
