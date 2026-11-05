#!/usr/bin/env python3
"""The root list's envelope frame by frame, which a still or a real-time hover cannot catch (r95).

    python3 tools/check_racine_frames.py [OUT] [--step MS] [--control clip|early]

Hovers a card, pauses every transition and seeks them together through time, opening then closing,
in Chrome and Firefox, and through the loop a screen with no pointer gets, in Chrome. Each moment is
shot three ways: as it is, with the flap hidden, with flap and letter hidden. It fails on:
- flap over letter: a pixel the letter draws, once risen out of the pocket, that the flap changes;
- flap adrift: the flap stands clear of the pocket but does not reach it at the hinge;
- a short read: on the loop, the letter holds at its full height for under 0.8 s (r99).
OUT gets a contact sheet per browser and phase.

--control early puts back the letter's start at 0.3 s: Firefox then draws the flap over it.
--control clip puts back the clip-paths: Chrome then draws the flap's tip adrift. Both must fail.
Needs Playwright, Chrome and its Firefox.
"""
import io
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw
from playwright.sync_api import sync_playwright

PAGE = (Path(__file__).resolve().parent.parent / "index.html").as_uri()
SCALE = 2
OVER_AT_MOST = 60       # CSS px of letter: the flap's soft edge against the letter's shadow is about 15
CLEAR_FROM = 10         # CSS px the flap stands above the pocket before its hinge is read
HINGE_AT_LEAST = 0.5    # share of the middle of the hinge the flap must draw
HOLD_AT_LEAST = 800     # ms the phone's letter stays up: it stood 0.9 s before r95, Simon's timing
CONTROLS = {
    "early": ".cible > a:hover .lettre { transition: transform 0.75s var(--ressort) 0.3s !important; }",
    "clip": """.rabat::before { -webkit-mask: none !important; mask: none !important;
                                clip-path: polygon(0 0, 100% 0, 50% 66%); }
               .rabat::after { -webkit-mask: none !important; mask: none !important;
                               clip-path: polygon(50% 34%, 100% 100%, 0 100%); }""",
}
SEEK = "t => { for (const a of document.getAnimations()) { a.pause(); a.currentTime = t; } }"
BOX = """c => { const r = document.querySelector('.cible.' + c + ' .poche').getBoundingClientRect();
                return {x: r.x - 12, y: r.y - r.height * 1.05, width: r.width + 24, height: r.height * 2.2,
                        pocket: r.height * 1.05, side: 12, pocketWidth: r.width}; }"""
RISEN = """c => { const k = document.querySelector('.cible.' + c);
  return k.querySelector('.poche').getBoundingClientRect().y - k.querySelector('.lettre').getBoundingClientRect().y; }"""


def differs(a, b):
    return ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v > 24 else 0)


def count(mask):
    return sum(1 for v in mask.tobytes() if v)


def read_moment(page, card):
    """What the frame shows, in CSS px: letter under the flap, how far the flap stands above the
    pocket, and the share of the hinge it draws."""
    box = page.evaluate(BOX, card)
    clip = {k: box[k] for k in ("x", "y", "width", "height")}

    def shot():
        return Image.open(io.BytesIO(page.screenshot(clip=clip))).convert("RGB")

    whole = shot()
    no_flap_tag = page.add_style_tag(content=f".cible.{card} .rabat {{ visibility: hidden !important; }}")
    no_flap = shot()
    no_letter_tag = page.add_style_tag(content=f".cible.{card} .lettre {{ visibility: hidden !important; }}")
    no_letter = shot()
    no_letter_tag.evaluate("e => e.remove()")
    no_flap_tag.evaluate("e => e.remove()")

    flap = differs(whole, no_flap)
    over = count(ImageChops.multiply(differs(no_flap, no_letter), flap)) // SCALE ** 2
    pocket = round(box["pocket"] * SCALE)
    above = flap.crop((0, 0, flap.width, pocket - SCALE)).getbbox()
    stands = (pocket - above[1]) / SCALE if above else 0
    left = round((box["side"] + box["pocketWidth"] * 0.3) * SCALE)
    right = round((box["side"] + box["pocketWidth"] * 0.7) * SCALE)
    strip = flap.crop((left, pocket - 4 * SCALE, right, pocket - 2 * SCALE))
    hinge = count(strip) / max(strip.width * strip.height, 1)
    return whole, over, stands, hinge


