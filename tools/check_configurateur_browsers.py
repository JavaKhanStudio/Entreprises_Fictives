#!/usr/bin/env python3
"""See Au Dernier Prix's 3D coffin drawn in Firefox, against Chrome, over file://, on the real card.

    python3 tools/check_configurateur_browsers.py OUT_DIR [--control flat|counter|hollow] [--card renderD128]

tools/check_configurateur.py reads computed matrices, and those read the same with the 3D
flattened: only pixels say what a browser drew. So at 1280 and 390, headed, in Chrome and
Playwright's Firefox, this freezes the coffin in six states and reads each picture:
- each picture is compared with the same frame with the coffin hidden, which gives its silhouette;
- side on, it is much wider than end on, and end on, from above, its length still shows;
- open, its top is above the closed one; in kit, the silhouette is taller and wider;
- oak with six handles: dark wood and gold inside the silhouette, and the total drawn right;
- Firefox differs from Chrome by no more than fonts and antialiasing do.
Then it runs every check of check_configurateur.py in Firefox.

--control breaks the page in Firefox only and must go red on the read it names: flat removes
preserve-3d, counter stops the browser summing, hollow draws the faces turned away, which Firefox
then sorts over the lid's top (seen on r79: a whole lid missing, 0.3 % of the scene). Exit 1 is that red; exit 2 means it stayed green
or failed for another reason.

Headed runs inside cage, as in tools/check_badge_browsers.py. Needs cage, Chrome,
`playwright install firefox`, Pillow. Safari: tools/check_configurateur_safari.py.
"""

import argparse
import io
import json
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_configurateur as cc  # noqa: E402

WIDTHS = (1280, 390)
CONTROLS = {
    "flat": (".camera, .balance, .plateau, .socle, .paroi, .couvercle, .poignee, .h-de { transform-style: flat !important; }",
             "seen from above"),
    "counter": (".compte { counter-increment: none !important; }", "the oak's total"),
    "hollow": (".f { backface-visibility: visible !important; }", "drawn as in Chrome"),
}
LIMIT = 0.05  # of the coffin's box: the hollow lid measured 10 to 26 %, a right one under this
SETTLE = "() => new Promise(d => requestAnimationFrame(() => requestAnimationFrame(d)))"
HIDE = ".socle, .fond, .paroi, .couvercle { visibility: hidden !important; } .paroi *, .couvercle *, .socle * { visibility: hidden !important; }"
# What each colour family is, in (r, g, b).
OAK = lambda r, g, b: 30 < r < 150 and g < 75 and b < 60 and r > 1.5 * g
GOLD = lambda r, g, b: r > 150 and g > 110 and 30 < b < 170 and r - b > 60
# (id of each choice, view, lid open)
STATES = {
    "ferme": (["m-pin"], "Trois-quarts", False),
    "face": (["m-pin"], "Face", False),
    "bout": (["m-pin"], "Bout", False),
    "ouvert": (["m-pin", "i-satin"], "Trois-quarts", True),
    "chene": (["m-chene", "n6"], "Trois-quarts", False),
    "kit": (["m-peuplier", "i-satin", "k-oui"], "Trois-quarts", False),
}


def silhouette(picture, empty):
    """The pixels the coffin changes: this picture against the same frame with the coffin hidden."""
    d = ImageChops.difference(picture, empty).convert("L").point(lambda v: 255 if v > 24 else 0)
    return d


def box_of(mask):
    """Where a mask is set, ignoring stray pixels: a row or a column needs a few."""
    w, h = mask.size
    px = mask.load()
    columns = [x for x in range(w) if sum(1 for y in range(0, h, 2) if px[x, y]) > 2]
    rows = [y for y in range(h) if sum(1 for x in range(0, w, 2) if px[x, y]) > 2]
    return (columns[0], rows[0], columns[-1] + 1, rows[-1] + 1) if columns and rows else (0, 0, 0, 0)


def share(picture, mask, kind):
    """The share of the coffin's own pixels that are of this colour family."""
    rgb, m = picture.tobytes(), mask.tobytes()
    inside = [i for i, v in enumerate(m) if v]
    return sum(1 for i in inside if kind(rgb[3 * i], rgb[3 * i + 1], rgb[3 * i + 2])) / max(1, len(inside))


def frames(browser, name, width, out, css):
    errors = []
    results = {"browser": name, "width": width}
    for state, (combo, view, lid) in STATES.items():
        context, page = cc.opened(browser, errors, width)
        if css:
            page.add_style_tag(content=css)
        page.locator(".scene").scroll_into_view_if_needed()
        cc.choose(page, *combo)
        page.locator(".vues label", has_text=view).click()
        if lid:
            page.locator("label.ouvrir").click()
        page.mouse.move(0, 0)
        page.evaluate(cc.FREEZE, 6000)  # the sway at its middle, the same in both browsers
        page.wait_for_timeout(cc.SETTLE)
        page.evaluate(SETTLE)
        path = out / f"{name}-{width}-{state}.png"
        page.locator(".scene").screenshot(path=path)
        picture = Image.open(path).convert("RGB")
        hide = page.add_style_tag(content=HIDE)
        page.evaluate(SETTLE)
        empty = Image.open(io.BytesIO(page.locator(".scene").screenshot())).convert("RGB")
        hide.evaluate("e => e.remove()")
        mask = silhouette(picture, empty)
        results[state] = {"box": box_of(mask), "oak": share(picture, mask, OAK), "gold": share(picture, mask, GOLD)}
        if state == "chene":
            results["total_right"] = cc.price_is(page, ".ticket .prixf", 833 + 72)
        context.close()
    results["errors"] = errors
    return results


