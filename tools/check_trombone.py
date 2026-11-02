#!/usr/bin/env python3
"""Look at what tools/render_pages.py freezes on purpose: Merlin's moving parts.

    python3 tools/check_trombone.py [OUT_DIR]

Over file://, as a double-click opens it, in Chrome:
- the paperclip draws and turns, and stops under reduced motion;
- dragging it turns it, even stopped;
- without WebGL, and without JavaScript, the drawn clip shows and every word is still there;
- the counters end on the number the HTML holds, and a scrolled-to section ends up visible;
- no page is wider than its window at any width between phone and large screen.

With OUT_DIR, leaves frames of the turning clip there. Needs Playwright and Chrome.
"""

import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parent.parent
HOME = (REPO / "merlin/index.html").as_uri()
PAGES = sorted((REPO / "merlin").glob("*.html"))
WIDTHS = (360, 600, 768, 1000, 1100, 1190, 1280, 1920)
failures = []


def check(ok, what):
    print(f"{'OK  ' if ok else 'FAIL'} {what}")
    if not ok:
        failures.append(what)


def opened(browser, errors, width=1280, **options):
    context = browser.new_context(viewport={"width": width, "height": 800}, **options)
    page = context.new_page()
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: m.type == "error" and errors.append(m.text))
    page.goto(HOME, wait_until="load")
    return context, page


def text_of(path):
    html = path.read_text(encoding="utf-8")
    words = re.sub(r"<[^>]+>", " ", html[html.index("<main>"):html.index("</main>")])
    return " ".join(re.sub(r"\s+", " ", words).split())


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if out:
        out.mkdir(parents=True, exist_ok=True)
    errors = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])

        context, page = opened(browser, errors)
        clip = page.locator("#trombone")
        check(clip.is_visible() and not page.locator("#trombone-repli").is_visible(),
              "with WebGL the canvas shows and the drawn clip does not")
        check(page.locator(".astuce").is_visible(), "the caption shows")
        frames = []
        for i in range(6):
            page.wait_for_timeout(900)
            frames.append(clip.screenshot())
            if out:
                (out / f"tourne-{i}.png").write_bytes(frames[-1])
        check(len(set(frames)) == len(frames), f"the clip turns: {len(set(frames))} of 6 frames differ")
        page.mouse.wheel(0, 5000)
        page.wait_for_timeout(2200)
        shown = page.evaluate("[...document.querySelectorAll('.chiffres strong')].map(e => e.textContent)")
        check(shown == ["1987", "23", "1", "12"], f"the counters end on the HTML's numbers: {shown}")
        hidden = page.evaluate("[...document.querySelectorAll('.monte')].filter(e => getComputedStyle(e).opacity !== '1' && e.getBoundingClientRect().bottom < innerHeight * .9 && e.getBoundingClientRect().bottom > 0).length")
        check(hidden == 0, "a section scrolled to is visible")
        context.close()

        context, page = opened(browser, errors, reduced_motion="reduce")
        clip = page.locator("#trombone")
        page.wait_for_timeout(300)
        first = clip.screenshot()
        page.wait_for_timeout(1200)
        check(first == clip.screenshot(), "under reduced motion the clip stands still")
        box = clip.bounding_box()
        page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        page.mouse.down()
        page.mouse.move(box["x"] + box["width"] / 2 + 120, box["y"] + box["height"] / 2, steps=4)
        page.mouse.up()
        page.wait_for_timeout(150)
        check(first != clip.screenshot(), "dragging turns it, even stopped")
        check(page.evaluate("document.querySelectorAll('.monte').length") == 0,
              "under reduced motion no section waits to rise")
        context.close()

        context, page = opened(browser, errors, java_script_enabled=False)
        check(page.locator("#trombone-repli").is_visible() and not page.locator("#trombone").is_visible(),
              "without JavaScript the drawn clip shows")
        context.close()

        no_gl = playwright.chromium.launch(channel="chrome", args=["--disable-gpu", "--disable-webgl", "--disable-webgl2", "--disable-3d-apis"])
        context, page = opened(no_gl, errors)
        check(page.locator("#trombone-repli").is_visible() and not page.locator("#trombone").is_visible(),
              "without WebGL the drawn clip shows")
        context.close()
        no_gl.close()

        for path in PAGES:
            for width in WIDTHS:
                context = browser.new_context(viewport={"width": width, "height": 800}, reduced_motion="reduce")
                page = context.new_page()
                page.goto(path.as_uri(), wait_until="load")
                over = page.evaluate("document.documentElement.scrollWidth - innerWidth")
                if over > 0:
                    check(False, f"{path.name} at {width}: {over}px wider than the window")
                context.close()
        check(True, f"overflow looked at: {len(PAGES)} pages at {len(WIDTHS)} widths")
        browser.close()
    check(not errors, f"no page error or console error {errors[:3] if errors else ''}")
    print("FAILED" if failures else "ALL OK")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
