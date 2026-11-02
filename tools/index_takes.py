#!/usr/bin/env python3
"""The takes of r10: the footer's words, the index's words and look, rendered to choose from.

    python3 tools/index_takes.py OUT_DIR

Works on `git archive HEAD` in a temporary folder, never on the checkout. Each take is applied
to the whole tree, every page's footer included, and must pass the gate. Pictures land in
OUT_DIR at 1100 wide, with the index takes also at 390.
"""

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

FOOTERS = {
    "A": "<strong>Site fictif à but pédagogique.</strong> Les entreprises, les employés et les "
         "domaines présentés ici n’existent pas : toute ressemblance avec une entreprise ou "
         "une personne réelle serait fortuite. Ce site ne collecte rien.",
    "B": "<strong>Site fictif à but pédagogique.</strong> Entreprises, employés et domaines "
         "inventés, toute ressemblance serait fortuite. Rien n’est collecté ici.",
    "C": "<strong>Ce site est une fiction pédagogique.</strong> Ces entreprises n’ont jamais "
         "existé, leurs employés non plus, et toute ressemblance serait fortuite, même avec "
         "votre patron. Ce site ne collecte rien.",
}

CHAPO_NOW = ("Ces trois entreprises n’existent pas, leurs employés non plus. Ce sont les kits "
             "OSINT de l’atelier « La meilleure défense, c’est l’attaque » du cours "
             "Social Engineering : une équipe en choisit une et monte contre elle un "
             "hameçonnage sur papier.")

INDEXES = {
    "A": {"title": "Entreprises fictives", "chapo": CHAPO_NOW, "css": ""},
    "B": {
        "title": "Annuaire des entreprises qui n’existent pas",
        "chapo": "Trois entreprises, zéro existence. Leurs employés non plus n’existent pas, ce "
                 "qui ne les empêche pas de trop en dire. Atelier « La meilleure défense, "
                 "c’est l’attaque », cours Social Engineering.",
        "css": """
body { background: #f7d94c; font-family: Georgia, 'Times New Roman', serif; }
h1 { padding-bottom: 0.75rem; border-bottom: 4px double #24262b; font-size: 2.1rem; }
.entreprises { columns: 2 18rem; column-gap: 2rem; }
.entreprises li { break-inside: avoid; border-top: 1px solid #24262b; }
.entreprises h2 { text-transform: uppercase; font-size: 1.05rem; letter-spacing: 0.04em; }
.a-venir { color: #24262b; text-transform: none; letter-spacing: 0; }
.entreprises a { color: #24262b; }
""",
    },
    "C": {
        "title": "Choisissez votre cible",
        "chapo": "Trois entreprises inventées, avec leurs employés inventés. Une équipe en "
                 "choisit une, lit tout ce qu’elle raconte sur elle-même, et monte contre elle "
                 "un hameçonnage sur papier. Atelier « La meilleure défense, c’est "
                 "l’attaque », cours Social Engineering.",
        "css": """
body { background: #3c4048; color: #24262b; font-family: 'Courier New', Courier, monospace; }
h1, .chapo { color: #f4f4f2; }
.entreprises li { position: relative; margin-bottom: 1.25rem; padding: 1.25rem;
  border: 0; border-radius: 3px 14px 3px 3px; background: #e6cf9f; }
.entreprises li::after { content: 'FICTIF'; position: absolute; top: 0.6rem; right: 0.8rem;
  padding: 0 0.35rem; border: 2px solid #9c2b22; color: #9c2b22; font-size: 0.8rem;
  font-weight: 700; transform: rotate(4deg); }
.entreprises h2 { padding-right: 4.5rem; }
.a-venir { color: #24262b; white-space: nowrap; }
.entreprises a { color: #24262b; }
""",
    },
}


def fresh_tree(work, name):
    """A copy of HEAD, to apply one take to."""
    tree = Path(work) / name
    tree.mkdir()
    archive = subprocess.run(["git", "-C", str(REPO), "archive", "HEAD"],
                             capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(tree)], input=archive, check=True)
    return tree


def set_footer(tree, words):
    for page in tree.rglob("*.html"):
        text = page.read_text(encoding="utf-8")
        start = text.index('<footer class="site-fictif">')
        end = text.index("</footer>", start)
        block = f'<footer class="site-fictif">\n    <p>{words}</p>\n  '
        page.write_text(text[:start] + block + text[end:], encoding="utf-8")


def set_index(tree, take):
    page = tree / "index.html"
    text = page.read_text(encoding="utf-8")
    assert CHAPO_NOW in text
    text = text.replace(CHAPO_NOW, take["chapo"]).replace(
        "<h1>Entreprises fictives</h1>", f"<h1>{take['title']}</h1>")
    page.write_text(text, encoding="utf-8")
    with open(tree / "index.css", "a", encoding="utf-8") as sheet:
        sheet.write(take["css"])


def gate(tree, label):
    refusals = check_sites.check_tree(str(tree))
    if refusals:
        sys.exit(f"take {label} is refused by the gate:\n" + "\n".join(refusals))


def shoot(browser, tree, width, out):
    page = browser.new_page(viewport={"width": width, "height": 800})
    page.goto((tree / "index.html").as_uri())
    page.screenshot(path=str(out), full_page=True)
    page.close()


def side_by_side(paths, out, gap=24):
    images = [Image.open(path) for path in paths]
    sheet = Image.new("RGB", (sum(i.width for i in images) + gap * (len(images) - 1),
                              max(i.height for i in images)), "white")
    x = 0
    for image in images:
        sheet.paste(image, (x, 0))
        x += image.width + gap
    sheet.save(out)


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    work = tempfile.mkdtemp(prefix="index_takes_")
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel="chrome")
            for label, words in FOOTERS.items():
                tree = fresh_tree(work, f"footer{label}")
                set_footer(tree, words)
                gate(tree, f"footer {label}")
                page = browser.new_page(viewport={"width": 1100, "height": 800})
                page.goto((tree / "index.html").as_uri())
                page.locator(".site-fictif").screenshot(path=str(out / f"footer-{label}.png"))
                page.close()
            narrow = []
            for label, take in INDEXES.items():
                tree = fresh_tree(work, f"index{label}")
                set_index(tree, take)
                gate(tree, f"index {label}")
                shoot(browser, tree, 1100, out / f"index-{label}-1100.png")
                narrow.append(out / f"index-{label}-390.png")
                shoot(browser, tree, 390, narrow[-1])
            browser.close()
        side_by_side(narrow, out / "index-390-side-by-side.png")
    finally:
        shutil.rmtree(work)


if __name__ == "__main__":
    main()
