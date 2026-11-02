#!/usr/bin/env python3
"""See Gobelin's 3D badge drawn in Firefox, against Chrome, over file://, on the real card.

    python3 tools/check_badge_browsers.py OUT_DIR [--control flat|gold] [--card renderD128]

tools/check_badge.py reads computed matrices, and those read the same with the 3D flattened: only
pixels say what a browser drew. So at 1280 and 390, headed, in Chrome (what Simon passed on r3) and
Playwright's Firefox, this freezes the badge at its front, its edge-on moment, the back the turn
shows and the back a real hover shows, and reads each picture:
- front: CRUNCH is gold, not the crimson of the layers under it, and the medal is there;
- edge-on: the card is a narrow strip with thickness;
- both backs: the Fiche technique on kraft, nothing of the front showing through;
- Firefox differs from Chrome by no more than fonts and antialiasing do.
Then it runs every check of check_badge.py in Firefox.

--control breaks the page in Firefox only and must go red on the read it names: flat removes
preserve-3d, gold puts background-clip: text back on the element with the transform (r59's bug).
Exit 1 is that red; exit 2 means it stayed green or failed for another reason.

Headed runs inside cage, a compositor of its own that shows nothing on screen, as in
tools/check_trombone_browsers.py. Needs cage, Chrome, `playwright install firefox`, Pillow.
Safari: tools/check_badge_safari.py.
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
import check_badge  # noqa: E402

WIDTHS = (1280, 390)
TURNED = 20750  # ms into the cycle: .tour has the back towards us
CONTROLS = {
    "flat": (".balance, .tour, .plaque, .relief, .tranche { transform-style: flat !important; }",
             "the turn shows the Fiche technique"),
    "gold": (""".crunch { background: var(--or); -webkit-background-clip: text; background-clip: text; color: transparent; }
                .crunch span { background: none; -webkit-background-clip: border-box; background-clip: border-box; }""",
             "CRUNCH is gold"),
}
PLACES = """() => {
  const c = document.querySelector('.vitrine').getBoundingClientRect();
  const of = s => { const r = document.querySelector(s).getBoundingClientRect();
    return [r.left - c.left, r.top - c.top, r.right - c.left, r.bottom - c.top].map(Math.round); };
  return { crunch: of('.crunch'), medal: of('.medaille') };
}"""
SETTLE = "() => new Promise(d => requestAnimationFrame(() => requestAnimationFrame(d)))"
# What each colour family is, in (r, g, b). Kraft is warm and pale, gold far more saturated.
CRIMSON = lambda r, g, b: r > 90 and g < 60 and b < 95 and r > 2 * g
GOLD = lambda r, g, b: r > 150 and g > 100 and r - b >= 120
GREEN = lambda r, g, b: g > 150 and b < 110 and g > r + 15
KRAFT = lambda r, g, b: r > 170 and g > 130 and 40 <= r - b <= 130
DARK = lambda r, g, b: r < 80 and g < 70 and b < 60
CARD = lambda r, g, b: r > 90 and r > g > b and r - b > 30


def share(picture, box, kind):
    raw = picture.crop(box).convert("RGB").tobytes()
    total = len(raw) // 3
    return sum(1 for i in range(0, len(raw), 3) if kind(raw[i], raw[i + 1], raw[i + 2])) / max(1, total)


def card_box(picture):
    """Where the card is drawn: the warm pixels in the case. The ribbon's pink is not warm enough."""
    w, h = picture.size
    rgb = picture.convert("RGB").load()
    columns = [x for x in range(w) if sum(CARD(*rgb[x, y]) for y in range(0, h, 4)) > 8]
    rows = [y for y in range(h) if sum(CARD(*rgb[x, y]) for x in range(0, w, 2)) > 2]
    return (columns[0], rows[0], columns[-1] + 1, rows[-1] + 1) if columns and rows else (0, 0, 1, 1)


def back_read(picture):
    box = card_box(picture)
    return {"kraft": share(picture, box, KRAFT), "dark": share(picture, box, DARK),
            "crimson": share(picture, box, CRIMSON), "green": share(picture, box, GREEN)}


