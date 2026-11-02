#!/usr/bin/env python3
"""The old photograph on Étude Courtepaille's home page (r68), and what ages it.

    python3 tools/courtepaille_images.py make [seed ...]    # paint, into RAW, under the GPU flock
    python3 tools/courtepaille_images.py sheet OUT [seed ...]  # each seed in each ageing, one picture
    python3 tools/courtepaille_images.py ship SEED AGE      # RAW/SEED.png aged, to courtepaille/img

Paints through tools/gobelin_images.py, so the same care for the shared machine, and ComfyUI is
started and stopped by whoever runs this. Raw PNGs stay in RAW. The ageing is in this file, with
fixed random seeds: the same painting gives the same shipped bytes.

The model never carries text, and this picture has no person in it: nobody in it can be real.
"""
import pathlib
import random
import sys

import numpy
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import gobelin_images as painter  # noqa: E402

RAW = pathlib.Path.home() / ".cache" / "courtepaille-images"
SHIPPED = painter.ROOT / "courtepaille" / "img" / "facade-photo.jpg"
SIZE = (400, 230)   # what courtepaille/index.html reserves, the size of the picture it replaces
PAINT = (1216, 704)

SUBJECT = ("old photograph of a modest provincial french notary office, a two storey stone town house "
           "on a quiet village square, slate roof, single old wooden door in the middle, tall shuttered windows, "
           "red geraniums in a terracotta pot just to the right of the door, two lime trees, cobblestones, overcast day, "
           "nobody in the street, straight on from across the square, amateur snapshot")
NEGATIVE = ("text, letters, words, sign, signage, plaque, writing, watermark, signature, logo, caption, "
            "people, person, man, woman, car, painting, illustration, drawing, 3d render, cgi, "
            "dramatic lighting, hdr, sharp, professional photography, nsfw")


