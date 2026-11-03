#!/usr/bin/env python3
"""Look at what tools/render_pages.py freezes on purpose: Au Dernier Prix's 3D coffin.

    python3 tools/check_configurateur.py [OUT_DIR]

Over file://, in Chrome, at phone and desktop widths:
- it sways, and stands still under reduced motion, where every choice below still works;
- the pointer turns it, strip by strip, and leaving brings back the chosen angle; a click stays;
- a real Tab and arrow keys turn it, a real finger too, the four view buttons go where they say;
- the lid's checkbox flashes until first used, and not under reduced motion;
- each option does what it says: the wood, the handles counted, the lining, the plate, the lid, the kit;
- the total the browser sums is the right one, read as pixels: a counter is not in the DOM;
- the page is no wider than its window, whatever is open, and the home's button leads here;
- nothing is fetched after load, no failed request, no console error.

What it reads is computed matrices, which stay right when the browser draws the 3D wrong: for what
is really on screen, and for Firefox, see tools/check_configurateur_browsers.py.
With OUT_DIR, leaves pictures there. Needs Playwright, Chrome, Pillow.
"""

import io
import sys
from pathlib import Path

from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parent.parent
PAGE = (REPO / "dernier-prix/configurateur.html").as_uri()
HOME = (REPO / "dernier-prix/index.html").as_uri()
WIDTHS = (360, 390, 768, 1280)
ANGLES = list(range(-180, 181, 30))
SETTLE = 950  # ms, the longest transition (.couvercle) and a margin
MODELS = {"m-pin": 449, "m-peuplier": 519, "m-chene": 833}
ADDS = {"n0": 0, "n2": 24, "n4": 48, "n6": 72, "i-brut": 0, "i-poly": 39, "i-satin": 89,
        "q-non": 0, "q-oui": 25, "k-non": 0, "k-oui": -40, "g-0": 0, "g-5": 29, "g-10": 49}
# Each option alone, then the extremes and a few in between.
TOTALS = [[m] for m in MODELS] + [["m-pin", a] for a in ADDS] + [
    ["m-chene", "n6", "i-satin", "q-oui", "g-10"],
    ["m-peuplier", "n6", "i-satin", "q-oui", "k-oui", "g-10"],
    ["m-pin", "n2", "i-poly", "k-oui", "g-5"],
    ["m-chene", "n4", "i-poly", "q-oui", "k-oui", "g-5"],
]
ANGLE = """() => {
  const m = new DOMMatrix(getComputedStyle(document.querySelector('.plateau')).transform);
  return Math.round(Math.atan2(-m.m13, m.m11) * 180 / Math.PI);
}"""
SWAY = "() => new DOMMatrix(getComputedStyle(document.querySelector('.balance')).transform).m13"
FREEZE = """t => document.getAnimations().forEach(a => {
  if (a.animationName) { a.pause(); a.currentTime = t; }
})"""
MATRIX = """s => { const m = new DOMMatrix(getComputedStyle(document.querySelector(s)).transform);
  return [m.m41, m.m42, m.m43, Math.round(Math.atan2(m.m23, m.m22) * 180 / Math.PI)]; }"""
SHOWN = "s => [...document.querySelectorAll(s)].filter(e => getComputedStyle(e).display !== 'none').length"
failures = []


def check(ok, what):
    print(f"{'OK  ' if ok else 'FAIL'} {what}")
    if not ok:
        failures.append(what)


def opened(browser, errors, width, url=PAGE, **options):
    context = browser.new_context(viewport={"width": width, "height": 900}, **options)
    page = context.new_page()
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: m.type == "error" and errors.append(m.text))
    page.on("requestfailed", lambda r: errors.append(f"failed: {r.url}"))
    page.goto(url, wait_until="load")
    return context, page


def same_angle(a, b):
    """-180 and 180 are the same place, and a matrix cannot tell them apart."""
    return abs((a - b + 180) % 360 - 180) <= 1


