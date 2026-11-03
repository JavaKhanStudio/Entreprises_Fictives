#!/usr/bin/env python3
"""Inviolia: the camera that follows the scroll, which the renders freeze.

    python3 tools/check_inviolia.py [OUT]     # OUT: frames of the scroll, as contact sheets

tools/render_pages.py renders under reduced motion, so its pictures show the still page. This runs
the seven pages over file:// with motion allowed, in Chrome and Firefox, at windows from a phone to
a big screen. It fails on a script error, a page wider than its window at any point of the scroll,
a word that differs from the still page, anything left faded or turned once the page has been
scrolled through, a stop that does not hold the page or shows a block still at an angle, a hero
that does not fit its pinned frame, an anchor under the sticky header, and any motion left under
reduced motion or without the script. Safari is not here: Playwright's WebKit is not Safari.
Needs Playwright, Chrome, `playwright install firefox`, Pillow for OUT.
"""

import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

SITE = Path(__file__).resolve().parent.parent / "inviolia"
PAGES = ("index", "a-propos", "equipe", "organigramme", "offre-emploi", "communique", "contact")
WINDOWS = ((1920, 1080), (1366, 768), (1280, 800), (1280, 672), (1000, 700), (800, 500), (390, 844), (360, 640))
PINNED = ((1920, 1080), (1366, 768), (1280, 800), (1280, 672), (1000, 700))
SHEET = {(1280, 800): (640, 400), (390, 844): (260, 563)}
failures = []

STUCK = """() => [...document.querySelectorAll('main *')].filter(e => {
  const c = getComputedStyle(e);
  return c.opacity !== '1' && !e.matches('.hero h1 .suite') ||
    (e.closest('.scene-hero') ? false : !e.matches('.bandeau img') && c.transform !== 'none' && !/^matrix(3d)?\\(1, 0, 0, (0, 0, )?1/.test(c.transform.replace(/, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1\\)/, ', 0, 0, 1, 0, 0)')));
}).map(e => e.tagName + '.' + e.className)"""


def expect(what, ok, more=""):
    if not ok:
        print(f"FAIL {what} {more}")
        failures.append(what)


def text(page):
    return re.sub(r"\s+", " ", page.locator("body > main").text_content()).strip()


def frames_settle(page):
    page.evaluate("() => new Promise(done => requestAnimationFrame(() => requestAnimationFrame(done)))")


def stills(browser):
    """The words of each page on the still page, and that it really is still both ways."""
    words = {}
    for name, options in (("reduced motion", {"reduced_motion": "reduce"}), ("no script", {"java_script_enabled": False})):
        page = browser.new_context(viewport={"width": 1280, "height": 800}, **options).new_page()
        for one in PAGES:
            page.goto((SITE / f"{one}.html").as_uri())
            shown = text(page)
            words.setdefault(one, shown)
            expect(f"{one}: the same words with {name}", words[one] == shown)
            if options.get("java_script_enabled", True):
                expect(f"{one}: {name} leaves no html.vivant", not page.evaluate("document.documentElement.classList.contains('vivant')"))
                expect(f"{one}: {name} leaves nothing moved", page.evaluate(STUCK) == [], page.evaluate(STUCK))
        page.context.close()
    return words


