#!/usr/bin/env python3
"""The takes of r55: what to do about the Merlin paperclip's cost where there is no GPU.

    python3 tools/clip_takes.py OUT_DIR [--lighthouse]

Works on `git archive HEAD` in a temporary folder, never on the checkout. Each take is a patch
of merlin/merlin.js. Writes OUT_DIR/clip.png, one equal column per take, for
`atelier attach --stamp 1A,1B,1C`. With --lighthouse, also runs Lighthouse three times on each take
over http and prints the score and the blocking time (needs npx; several minutes).
"""

import json
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parent.parent
SERVE = Path.home() / "Documents/GitHub/atelier/tools/serve_static.py"
# What tools/check_trombone.py launches, and the renderer Lighthouse's Chrome ends up with.
SOFTWARE_GL = ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
STILL_ON_SOFTWARE = """if (!gl) return;
    /* No GPU: the loop would take the page's whole thread, so the drawn clip stays. */
    if (sansGpu()) return;
"""
NO_GPU = """function sansGpu() {
    var essai = document.createElement("canvas").getContext("webgl");
    var pilote = essai && essai.getExtension("WEBGL_debug_renderer_info");
    return !!pilote && /swiftshader|llvmpipe|software/i.test(essai.getParameter(pilote.UNMASKED_RENDERER_WEBGL));
  }

  function trombone(toile, repli) {"""


def replace(text, old, new):
    if old not in text:
        sys.exit(f"merlin.js no longer holds: {old}")
    return text.replace(old, new)


def as_is(js):
    return js


def with_probe(js):
    return replace(js, "function trombone(toile, repli) {", NO_GPU)


def cheaper_on_software(js):
    """Only where there is no GPU: no antialiasing, 1x pixels, 30 frames a second."""
    js = with_probe(js)
    js = replace(js, "    var gl = null;\n", "    var gl = null, leger = sansGpu();\n")
    js = replace(js, "antialias: true", "antialias: !leger")
    js = replace(js, "Math.min(window.devicePixelRatio || 1, 2)", "leger ? 1 : Math.min(window.devicePixelRatio || 1, 2)")
    js = replace(js, "var dernier = 0, debut = 0;", "var dernier = 0, debut = 0, pair = false;")
    return replace(js, "if (vu) dessine(t - debut);", "if (vu && (!leger || (pair = !pair))) dessine(t - debut);")


def still_on_software(js):
    return replace(with_probe(js), "if (!gl) return;\n", STILL_ON_SOFTWARE)


TAKES = {"A": as_is, "B": cheaper_on_software, "C": still_on_software}


def tree(work, letter):
    root = Path(work) / letter
    root.mkdir()
    archive = subprocess.run(["git", "archive", "HEAD"], cwd=REPO, capture_output=True, check=True)
    subprocess.run(["tar", "-x", "-C", str(root)], input=archive.stdout, check=True)
    js = root / "merlin/merlin.js"
    js.write_text(TAKES[letter](js.read_text(encoding="utf-8")), encoding="utf-8")
    return root


def shoot(browser, root, target):
    context = browser.new_context(viewport={"width": 1280, "height": 800}, device_scale_factor=2,
                                  reduced_motion="reduce")
    page = context.new_page()
    page.goto((root / "merlin/index.html").as_uri())
    page.wait_for_timeout(800)
    page.locator("#trombone-repli").locator("..").screenshot(path=target)
    context.close()


def lighthouse(root):
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    server = subprocess.Popen(["python3", str(SERVE), str(port)], cwd=root,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    try:
        out = subprocess.run(
            ["npx", "-y", "lighthouse@12", f"http://127.0.0.1:{port}/merlin/index.html", "--quiet",
             "--chrome-flags=--headless=new", "--only-categories=performance",
             "--output=json", "--output-path=stdout"],
            capture_output=True, text=True, timeout=180, check=True).stdout
    finally:
        server.kill()
    report = json.loads(out)
    return (round(report["categories"]["performance"]["score"] * 100),
            round(report["audits"]["total-blocking-time"]["numericValue"]))


def main():
    args = [a for a in sys.argv[1:] if a != "--lighthouse"]
    if len(args) != 1:
        sys.exit(__doc__)
    out = Path(args[0])
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="clip-takes-") as work, sync_playwright() as p:
        roots = {letter: tree(work, letter) for letter in TAKES}
        browser = p.chromium.launch(channel="chrome", args=SOFTWARE_GL)
        shots = []
        for letter, root in roots.items():
            shot = Path(work) / f"{letter}.png"
            shoot(browser, root, shot)
            shots.append(Image.open(shot).convert("RGB"))
        browser.close()
        width, height = max(s.width for s in shots), max(s.height for s in shots)
        sheet = Image.new("RGB", (width * len(shots), height), "#fff")
        for n, shot in enumerate(shots):
            sheet.paste(shot, (width * n, 0))
        sheet.save(out / "clip.png")
        print(out / "clip.png")
        if "--lighthouse" in sys.argv:
            for letter, root in roots.items():
                print(letter, [lighthouse(root) for _ in range(3)])


if __name__ == "__main__":
    main()
