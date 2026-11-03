#!/usr/bin/env python3
"""The takes of r89: a dead body in Au Dernier Prix's 3D coffin, man or woman, put on top of the real page.

    python3 tools/dernier_prix_corps_takes.py OUT     # take-*.png in OUT, for `atelier attach --stamp`

Not on the site: students see nothing of this until Simon has said yes, since the body is spicy. Boxes
of six planes, placed like the coffin's own (x along it, y down, z towards the viewer), showing from
their outside only. It lies high, near the walls' top, or the near wall hides it from this camera; in
kit it comes down onto the floor. Shut, it is hidden, or hairlines of it show at the planes' seams (598 px
measured). Prints whether the closed coffin still hides it. Needs Playwright,
Chrome, Pillow.
"""
import sys
from pathlib import Path

from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_configurateur as cc  # noqa: E402

SKIN, HAIR_M, HAIR_F, SHOE = "#d9cfc4", "#8b8b86", "#6d5a48", "#141414"
SUIT, DRESS, SHIRT, TIE = "#23262e", "#4a2233", "#ece9e2", "#6b1420"


def shade(colour, dark):
    r, g, b = (int(colour[i:i + 2], 16) for i in (1, 3, 5))
    return f"rgb({r * dark:.0f} {g * dark:.0f} {b * dark:.0f})"


def box(x0, x1, z0, z1, top, bottom, colour, cover=None):
    """A box's five faces that can show, each a plane like the coffin's. cover paints its top."""
    w, d, h = x1 - x0, z1 - z0, bottom - top
    faces = [(w, h, f"translate3d({x0}px, {top}px, {z1}px)", .78), (w, h, f"translate3d({x1}px, {top}px, {z0}px) rotateY(180deg)", .55),
             (d, h, f"translate3d({x1}px, {top}px, {z1}px) rotateY(90deg)", .65), (d, h, f"translate3d({x0}px, {top}px, {z0}px) rotateY(-90deg)", .7),
             (w, d, f"translate3d({x0}px, {top}px, {z0}px) rotateX(90deg)", 1)]
    out = []
    for fw, fh, transform, dark in faces:
        ground = cover if cover and dark == 1 else shade(colour, dark)
        out.append(f'<i class="f" style="width:{fw}px;height:{fh}px;transform:{transform};background:{ground}"></i>')
    return "".join(out)


def face(hair):
    """Seen from above, the head towards -x: a forehead under its hair, closed eyes, a mouth."""
    return (f"linear-gradient(90deg, {hair} 0 26%, transparent 26%), "
            "linear-gradient(#2a2420, #2a2420) 42% 30% / 3px 9px no-repeat, linear-gradient(#2a2420, #2a2420) 42% 70% / 3px 9px no-repeat, "
            f"linear-gradient(#8a6a60, #8a6a60) 80% 50% / 3px 12px no-repeat, {SKIN}")


def man():
    y = (-80, -52)
    chest = (f"linear-gradient(90deg, {SHIRT} 0 30%, transparent 30%) 0 50% / 100% 26% no-repeat, "
             f"linear-gradient({TIE}, {TIE}) 0 50% / 42% 7% no-repeat, {SUIT}")
    return "".join((box(-186, -134, -21, 21, -84, -52, SKIN, face(HAIR_M)), box(-132, -14, -34, 34, *y, SUIT, chest),
                    box(-124, -28, -46, -35, -74, -52, SUIT), box(-124, -28, 35, 46, -74, -52, SUIT),
                    box(-28, -8, -46, -35, -74, -52, SKIN), box(-28, -8, 35, 46, -74, -52, SKIN),
                    box(-14, 132, -30, -2, -74, -52, SUIT), box(-14, 132, 2, 30, -74, -52, SUIT),
                    box(132, 168, -29, -5, -84, -52, SHOE), box(132, 168, 5, 29, -84, -52, SHOE)))


def woman():
    return "".join((box(-192, -134, -30, 30, -74, -52, HAIR_F), box(-184, -134, -20, 20, -84, -52, SKIN, face(HAIR_F)),
                    box(-132, -30, -28, 28, -80, -52, DRESS), box(-30, 80, -33, 33, -76, -52, DRESS),
                    box(-122, -40, -38, -29, -72, -52, DRESS), box(-122, -40, 29, 38, -72, -52, DRESS),
                    box(-40, -22, -38, -29, -72, -52, SKIN), box(-40, -22, 29, 38, -72, -52, SKIN),
                    box(80, 134, -24, -6, -68, -52, SKIN), box(80, 134, 6, 24, -68, -52, SKIN),
                    box(134, 162, -24, -6, -78, -52, SHOE), box(134, 162, 6, 24, -78, -52, SHOE)))


CSS = """.corps { position: absolute; left: 0; top: 0; width: 0; height: 0; transform-style: preserve-3d;
  transform: translateY(calc(33px * var(--k))); visibility: hidden; transition: transform .7s cubic-bezier(.3, 1.1, .5, 1), visibility 0s .8s; }
.config:has(#ouvert:checked) .corps, .config:has(#k-oui:checked) .corps { visibility: visible; transition: transform .7s cubic-bezier(.3, 1.1, .5, 1), visibility 0s; }"""
ADD = "html => { const c = document.createElement('div'); c.className = 'corps'; c.innerHTML = html; document.querySelector('.plateau').appendChild(c); }"
TAKES = {"homme": (man, ["m-pin", "i-satin"], "Trois-quarts", True), "femme": (woman, ["m-pin", "i-satin"], "Trois-quarts", True),
         "homme-chene-brut": (man, ["m-chene", "i-brut"], "Face", True), "femme-kit": (woman, ["m-chene", "i-satin", "k-oui"], "Trois-quarts", False)}


def shoot(page, name, out):
    page.mouse.move(0, 0)
    page.evaluate(cc.FREEZE, 6000)
    page.wait_for_timeout(cc.SETTLE)
    path = out / f"take-{name}.png"
    page.locator(".scene").screenshot(path=path)
    return Image.open(path).convert("RGB")


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome")
        for name, (who, combo, view, lid) in TAKES.items():
            context, page = cc.opened(browser, [], 1280)
            page.add_style_tag(content=CSS)
            page.evaluate(ADD, who())
            cc.choose(page, *combo)
            page.locator(".vues label", has_text=view).click()
            if lid:
                page.locator("label.ouvrir").click()
            shoot(page, name, out)
            context.close()
        # Shut, with or without a body: not one pixel may differ.
        pictures = []
        for who in (man, None):
            context, page = cc.opened(browser, [], 1280)
            page.add_style_tag(content=CSS)
            if who:
                page.evaluate(ADD, who())
            pictures.append(shoot(page, "ferme", out))
            context.close()
        browser.close()
    print("closed, the body shows:", ImageChops.difference(*pictures).getbbox())
    (out / "take-ferme.png").unlink()
    return 0


if __name__ == "__main__":
    sys.exit(main())
