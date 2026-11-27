"""What the check_*_safari.py tools share on the Mac, standard library only: safaridriver's session,
a local server that also hears the pages' beacons, the screen, and the frames they print into the
log. Also --extract's reading of those frames back here.

It travels with them: os_check.py checks the whole repo out on the runner, and each tool imports
this from tools/, its own folder.
"""

import base64
import contextlib
import functools
import http.server
import json
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DRIVER = "http://127.0.0.1:4444"
BEGIN, END, META = "=====FRAME", "=====END", "=====META"

reports = {}


def call(method, path, body=None, timeout=60):
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(DRIVER + path, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as answer:
            return json.load(answer)["value"]
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {path}: {e.code} {e.read()[:400]!r}") from None


@contextlib.contextmanager
def safari_session():
    """safaridriver started, a Safari session opened: yields its path, /session/<id>. Deleted on the
    way out unless the body failed; the driver is stopped either way."""
    enable = subprocess.run(["sudo", "safaridriver", "--enable"], capture_output=True, text=True, check=False)
    print("safaridriver --enable:", enable.returncode, enable.stderr.strip())
    driver = subprocess.Popen(["safaridriver", "-p", "4444"])
    try:
        for _ in range(40):
            try:
                call("GET", "/status", timeout=2)
                break
            except (OSError, RuntimeError):
                time.sleep(0.5)
        session = call("POST", "/session", {"capabilities": {"alwaysMatch": {"browserName": "safari"}}}, timeout=120)
        print("Safari", session["capabilities"].get("browserVersion"), flush=True)
        here = f"/session/{session['sessionId']}"
        yield here
        call("DELETE", here)
    finally:
        driver.terminate()


def small_jpeg(png, size=1000, quality=80):
    """A retina PNG is too much for a log: sips, which every Mac has, makes it a small JPEG."""
    with tempfile.TemporaryDirectory() as d:
        source, target = Path(d) / "s.png", Path(d) / "t.jpg"
        source.write_bytes(png)
        subprocess.run(["sips", "-Z", str(size), "-s", "format", "jpeg", "-s", "formatOptions", str(quality),
                        str(source), "--out", str(target)], check=True, capture_output=True)
        return target.read_bytes()


def print_frame(name, jpeg):
    print(f"{BEGIN} {name}")
    text = base64.b64encode(jpeg).decode()
    for i in range(0, len(text), 100):
        print(text[i:i + 100])
    print(END, flush=True)


def screen(name, size=1400, quality=80):
    """The whole screen into the log, the only eye on a page opened by double-click. False if none."""
    with tempfile.TemporaryDirectory() as d:
        picture = Path(d) / "s.png"
        done = subprocess.run(["screencapture", "-x", str(picture)], capture_output=True, text=True, check=False)
        if picture.exists():
            print_frame(name, small_jpeg(picture.read_bytes(), size, quality))
            return True
        print("screencapture took nothing:", name, done.returncode, done.stderr.strip(), flush=True)
        return False


class Quiet(http.server.SimpleHTTPRequestHandler):
    """Serves the repo, and keeps what a page's beacon says (/sonde?n=NAME&d=JSON) in reports."""

    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path.startswith("/sonde?"):
            query = urllib.parse.parse_qs(self.path.split("?", 1)[1])
            reports[query["n"][0]] = json.loads(query["d"][0])
            self.send_response(204)
            self.end_headers()
            return
        super().do_GET()


def serve(handler=Quiet):
    """A local server on a free port, in a thread: returns the port."""
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(handler, directory=str(REPO)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server.server_address[1]


def wait_for(name, seconds=20, ready=lambda said: True):
    """A beacon's report once it is ready, or what came at all by then (None if nothing)."""
    for _ in range(seconds * 4):
        if name in reports and ready(reports[name]):
            return reports[name]
        time.sleep(0.25)
    return reports.get(name)


def read_frames(log, out, prefix="safari"):
    """--extract: each frame of a log as out/<prefix>-<name>.jpg. Returns the META states by name,
    and how many frames were written."""
    out.mkdir(parents=True, exist_ok=True)
    name, parts, metas, wrote = None, [], {}, 0
    for line in log.read_text(errors="replace").splitlines():
        if META in line:
            key, state = line.split(META, 1)[1].strip().split(" ", 1)
            metas[key] = json.loads(state)
        elif BEGIN in line:
            name, parts = line.split(BEGIN, 1)[1].strip(), []
        elif END in line and name:
            (out / f"{prefix}-{name}.jpg").write_bytes(base64.b64decode("".join(parts)))
            name, wrote = None, wrote + 1
        elif name and line.strip():
            parts.append(line.split()[-1])
    print(f"{wrote} frames in {out}")
    return metas, wrote
