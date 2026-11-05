#!/usr/bin/env python3
"""The root list's moving parts, which tools/render_pages.py freezes, in Chrome and Firefox.

    python3 tools/check_racine.py [OUT] [--control flat|big]

For each of the six cards: its picture is loaded, and resting it hides its letter. Hovering, then
keyboard focus, swings the flap over and lifts the letter clear of the envelope, in front of the
open flap: read from the pixels, since computed matrices come out the same with the 3D flattened
(r59). On Chrome: a screen with no pointer opens the envelopes by itself, reduced motion stops all
of it, no width overflows, and at no width does a word go under an envelope, at rest or with its
card hovered. OUT gets a rest, mid and open picture per browser.

--control flat flattens the 3D: the open flap then covers the letter, and this must fail.
--control big puts back r82's scale(1.3) on hover: a word goes under the envelope, and this must fail.
Needs Playwright, Chrome and its Firefox, which a student never does.
"""
import io
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

PAGE = (Path(__file__).resolve().parent.parent / "index.html").as_uri()
CARDS = ("merlin", "gobelin", "courtepaille", "inviolia", "dernier-prix", "source-eclat")
# 1007 and 1265 are 1024 and 1280 less a classic scrollbar: the widest overlaps of r82 stood there.
WIDTHS = (320, 390, 600, 800, 1000, 1007, 1024, 1265, 1280, 1600, 1920)
FLAT = ".plaque, .enveloppe, .rabat { transform-style: flat !important; }"
BIG = ".cible > a:hover .enveloppe { transform: translateZ(5.5rem) rotate(0deg) scale(1.3); }"
SETTLE_MS = 1500
HOVER_SETTLE_MS = 750   # the envelope's transition is 0.55 s
PAPER_AT_LEAST = 0.6    # share of paper where the letter stands, above the envelope

PARTS = """c => {
  const card = document.querySelector('.cible.' + c);
  const box = s => { const r = card.querySelector(s).getBoundingClientRect();
                     return {x: r.x, y: r.y, w: r.width, h: r.height}; };
  const img = card.querySelector('.photo');
  return {flap: new DOMMatrix(getComputedStyle(card.querySelector('.rabat')).transform).m22,
          letter: box('.lettre'), envelope: box('.poche'),
          picture: img.complete ? img.naturalWidth : 0, words: card.querySelector('h2').textContent};
}"""

# How far a line of the card's words passes the envelope's left edge, in px; negative is clear.
OVER = """c => {
  const k = document.querySelector('.cible.' + c), e = k.querySelector('.poche').getBoundingClientRect();
  let worst = -1e9;
  for (const s of ['h2', 'p']) {
    const r = document.createRange(); r.selectNodeContents(k.querySelector('.texte ' + s));
    for (const b of r.getClientRects())
      if (b.bottom > e.top + 1 && b.top < e.bottom - 1) worst = Math.max(worst, b.right - e.left);
  }
  const t = k.querySelector('.texte').getBoundingClientRect(), p = k.querySelector('.plaque').getBoundingClientRect();
  return {over: worst, above: p.top - t.top};
}"""


def paper_share(picture, area):
    """The share of paper in the middle of the part of the letter above the envelope. Paper is
    near white in every channel: the manila flap is light too, but its blue is far lower."""
    letter, envelope = area
    box = (round(letter["x"] + letter["w"] * 0.3), round(letter["y"] + 2),
           round(letter["x"] + letter["w"] * 0.7), round(envelope["y"] - 2))
    crop = Image.open(io.BytesIO(picture)).convert("RGB").crop(box)
    pixels = [crop.getpixel((x, y)) for x in range(crop.width) for y in range(crop.height)]
    return sum(min(p) > 200 for p in pixels) / max(len(pixels), 1)


def check_open(page, card, how, problems):
    parts = page.evaluate(PARTS, card)
    risen = parts["envelope"]["y"] - parts["letter"]["y"]
    if parts["flap"] > -0.9:
        problems.append(f"{card}, {how}: the flap did not swing over (m22 {parts['flap']:.2f})")
    if risen < 20:
        problems.append(f"{card}, {how}: the letter rose only {risen:.0f} px above the envelope")
    share = paper_share(page.screenshot(), (parts["letter"], parts["envelope"]))
    if share < PAPER_AT_LEAST:
        problems.append(f"{card}, {how}: {share:.0%} paper where the letter stands: something is over it")