def frames(browser, name, width, out, css):
    """The four frozen pictures of one browser at one width, and what they read."""
    errors = []
    context, page = check_badge.opened(browser, errors, width)
    page.evaluate("document.querySelector('.vitrine').scrollIntoView({block: 'center'})")
    if css:
        page.add_style_tag(content=css)

    def freeze(t):
        page.evaluate(check_badge.FREEZE, t)
        page.evaluate(SETTLE)
        page.wait_for_timeout(150)

    def picture(label):
        path = out / f"{name}-{width}-{label}.png"
        check_badge.shot(page, path)
        return Image.open(path).convert("RGB")

    freeze(0)
    front = picture("front")
    places = page.evaluate(PLACES)
    # The edge-on moment is where the chain of transforms crosses zero, searched not assumed.
    moments = []
    for t in range(19500, 20100, 10):
        page.evaluate(check_badge.FREEZE, t)
        moments.append((abs(page.evaluate(check_badge.FACING)), t))
    angle, edge_at = min(moments)
    freeze(edge_at)
    edge = picture("edge")
    freeze(TURNED)
    turned = picture("turned")
    freeze(0)
    box = page.locator(".vitrine").bounding_box()
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.wait_for_timeout(1200)
    back = picture("back")
    context.close()

    edge_box = card_box(edge)
    return {
        "browser": name, "width": width, "errors": errors, "edge_at": edge_at, "edge_angle": round(angle, 3),
        "gold": share(front, places["crunch"], GOLD), "crimson": share(front, places["crunch"], CRIMSON),
        "green": share(front, places["medal"], GREEN), "edge_width": edge_box[2] - edge_box[0],
        "front_width": card_box(front)[2] - card_box(front)[0],
        "turned": back_read(turned), "back": back_read(back),
    }


def apart(out, width, label):
    """The share of pixels Firefox draws far from Chrome: more than fonts and antialiasing can."""
    a = Image.open(out / f"chrome-{width}-{label}.png").convert("RGB")
    b = Image.open(out / f"firefox-{width}-{label}.png").convert("RGB")
    d = ImageChops.difference(a, b).convert("L")
    return sum(d.histogram()[60:]) / (d.width * d.height)


def judge(r, out):
    """(what, ok) for one browser at one width."""
    checks = [
        ("CRUNCH is gold", r["gold"] > 0.12 and r["crimson"] < 0.10),
        ("the medal is on the front", r["green"] > 0.02),
        ("edge-on is a strip with thickness", 3 <= r["edge_width"] <= 40 and r["edge_width"] < r["front_width"] / 4),
        ("no page error", not r["errors"]),
    ]
    for key, what in (("turned", "the turn"), ("back", "a hover")):
        b = r[key]
        checks.append((f"{what} shows the Fiche technique",
                       b["kraft"] > 0.55 and b["dark"] > 0.012 and b["crimson"] < 0.002 and b["green"] < 0.002))
    if r["browser"] == "firefox":
        for label in ("front", "edge", "turned", "back"):
            d = apart(out, r["width"], label)
            checks.append((f"{label} is drawn as in Chrome ({d:.1%} far apart)", d < 0.05))
    return checks


def sheets(out):
    for width in WIDTHS:
        pictures = [Image.open(out / f"{n}-{width}-{l}.png").convert("RGB")
                    for n in ("chrome", "firefox") for l in ("front", "edge", "back", "turned")]
        w, h = min(p.width for p in pictures), pictures[0].height
        w = min(w, 360)
        sheet = Image.new("RGB", (w * 4, h * 2))
        for i, p in enumerate(pictures):
            x = (p.width - w) // 2
            sheet.paste(p.crop((x, 0, x + w, h)), ((i % 4) * w, (i // 4) * h))
        sheet.save(out / f"planche-{width}.png")


def inside(out, results_file, control):
    css = CONTROLS[control][0] if control else ""
    results, behaviour = [], []
    with sync_playwright() as playwright:
        chrome = playwright.chromium.launch(channel="chrome", headless=False,
                                            # A classic scrollbar narrows Chrome's case by 15 px: Firefox's overlays.
                                            args=["--ozone-platform=wayland", "--hide-scrollbars"])
        firefox = playwright.firefox.launch(headless=False, firefox_user_prefs={"gfx.webrender.all": True})
        print("versions: chrome", chrome.version, "firefox", firefox.version, flush=True)
        for width in WIDTHS:
            results.append(frames(chrome, "chrome", width, out, ""))
            results.append(frames(firefox, "firefox", width, out, css))
        chrome.close()
        if not control:
            errors = []
            check_badge.run(firefox, WIDTHS, None, errors, is_mobile=False)
            behaviour = list(check_badge.failures) + [f"page error: {e}" for e in errors[:3]]
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
    subprocess.run(command, env=env, timeout=540, check=False)
    if not results_file.exists():
        print("FAILED: the run inside cage left no results")
        return 2 if args.control else 1
    found = json.loads(results_file.read_text())
    failed = list(found["behaviour"])
    for r in found["frames"]:
        label = f"{r['browser']} at {r['width']}"
        print(f"     {label}: gold {r['gold']:.1%}, crimson {r['crimson']:.1%}, medal green {r['green']:.1%}, "
              f"edge {r['edge_width']}px of {r['front_width']}px at {r['edge_at']} ms, "
              f"turned {r['turned']}, back {r['back']}".replace("'", ""))
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
