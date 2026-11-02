#!/usr/bin/env python3
"""Look at what tools/render_pages.py freezes on purpose: Gobelin's 3D badge.

    python3 tools/check_badge.py [OUT_DIR]

Over file://, in Chrome, at phone and desktop widths:
- it sways and turns, and stands still at an angle under reduced motion;
- hovering the case shows the back, and the pointer stays on it through the whole flip;
- focus shows the back too, a real tap and a real Tab key do, and leaving brings the front back;
- the card stays inside its case and the page no wider than its window, at any angle;
- the sticky header stays above the case;
- no failed request or console error.

With OUT_DIR, leaves pictures there: the sway, the turn, the back, a close-up. Needs Playwright and Chrome.

What it reads is computed matrices, which stay right when the browser draws the 3D wrong: for what
is really on screen, and for Firefox and Safari, see tools/check_badge_browsers.py.
"""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parent.parent
PAGE = (REPO / "gobelin/a-propos.html").as_uri()
WIDTHS = (360, 390, 768, 1280)
CYCLE = 26000  # ms, the longest animation (.tour)
failures = []

# The x scale of a whole chain of transforms: 1 facing us, -1 showing its back.
FACING = """() => {
  let m = new DOMMatrix();
  const chain = [];
  for (let e = document.querySelector('.plaque'); !e.classList.contains('vitrine');
       e = e.parentElement) chain.unshift(e);
  for (const e of chain) m = m.multiply(new DOMMatrix(getComputedStyle(e).transform));
  return m.m11;
}"""
FREEZE = """t => document.getAnimations().forEach(a => {
  if (a.animationName) { a.pause(); a.currentTime = t; }
})"""


def check(ok, what):
    print(f"{'OK  ' if ok else 'FAIL'} {what}")
    if not ok:
        failures.append(what)


def opened(browser, errors, width, **options):
    context = browser.new_context(viewport={"width": width, "height": 800}, **options)
    page = context.new_page()
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: m.type == "error" and errors.append(m.text))
    page.on("requestfailed", lambda r: errors.append(f"failed: {r.url}"))
    page.goto(PAGE, wait_until="load")
    page.locator(".vitrine").scroll_into_view_if_needed()
    return context, page


def shot(page, target):
    """A crop of the page, not an element screenshot: the sticky header would paint over it."""
    box = page.locator(".vitrine").bounding_box()
    page.screenshot(path=target, clip=box)