def choose(page, *ids):
    """A real click on the label a student clicks."""
    for i in ids:
        page.locator(f"label:has(#{i})").click()


def options(page, settle=SETTLE):
    choose(page, "m-chene")
    wood = page.evaluate("getComputedStyle(document.querySelector('.avant .bois')).backgroundImage")
    check("bois-chene.webp" in wood, "the oak puts the oak on the walls")
    choose(page, "m-peuplier")
    wood = page.evaluate("getComputedStyle(document.querySelector('.h-de')).backgroundImage")
    check("bois-peuplier.webp" in wood, "the poplar puts the poplar on the lid")
    for option, count in (("n0", 0), ("n2", 2), ("n4", 4), ("n6", 6)):
        choose(page, option)
        check(page.evaluate(SHOWN, ".poignee") == count, f"{option} shows {count} handles")
    choose(page, "n0", "i-satin")
    check("gradient" in page.evaluate("getComputedStyle(document.querySelector('.fond')).backgroundImage")
          and "bois" not in page.evaluate("getComputedStyle(document.querySelector('.fond')).backgroundImage"),
          "the lining replaces the bare wood")
    choose(page, "i-brut")
    check(page.evaluate(SHOWN, ".plaque-laiton") == 0, "no plate at first")
    choose(page, "q-oui")
    check(page.evaluate(SHOWN, ".plaque-laiton") == 1, "the plate appears")
    choose(page, "q-non")

    closed = page.evaluate(MATRIX, ".couvercle")
    page.locator("label.ouvrir").click()
    page.wait_for_timeout(settle)
    opened_lid = page.evaluate(MATRIX, ".couvercle")
    check(abs(closed[3]) < 2 and 100 <= opened_lid[3] <= 108, f"the lid turns on its hinge ({closed[3]} to {opened_lid[3]})")
    page.locator("label.ouvrir").click()
    page.wait_for_timeout(settle)
    check(abs(page.evaluate(MATRIX, ".couvercle")[3]) < 2, "the lid closes")

    walls = {s: page.evaluate(MATRIX, s) for s in (".avant", ".arriere", ".bout-d", ".bout-g", ".couvercle")}
    choose(page, "k-oui")
    page.wait_for_timeout(settle)
    kit = {s: page.evaluate(MATRIX, s) for s in walls}
    check(abs(kit[".avant"][2] - walls[".avant"][2] - 92) < 1 and abs(kit[".arriere"][2] - walls[".arriere"][2] + 92) < 1
          and abs(kit[".bout-d"][0] - walls[".bout-d"][0] - 92) < 1 and abs(kit[".bout-g"][0] - walls[".bout-g"][0] + 92) < 1,
          "the kit moves four walls apart")
    check(abs(kit[".couvercle"][1] - walls[".couvercle"][1] + 150) < 1, "the kit lifts the lid")
    wide = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
    check(wide <= 0, f"the kit does not widen the page ({wide}px)")
    choose(page, "k-non", "m-pin")
    page.wait_for_timeout(settle)


FLASH = """() => { const label = document.querySelector('label.ouvrir');
  const running = document.getAnimations().filter(a => a.animationName === 'eclat').length;
  return [running, getComputedStyle(label, '::after').opacity]; }"""


def flash(browser, errors):
    """The lid's checkbox flashes until it is first used, shut again or not; it can be seen, not only run."""
    context, page = opened(browser, errors, 1280)
    label = page.locator("label.ouvrir")
    running, shown = page.evaluate(FLASH)
    check(running == 1 and shown == "1", f"the lid's checkbox flashes before it is used ({running}, {shown})")
    page.mouse.move(0, 0)
    page.evaluate("t => document.getAnimations().forEach(a => { if (a.animationName === 'eclat') { a.pause(); a.currentTime = t; } })", 1650)
    bright = tile(page, "label.ouvrir")
    page.evaluate("t => document.getAnimations().forEach(a => { if (a.animationName === 'eclat') a.currentTime = t; })", 0)
    dim = tile(page, "label.ouvrir")
    check(ImageChops.difference(bright, dim).getbbox() is not None, "the flash changes pixels")
    label.click()
    page.wait_for_timeout(50)
    check(page.evaluate(FLASH)[1] == "0", "using it stops the flash")
    label.click()
    page.wait_for_timeout(300)
    check(page.evaluate(FLASH)[1] == "0", "shut again, it does not flash again")
    context.close()


