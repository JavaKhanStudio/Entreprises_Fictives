#!/usr/bin/env python3
"""The takes of r19: the icon each company wears in a browser tab.

    python3 tools/icon_takes.py OUT_DIR

Writes one sheet per company in OUT_DIR, one equal column per take, so that
`atelier attach --stamp 1A,1B,1C` can letter them. Each column shows the icon in a light tab and
a dark tab, drawn at the real 16 px then enlarged 3 times without smoothing, then the drawing
at 128 px. Touches nothing in the checkout.
"""

import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parent.parent
SCALE = 3
TAB_W, TAB_H = 200, 34
PANEL_W = TAB_W * SCALE + 40
PANEL_H = TAB_H * SCALE * 2 + 128 + 80


def svg(body, box=64):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {box} {box}">{body}</svg>'


MERLIN_GRADIENT = ('<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
                   '<stop offset="0" stop-color="#818cf8"/><stop offset=".55" stop-color="#a855f7"/>'
                   '<stop offset="1" stop-color="#fb7185"/></linearGradient></defs>'
                   '<rect width="64" height="64" rx="16" fill="url(#g)"/>')
BOLD_CLIP = "M46 24V45a11 11 0 0 1-22 0V17a7.500 7.500 0 0 1 15 0V43a4.500 4.500 0 0 1-9 0V24"

COURTEPAILLE_DISC = '<circle cx="32" cy="32" r="31" fill="#8c1c13"/>'


def sheaf(colour):
    """The seal's sheaf with fewer straws, thick enough for 16 px, the middle one short."""
    tops = "".join(f'<path d="M32 42L{x} {y}"/>' for x, y in ((15, 13), (24, 9), (32, 25), (40, 9), (49, 13)))
    return (f'<g stroke="{colour}" stroke-width="4.500" stroke-linecap="round" fill="none">{tops}'
            '<path d="M32 42L20 54M32 42L44 54"/></g>'
            f'<rect x="23" y="38" width="18" height="7" rx="2" fill="{colour}"/>')


TAKES = {
    "merlin": ("Accueil | Papeterie Merlin", {
        "A": REPO.joinpath("merlin/img/logo.svg").read_text(encoding="utf-8"),
        "B": svg(MERLIN_GRADIENT + f'<path d="{BOLD_CLIP}" transform="translate(-3 0)" '
                 'fill="none" stroke="#fff" stroke-width="4.500" stroke-linecap="round"/>'),
        "C": svg('<rect width="64" height="64" rx="16" fill="#0a0d24"/>'
                 f'<path d="{BOLD_CLIP}" transform="translate(-3 0)" fill="none" '
                 'stroke="#fb7185" stroke-width="4.500" stroke-linecap="round"/>'),
    }),
    "gobelin": ("Accueil · Gobelin Hurlant", {
        "A": REPO.joinpath("gobelin/img/logo.svg").read_text(encoding="utf-8"),
        "B": svg('<rect width="64" height="64" rx="10" fill="#0c0e11"/>'
                 '<path d="M17 28 L2 15 L16 40Z M47 28 L62 15 L48 40Z" fill="#b9f73e"/>'
                 '<path d="M13 31Q13 8 32 8Q51 8 51 31Q51 60 32 61Q13 60 13 31Z" fill="#b9f73e"/>'
                 '<path d="M20 23l9 5-2 4-8-4zM44 23l-9 5 2 4 8-4z" fill="#12160f"/>'
                 '<path d="M20 37Q32 31 44 37Q42 57 32 58Q22 57 20 37Z" fill="#12160f"/>'
                 '<path d="M23 36l3 7 3-8zM35 35l3 8 3-7z" fill="#f0f5e4"/>'),
        "C": svg('<rect width="64" height="64" rx="10" fill="#b9f73e"/>'
                 '<path d="M8 20Q32 8 56 20Q52 60 32 60Q12 60 8 20Z" fill="#12160f"/>'
                 '<path d="M14 19l6 13 7-16zM37 16l7 16 6-13z" fill="#f0f5e4"/>'
                 '<ellipse cx="32" cy="50" rx="11" ry="7" fill="#ff6fb5"/>'),
    }),
    "courtepaille": ("Accueil | Étude Courtepaille, notaires", {
        "A": REPO.joinpath("courtepaille/img/sceau.svg").read_text(encoding="utf-8"),
        "B": svg(COURTEPAILLE_DISC + sheaf("#e9d9a6")),
        "C": svg(COURTEPAILLE_DISC + '<path d="M45 19A18.500 18.500 0 1 0 45 45" fill="none" '
                 'stroke="#e9d9a6" stroke-width="9"/>'),
    }),
}

