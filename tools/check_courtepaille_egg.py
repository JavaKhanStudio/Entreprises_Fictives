#!/usr/bin/env python3
"""Courtepaille's easter egg (r68): the home page's counter must look like every other page's.

    python3 tools/check_courtepaille_egg.py [OUT]

Its number links img/facade.svg, and `nav a` would turn that link into a grey button. Fails if
the counter differs by one pixel from the one on a-propos.html, which has no link, or if the link
does not land on the picture. Works over file://, at 1280 and 390.
"""
import pathlib
import sys

from playwright.sync_api import sync_playwright

SITE = pathlib.Path(__file__).resolve().parent.parent / "courtepaille"
OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/courtepaille-egg")
OUT.mkdir(parents=True, exist_ok=True)
failed = False
with sync_playwright() as play:
    browser = play.chromium.launch()
    for width in (1280, 390):
        page = browser.new_page(viewport={"width": width, "height": 800})
        shots = []
        for name in ("a-propos", "index"):
            page.goto((SITE / f"{name}.html").as_uri())
            shots.append(page.locator(".compteur").screenshot(path=str(OUT / f"{name}-{width}.png")))
        same = shots[0] == shots[1]
        page.locator(".compteur a").click()
        page.wait_for_load_state()
        landed = page.url.endswith("/img/facade.svg")
        print(f"{width}: counter identical {same}, link lands on the picture {landed}")
        failed = failed or not (same and landed)
        page.close()
    browser.close()
sys.exit(1 if failed else 0)