def walk(page, card, name, moments, problems, out):
    """One phase: the transitions are already running, each moment is sought and read."""
    sheet, heights = [], []
    for moment in moments:
        page.evaluate(SEEK, moment)
        whole, over, stands, hinge = read_moment(page, card)
        risen = page.evaluate(RISEN, card)
        print(f"{name} {moment:4d} ms  letter risen {risen:5.1f}  flap over {over:5d}  "
              f"flap stands {stands:5.1f}  hinge {hinge:4.0%}")
        if risen > 1 and over > OVER_AT_MOST:
            problems.append(f"{name} at {moment} ms: the flap is over {over} px of the risen letter")
        if risen <= 1 and stands >= CLEAR_FROM and hinge < HINGE_AT_LEAST:
            problems.append(f"{name} at {moment} ms: the flap stands {stands:.0f} px adrift, "
                            f"{hinge:.0%} of its hinge drawn")
        sheet.append((moment, whole, over))
        heights.append(risen)
    if out:
        write_sheet(sheet, out / f"racine-images-{name}.png")
    return heights


def write_sheet(sheet, path):
    w, h = sheet[0][1].size
    columns = 12
    rows = (len(sheet) + columns - 1) // columns
    board = Image.new("RGB", (columns * (w + 6), rows * (h + 26)), "white")
    pen = ImageDraw.Draw(board)
    for i, (moment, picture, over) in enumerate(sheet):
        x, y = (i % columns) * (w + 6), (i // columns) * (h + 26)
        board.paste(picture, (x, y + 22))
        pen.text((x + 2, y + 4), f"{moment} ms  over {over}", fill="black")
    board.save(path)


def longest(page):
    return page.evaluate("""() => Math.max(...document.getAnimations().map(a => {
        const e = a.effect.getComputedTiming(); return e.delay + e.duration; }))""")


def check_hover(browser, name, css, step, problems, out):
    card = "inviolia"
    context = browser.new_context(viewport={"width": 1280, "height": 1000}, device_scale_factor=SCALE)
    page = context.new_page()
    page.goto(PAGE)
    if css:
        page.add_style_tag(content=css)
    page.wait_for_timeout(1500)
    page.locator(f".cible.{card} > a").scroll_into_view_if_needed()
    page.hover(f".cible.{card} > a")
    page.evaluate(SEEK, 0)
    walk(page, card, f"{name}-ouvre", range(0, int(longest(page)) + step, step), problems, out)
    page.evaluate("() => { for (const a of document.getAnimations()) a.finish(); }")
    page.wait_for_timeout(100)
    page.mouse.move(0, 0)
    page.evaluate(SEEK, 0)
    walk(page, card, f"{name}-ferme", range(0, int(longest(page)) + step, step), problems, out)
    context.close()


def check_loop(browser, css, step, problems, out):
    """The first card's loop on a screen with no pointer: opening, then closing, of its 9 s."""
    card = "merlin"
    context = browser.new_context(viewport={"width": 390, "height": 800}, has_touch=True,
                                  is_mobile=True, device_scale_factor=SCALE)
    page = context.new_page()
    page.goto(PAGE)
    if css:
        page.add_style_tag(content=css)
    page.wait_for_timeout(300)
    every = max(step, 100)
    heights = walk(page, card, "chrome-boucle", range(150, 3800, every), problems, out)
    held = sum(height >= max(heights) - 1 for height in heights) * every
    print(f"chrome-boucle: the letter holds at full height about {held} ms")
    if held < HOLD_AT_LEAST:
        problems.append(f"chrome-boucle: the letter holds at full height only about {held} ms")
    context.close()


def main(args):
    step = 50
    control = None
    if "--step" in args:
        at = args.index("--step")
        step = int(args[at + 1])
        del args[at:at + 2]
    if "--control" in args:
        at = args.index("--control")
        control = args[at + 1]
        if control not in CONTROLS:
            sys.exit(f"--control {' or '.join(CONTROLS)}, not {control}")
        del args[at:at + 2]
    css = CONTROLS.get(control, "")
    out = Path(args[0]) if args else None
    if out:
        out.mkdir(parents=True, exist_ok=True)
    problems = []
    with sync_playwright() as playwright:
        chrome = playwright.chromium.launch(channel="chrome")
        check_hover(chrome, "chrome", css, step, problems, out)
        check_loop(chrome, css, step, problems, out)
        chrome.close()
        firefox = playwright.firefox.launch()
        check_hover(firefox, "firefox", css, step, problems, out)
        firefox.close()
    for problem in problems:
        print(f"FAILED: {problem}")
    print("OK" if not problems else f"{len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
