#!/usr/bin/env python3
"""The Au Dernier Prix pictures, painted by the local ComfyUI, then shipped as lighter .webp.

    python3 tools/dernier_prix_images.py make [name[:seed] ...]   # into ~/.cache/dernier-prix-images
    python3 tools/dernier_prix_images.py ship                     # into dernier-prix/img, no ComfyUI

generate() is tools/gobelin_images.py's: one image at a time, under the GPU flock, only with memory
free. ComfyUI is started and stopped by whoever runs this: nice -n 15 venv/bin/python main.py in
~/ComfyUI, and another session may be using the same one, so look before stopping it. The coffin, wreath and urn are
the ones Simon chose on r70, painted by tools/new_site_images.py into ~/.cache/new-site-takes.
No lettering comes from the model; what must be read is HTML, or pasted on by ship.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gobelin_images import generate  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = pathlib.Path.home() / ".cache" / "dernier-prix-images"
TAKES = pathlib.Path.home() / ".cache" / "new-site-takes"
IMG = ROOT / "dernier-prix" / "img"
PACK = "catalogue product photograph, isolated on a pure white background, e-commerce packshot"
PHOTO = "amateur corporate photograph, natural colours, sharp focus, fluorescent light"
HEAD = ("corporate staff headshot photograph of a french {who}, plain yellow polo shirt, in front of a "
        "blurred discount store aisle, looking at the camera, natural skin, sharp focus, {mood}")
# name: seed, width, height, subject.
PICTURES = {
    "chene": (41, 1216, 832, "catalogue product photograph of a dark polished oak coffin with brass handles, "
              f"three quarter view, {PACK}"),
    "peuplier": (42, 1216, 832, "catalogue product photograph of a very plain white painted coffin without any "
                 f"decoration, three quarter view, {PACK}"),
    "plaque": (43, 1024, 1024, "catalogue product photograph of a blank polished grey granite memorial plaque "
               f"with a small brass vase, no inscription, {PACK}"),
    "bouquet": (44, 1024, 1024, f"catalogue product photograph of a modest bunch of white chrysanthemums in a plastic pot, {PACK}"),
    "bambou": (45, 1024, 1024, f"catalogue product photograph of a plain bamboo funeral urn with a lid, {PACK}"),
    "rayon": (146, 1216, 832, "discount warehouse store aisle, on both sides tall metal pallet racking, on every shelf "
              "light pine wood funeral coffins lying side by side, clearly coffins with handles and tapered lids, polished "
              f"concrete floor, fluorescent tube lights, {PHOTO}"),
    "facade": (47, 1216, 832, "exterior of a low cheap big box discount store in a french retail park, blank bright "
               "yellow and red metal cladding facade, automatic glass doors, empty car park with white lines, grey "
               f"overcast sky, wide shot, {PHOTO}"),
    "camion": (48, 1216, 832, "bright yellow delivery van with blank sides parked in a small french village street "
               f"in front of an old stone church, overcast day, {PHOTO}"),
    "palettes": (249, 1216, 832, "a yellow forklift lifting one single light pine wood funeral coffin with metal handles, "
                 f"the coffin lying on a wooden pallet, warehouse loading bay, {PHOTO}"),
    "caisse": (250, 1216, 832, "close-up of a supermarket checkout counter, black rubber conveyor belt, lying flat on the "
               f"belt a round funeral wreath of white flowers, a card payment terminal beside it, nobody, {PHOTO}"),
    "didier": (51, 1024, 1024, HEAD.format(who="man of fifty-eight, greying hair, wearing a navy blazer over the polo",
                                           mood="huge confident salesman smile")),
    "nathalie": (52, 1024, 1024, HEAD.format(who="woman accountant of fifty, short brown hair, reading glasses",
                                             mood="tired polite smile")),
    "jordan": (53, 1024, 1024, HEAD.format(who="young man of twenty-four, gelled hair, thin beard",
                                           mood="bright winner smile")),
    "oceane": (54, 1024, 1024, HEAD.format(who="woman of twenty-two, long blond hair, name badge",
                                           mood="warm radiant smile")),
    "gaetan": (55, 1024, 1024, HEAD.format(who="man of thirty-one, trendy round glasses, lanyard",
                                           mood="smug little smile")),
    "bernadette": (56, 1024, 1024, "corporate staff headshot photograph of a french woman of sixty-two, grey chignon, "
                   "severe black suit, white shirt, in front of a blurred discount store aisle, looking at the camera, "
                   "natural skin, sharp focus, solemn, unsmiling"),
    "loic": (57, 1024, 1024, HEAD.format(who="man of forty-five, stocky delivery driver, shaved head",
                                         mood="cheerful")),
}
# The name, the width it ships at, its webp quality. Portraits are shown small.
SHIP = {"cercueil": (1216, 80), "urne": (560, 78), "gerbe": (560, 78), "chene": (640, 78), "peuplier": (640, 78),
        "plaque": (480, 78), "bouquet": (480, 78), "bambou": (480, 78), "rayon": (1400, 74), "facade": (1100, 76),
        "camion": (900, 76), "palettes": (900, 76), "caisse": (900, 76)}
SHIP |= {name: (256, 80) for name in ("didier", "nathalie", "jordan", "oceane", "gaetan", "bernadette", "loic")}
# A lighter copy for the cards of the home page, named name-width.webp.
SMALLER = {"cercueil": (560, 78)}


PORTRAITS = ("didier", "nathalie", "jordan", "oceane", "gaetan", "bernadette", "loic")
BOLD = "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Bold.ttf"


def source(name):
    seed = PICTURES[name][0] if name in PICTURES else 0     # the take that won, when it was a take
    return next(path for path in (RAW / f"{name}-{seed}.png", RAW / f"{name}.png", TAKES / f"{name}.png")
                if path.exists())


def sign(picture):
    """Mirror the shop, so the page's words sit on the empty side, then letter its red cladding
    along the painted perspective, column by column: the model's lettering is always false."""
    from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
    mirrored = ImageOps.mirror(picture)
    font = ImageFont.truetype(BOLD, 150)
    text = "AU DERNIER PRIX"
    width = round(ImageDraw.Draw(mirrored).textlength(text, font=font))
    lettering = Image.new("L", (width, 170), 0)
    ImageDraw.Draw(lettering).text((0, 5), text, font=font, fill=255)
    mask = Image.new("L", mirrored.size, 0)
    left, right = 530, 980       # the cladding's run, in the mirrored 1216x832 picture
    for x in range(left, right):
        run = (1106 - x) / 595   # 0 at the far end of the shop, 1 at the near corner
        top = 382 - 80 * run + 8
        bottom = 418 - 43 * run - 8
        column = lettering.crop((int((x - left) / (right - left) * width), 0,
                                 int((x - left) / (right - left) * width) + 1, 170))
        column = column.resize((1, max(1, round(bottom - top))), Image.BICUBIC)
        mask.paste(column, (x, round(top)))
    mirrored.paste((255, 212, 0), (0, 0), mask.filter(ImageFilter.GaussianBlur(0.7)))
    return mirrored


def ship():
    from PIL import Image
    IMG.mkdir(parents=True, exist_ok=True)
    for name, (width, quality) in SHIP.items():
        picture = Image.open(source(name)).convert("RGB")
        if name in PORTRAITS:       # the head and shoulders: the model writes false logos on the polo
            side = round(picture.width * 0.72)
            left = (picture.width - side) // 2
            picture = picture.crop((left, 0, left + side, side))
        if name == "facade":
            picture = sign(picture)
        out = [(IMG / f"{name}.webp", width, quality)]
        if name in SMALLER:
            small, small_quality = SMALLER[name]
            out.append((IMG / f"{name}-{small}.webp", small, small_quality))
        for target, size, q in out:
            height = round(picture.height * size / picture.width)
            picture.resize((size, height), Image.LANCZOS).save(target, quality=q, method=6)
            print(f"{target.name}: {size}x{height}, {target.stat().st_size // 1024} KB")


def make(names):
    for name in names or PICTURES:
        name, _, other = name.partition(":")
        seed, width, height, subject = PICTURES[name]
        generate(f"{name}-{other}" if other else name, subject, int(other or seed), width, height, RAW)


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    if action == "make":
        make(sys.argv[2:])
    elif action == "ship":
        ship()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