TAKES["racine"] = ("Choisissez votre cible", {
    "A": REPO.joinpath("icon.svg").read_text(encoding="utf-8"),
})

TAB = """<!doctype html><meta charset="utf-8"><style>
html,body{{margin:0;background:{strip}}}
.tab{{width:{w}px;height:{h}px;box-sizing:border-box;padding:0 8px;display:flex;align-items:center;gap:8px;
background:{tab};color:{text};font:12px sans-serif;overflow:hidden;white-space:nowrap;
border-radius:8px 8px 0 0;margin-top:0}}
img{{width:16px;height:16px;flex:none}}
</style><div class="tab"><img src="{icon}"><span>{title}</span></div>"""

THEMES = (("#dee1e6", "#fff", "#202124"), ("#202124", "#35363a", "#e8eaed"))


def shoot(browser, html, width, height, tmp, name):
    page_file = Path(tmp) / f"{name}.html"
    page_file.write_text(html, encoding="utf-8")
    page = browser.new_page(viewport={"width": width, "height": height})
    page.goto(page_file.as_uri())
    page.wait_for_load_state("load")
    target = Path(tmp) / f"{name}.png"
    page.screenshot(path=target, omit_background=True)
    page.close()
    return Image.open(target).convert("RGBA")


def panel(browser, title, code, tmp, stem):
    icon = Path(tmp) / f"{stem}.svg"
    icon.write_text(code, encoding="utf-8")
    sheet = Image.new("RGBA", (PANEL_W, PANEL_H), "#f4f4f4")
    y = 20
    for n, (strip, tab, text) in enumerate(THEMES):
        html = TAB.format(strip=strip, tab=tab, text=text, w=TAB_W, h=TAB_H, icon=icon.as_uri(),
                          title=title)
        shot = shoot(browser, html, TAB_W, TAB_H, tmp, f"{stem}-tab{n}")
        big = shot.resize((TAB_W * SCALE, TAB_H * SCALE), Image.NEAREST)
        sheet.paste(big, (20, y))
        y += TAB_H * SCALE + 10
    html = (f'<!doctype html><style>html,body{{margin:0;background:#f4f4f4}}'
            f'img{{width:128px;height:128px;display:block}}</style><img src="{icon.as_uri()}">')
    drawing = shoot(browser, html, 128, 128, tmp, f"{stem}-big")
    sheet.paste(drawing, ((PANEL_W - 128) // 2, y + 10))
    return sheet


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="icon-takes-") as tmp, sync_playwright() as p:
        browser = p.chromium.launch()
        for company, (title, takes) in TAKES.items():
            sheet = Image.new("RGB", (PANEL_W * len(takes), PANEL_H), "#f4f4f4")
            for n, (letter, code) in enumerate(takes.items()):
                sheet.paste(panel(browser, title, code, tmp, f"{company}-{letter}"), (PANEL_W * n, 0))
            draw = ImageDraw.Draw(sheet)
            for n in range(1, len(takes)):
                draw.line([(PANEL_W * n, 0), (PANEL_W * n, PANEL_H)], fill="#bbb", width=2)
            target = out / f"{company}.png"
            sheet.save(target)
            print(target)
        browser.close()


if __name__ == "__main__":
    main()
