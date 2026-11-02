#!/usr/bin/env python3
"""The takes of r10: the short description under each company on the root index.

    python3 tools/index_takes.py OUT_DIR

Works on `git archive HEAD` in a temporary folder, never on the checkout. Each take is applied
to index.html and must pass the gate. Pictures land in OUT_DIR at 1100 wide and 390 wide, with
the three 390 ones side by side.
"""

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
import check_sites  # noqa: E402


def line(words):
    return f"<p>{words}</p>"


def sheet(trade, since, trait):
    return (f"<dl><div><dt>Métier</dt><dd>{trade}</dd></div>"
            f"<div><dt>Depuis</dt><dd>{since}</dd></div>"
            f"<div><dt>Signe particulier</dt><dd>{trait}</dd></div></dl>")


SHEET_CSS = """
.entreprises dl { margin: 0.5rem 0 0; }
.entreprises dl div { display: flex; flex-wrap: wrap; gap: 0 0.5rem; }
.entreprises dt { font-weight: 700; }
.entreprises dt::after { content: ' :'; }
.entreprises dd { margin: 0; }
"""

TAKES = {
    "A": {"css": "", "merlin": line("Papeterie. Disrupte le papier depuis 1987."),
          "gobelin": line("Studio de jeu vidéo. Hurle depuis 2019."),
          "courtepaille": line("Étude notariale. Cultive la lenteur depuis 1897.")},
    "B": {"css": SHEET_CSS,
          "merlin": sheet("papeterie", "1987", "une présidente qui se like toute seule"),
          "gobelin": sheet("studio de jeu vidéo", "2019", "personne ne dort, tout va bien"),
          "courtepaille": sheet("notaires de père en fils", "1897",
                                "un site dont le neveu assure qu’il existe")},
    "C": {"css": "", "merlin": line("Une papeterie, une présidente en voyage, un comptable ninja."),
          "gobelin": line("Un studio de jeu, un Discord, un build sous NDA."),
          "courtepaille": line("Une étude notariale, de gros virements, un notaire injoignable.")},
}


def fresh_tree(work, name):
    """A copy of HEAD, to apply one take to."""
    tree = Path(work) / name
    tree.mkdir()
    archive = subprocess.run(["git", "-C", str(REPO), "archive", "HEAD"],
                             capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(tree)], input=archive, check=True)
    return tree


def apply_take(tree, take):
    page = tree / "index.html"
    text = page.read_text(encoding="utf-8")
    for company in check_sites.COMPANIES:
        text, done = re.subn(rf'(<a href="{company}/index.html">.*?</h2>\s*)<p>.*?</p>',
                             lambda found: found.group(1) + take[company], text, flags=re.S)
        assert done == 1, company
    page.write_text(text, encoding="utf-8")
    with open(tree / "index.css", "a", encoding="utf-8") as stylesheet:
        stylesheet.write(take["css"])


def shoot(browser, tree, width, out):
    page = browser.new_page(viewport={"width": width, "height": 800})
    page.goto((tree / "index.html").as_uri())
    page.screenshot(path=str(out), full_page=True)
    page.close()


def side_by_side(paths, out, gap=24):
    images = [Image.open(path) for path in paths]
    board = Image.new("RGB", (sum(i.width for i in images) + gap * (len(images) - 1),
                              max(i.height for i in images)), "white")
    x = 0
    for image in images:
        board.paste(image, (x, 0))
        x += image.width + gap
    board.save(out)


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    work = tempfile.mkdtemp(prefix="index_takes_")
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel="chrome")
            narrow = []
            for label, take in TAKES.items():
                tree = fresh_tree(work, f"take{label}")
                apply_take(tree, take)
                refusals = check_sites.check_tree(str(tree))
                if refusals:
                    sys.exit(f"take {label} is refused by the gate:\n" + "\n".join(refusals))
                shoot(browser, tree, 1100, out / f"descriptions-{label}-1100.png")
                narrow.append(out / f"descriptions-{label}-390.png")
                shoot(browser, tree, 390, narrow[-1])
            browser.close()
        side_by_side(narrow, out / "descriptions-390-side-by-side.png")
    finally:
        shutil.rmtree(work)


if __name__ == "__main__":
    main()
