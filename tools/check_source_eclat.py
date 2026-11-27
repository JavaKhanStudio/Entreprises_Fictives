#!/usr/bin/env python3
"""Source & Éclat: what the renders freeze, and the numbers its pages must keep agreeing on.

    python3 tools/check_source_eclat.py

tools/render_pages.py renders under reduced motion, so its pictures show the countdown standing
still. This runs the page with motion allowed, over file://: the band must tick, must read the
same again after a reload, and must stand still under reduced motion. It also adds up the ladder
of the home page (9 170 people, 5,8 M€ of commissions a year) and looks for overflow at 8 widths.
Needs Playwright and Chrome, which a student never does.
"""

import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

SITE = Path(__file__).resolve().parent.parent / "source-eclat"
PAGES = ("index", "a-propos", "equipe", "organigramme", "offre-emploi", "communique", "contact")
WIDTHS = (320, 360, 390, 480, 720, 721, 1100, 1280)
failures = []


def band(page):
    return page.locator(".compte").inner_text()


def expect(what, ok):
    print(("ok  " if ok else "FAIL") + " " + what)
    if not ok:
        failures.append(what)


with sync_playwright() as p:
    browser = p.chromium.launch()
    home = (SITE / "index.html").as_uri()

    page = browser.new_context(reduced_motion="no-preference").new_page()
    page.goto(home)
    first = band(page)
    page.wait_for_timeout(2500)
    expect("the countdown ticks", band(page) != first)
    page.reload()
    expect("a reload gives the same reading again", band(page)[:40] == first[:40])
    page.close()

    page = browser.new_context(reduced_motion="reduce").new_page()
    page.goto(home)
    first = band(page)
    page.wait_for_timeout(2500)
    expect("under reduced motion it stands still", band(page) == first)

    rows = page.locator(".rang").all()
    people, month = 0, 0
    for row in rows:
        cells = [re.sub(r"\D", "", cell) for cell in row.locator("> span").all_inner_texts()]
        people += int(cells[0])
        month += int(cells[0]) * int(cells[1])
    expect(f"the ladder adds up to 9 170 ({people})", people == 9170)
    expect(f"its incomes make 5,8 M€ a year ({month * 12})", round(month * 12 / 1e6, 1) == 5.8)
    page.close()

    for width in WIDTHS:
        page = browser.new_context(viewport={"width": width, "height": 800}, reduced_motion="reduce").new_page()
        for name in PAGES:
            page.goto((SITE / f"{name}.html").as_uri())
            wide = page.evaluate("document.documentElement.scrollWidth")
            expect(f"{name} at {width}: no overflow ({wide})", wide <= width)
        page.close()
    browser.close()

sys.exit(1 if failures else 0)