def noise(shape, rng, blur):
    """Soft noise from 0 to 1, grown from a small field so that it comes in blotches."""
    small = (max(2, shape[0] // blur), max(2, shape[1] // blur))
    field = Image.fromarray((rng.random((small[1], small[0])) * 255).astype("uint8"))
    return numpy.asarray(field.resize(shape, Image.BICUBIC), dtype=float) / 255


def vignette(shape, strength):
    """1 in the middle, falling to 1 - strength in the corners."""
    x = numpy.linspace(-1, 1, shape[0])
    y = numpy.linspace(-1, 1, shape[1])
    return 1 - strength * numpy.clip(x[None, :] ** 2 + y[:, None] ** 2, 0, 2) / 2


def dust(picture, seed, specks, hairs):
    """White specks and hairs: what a flatbed scanner adds to a print."""
    rng = random.Random(seed)
    layer = Image.new("L", picture.size, 0)
    draw = ImageDraw.Draw(layer)
    width, height = picture.size
    for _ in range(specks):
        x, y = rng.uniform(0, width), rng.uniform(0, height)
        radius = rng.choice((0.4, 0.5, 0.5, 0.8))
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=rng.randint(120, 230))
    for _ in range(hairs):
        x, y = rng.uniform(0, width), rng.uniform(0, height)
        points = [(x, y)]
        for _ in range(3):
            x += rng.uniform(-7, 7)
            y += rng.uniform(-4, 4)
            points.append((x, y))
        draw.line(points, fill=rng.randint(50, 90), width=1)
    return Image.composite(Image.new("RGB", picture.size, (246, 240, 224)), picture, layer)


def scanned(picture, angle, border):
    """A print laid a little crooked on the scanner, its white edge showing."""
    bordered = Image.new("RGB", (picture.width + 2 * border, picture.height + 2 * border), (236, 230, 214))
    bordered.paste(picture, (border, border))
    turned = bordered.rotate(angle, resample=Image.BICUBIC, fillcolor=(214, 208, 192))
    return turned.resize(picture.size, Image.BICUBIC)


def sepia(raw, seed):
    """A print from the founders' time, browned and spotted."""
    rng = numpy.random.default_rng(seed)
    small = raw.convert("L").filter(ImageFilter.GaussianBlur(3)).resize(SIZE, Image.BICUBIC)
    grey = numpy.asarray(small, dtype=float) / 255
    grey = 0.16 + 0.68 * grey                       # no true black, no true white
    grey = grey * vignette(SIZE, 0.5) * (0.86 + 0.26 * noise(SIZE, rng, 24))
    grey = numpy.clip(grey + rng.normal(0, 0.022, grey.shape), 0, 1)
    colour = numpy.stack((grey * 1.07, grey * 0.90, grey * 0.66), axis=2)
    picture = Image.fromarray((numpy.clip(colour, 0, 1) * 255).astype("uint8"))
    return scanned(dust(picture, seed, 30, 1), 0.7, 7)


def faded(raw, seed):
    """A colour print from an album: the cyan has gone, what is left is orange."""
    rng = numpy.random.default_rng(seed)
    small = raw.convert("RGB").filter(ImageFilter.GaussianBlur(2.2)).resize(SIZE, Image.BICUBIC)
    colour = numpy.asarray(small, dtype=float) / 255
    grey = colour.mean(axis=2, keepdims=True)
    colour = grey + (colour - grey) * 0.55          # washed out
    colour = 0.14 + 0.72 * colour                   # raised blacks
    colour = colour * numpy.array((1.10, 0.96, 0.72))
    colour = colour * vignette(SIZE, 0.28)[:, :, None]
    colour = numpy.clip(colour + rng.normal(0, 0.02, colour.shape), 0, 1)
    picture = Image.fromarray((colour * 255).astype("uint8"))
    return scanned(dust(picture, seed, 22, 1), -0.6, 6)


def photocopy(raw, seed):
    """A black and white photocopy of a print, scanned: dark, hard, and streaked by the drum."""
    rng = numpy.random.default_rng(seed)
    small = raw.convert("L").filter(ImageFilter.GaussianBlur(2.5)).resize(SIZE, Image.BICUBIC)
    grey = numpy.asarray(small, dtype=float) / 255
    grey = numpy.clip((grey - 0.5) * 1.7 + 0.46, 0, 1)
    streaks = 1 - 0.1 * noise((SIZE[0], 1), rng, 9).repeat(SIZE[1], axis=0)
    grey = numpy.clip(grey * streaks + rng.normal(0, 0.035, grey.shape), 0, 1)
    colour = numpy.stack((grey * 0.97, grey * 0.96, grey * 0.90), axis=2)
    picture = Image.fromarray((colour * 255).astype("uint8"))
    return scanned(dust(picture, seed, 18, 1), 0.5, 5)


AGES = {"sepia": sepia, "faded": faded, "photocopy": photocopy}


def make(seeds):
    painter.CHECKPOINT = "Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors"
    painter.NEGATIVE = NEGATIVE
    for seed in seeds:
        painter.generate(str(seed), SUBJECT, int(seed), *PAINT, RAW)


def sheet(out, seeds):
    """Rows of seeds, columns of ageings, at twice their size so that a reader sees the grain."""
    tile = (SIZE[0] * 2, SIZE[1] * 2)
    picture = Image.new("RGB", (tile[0] * len(AGES), tile[1] * len(seeds)), "white")
    for row, seed in enumerate(seeds):
        raw = Image.open(RAW / f"{seed}.png")
        for column, age in enumerate(AGES.values()):
            aged = age(raw, int(seed)).resize(tile, Image.NEAREST)
            picture.paste(aged, (column * tile[0], row * tile[1]))
    out = pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    picture.save(out / "sheet.png")
    print(out / "sheet.png")


def ship(seed, age):
    aged = AGES[age](Image.open(RAW / f"{seed}.png"), int(seed))
    aged.save(SHIPPED, quality=38, optimize=False, subsampling=2)  # a scanner's small JPEG
    print(SHIPPED, SHIPPED.stat().st_size, "bytes")


if __name__ == "__main__":
    verb, *rest = sys.argv[1:] or ["help"]
    if verb == "make" and rest:
        make(rest)
    elif verb == "sheet" and len(rest) >= 2:
        sheet(rest[0], rest[1:])
    elif verb == "ship" and len(rest) == 2:
        ship(*rest)
    else:
        sys.exit(__doc__)