def tile(page, selector):
    return Image.open(io.BytesIO(page.locator(selector).screenshot())).convert("RGB")


def price_is(page, selector, amount):
    """The drawn total against the same box holding the amount as written text. Pixels, or nothing.

    Digits only: a counter and the string after it are two runs, and " €" lands a fraction of a
    pixel away from where one written run puts it (seen at 474 €, in Chrome)."""
    digits = page.add_style_tag(content='.total::after { content: counter(total) !important; }')
    drawn = tile(page, selector)
    digits.evaluate("e => e.remove()")
    style = page.add_style_tag(content=f'.total::after {{ content: "{amount}" !important; }}')
    written = tile(page, selector)
    style.evaluate("e => e.remove()")
    return drawn.size == written.size and ImageChops.difference(drawn, written).getbbox() is None


def totals(page):
    resets = ("n0", "i-brut", "q-non", "k-non", "g-0", "m-pin")
    for combo in TOTALS:
        choose(page, *resets)
        choose(page, *combo)
        amount = sum(MODELS.get(i, 0) + ADDS.get(i, 0) for i in combo)
        check(price_is(page, ".ticket .prixf", amount) and price_is(page, ".prix-scene", amount),
              f"{' + '.join(combo)} = {amount} €, on the ticket and on the scene")
    choose(page, *resets)
    # Without this, a read that sees no difference proves nothing.
    check(not price_is(page, ".ticket .prixf", 450), "the read tells 449 € from 450 €")


