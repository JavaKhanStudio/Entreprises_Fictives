#!/usr/bin/env python3
"""Write the dead body of Au Dernier Prix's 3D coffin, man and woman, into the page, between its markers.

    python3 tools/dernier_prix_corps.py      # rewrites the two bodies in dernier-prix/configurateur.html

Boxes of six planes, placed like the coffin's own (x along it, y down, z towards the viewer), showing from
their outside only. It lies high, near the walls' top, or the near wall hides it from this camera; in
kit it comes down onto the floor (dernier-prix/configurateur.css, .corps). Shut, it is hidden there, or
hairlines of it show at the planes' seams (598 px measured).
"""
import re
from pathlib import Path

PAGE = Path(__file__).resolve().parent.parent / "dernier-prix/configurateur.html"
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


def main():
    html = PAGE.read_text(encoding="utf-8")
    bodies = "".join(f'              <div class="corps {name}">{who()}</div>\n' for name, who in (("homme", man), ("femme", woman)))
    html, count = re.subn(r"( *<!-- corps -->\n).*?( *<!-- /corps -->\n)", lambda m: m[1] + bodies + m[2], html, flags=re.S)
    if count != 1:
        raise SystemExit("the page's corps markers are not there once")
    PAGE.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
