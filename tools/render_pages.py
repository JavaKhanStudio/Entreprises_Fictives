#!/usr/bin/env python3
"""Open pages both ways a student can, check them, and take a picture of each.

    python3 tools/render_pages.py OUT_DIR index.html [merlin/index.html ...]

Each page is opened over file:// (a double-click) and over http from a server of this run's own,
on a free port the system picks, at 1280 and 390 wide. It fails on a request that fails or
a console error, on base.css not applied, on a page wider than its window, and when the two
ways do not give the same picture. Pictures land in OUT_DIR as <page>-<width>.png.

The gate (tools/check_sites.py) reads the source; this one looks at what a browser made of it.
Needs Playwright and Chrome, which a student never does.
"""

import functools
import http.server
import os
import sys
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parent.parent
WIDTHS = (1280, 390)
FOOTER_BACKGROUND = "rgb(36, 38, 43)"  # .site-fictif in shared/base.css


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def whole_page(page, width):
    """A picture of the whole page, the same every time.

    Not screenshot(full_page=True): that resizes the page inside the capture, and the rounded
    corners on a composited layer (Gobelin's sticky blurred .haut, its active menu pill) came
    out in one of two rasters, 39 pixels apart by at most 4/255. The window takes the page's
    height first, and the page gets two frames to settle (r41, tools/render_diff_probe.py).
    A page of fractional height is rounded up, so a min-height: 100vh footer can sit under a
    pixel lower than in a smaller window: one line of its text may land a pixel off (r41).
    """
    height = page.evaluate("document.documentElement.scrollHeight")
    page.set_viewport_size({"width": width, "height": height})
    page.evaluate("() => new Promise(done => requestAnimationFrame("
                  "() => requestAnimationFrame(done)))")
    return page.screenshot()


def open_page(browser, url, width):
    """Load url at this width. Returns the picture and what went wrong."""
    problems = []
    # What moves stops under reduced motion (merlin/merlin.js, merlin/merlin.css): two pictures
    # of a turning page would never match. tools/check_trombone.py looks at the moving one.
    context = browser.new_context(viewport={"width": width, "height": 800},
                                  reduced_motion="reduce")
    page = context.new_page()
    page.on("requestfailed", lambda r: problems.append(f"request failed: {r.url}"))
    page.on("response", lambda r: r.status >= 400 and "favicon" not in r.url
            and problems.append(f"{r.status}: {r.url}"))
    # Chrome asks for /favicon.ico by itself, over http only: no page asked for it.
    page.on("console", lambda m: m.type == "error" and "favicon" not in m.location["url"]
            and problems.append(f"console: {m.text} ({m.location['url']})"))
    page.on("pageerror", lambda e: problems.append(f"page error: {e}"))
    page.goto(url, wait_until="load")
    background = page.evaluate(
        "getComputedStyle(document.querySelector('.site-fictif')).backgroundColor")
    if background != FOOTER_BACKGROUND:
        problems.append(f"base.css not applied: the footer's background is {background}")
    overflow = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
    if overflow > 0:
        problems.append(f"{overflow}px wider than the window")
    picture = whole_page(page, width)
    context.close()
    return picture, problems


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    handler = functools.partial(QuietHandler, directory=str(REPO))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_address[1]
    failed = 0
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel="chrome")
            for name in sys.argv[2:]:
                for width in WIDTHS:
                    by_file, problems = open_page(browser, (REPO / name).as_uri(), width)
                    by_http, more = open_page(browser, f"http://127.0.0.1:{port}/{name}", width)
                    problems += [f"http: {p}" for p in more]
                    if by_file != by_http:
                        problems.append("file:// and http:// give different pictures")
                    target = out / f"{name.replace(os.sep, '_').replace('/', '_')}-{width}.png"
                    target.write_bytes(by_file)
                    print(f"{name} at {width}: {'OK' if not problems else 'FAILED'} -> {target}")
                    for problem in problems:
                        print(f"  {problem}")
                    failed += bool(problems)
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
