#!/usr/bin/env python3
"""What tools/check_configurateur_safari.py runs on a Mac, tried in Chrome here, since a macOS minute counts
ten times: its whole flow through a stand-in driver, its file:// probe, its read of the pixels on a right
log and on one whose lid is really missing.

    python3 tests/test_check_configurateur_safari.py
"""
import base64
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

from playwright.sync_api import sync_playwright

import check_configurateur as cc
import check_configurateur_browsers as ccb
import check_configurateur_safari as tool
from check_trombone_safari import BEGIN, END, serve


def as_function(source):
    """A driver's script is a function body reading `arguments`: the same for Playwright."""
    return "(args) => (function () {" + source + "}).apply(null, args)"


class Stand(tool.Safari):
    """The same moves as tool.Safari, by Playwright. `extra` goes on every page: a bug to find."""

    def __init__(self, browser, port, lines, extra=""):
        self.narrow = False
        self.url, self.lines, self.extra = f"http://127.0.0.1:{port}/{tool.PAGE}", lines, extra
        self.top = browser.new_page(viewport={"width": 1280, "height": 900})
        self.at = self.top

    def script(self, source, *args):
        return self.at.evaluate(as_function(source), list(args))

    def open(self, narrow):
        self.top.goto(self.url, wait_until="load")
        self.at = self.top
        if narrow:
            self.top.evaluate(as_function(tool.IN_FRAME.replace("done(f)", "done(true)")), [])
            self.at = self.top.frames[1]
        if self.extra:
            self.at.add_style_tag(content=self.extra)

    def click(self, selector):
        self.at.locator(selector).click()

    def move(self, origin, x=0, y=0):
        self.top.mouse.move(0, 0)

    def hover(self, selector):
        self.at.locator(selector).hover()

    def shot(self, selector):
        return base64.b64encode(self.at.locator(selector).screenshot()).decode()

    def frame(self, name, state):
        text = base64.b64encode(self.top.screenshot(type="jpeg", quality=80)).decode()
        self.lines += [f"{BEGIN} {name}", text, END]


def main():
    failures = []
    if tool.STATES != ccb.STATES:
        failures.append("STATES differ from tools/check_configurateur_browsers.py")
    if tool.HIDE != ccb.HIDE or tool.FLAT != ccb.CONTROLS["flat"][0] or tool.HOLLOW != ccb.CONTROLS["hollow"][0]:
        failures.append("HIDE, FLAT or HOLLOW differ from tools/check_configurateur_browsers.py")
    if tool.FREEZE_AT != 6000:
        failures.append("the sway is not frozen where check_configurateur_browsers freezes it")
    for combo, amount in tool.TOTALS:
        if sum(cc.MODELS.get(i, 0) + cc.ADDS.get(i, 0) for i in combo) != amount:
            failures.append(f"TOTALS: {combo} is not {amount}")
    if {i for combo, _ in tool.TOTALS for i in combo} | set(tool.RESETS) != set(cc.MODELS) | set(cc.ADDS):
        failures.append("TOTALS leaves an option untried")
    html = (REPO / tool.PAGE).read_text(encoding="utf-8")
    for view, (radio, angle) in tool.VIEWS.items():
        if f'<label for="{radio}">{view}</label>' not in html or f'id="{radio}"' not in html:
            failures.append(f"the view {view} is not on {radio}")

    port = serve()
    logs = {}
    d = tempfile.mkdtemp()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", args=["--hide-scrollbars"])
        # The flow, in Chrome: must pass. A lid with no top: must be caught.
        for name, extra in (("right", ""), ("lidless", ".h-de { visibility: hidden !important; }")):
            lines, failed = [], []
            stand = Stand(browser, port, lines, extra)
            if name == "right":
                tool.run_turn(stand, failed)
                tool.run_totals(stand, failed)
                # The read must see a wrong total: a browser that stopped summing.
                stand.open(False)
                stand.script(tool.ADD_STYLE, ".compte { counter-increment: none !important; }")
                stand.pick(["n6"])
                if stand.price_is(".ticket .prixf", 449 + 72):
                    failures.append("the total's read passed a browser that does not sum")
            tool.run_states(stand, lines.append, failed)
            stand.top.close()
            if name == "right" and failed:
                failures.append(f"the flow on a right page: {failed}")
            logs[name] = Path(d) / name
            logs[name].write_text("\n".join(lines) + "\n")

        # Over file://: the beacon comes back and the steps do what they say.
        scratch = REPO / "dernier-prix/_sonde_test.html"
        try:
            scratch.write_text(tool.scratch_page(port, "t"), encoding="utf-8")
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.goto(scratch.as_uri())
            load = tool.wait_for("t-load", 8)
            failures.extend(tool.load_problems(load))
            expected = {"ferme": ("pin", 0, 0, 0), "ouvert": ("pin", 104, 0, 0), "kit": ("pin", 0, 92, 0),
                        "bout": ("pin", 0, 0, 0), "chene": ("chene", 0, 0, 6)}
            for name, _, angle, _ in tool.STEPS:
                said = tool.wait_for(f"t-{name}", 12)
                failures.extend(tool.step_problems(name, angle, said))
                wood, lid, kit, handles = expected[name]
                if not said or wood not in said["wood"] or abs(said["lid"] - lid) > 2 or abs(said["kit"] - 70 - kit) > 1 or said["handles"] != handles:
                    failures.append(f"file:// step {name}: {said}")
            page.close()
        finally:
            scratch.unlink(missing_ok=True)
        browser.close()

    # Outside the block: extract opens its own Playwright, which cannot nest.
    if tool.extract(logs["right"], Path(d) / "right-out"):
        failures.append("--extract refused the right page")
    if not tool.extract(logs["lidless"], Path(d) / "lidless-out"):
        failures.append("--extract passed a lid with no top")
    shutil.rmtree(d)
    for failure in failures:
        print("FAILED:", failure)
    print("OK" if not failures else f"{len(failures)} failures")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