def apart(out, width, state, box):
    """The share of the coffin's own box Firefox draws far from Chrome, more than antialiasing can.

    Measured on the box, not the scene: a whole lid top missing in Firefox was 0.3 % of the scene."""
    if box[2] <= box[0] or box[3] <= box[1]:
        return 1.0  # nothing of the coffin was drawn
    a = Image.open(out / f"chrome-{width}-{state}.png").convert("RGB").crop(box)
    b = Image.open(out / f"firefox-{width}-{state}.png").convert("RGB").crop(box)
    d = ImageChops.difference(a, b).convert("L")
    return sum(d.histogram()[25:]) / (d.width * d.height)


def judge(r, out):
    """(what, ok) for one browser at one width."""
    box = {state: r[state]["box"] for state in STATES}
    wide = {state: b[2] - b[0] for state, b in box.items()}
    high = {state: b[3] - b[1] for state, b in box.items()}
    scale = wide["face"] / 416  # the plinth is 416 px long, seen side on
    checks = [
        (f"side on is wider than end on ({wide['face']} against {wide['bout']} px)",
         wide["face"] > 2 * wide["bout"] > 0),
        (f"seen from above, end on still shows its length ({high['bout']} high, {wide['bout']} wide)",
         high["bout"] > wide["bout"] > 0),
        (f"the lid rises above the coffin (top {box['ouvert'][1]}, closed {box['ferme'][1]})",
         box["ferme"][1] - box["ouvert"][1] > 40 * scale),
        (f"the kit lifts the lid and spreads the walls ({wide['kit']}x{high['kit']} against {wide['ferme']}x{high['ferme']})",
         high["kit"] > high["ferme"] + 80 * scale and wide["kit"] > wide["ferme"] + 40 * scale),
        (f"oak with its handles ({r['chene']['oak']:.1%} oak, {r['chene']['gold']:.2%} gold)",
         r["chene"]["oak"] > 0.3 and r["chene"]["gold"] > 0.008),
        ("the oak's total is 905 €, in pixels", r["total_right"]),
        ("no page error", not r["errors"]),
    ]
    if r["browser"] == "firefox":
        for state in STATES:
            d = apart(out, r["width"], state, r[state]["box"])
            checks.append((f"{state} is drawn as in Chrome ({d:.1%} of its box far apart)", d < LIMIT))
    return checks


def sheets(out):
    for width in WIDTHS:
        pictures = [Image.open(out / f"{n}-{width}-{s}.png").convert("RGB") for n in ("chrome", "firefox") for s in STATES]
        w, h = pictures[0].size
        scale = min(1, 420 / w)
        w2, h2 = int(w * scale), int(h * scale)
        sheet = Image.new("RGB", (w2 * len(STATES), h2 * 2))
        for i, p in enumerate(pictures):
            sheet.paste(p.resize((w2, h2)), ((i % len(STATES)) * w2, (i // len(STATES)) * h2))
        sheet.save(out / f"planche-{width}.png")


def inside(out, results_file, control):
    css = CONTROLS[control][0] if control else ""
    results, behaviour = [], []
    with sync_playwright() as playwright:
        chrome = playwright.chromium.launch(channel="chrome", headless=False,
                                            args=["--ozone-platform=wayland", "--hide-scrollbars"])
        firefox = playwright.firefox.launch(headless=False, firefox_user_prefs={"gfx.webrender.all": True})
        print("versions: chrome", chrome.version, "firefox", firefox.version, flush=True)
        for width in WIDTHS:
            results.append(frames(chrome, "chrome", width, out, ""))
            results.append(frames(firefox, "firefox", width, out, css))
        chrome.close()
        if not control:
            errors = []
            cc.run(firefox, None, errors, is_mobile=False)
            behaviour = list(cc.failures) + [f"page error: {e}" for e in errors[:3]]
        firefox.close()
    results_file.write_text(json.dumps({"frames": results, "behaviour": behaviour}))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("out")
    parser.add_argument("--control", choices=CONTROLS)
    parser.add_argument("--card", default="renderD128")
    parser.add_argument("--inside", help=argparse.SUPPRESS)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    if args.inside:
        inside(out, Path(args.inside), args.control)
        return 0
    out.mkdir(parents=True, exist_ok=True)
    results_file = out / "results.json"
    results_file.unlink(missing_ok=True)
    env = {**os.environ, "WLR_BACKENDS": "headless", "WLR_RENDER_DRM_DEVICE": f"/dev/dri/{args.card}",
           "WLR_LIBINPUT_NO_DEVICES": "1", "XDG_CURRENT_DESKTOP": "cage", "WLR_LOG": "error"}
    env.pop("DISPLAY", None)
    env.pop("WAYLAND_DISPLAY", None)
    command = ["cage", "--", sys.executable, __file__, str(out), "--inside", str(results_file)]
    if args.control:
        command += ["--control", args.control]
    subprocess.run(command, env=env, timeout=570, check=False)
    if not results_file.exists():
        print("FAILED: the run inside cage left no results")
        return 2 if args.control else 1
    found = json.loads(results_file.read_text())
    failed = list(found["behaviour"])
    for r in found["frames"]:
        label = f"{r['browser']} at {r['width']}"
        for what, ok in judge(r, out):
            print(f"{'OK  ' if ok else 'FAIL'} {label}: {what}")
            if not ok:
                failed.append(f"{label}: {what}")
    for what in found["behaviour"]:
        print(f"FAIL firefox behaviour: {what}")
    sheets(out)
    if args.control:
        named = CONTROLS[args.control][1]
        chrome_red = [f for f in failed if f.startswith("chrome")]
        right = any(f.startswith("firefox") and named in f for f in failed) and not chrome_red
        print(f"CONTROL {args.control}: " + ("red on the read it names" if right else f"did NOT go red on {named!r}"))
        return 1 if right else 2
    print("FAILED" if failed else "ALL OK")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
