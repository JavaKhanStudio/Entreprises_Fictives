#!/usr/bin/env python3
"""What tools/check_racine_safari.py runs on a Mac, tried in Chrome here, since a macOS minute counts ten
times: its page scripts, its scratch page's beacon over file://, its forced open, its read of the
pixels on a real open card and on a flattened one.

    python3 tests/test_check_racine_safari.py
"""
import base64
import json
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

from playwright.sync_api import sync_playwright

import check_racine
import check_racine_safari as tool
from check_trombone_safari import BEGIN, END, reports, serve


def as_function(source):
    """A driver's script is a function body reading `arguments`: the same for Playwright."""
    return "(args) => (function () {" + source + "}).apply(null, args)"


def frame_lines(name, jpeg):
    text = base64.b64encode(jpeg).decode()
    return [f"{BEGIN} {name}", text, END]


def main():
    failures = []
    if tool.CARDS != check_racine.CARDS:
        failures.append(f"CARDS differ from tools/check_racine.py: {tool.CARDS}")
    pictures = (REPO / "index.html").read_text(encoding="utf-8").count("<img")
    port = serve()
    with sync_playwright() as playwright, tempfile.TemporaryDirectory() as d:
        browser = playwright.chromium.launch(channel="chrome")
        scratch = REPO / "_sonde_test.html"
        forced = REPO / "_sonde_test_force.html"
        try:
            # Over file://: the beacon comes back, and says the pictures loaded.
            scratch.write_text(tool.scratch_page(port, "t"), encoding="utf-8")
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.goto(scratch.as_uri())
            load = tool.wait_for("t-load", 8)
            if not load or load["failed"] or not all(w for _, w in load["images"]) or len(load["images"]) != pictures:
                failures.append(f"file:// beacon: {load}")
            if not tool.wait_for("t-state", 4) or reports["t-state"]["hover"] or reports["t-state"]["flap"] < 0.9:
                failures.append(f"rest over file://: {reports.get('t-state')}")
            # The centre it reports is where the card is: playwright's window has no chrome, so inner = outer.
            page.mouse.move(*load["centre"])
            time.sleep(tool.SETTLE)
            reports.pop("t-state", None)
            said = tool.wait_for("t-state", 4)
            if not said or not said["hover"] or said["flap"] > -0.9 or said["risen"] < 20:
                failures.append(f"a mouse on the reported centre: {said}")
            page.close()

            # The forced page opens with no pointer.
            forced.write_text(tool.scratch_page(port, "f", force=True), encoding="utf-8")
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.goto(forced.as_uri())
            time.sleep(1.5 + tool.SETTLE)
            said = tool.wait_for("f-state", 4)
            if not said or said["hover"] or not said["force"] or said["flap"] > -0.9 or said["risen"] < 20:
                failures.append(f"forced open: {said}")
            page.close()

            # The driver's scripts, and the pixel read: open passes, flat must not.
            lines = []
            for flat in (False, True):
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                page.goto(f"http://127.0.0.1:{port}/index.html")
                time.sleep(1.5)
                if flat:
                    page.evaluate(as_function(tool.ADD_STYLE), [tool.FLAT])
                card = "inviolia"
                page.evaluate(f"document.querySelector('.cible.{card}').scrollIntoView({{block: 'center'}})")
                if not flat:
                    page.evaluate(as_function(tool.WATCH), [card])
                page.hover(f".cible.{card} > a")
                time.sleep(tool.SETTLE)
                state = page.evaluate(as_function(tool.PARTS), [card])
                if not flat:
                    problems = tool.open_problems(card, state)
                    if problems:
                        failures.append(f"open_problems on an open card: {problems}")
                    swing = page.evaluate("window.__swing")
                    if not any(-0.8 < v < 0.8 for v in swing):
                        failures.append(f"the watch saw no part-way frame: {swing[:20]}")
                name = f"{'plat' if flat else 'ouvert'}-{card}"
                lines.append(f"{tool.META} {name} {json.dumps(state)}")
                lines += frame_lines(name, page.screenshot(type="jpeg", quality=85))
                page.close()
            log = Path(d) / "log"
            log.write_text("\n".join(lines) + "\n")
            verdict = tool.extract(log, Path(d) / "out")
            if verdict:
                failures.append("--extract refused a real open card and a real flat one")

            # A flat control that reads as open must fail the extract.
            swapped = list(lines)
            opened = [i for i, l in enumerate(swapped) if l.startswith(f"{BEGIN} ouvert")][0]
            flat = [i for i, l in enumerate(swapped) if l.startswith(f"{BEGIN} plat")][0]
            swapped[opened + 1], swapped[flat + 1] = swapped[flat + 1], swapped[opened + 1]
            log.write_text("\n".join(swapped) + "\n")
            if not tool.extract(log, Path(d) / "out2"):
                failures.append("--extract passed a flattened picture as open")
        finally:
            scratch.unlink(missing_ok=True)
            forced.unlink(missing_ok=True)
        browser.close()
    for failure in failures:
        print("FAILED:", failure)
    print("OK" if not failures else f"{len(failures)} failures")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
