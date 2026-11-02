#!/usr/bin/env python3
"""The takes of r64: where the caption of Merlin's clip goes, none covering the clip.

    python3 tools/astuce_takes.py OUT_DIR

Works on `git archive` of TAKEN_FROM in a temporary folder, never on the checkout: each take is CSS
added to its merlin/merlin.css. Writes OUT_DIR/astuce-A.png and so on, the hero alone at 1280, under
reduced motion so that all stand at one angle, for `atelier attach --stamp 1A`. Runs that copy's
tools/check_trombone.py on each take that keeps the caption: it turns the clip through 48 angles at
1280 and 390 and refuses a caption not under the canvas or a clip past its rim. Without a caption,
nothing can cover the clip and the clip is A's, so C skips it (the check needs a caption to measure).
"""

import io
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parent.parent
TAKEN_FROM = "6bca51d"
SOFTWARE_GL = ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
TAKES = {
    "A": "",
    # The canvas stops short of the square's foot, so the clip shrinks with it and the caption
    # takes the foot of the square. The room left under the square for the caption goes.
    "B": """
.scene { margin-bottom: 0; }
.scene img, .scene canvas { width: 90%; height: 90%; align-self: start; }
.astuce { top: auto; bottom: 0; }
""",
    "C": """
.scene { margin-bottom: 0; }
.astuce { display: none; }
""",
}


def tree(where, css):
    archive = subprocess.run(["git", "-C", str(REPO), "archive", TAKEN_FROM], check=True, capture_output=True).stdout
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(where, filter="data")
    with (where / "merlin/merlin.css").open("a", encoding="utf-8") as sheet:
        sheet.write(css)


def picture(browser, where, out):
    page = browser.new_context(viewport={"width": 1280, "height": 900}, reduced_motion="reduce").new_page()
    page.goto((where / "merlin/index.html").as_uri(), wait_until="load")
    page.wait_for_timeout(500)
    page.locator(".une").screenshot(path=str(out))
    page.context.close()


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    failed = False
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", args=SOFTWARE_GL)
        for letter, css in TAKES.items():
            with tempfile.TemporaryDirectory() as folder:
                where = Path(folder)
                tree(where, css)
                picture(browser, where, out / f"astuce-{letter}.png")
                if letter != "C":
                    done = subprocess.run([sys.executable, str(where / "tools/check_trombone.py")],
                                          capture_output=True, text=True)
                    said = [line for line in done.stdout.splitlines() if not line.startswith("OK")]
                    print(letter, "check_trombone:", done.returncode, said)
                    failed = failed or done.returncode != 0
        browser.close()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
