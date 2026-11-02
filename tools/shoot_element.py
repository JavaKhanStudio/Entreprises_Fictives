#!/usr/bin/env python3
"""A zoomed picture of one element of a page, at the two widths render_pages.py uses.

    python3 tools/shoot_element.py OUT_DIR merlin/contact.html img.plan [NAME]

render_pages.py shoots whole pages, where a detail of a small picture cannot be judged (r43).
Opens the page over file://, three times the pixels. Pictures land as OUT_DIR/NAME-<width>.png.
"""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parent.parent
WIDTHS = (1280, 390)


def main():
    if len(sys.argv) not in (4, 5):
        sys.exit(__doc__)
    out, page_path, selector = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    name = sys.argv[4] if len(sys.argv) == 5 else Path(page_path).stem
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for width in WIDTHS:
            context = browser.new_context(viewport={"width": width, "height": 800},
                                          device_scale_factor=3, reduced_motion="reduce")
            page = context.new_page()
            page.goto((REPO / page_path).as_uri())
            target = out / f"{name}-{width}.png"
            page.locator(selector).first.screenshot(path=target)
            print(target)
            context.close()
        browser.close()


if __name__ == "__main__":
    main()