def run(browser, out, errors, is_mobile=True):
    """Every check below, in one browser. Firefox refuses is_mobile; has_touch alone taps there."""
    for width in WIDTHS:
        context, page = opened(browser, errors, width)
        page.locator(".scene").scroll_into_view_if_needed()
        page.evaluate(FREEZE, 0)
        a = page.evaluate(SWAY)
        page.evaluate(FREEZE, 12000)
        b = page.evaluate(SWAY)
        check(abs(a - b) > 0.1, f"{width}: it sways ({a:.2f}, {b:.2f})")
        page.evaluate(FREEZE, 6000)
        check(same_angle(page.evaluate(ANGLE), -30), f"{width}: it starts at three quarters")

        box = page.locator(".scene").bounding_box()
        hover = list(enumerate(ANGLES)) if width == 1280 else list(enumerate(ANGLES))[::4]
        for i, angle in hover:
            page.mouse.move(box["x"] + box["width"] * (i + 0.5) / 13, box["y"] + box["height"] / 2)
            page.wait_for_timeout(650)
            found = page.evaluate(ANGLE)
            check(same_angle(found, angle), f"{width}: the pointer on strip {i} turns it to {angle} ({found})")
        page.mouse.move(0, 0)
        page.wait_for_timeout(650)
        check(same_angle(page.evaluate(ANGLE), -30), f"{width}: leaving brings the chosen angle back")
        page.mouse.click(box["x"] + box["width"] * 10.5 / 13, box["y"] + box["height"] / 2)
        page.mouse.move(0, 0)
        page.wait_for_timeout(650)
        check(same_angle(page.evaluate(ANGLE), 120), f"{width}: a click stays when the pointer leaves")
        for label, angle in (("Face", 0), ("Trois-quarts", -30), ("Bout", 90), ("Dos", 180)):
            page.locator(".vues label", has_text=label).click()
            page.mouse.move(0, 0)
            page.wait_for_timeout(650)
            check(same_angle(page.evaluate(ANGLE), angle), f"{width}: {label} goes to {angle}")
        wide = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
        check(wide <= 0, f"{width}: the page is no wider than its window ({wide}px)")
        if width in (390, 1280):
            options(page)
        if out:
            page.screenshot(path=out / f"page-{width}.png", full_page=True)
        context.close()

    flash(browser, errors)

    context, page = opened(browser, errors, 1280)
    totals(page)
    context.close()

    context, page = opened(browser, errors, 1280)
    seen = []
    page.on("request", lambda r: seen.append(r.url))
    choose(page, "m-chene", "n6", "i-satin", "q-oui", "k-oui", "g-10", "m-peuplier", "m-pin")
    page.locator("label.ouvrir").click()
    page.wait_for_timeout(300)
    fetched = [u for u in seen if not u.endswith((".webp", ".svg"))]
    check(not fetched, f"choosing sends nothing and asks for nothing but its woods {fetched[:3]}")
    context.close()

    # Reduced motion: stands still, jumps at once, and every choice still works.
    context, page = opened(browser, errors, 1280, reduced_motion="reduce")
    check(page.evaluate("document.getAnimations().length") == 0, "reduced motion: nothing runs")
    check(abs(page.evaluate(SWAY)) < 0.01 and same_angle(page.evaluate(ANGLE), -30), "reduced motion: stands still at three quarters")
    box = page.locator(".scene").bounding_box()
    page.mouse.move(box["x"] + box["width"] * 9.5 / 13, box["y"] + box["height"] / 2)
    page.wait_for_timeout(50)
    check(same_angle(page.evaluate(ANGLE), 90), "reduced motion: the pointer still turns it, at once")
    page.mouse.move(0, 0)
    options(page, settle=50)
    context.close()

    # A real finger and a real Tab key: nothing above proves either.
    context, page = opened(browser, errors, 390, has_touch=True, **({"is_mobile": True} if is_mobile else {}))
    box = page.locator(".scene").bounding_box()
    page.locator(".scene").tap(position={"x": box["width"] * 3.5 / 13, "y": box["height"] / 2})
    page.wait_for_timeout(650)
    check(same_angle(page.evaluate(ANGLE), -90), "phone: a tap on a strip turns it")
    if is_mobile:
        check(page.locator(".au-doigt").is_visible() and not page.locator(".a-souris").is_visible(),
              "phone: it says touch, not mouse")
    page.locator("label:has(#n4)").tap()
    check(page.evaluate(SHOWN, ".poignee") == 4, "phone: a tap chooses an option")
    context.close()
    context, page = opened(browser, errors, 1280)
    for _ in range(40):
        page.keyboard.press("Tab")
        if page.evaluate("document.activeElement.name === 'vue'"):
            break
    check(page.evaluate("document.activeElement.name") == "vue", "keyboard: Tab reaches the coffin")
    check(page.evaluate("getComputedStyle(document.querySelector('.scene')).outlineStyle") == "solid",
          "keyboard: the coffin shows it has the focus")
    page.keyboard.press("ArrowRight")
    page.wait_for_timeout(650)
    check(same_angle(page.evaluate(ANGLE), 0), "keyboard: an arrow turns it")
    for _ in range(40):
        page.keyboard.press("Tab")
        if page.evaluate("document.activeElement.id") == "ouvert":
            break
    page.keyboard.press("Space")
    page.wait_for_timeout(SETTLE)
    check(page.evaluate(MATRIX, ".couvercle")[3] > 100, "keyboard: Space opens the lid")
    context.close()

    context, page = opened(browser, errors, 1280, url=HOME)
    page.locator(".go.c", has_text="Configurer en 3D").click()
    page.wait_for_load_state("load")
    check(page.url.endswith("dernier-prix/configurateur.html"), "the home's button opens the configurator")
    context.close()


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if out:
        out.mkdir(parents=True, exist_ok=True)
    errors = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome")
        run(browser, out, errors)
        browser.close()
    check(not errors, f"no error on the page {errors[:3] if errors else ''}")
    print(f"{len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
