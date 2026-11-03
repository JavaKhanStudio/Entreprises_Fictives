#!/usr/bin/env python3
"""Inviolia: the camera that follows the scroll, which the renders freeze.

    python3 tools/check_inviolia.py [OUT]     # OUT: frames of the scroll, as contact sheets
    python3 tools/check_inviolia.py --live    # the home's live map only, a minute against many

tools/render_pages.py renders under reduced motion, so its pictures show the still page. This runs
the seven pages over file:// with motion allowed, in Chrome and Firefox, at windows from a phone to
a big screen. It fails on a script error, a page wider than its window at any point of the scroll,
a word that differs from the still page, anything left faded or turned once the page has been
scrolled through, a stop that does not hold the page or shows a block still at an angle, a hero
that does not fit its pinned frame, an anchor under the sticky header, and any motion left under
reduced motion or without the script. On the home's live map it fails on a counter that does not
climb at the rate its own words give, a feed that does not roll or changes its words or height, a
globe with no comets, a band that changes height, and anything that runs off screen.
OUT also gets a film and frames of the live map.
Safari is not here: Playwright's WebKit is not Safari.
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
START = "4\u00a0812\u00a0336"
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
    # The counter is the one word that may change; stills() holds its starting value.
    return re.sub(r"\d \d{3} \d{3}(?=attaques)", "COMPTEUR", re.sub(r"\s+", " ", page.locator("body > main").text_content())).strip()


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
            if one == "index":
                page.wait_for_timeout(1000)
                expect(f"home: {name} keeps the counter at its written value", page.locator(".chiffres .rouge").text_content() == START, page.locator(".chiffres .rouge").text_content())
                expect(f"home: {name} paints no comet", page.locator("canvas").count() == 0)
                orders = [line.get_attribute("style") for line in page.locator(".flux p").all()]
                expect(f"home: {name} leaves the feed unrolled", not any(orders), orders)
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


def live(page, width, height, words):
    """The counter, the feed and the comets, each on and off screen."""
    label = f"live {width}x{height}"
    page.goto((SITE / "index.html").as_uri())
    page.wait_for_load_state("load")
    center = lambda what: page.evaluate(f"(() => {{ const r = document.querySelector('{what}').getBoundingClientRect(); scrollTo(0, scrollY + r.top + r.height / 2 - innerHeight / 2); }})()")
    first_screen = page.evaluate("""() => {
      const f = document.querySelector('.flux').getBoundingClientRect(), c = document.querySelector('.tirs');
      let n = 0; if (c.width) { const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; for (let i = 3; i < d.length; i += 4) if (d[i]) n++; }
      return {inView: f.bottom > 0 && f.top < innerHeight, painted: n, canvas: c.getBoundingClientRect().top < innerHeight};
    }""")
    if not first_screen["inView"]:
        page.wait_for_timeout(1800)
        expect(f"{label}: the feed waits while off screen", page.evaluate("[...document.querySelectorAll('.flux p')].map(p => p.style.order).join('')") == "")
    if not first_screen["canvas"]:
        expect(f"{label}: no comet while off screen", first_screen["painted"] == 0, first_screen["painted"])
    center(".chiffres")
    count = lambda: int(re.sub(r"\D", "", page.locator(".chiffres .rouge").text_content()))
    band = "document.querySelector('.chiffres').offsetHeight"
    high = page.evaluate(band)
    page.wait_for_timeout(300)
    one = count()
    expect(f"{label}: the counter starts where the page says", 0 <= one - int(re.sub(r"\D", "", START)) < 500, one)
    page.wait_for_timeout(2000)
    rate = (count() - one) / 2
    expect(f"{label}: the counter climbs at what its words say, 56 a second", 20 < rate < 110, rate)
    shown = page.locator(".chiffres .rouge").text_content()
    expect(f"{label}: the counter stays grouped as written", re.fullmatch("\\d\u00a0\\d{3}\u00a0\\d{3}", shown), repr(shown))
    expect(f"{label}: the band keeps its height", page.evaluate(band) == high, (high, page.evaluate(band)))
    wider = page.evaluate(f"(() => {{ const b = document.querySelector('.chiffres .rouge'), s = b.textContent; b.textContent = '8\\u00a0888\\u00a0888'; const h = {band}; b.textContent = s; return h; }})()")
    expect(f"{label}: the band keeps its height on the widest digits", wider == high, (high, wider))

    state = """() => {
      const f = document.querySelector('.flux'), ps = [...f.children], box = f.getBoundingClientRect();
      const c = document.querySelector('.tirs'), i = document.querySelector('.carte img');
      const a = c.getBoundingClientRect(), b = i.getBoundingClientRect();
      let painted = 0;
      if (c.width) { const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; for (let n = 3; n < d.length; n += 4) if (d[n]) painted++; }
      return {first: ps.reduce((m, p) => p.getBoundingClientRect().top < m[0] ? [p.getBoundingClientRect().top, p.textContent] : m, [1e9, ''])[1],
              inView: box.bottom > 0 && box.top < innerHeight, order: ps.map(p => p.style.order).join(), high: f.offsetHeight, text: f.textContent,
              painted, pic: c.toDataURL(), moving: f.getAnimations({subtree: true}).length, wide: f.scrollWidth - f.clientWidth,
              box: [box.top, box.bottom], lines: ps.map(p => { const r = p.getBoundingClientRect(); return [r.top, r.bottom]; }),
              same: Math.abs(a.left - b.left) < 2 && Math.abs(a.top - b.top) < 2 && Math.abs(a.width - b.width) < 2 && Math.abs(a.height - b.height) < 2,
              hidden: c.getAttribute('aria-hidden'), canvasInView: a.bottom > 0 && a.top < innerHeight};
    }"""
    center(".carte img")
    page.wait_for_timeout(900)
    start = page.evaluate(state)
    expect(f"{label}: the comets' frame lies on the globe", start["same"])
    expect(f"{label}: the comets are hidden from a screen reader", start["hidden"] == "true")
    pics, painted = set(), 0
    for _ in range(12):
        page.wait_for_timeout(300)
        s = page.evaluate(state)
        pics.add(s["pic"])
        painted = max(painted, s["painted"])
    expect(f"{label}: comets are painted", painted > 50, painted)
    expect(f"{label}: the comets move", len(pics) >= 9, len(pics))

    center(".flux")
    page.wait_for_timeout(600)
    start = page.evaluate(state)
    seen = []
    for _ in range(16):
        page.wait_for_timeout(350)
        s = page.evaluate(state)
        if not seen or seen[-1] != s["first"]:
            seen.append(s["first"])
        expect(f"{label}: the feed keeps its height", s["high"] == start["high"], (start["high"], s["high"]))
        expect(f"{label}: the feed keeps its words", s["text"] == start["text"])
        expect(f"{label}: no line wider than the feed", s["wide"] <= 0, s["wide"])
        if not s["moving"]:
            out = [line for line in s["lines"] if line[0] < s["box"][0] - 1 or line[1] > s["box"][1] + 1]
            expect(f"{label}: at rest every line is in its box", not out, (s["box"], out))
    expect(f"{label}: the feed rolls", len(seen) >= 3, seen)
    expect(f"{label}: the same words on the page", text(page) == words["index"])

    page.evaluate("scrollTo(0, document.documentElement.scrollHeight)")
    page.wait_for_timeout(900)
    s = page.evaluate(state)
    gone = page.evaluate("document.querySelector('.chiffres').getBoundingClientRect().bottom < 0")
    expect(f"{label}: the band has left the screen at the page's end", gone)
    before, pic, was = count(), s["pic"], s["order"]
    page.wait_for_timeout(2000)
    after = page.evaluate(state)
    expect(f"{label}: the counter's digits wait off screen", count() == before, count() - before)
    if not s["inView"]:  # a big window still shows the feed at the page's end; its first screen proved this
        expect(f"{label}: the feed waits off screen", after["order"] == was)
    if not after["canvasInView"]:
        expect(f"{label}: the comets wait off screen", after["pic"] == pic)
    center(".chiffres")
    page.wait_for_timeout(500)
    expect(f"{label}: the counter catches up on return", count() - before > 60, count() - before)


def film(browser, out):
    from PIL import Image
    out.mkdir(parents=True, exist_ok=True)
    video = out / ".video"
    context = browser.new_context(viewport={"width": 1280, "height": 800}, reduced_motion="no-preference",
                                  record_video_dir=str(video), record_video_size={"width": 1280, "height": 800})
    page = context.new_page()
    page.goto((SITE / "index.html").as_uri())
    page.wait_for_load_state("load")
    page.mouse.move(640, 400)
    page.wait_for_timeout(2500)
    page.evaluate("(() => { const r = document.querySelector('.carte').getBoundingClientRect(); scrollTo(0, scrollY + r.top + r.height / 2 - innerHeight / 2); })()")
    page.wait_for_timeout(8000)
    path = Path(page.video.path())
    context.close()
    path.rename(out / "vivant-accueil-1280.webm")
    video.rmdir()
    for width, height in ((1280, 800), (390, 844)):
        page = browser.new_context(viewport={"width": width, "height": height}, reduced_motion="no-preference").new_page()
        page.goto((SITE / "index.html").as_uri())
        page.wait_for_load_state("load")
        page.evaluate("(() => { const r = document.querySelector('.carte').getBoundingClientRect(); scrollTo(0, scrollY + r.top + r.height / 2 - innerHeight / 2); })()")
        page.wait_for_timeout(900)
        shots = []
        for k in range(3):
            page.wait_for_timeout(1700)
            shot = out / f".vivant-{k}.png"
            page.screenshot(path=shot)
            shots.append(shot)
        sheet = Image.new("RGB", (width * 3, height))
        for k, shot in enumerate(shots):
            sheet.paste(Image.open(shot), (k * width, 0))
            shot.unlink()
        sheet.save(out / f"vivant-carte-{width}.png")
        page.context.close()


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


only_live = "--live" in sys.argv
out_dir = next((a for a in sys.argv[1:] if a != "--live"), None)

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
            for one in () if only_live else PAGES:
                sweep(page, one, width, height, words)
            if (width, height) in PINNED and not only_live:
                pinned(page, width, height)
                stops(page, width, height)
                anchors(page)
            live(page, width, height, words)
            expect(f"{width}x{height}: no script or console error", not errors, errors[:3])
            page.context.close()
        print(f"{kind}: {len(failures) - before} failure(s)")
        if kind == "chromium" and out_dir:
            sheets(browser, Path(out_dir))
            film(browser, Path(out_dir))
        browser.close()

print("OK" if not failures else f"{len(failures)} failure(s)")
sys.exit(1 if failures else 0)