def run(browser, widths, out, errors, is_mobile=True):
    """Every check below, in one browser. Firefox refuses is_mobile; has_touch alone taps there."""
    for width in widths:
        context, page = opened(browser, errors, width)
        case = page.locator(".vitrine")

        page.evaluate(FREEZE, 0)
        a = page.evaluate(FACING)
        page.evaluate(FREEZE, 5500)
        b = page.evaluate(FACING)
        page.evaluate("() => document.getAnimations().forEach(a => a.play())")
        check(page.evaluate("document.getAnimations().filter(a => a.animationName).length") >= 5,
              f"{width}: five parts are animated")
        check(0.8 < a < 1 and 0.8 < b < 1, f"{width}: the sway stays readable ({a:.2f}, {b:.2f})")

        worst_box = worst_page = 0
        case_box = case.bounding_box()
        faces = []
        for t in range(0, CYCLE, 1000):
            page.evaluate(FREEZE, t)
            faces.append(page.evaluate(FACING))
            overflow = page.evaluate("""() => {
              const c = document.querySelector('.vitrine').getBoundingClientRect();
              const p = document.querySelector('.plaque').getBoundingClientRect();
              return Math.max(c.left - p.left, p.right - c.right, p.bottom - c.bottom);
            }""")
            worst_box = max(worst_box, overflow)
            worst_page = max(worst_page, page.evaluate(
                "document.documentElement.scrollWidth - window.innerWidth"))
            if out and width in (390, 1280) and t in (0, 5000, 19000, 20000, 21000):
                shot(page, out / f"tour-{width}-{t // 1000:02d}s.png")
        check(min(faces) < -0.7, f"{width}: the card turns round in the cycle ({min(faces):.2f})")
        check(worst_box <= 0, f"{width}: the card stays in its case ({worst_box:.1f}px out)")
        check(worst_page <= 0, f"{width}: the page is never wider than the window ({worst_page}px)")
        page.evaluate(FREEZE, 0)

        page.mouse.move(case_box["x"] + case_box["width"] / 2, case_box["y"] + 300)
        stayed = True
        for _ in range(10):
            page.wait_for_timeout(100)
            stayed = stayed and page.evaluate("document.querySelector('.vitrine').matches(':hover')")
        page.wait_for_timeout(200)
        check(stayed, f"{width}: the pointer stays on the case through the flip")
        check(page.evaluate(FACING) < -0.8, f"{width}: hover shows the back")
        if out and width in (390, 1280):
            shot(page, out / f"verso-{width}.png")
        page.mouse.move(0, 0)
        page.wait_for_timeout(1100)
        check(page.evaluate(FACING) > 0.8, f"{width}: leaving brings the front back")

        page.evaluate("document.querySelector('.vitrine').focus()")
        page.wait_for_timeout(1100)
        check(page.evaluate(FACING) < -0.8, f"{width}: focus shows the back")
        page.evaluate("document.querySelector('.vitrine').blur()")

        page.evaluate("""() => {
          const c = document.querySelector('.vitrine').getBoundingClientRect();
          window.scrollBy(0, c.top + 200);
        }""")
        on_top = page.evaluate("""() => {
          const h = document.querySelector('.haut').getBoundingClientRect();
          return !!document.elementFromPoint(window.innerWidth / 2, h.bottom - 2).closest('.haut');
        }""")
        check(on_top, f"{width}: the sticky header stays above the case")
        context.close()

        context, page = opened(browser, errors, width, reduced_motion="reduce")
        running = page.evaluate("document.getAnimations().length")
        face = page.evaluate(FACING)
        check(running == 0 and 0.8 < face < 1,
              f"{width}: reduced motion stands still at an angle ({running} running, {face:.2f})")
        page.evaluate("document.querySelector('.vitrine').focus()")
        page.wait_for_timeout(100)
        check(page.evaluate(FACING) < -0.8, f"{width}: reduced motion still shows the back")
        context.close()
    # A real finger and a real Tab key, with everything moving: focus() above proves neither.
    context, page = opened(browser, errors, 390, has_touch=True, **({"is_mobile": True} if is_mobile else {}))
    page.locator(".vitrine").tap(position={"x": 170, "y": 300})
    page.wait_for_timeout(1100)
    check(page.evaluate(FACING) < -0.8, "phone: a tap shows the back")
    page.locator("h1").tap()
    page.wait_for_timeout(1100)
    check(page.evaluate(FACING) > 0.5, "phone: a tap elsewhere brings the front back")
    context.close()
    context, page = opened(browser, errors, 1280)
    for _ in range(40):
        page.keyboard.press("Tab")
        if page.evaluate("document.activeElement.classList.contains('vitrine')"):
            break
    page.wait_for_timeout(1100)
    check(page.evaluate(FACING) < -0.8, "keyboard: Tab reaches the case and shows the back")
    context.close()
    if out:
        context, page = opened(browser, errors, 1280, reduced_motion="reduce",
                               device_scale_factor=2)
        box = page.locator(".plaque").bounding_box()
        page.screenshot(path=out / "gros-plan.png", clip=box)
        context.close()


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if out:
        out.mkdir(parents=True, exist_ok=True)
    errors = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome")
        run(browser, WIDTHS, out, errors)
        browser.close()
    check(not errors, f"no error on the page {errors[:3] if errors else ''}")
    print(f"{len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
