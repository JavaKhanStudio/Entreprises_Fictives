#!/usr/bin/env python3
"""See the turning clip in other browsers and on this machine's graphics card, over file://.

    python3 tools/check_trombone_browsers.py OUT_DIR [card]     # card: renderD128 (default) ...

tools/check_trombone.py is Chrome on software rendering. This opens merlin/index.html headed, in
Chrome and in Playwright's Firefox, at 1280 and 390, and for each says what really drew: it fails
if the drawn clip (#trombone-repli) shows instead of the canvas, because a green run on the
fallback proves the fallback. Safari is not here: it runs on a Mac only, and Playwright's WebKit
build, which would not be Safari either, lacks system libraries on this Fedora.

Headed means a real window, and a board session is not to put one on Simon's screen. So everything
runs inside cage, a compositor of its own with WLR_BACKENDS=headless: it shows nothing anywhere
and renders on the card named. Needs cage, Chrome, `playwright install firefox`.
"""

import io
import json
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parent.parent
HOME = (REPO / "merlin/index.html").as_uri()
WIDTHS = (1280, 390)
FRAMES = 6
SOFTWARE = ("swiftshader", "llvmpipe", "softpipe", "software")

# What the page's WebGL is really running on. Firefox hides the renderer behind a generic name
# unless its pref below is set, and a context of our own asks the same driver the page's asked.
RENDERER = """() => {
  const gl = document.createElement('canvas').getContext('webgl');
  if (!gl) return null;
  const info = gl.getExtension('WEBGL_debug_renderer_info');
  return info ? gl.getParameter(info.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER);
}"""
FPS = """() => new Promise(done => {
  let n = 0; const t0 = performance.now();
  (function tick() { n++; performance.now() - t0 < 2000 ? requestAnimationFrame(tick) : done(Math.round(n / 2)); })();
})"""


# On a real card the clip keeps its full quality: merlin.js only lowers it where there is no GPU.
FULL_QUALITY = """() => {
  const c = document.getElementById('trombone');
  return c.width === Math.round(c.clientWidth * 2) && c.getContext('webgl').getContextAttributes().antialias;
}"""


def full_quality(browser, width):
    context = browser.new_context(viewport={"width": width, "height": 1300}, device_scale_factor=2)
    page = context.new_page()
    page.goto(HOME, wait_until="load")
    page.wait_for_timeout(500)
    answer = page.evaluate(FULL_QUALITY)
    context.close()
    return answer


def drawn_share(png):
    """The share of the canvas that is clip, on the black ground the probe gives it."""
    shot = Image.open(io.BytesIO(png)).convert("L")
    w, h = shot.size
    return sum(shot.histogram()[41:]) / (w * h)


def one(browser, name, width, out):
    result = {"browser": name, "width": width, "errors": []}
    context = browser.new_context(viewport={"width": width, "height": 1300})
    page = context.new_page()
    page.on("pageerror", lambda e: result["errors"].append(str(e)))
    page.on("console", lambda m: m.type == "error" and result["errors"].append(m.text))
    page.goto(HOME, wait_until="load")
    clip, drawn = page.locator("#trombone"), page.locator("#trombone-repli")
    result["canvas_shows"] = clip.is_visible() and not drawn.is_visible()
    result["renderer"] = page.evaluate(RENDERER)
    result["fps"] = page.evaluate(FPS)
    if not result["canvas_shows"]:
        page.screenshot(path=str(out / f"{name}-{width}-repli.png"))
        context.close()
        return result
    box = page.locator(".scene").bounding_box()
    cap = page.locator(".astuce").bounding_box()
    area = {"x": box["x"], "y": box["y"], "width": box["width"], "height": cap["y"] + cap["height"] + 6 - box["y"]}
    pictures = []
    for i in range(FRAMES):
        page.wait_for_timeout(900)
        path = out / f"{name}-{width}-{i}.png"
        page.screenshot(path=str(path), clip=area)
        pictures.append(path.read_bytes())
    result["frames_differ"] = len(set(pictures))
    # A blank canvas shows the hero's ground and still differs nowhere; a canvas that draws wrong
    # shows far too little or far too much clip. Same frames again, on black.
    page.add_style_tag(content=".une { background: #000 !important; } .une::before, .une::after, .scene::before { display: none !important; }")
    page.wait_for_timeout(100)
    shares = []
    for _ in range(FRAMES):
        shares.append(drawn_share(clip.screenshot()))
        page.wait_for_timeout(900)
    result["clip_share"] = [round(s, 3) for s in shares]
    context.close()
    result["full_quality"] = full_quality(browser, width)
    return result


def inside(out, results_file):
    results = []
    with sync_playwright() as playwright:
        chrome = playwright.chromium.launch(
            channel="chrome", headless=False,
            args=["--ozone-platform=wayland", "--ignore-gpu-blocklist", "--enable-gpu-rasterization"])
        firefox = playwright.firefox.launch(
            headless=False,
            firefox_user_prefs={"webgl.disabled": False, "webgl.enable-debug-renderer-info": True,
                                "webgl.force-enabled": True, "gfx.webrender.all": True})
        for name, browser in (("chrome", chrome), ("firefox", firefox)):
            print("version", name, browser.version, flush=True)
            for width in WIDTHS:
                results.append(one(browser, name, width, out))
                print(json.dumps(results[-1]), flush=True)
            browser.close()
    results_file.write_text(json.dumps(results))


def verdict(results):
    failed = []
    for r in results:
        label = f"{r['browser']} at {r['width']}"
        renderer = (r.get("renderer") or "").lower()
        checks = [("the canvas shows, not the drawn clip", r["canvas_shows"]),
                  ("no page error", not r["errors"])]
        if r["canvas_shows"]:
            checks += [(f"the clip turns: {r['frames_differ']} of {FRAMES} frames differ", r["frames_differ"] == FRAMES),
                       (f"the canvas holds a clip: {r['clip_share']}", all(0.005 < s < 0.4 for s in r["clip_share"])),
                       ("full quality: antialiased, at 2x pixels", r["full_quality"])]
        checks.append((f"on a real card: {r.get('renderer')}", bool(renderer) and not any(s in renderer for s in SOFTWARE)))
        for what, ok in checks:
            print(f"{'OK  ' if ok else 'FAIL'} {label}: {what}")
            if not ok:
                failed.append(f"{label}: {what}")
        print(f"     {label}: {r.get('fps')} frames a second, WebGL on {r.get('renderer')}")
    return failed


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--inside":
        inside(Path(sys.argv[2]), Path(sys.argv[3]))
        return 0
    out = Path(sys.argv[1]).resolve()
    card = sys.argv[2] if len(sys.argv) > 2 else "renderD128"
    out.mkdir(parents=True, exist_ok=True)
    results_file = out / "results.json"
    results_file.unlink(missing_ok=True)
    env = {**os.environ, "WLR_BACKENDS": "headless", "WLR_RENDER_DRM_DEVICE": f"/dev/dri/{card}",
           "WLR_LIBINPUT_NO_DEVICES": "1", "XDG_CURRENT_DESKTOP": "cage"}
    env.pop("DISPLAY", None)
    env.pop("WAYLAND_DISPLAY", None)
    subprocess.run(["cage", "--", sys.executable, __file__, "--inside", str(out), str(results_file)],
                   env=env, timeout=420, check=False)
    if not results_file.exists():
        print("FAILED: the run inside cage left no results")
        return 1
    failed = verdict(json.loads(results_file.read_text()))
    print("FAILED" if failed else "ALL OK")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