def sweep(page, one, width, height, words):
    page.goto((SITE / f"{one}.html").as_uri())
    page.wait_for_load_state("load")
    label = f"{one} {width}x{height}"
    expect(f"{label}: html.vivant", page.evaluate("document.documentElement.classList.contains('vivant')"))
    expect(f"{label}: the same words as the still page", text(page) == words[one])
    page.wait_for_timeout(900)  # the hero's entrance
    faded = page.evaluate("""() => [...document.querySelectorAll('main p, main h1, main h2, main h3, main li, main td, main img')].filter(e => {
      const r = e.getBoundingClientRect();
      if (r.height === 0 || r.top >= innerHeight * .85 || r.bottom <= 0) return false;
      let o = 1; for (let n = e; n && n.nodeType === 1; n = n.parentElement) o *= +getComputedStyle(n).opacity;
      return o < .4;
    }).map(e => e.tagName + ': ' + e.textContent.slice(0, 30))""")
    expect(f"{label}: nothing faded in the first screen", not faded, faded)
    last = page.evaluate("document.documentElement.scrollHeight - innerHeight")
    y = 0
    while True:
        page.evaluate(f"scrollTo(0, {y})")
        frames_settle(page)
        wide = page.evaluate("document.documentElement.scrollWidth - innerWidth")
        expect(f"{label}: no sideways scroll at y={y}", wide <= 0, wide)
        if y >= last:
            break
        y = min(last, y + height // 2)
    page.wait_for_timeout(450)
    left = page.evaluate(STUCK)
    expect(f"{label}: nothing left faded or turned at the end", not left, left[:6])
    expect(f"{label}: the quote fully lit", page.evaluate("[...document.querySelectorAll('.mot:not(.allume)')].length") == 0)


def pinned(page, width, height):
    label = f"home {width}x{height}"
    page.goto((SITE / "index.html").as_uri())
    page.wait_for_load_state("load")
    page.wait_for_timeout(900)
    state = """() => {
      const m = getComputedStyle(document.querySelector('.hero-img')).transform, a = m.match(/matrix\\(([-\\d.]+)/);
      const t = document.querySelector('.hero-txt').getBoundingClientRect(), h = document.querySelector('.hero').getBoundingClientRect();
      const c = document.querySelector('.cadre').getBoundingClientRect(), b = document.querySelector('.haut').getBoundingClientRect();
      const f = document.querySelector('.chiffres').getBoundingClientRect();
      return {scale: a ? +a[1] : 1, txt: [t.top, t.bottom], hero: [h.top, h.bottom], cadre: c.top, bar: b.bottom, figures: f.bottom,
              suite: +getComputedStyle(document.querySelector('.suite')).opacity, end: document.querySelector('.scene-fin').getBoundingClientRect().bottom};
    }"""
    s = page.evaluate(state)
    expect(f"{label}: the camera starts wide", abs(s["scale"] - 1) < .01, s["scale"])
    expect(f"{label}: the headline's end starts dim, still legible", .4 < s["suite"] < .5, s["suite"])
    expect(f"{label}: the hero's words fit its frame", s["txt"][0] >= s["hero"][0] and s["txt"][1] <= s["hero"][1], s)
    expect(f"{label}: the figures close the first screen", abs(s["figures"] - height) < 2, s)
    course = page.evaluate("document.querySelector('.scene-hero').offsetHeight - document.querySelector('.cadre').offsetHeight")
    page.evaluate(f"scrollTo(0, {course})")
    frames_settle(page)
    page.wait_for_timeout(120)
    e = page.evaluate(state)
    expect(f"{label}: held under the header to the end of its course", abs(e["cadre"] - e["bar"]) < 2, e)
    expect(f"{label}: the camera ends on the mask", abs(e["scale"] - 1.55) < .01, e["scale"])
    expect(f"{label}: the headline ends lit", e["suite"] == 1, e["suite"])


def stops(page, width, height):
    """A real wheel, stopped near each stop: the page must rest on it, what it shows face-on."""
    label = f"home {width}x{height}"
    page.goto((SITE / "index.html").as_uri())
    page.wait_for_load_state("load")
    page.mouse.move(width / 2, height / 2)
    held = page.evaluate("inviolia.arrets()")
    expect(f"{label}: at least four stops", len(held) >= 4, held)
    expect(f"{label}: the page's end is a stop", held[-1] == page.evaluate("document.documentElement.scrollHeight - innerHeight"), held)
    for before, target in zip(held, held[1:]):
        # from nearer this stop than the one before it, inside its reach
        page.evaluate(f"scrollTo(0, {target - min(height // 8, (target - before) // 2 - 15)})")
        page.wait_for_timeout(100)
        page.mouse.wheel(0, 10)
        page.wait_for_timeout(1300)
        rested = page.evaluate("scrollY")
        expect(f"{label}: rests on the stop at {target}", abs(rested - target) <= 2, rested)
        left = page.evaluate("""() => [...document.querySelectorAll('main *')].filter(e => {
          const r = e.getBoundingClientRect();
          // what has passed FIN in inviolia.js has arrived; below it the next block may still be on its way
          if (r.top < 0 || r.top > innerHeight * .5 || r.bottom > innerHeight || e.matches('.mot, .hero h1 .suite') || e.closest('.scene-hero')) return false;
          let o = 1; for (let n = e; n && n.nodeType === 1; n = n.parentElement) o *= +getComputedStyle(n).opacity;
          return o !== 1;
        }).map(e => e.tagName + '.' + e.className)""")
        expect(f"{label}: all it shows is whole at the stop {target}", not left, left[:5])


def anchors(page):
    for one, anchor in (("contact", "pirate"), ("contact", "audit"), ("contact", "livre-blanc"), ("equipe", "anais")):
        page.goto((SITE / f"{one}.html").as_uri() + "#" + anchor)
        page.wait_for_load_state("load")
        page.wait_for_timeout(1000)
        s = page.evaluate(f"""() => {{
          const t = document.getElementById('{anchor}').getBoundingClientRect(), b = document.querySelector('.haut').getBoundingClientRect();
          return [t.top, b.bottom, document.documentElement.scrollHeight - innerHeight - scrollY];
        }}""")
        expect(f"{one}#{anchor}: not under the header", s[0] >= s[1] - 2 or s[2] < 2, s)


def sheets(browser, out):
    from PIL import Image
    out.mkdir(parents=True, exist_ok=True)
    for (width, height), (w, h) in SHEET.items():
        for one in ("index", "a-propos", "equipe", "organigramme", "communique"):
            page = browser.new_context(viewport={"width": width, "height": height}, reduced_motion="no-preference").new_page()
            page.goto((SITE / f"{one}.html").as_uri())
            page.wait_for_load_state("load")
            page.wait_for_timeout(900)
            last = page.evaluate("document.documentElement.scrollHeight - innerHeight")
            shots = []
            for k in range(9):
                page.evaluate(f"scrollTo(0, {last * k // 8})")
                page.wait_for_timeout(450)
                path = out / f".{one}-{width}-{k}.png"
                page.screenshot(path=path)
                shots.append(path)
            sheet = Image.new("RGB", (w * 3, h * 3))
            for k, path in enumerate(shots):
                sheet.paste(Image.open(path).resize((w, h)), (k % 3 * w, k // 3 * h))
                path.unlink()
            sheet.save(out / f"scroll-{one}-{width}.png")
            page.context.close()


with sync_playwright() as p:
    for kind in ("chromium", "firefox"):
        before = len(failures)
        browser = getattr(p, kind).launch()
        words = stills(browser)
        for width, height in WINDOWS:
            page = browser.new_context(viewport={"width": width, "height": height}, reduced_motion="no-preference").new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            for one in PAGES:
                sweep(page, one, width, height, words)
            if (width, height) in PINNED:
                pinned(page, width, height)
                stops(page, width, height)
                anchors(page)
            expect(f"{width}x{height}: no script or console error", not errors, errors[:3])
            page.context.close()
        print(f"{kind}: {len(failures) - before} failure(s)")
        if kind == "chromium" and len(sys.argv) > 1:
            sheets(browser, Path(sys.argv[1]))
        browser.close()

print("OK" if not failures else f"{len(failures)} failure(s)")
sys.exit(1 if failures else 0)
