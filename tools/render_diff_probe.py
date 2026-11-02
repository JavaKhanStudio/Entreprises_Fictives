#!/usr/bin/env python3
"""Where and how much file:// and http:// differ, when render_pages says "different pictures".

    python3 tools/render_diff_probe.py [--runs 5] [--width 390] [--load N] gobelin/index.html ...

Prints, per run, "same" or the box that differs and its largest difference out of 255, and exits
1 if any run differed. --load N keeps N processes spinning meanwhile, for a flake that only shows
on a busy machine.
Needs Playwright, Chrome and Pillow.
"""
import argparse
import functools
import http.server
import io
import multiprocessing
import sys
import threading

from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

import render_pages


def spin():
    while True:
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--width", type=int, default=390)
    parser.add_argument("--load", type=int, default=0)
    parser.add_argument("pages", nargs="+")
    args = parser.parse_args()
    spinners = [multiprocessing.Process(target=spin, daemon=True) for _ in range(args.load)]
    for spinner in spinners:
        spinner.start()
    differed = 0
    handler = functools.partial(render_pages.QuietHandler, directory=str(render_pages.REPO))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_address[1]
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome")
        for name in args.pages:
            for run in range(args.runs):
                by_file, _ = render_pages.open_page(browser, (render_pages.REPO / name).as_uri(), args.width)
                by_http, _ = render_pages.open_page(browser, f"http://127.0.0.1:{port}/{name}", args.width)
                if by_file == by_http:
                    print(f"{name} run {run}: same")
                    continue
                differed += 1
                first = Image.open(io.BytesIO(by_file)).convert("RGB")
                second = Image.open(io.BytesIO(by_http)).convert("RGB")
                if first.size != second.size:
                    print(f"{name} run {run}: sizes {first.size} and {second.size}")
                    continue
                difference = ImageChops.difference(first, second)
                worst = max(high for _, high in difference.getextrema())
                print(f"{name} run {run}: box {difference.getbbox()}, at most {worst}/255")
        browser.close()
    server.shutdown()
    for spinner in spinners:
        spinner.terminate()
    return 1 if differed else 0


if __name__ == "__main__":
    sys.exit(main())
