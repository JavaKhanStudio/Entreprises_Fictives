#!/usr/bin/env python3
"""The takes of r82: how the root list's open envelope stops covering a word. A: the words stop
sooner. B: the envelope grows less on hover.

    python3 tools/racine_takes.py sweep          # how far each take's words go under the envelope
    python3 tools/racine_takes.py OUT            # take-*.png in OUT, for `atelier attach --stamp`

A take is CSS put on top of the real index.html, opened over file://. The overlap is each line of a
card's words, read with a Range, against the left edge of .poche, each card hovered in turn. Width
1007 and 1265 are 1024 and 1280 less a classic scrollbar. Needs Playwright and Chrome, and Pillow.
"""
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

PAGE = (Path(__file__).resolve().parent.parent / "index.html").as_uri()
CARDS = ("merlin", "gobelin", "courtepaille", "inviolia", "dernier-prix", "source-eclat")
WIDTHS = (640, 800, 1000, 1007, 1024, 1265, 1280, 1600, 1920)
HOVER = ".cible > a:hover .enveloppe { transform: translateZ(5.5rem) rotate(0deg) scale(%s); }"
TAKES = {"maintenant": "", "A": ".texte { right: 9.5rem; }", "B": HOVER % 1.1}
SHOTS = ((1280, "courtepaille"), (1024, "merlin"))    # each the worst of its width as it stands
BAND = 90       # plain, on top of each panel, where the stamp lands: it covers no word

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


def overlap(browser, css, widths=WIDTHS):
    """(cards with a word under the envelope, of how many, worst px, cards whose words leave the plate)."""
    hit, worst, out = 0, 0, 0
    for width in widths:
        page = browser.new_page(viewport={"width": width, "height": 900})
        page.goto(PAGE)
        if css:
            page.add_style_tag(content=css)
        page.wait_for_timeout(1400)
        for card in CARDS:
            out += page.evaluate(OVER, card)["above"] > 0
            page.locator(f".cible.{card} > a").scroll_into_view_if_needed()
            page.hover(f".cible.{card} > a")
            page.wait_for_timeout(750)
            over = page.evaluate(OVER, card)["over"]
            hit += over > 0
            worst = max(worst, over)
        page.close()
    return hit, len(widths) * len(CARDS), round(worst, 1), out


def sweep():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome")
        print("now", overlap(browser, ""))
        for right in (8.5, 9, 9.5, 10):
            print(f"text right {right}rem", overlap(browser, f".texte {{ right: {right}rem; }}"))
        for scale in (1.2, 1.15, 1.1, 1.05):
            print(f"hover scale {scale}", overlap(browser, HOVER % scale))
        browser.close()


def pictures(out):
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome")
        for name, css in TAKES.items():
            print(name, overlap(browser, css))
            panels = []
            for width, card in SHOTS:
                page = browser.new_page(viewport={"width": width, "height": 860})
                page.goto(PAGE)
                if css:
                    page.add_style_tag(content=css)
                page.wait_for_timeout(1400)
                page.locator(f".cible.{card} > a").scroll_into_view_if_needed()
                page.hover(f".cible.{card} > a")
                page.wait_for_timeout(1300)
                shot = out / f"{name}-{width}.png"
                page.screenshot(path=shot)
                panels.append(Image.open(shot).convert("RGB"))
                page.close()
            sheet = Image.new("RGB", (sum(p.width for p in panels), 860 + BAND), "#2a2d36")
            x = 0
            for panel in panels:
                sheet.paste(panel, (x, BAND))
                x += panel.width
            sheet.save(out / f"take-{name}.png")
            for width, _ in SHOTS:
                (out / f"{name}-{width}.png").unlink()
        browser.close()


if __name__ == "__main__":
    if sys.argv[1:] == ["sweep"]:
        sweep()
    else:
        pictures(Path(sys.argv[1]))
