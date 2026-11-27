#!/usr/bin/env python3
"""What tools/check_racine_safari.py runs on a Mac, tried in Chrome here, since a macOS minute counts ten
times: its page scripts, its scratch page's beacon over file://, its forced open, its read of the
pixels on a real open card and on a flattened one.

    python3 tests/test_check_racine_safari.py
"""
import base64
import contextlib
import io
import json
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

from PIL import Image
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


def black_jpeg():
    """The frame of r97: the size it came back at, nothing above 16."""
    buffer = io.BytesIO()
    Image.new("RGB", (1400, 1037), (16, 16, 16)).save(buffer, "JPEG", quality=85)
    return buffer.getvalue()


def check_black_frames(lines, d, failures):
    """--extract names a black window, open or flat, and never takes it for a read of the letter."""
    for i, kind in enumerate(("ouvert", "plat")):
        black = list(lines)
        at = [n for n, l in enumerate(black) if l.startswith(f"{BEGIN} {kind}")][0]
        black[at + 1] = base64.b64encode(black_jpeg()).decode()
        log = Path(d) / f"black-{kind}"
        log.write_text("\n".join(black) + "\n")
        said = io.StringIO()
        with contextlib.redirect_stdout(said):
            verdict = tool.extract(log, Path(d) / f"out-black-{kind}")
        if not verdict:
            failures.append(f"--extract passed a black window as {kind}")
        if "a black window" not in said.getvalue():
            failures.append(f"--extract did not name the black {kind} window: {said.getvalue()}")


def check_steady_shot(real, failures):
    """A blank shot is taken once more, a good one never; the blank's size is the one r97 measured."""
    black = black_jpeg()
    for shots, want, takes, note in (([real], real, 1, False), ([black, real], real, 2, True), ([black, black], black, 2, True)):
        left, said = list(shots), io.StringIO()
        with contextlib.redirect_stdout(said):
            got = tool.steady_shot("ouvert-merlin", lambda: left.pop(0), wait=0)
        if got != want or len(shots) - len(left) != takes or ("shooting it again" in said.getvalue()) != note:
            failures.append(f"steady_shot on {[len(s) for s in shots]}: {len(got)} bytes, {said.getvalue()!r}")


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
            check_black_frames(lines, d, failures)
            real = base64.b64decode([lines[i + 1] for i, l in enumerate(lines) if l.startswith(f"{BEGIN} ouvert")][0])
            check_steady_shot(real, failures)
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
