#!/usr/bin/env python3
"""The Inviolia pictures, painted by the local ComfyUI, shipped as lighter .webp.

    python3 tools/inviolia_images.py make [name[:seed] ...]   # paint into RAW
    python3 tools/inviolia_images.py ship                     # RAW to inviolia/img, needs no ComfyUI

pirate and globe are the pictures Simon saw on r70: ship takes them from ~/.cache/new-site-takes,
where tools/new_site_images.py paints them. Reuses generate() from tools/gobelin_images.py, so one
image at a time under the GPU flock, and only with memory free. ComfyUI is started and stopped by
whoever runs this: nice -n 15 venv/bin/python main.py in ~/ComfyUI. A take with another seed lands
as name-seed.png; KEPT says which take ships. No lettering comes from the model: the words are HTML.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gobelin_images import generate  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = pathlib.Path.home() / ".cache" / "inviolia-images"
TAKES = pathlib.Path.home() / ".cache" / "new-site-takes"
IMG = ROOT / "inviolia" / "img"
STOCK = "corporate stock photograph, sharp focus, professional lighting"
HEAD = ("corporate headshot portrait photograph, head and shoulders, looking at the camera, plain very dark "
        "navy background, cool blue rim light, sharp focus, realistic skin")
PICTURES = {
    "soc": (41, 1216, 832, "security operations center, dark room, analysts seen from behind at desks, huge wall "
            f"of blue screens with world maps and graphs, red alerts glowing, {STOCK}"),
    "accueil": (42, 1216, 832, "empty modern glass office reception desk, a row of blue lanyards with blank white "
                f"access cards hanging from hooks on the desk, nobody present, cool light, {STOCK}"),
    "serveurs": (43, 1216, 832, "data center corridor between server racks, blue light, blinking leds, symmetrical "
                 f"perspective, {STOCK}"),
    "poignee": (44, 1216, 832, "two businessmen in dark suits shaking hands in front of a window, faces out of "
                f"frame, close on the hands, blue tint, {STOCK}"),
    "cadenas": (45, 1216, 832, "glowing blue digital padlock floating over a dark circuit board, cybersecurity "
                "concept, 3d render, high tech"),
    "scene": (46, 1216, 832, "man in a dark suit seen from behind on a conference stage, arms open, facing a dark "
              f"audience, giant red glowing screen behind him, no words on the screen, {STOCK}"),
    "immeuble": (47, 1216, 832, "low modern office building of dark glass in a business park at dusk, small car "
                 f"park, blue lit lobby, {STOCK}"),
    "jean-marc": (51, 832, 832, f"man of 58, silver hair, navy suit, no tie, arms crossed, stern, {HEAD}"),
    "sylvie": (52, 832, 832, f"woman of 55, short grey hair, glasses, dark blazer, tight smile, {HEAD}"),
    "marc-antoine": (53, 832, 832, f"man of 45, tanned, very white smile, slim blue suit, pocket square, {HEAD}"),
    "clemence": (54, 832, 832, f"woman of 34, dark hair in a bun, black turtleneck, confident smile, {HEAD}"),
    "steven": (55, 832, 832, f"tired man of 29, short beard, black hoodie, slight smile, {HEAD}"),
    "ines": (56, 832, 832, f"young woman of 22, curly hair, grey hoodie, big smile, {HEAD}"),
    "thibault": (57, 832, 832, f"man of 38, round glasses, checked shirt, fleece vest, {HEAD}"),
    "anais": (58, 832, 832, f"young woman of 26, long auburn hair, white blouse, radiant smile, {HEAD}"),
}
# Shipped width and webp quality.
SHIP = {"pirate": (1216, 72), "globe": (800, 70), "soc": (1216, 68), "accueil": (960, 70), "serveurs": (1216, 66),
        "poignee": (960, 70), "cadenas": (1216, 66), "scene": (1216, 68), "immeuble": (960, 70),
        "jean-marc": (320, 74), "sylvie": (320, 74), "marc-antoine": (320, 74), "clemence": (320, 74),
        "steven": (320, 74), "ines": (320, 74), "thibault": (320, 74), "anais": (320, 74)}
KEPT = {}     # name: seed, when the take that won is not the first


def make(names):
    for name in names or PICTURES:
        name, _, other = name.partition(":")
        seed, width, height, subject = PICTURES[name]
        generate(f"{name}-{other}" if other else name, subject, int(other or seed), width, height, RAW)


def ship():
    from PIL import Image
    IMG.mkdir(parents=True, exist_ok=True)
    for name, (width, quality) in SHIP.items():
        if name in ("pirate", "globe"):
            source = TAKES / f"{name}.png"
        else:
            source = RAW / (f"{name}-{KEPT[name]}.png" if name in KEPT else f"{name}.png")
        picture = Image.open(source).convert("RGB")
        height = round(picture.height * width / picture.width)
        target = IMG / f"{name}.webp"
        picture.resize((width, height), Image.LANCZOS).save(target, quality=quality, method=6)
        print(f"{target.name}: {width}x{height}, {target.stat().st_size // 1024} KB")


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    if action == "make":
        make(sys.argv[2:])
    elif action == "ship":
        ship()
    else:
        sys.exit(__doc__)