def check_browser(browser, name, out, flat, problems):
    page = browser.new_page(viewport={"width": 1280, "height": 1000})
    page.goto(PAGE)
    if flat:
        page.add_style_tag(content=FLAT)
    page.wait_for_timeout(SETTLE_MS + 500)
    for card in CARDS:
        rest = page.evaluate(PARTS, card)
        if not rest["picture"]:
            problems.append(f"{name} {card}: its picture did not load")
        if not rest["words"].strip():
            problems.append(f"{name} {card}: no name on the card")
        if rest["flap"] < 0.9 or rest["letter"]["y"] < rest["envelope"]["y"] - 1:
            problems.append(f"{name} {card}: not closed at rest")
    if out:
        page.screenshot(path=out / f"racine-{name}-repos.png")
    for card in CARDS:
        page.locator(f".cible.{card} > a").scroll_into_view_if_needed()
        page.hover(f".cible.{card} > a")
        if card == "inviolia":
            page.wait_for_timeout(300)
            mid = page.evaluate(PARTS, card)["flap"]
            if out:
                page.screenshot(path=out / f"racine-{name}-milieu.png")
            print(f"{name}: flap m22 {mid:.2f} part-way")
            if mid in (1, -1):
                problems.append(f"{name}: the flap jumps instead of swinging (m22 {mid})")
        page.wait_for_timeout(SETTLE_MS)
        check_open(page, card, f"{name} hover", problems)
        if out and card == "inviolia":
            page.screenshot(path=out / f"racine-{name}-ouvert.png")
    page.mouse.move(0, 0)
    page.wait_for_timeout(SETTLE_MS)
    page.evaluate("window.scrollTo(0, 0)")
    page.keyboard.press("Tab")
    page.wait_for_timeout(SETTLE_MS)
    check_open(page, CARDS[0], f"{name} keyboard", problems)
    page.close()


def check_chrome_only(browser, css, problems):
    touch = browser.new_context(viewport={"width": 390, "height": 800}, has_touch=True, is_mobile=True)
    page = touch.new_page()
    page.goto(PAGE)
    if not page.evaluate("matchMedia('(hover: none)').matches"):
        problems.append("the touch context still hovers: this test proved nothing")
    # The first card's cycle is 9 s from load: at about a second in, it stands open.
    seen = []
    for _ in range(12):
        page.wait_for_timeout(250)
        seen.append(page.evaluate(PARTS, CARDS[0])["flap"])
    if min(seen) > -0.9:
        problems.append(f"no pointer: the first flap never opened by itself, lowest m22 {min(seen):.2f}")
    touch.close()

    still = browser.new_context(viewport={"width": 1280, "height": 1000}, reduced_motion="reduce")
    page = still.new_page()
    page.goto(PAGE)
    running = page.evaluate("document.getAnimations().length")
    page.hover(f".cible.{CARDS[0]} > a")
    moving = page.evaluate("document.getAnimations().length")
    if running or moving:
        problems.append(f"reduced motion: {running} animations at rest, {moving} on hover")
    if page.evaluate(PARTS, CARDS[0])["flap"] > -0.9:
        problems.append("reduced motion: the envelope does not open on hover")
    still.close()

    for width in WIDTHS:
        page = browser.new_page(viewport={"width": width, "height": 800})
        page.goto(PAGE)
        if css:
            page.add_style_tag(content=css)
        page.wait_for_timeout(1400)
        over = page.evaluate("document.documentElement.scrollWidth - innerWidth")
        if over > 0:
            problems.append(f"{over} px wider than a {width} window")
        hits = page.evaluate("""() => [...document.querySelectorAll('.cible')].filter(c => {
            const a = c.querySelector('.texte p').getBoundingClientRect();
            const b = c.querySelector('.poche').getBoundingClientRect();
            const t = c.querySelector('.texte').getBoundingClientRect();
            const p = c.querySelector('.plaque').getBoundingClientRect();
            return a.right > b.left + 1 || t.top < p.top; }).length""")
        if hits:
            problems.append(f"at {width}: {hits} cards have words under the envelope or above the plate")
        for card in CARDS:
            page.locator(f".cible.{card} > a").scroll_into_view_if_needed()
            page.hover(f".cible.{card} > a")
            page.wait_for_timeout(HOVER_SETTLE_MS)
            under = page.evaluate(OVER, card)["over"]
            if under > 0:
                problems.append(f"at {width}, {card} hovered: a word goes {under:.1f} px under the open envelope")
        page.close()


def main(args):
    control = None
    if "--control" in args:
        at = args.index("--control")
        control = args[at + 1]
        if control not in ("flat", "big"):
            sys.exit(f"--control flat or big, not {control}")
        del args[at:at + 2]
    flat = control == "flat"
    out = Path(args[0]) if args else None
    if out:
        out.mkdir(parents=True, exist_ok=True)
    problems = []
    with sync_playwright() as playwright:
        chrome = playwright.chromium.launch(channel="chrome")
        check_browser(chrome, "chrome", out, flat, problems)
        if not flat:
            check_chrome_only(chrome, BIG if control == "big" else "", problems)
        chrome.close()
        firefox = playwright.firefox.launch()
        check_browser(firefox, "firefox", out, flat, problems)
        firefox.close()
    for problem in problems:
        print(f"FAILED: {problem}")
    print("OK" if not problems else f"{len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
