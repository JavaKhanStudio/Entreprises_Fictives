#!/usr/bin/env python3
"""Open pages both ways a student can, check them, and take a picture of each.

    python3 tools/render_pages.py OUT_DIR index.html [merlin/index.html ...]

Each page is opened over file:// (a double-click) and over http://127.0.0.1:8802 (the port
CLAUDE.md names, which must be free), at 1280 and 390 wide. It fails on a request that fails or
a console error, on base.css not applied, on a page wider than its window, and when the two
ways do not give the same picture. Pictures land in OUT_DIR as <page>-<width>.png.

The gate (tools/check_sites.py) reads the source; this one looks at what a browser made of it.
Needs Playwright and Chrome, which a student never does.
"""

import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parent.parent
PORT = 8802
WIDTHS = (1280, 390)
FOOTER_BACKGROUND = "rgb(36, 38, 43)"  # .site-fictif in shared/base.css


def open_page(browser, url, width):
    """Load url at this width. Returns the picture and what went wrong."""
    problems = []
    context = browser.new_context(viewport={"width": width, "height": 800})
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
    picture = page.screenshot(full_page=True)
    context.close()
    return picture, problems


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    server = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT),
                               "--bind", "127.0.0.1", "--directory", str(REPO)],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    failed = 0
    try:
        for _ in range(50):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{PORT}/", timeout=1)
                break
            except OSError:
                time.sleep(0.1)
        if server.poll() is not None:
            print(f"port {PORT} is taken: free it first")
            return 2
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel="chrome")
            for name in sys.argv[2:]:
                for width in WIDTHS:
                    by_file, problems = open_page(browser, (REPO / name).as_uri(), width)
                    by_http, more = open_page(browser, f"http://127.0.0.1:{PORT}/{name}", width)
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
        server.terminate()
        server.wait()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
