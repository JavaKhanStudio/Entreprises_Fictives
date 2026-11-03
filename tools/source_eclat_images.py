#!/usr/bin/env python3
"""The Source & Éclat pictures, painted by the local ComfyUI.

    python3 tools/source_eclat_images.py make [name[:seed] ...]   # into RAW
    python3 tools/source_eclat_images.py ship                     # RAW to source-eclat/img, as .webp

generate() is the one of tools/gobelin_images.py: one image at a time, under the GPU flock, only
with memory free. ComfyUI is started and stopped by whoever runs this, from ~/ComfyUI/venv/bin/python.
plage and eau are the two Simon chose on r70's mock-up: ship takes them from the cache of
tools/new_site_images.py when RAW has none. The portraits of Marie-Ange come from plage, so the
woman on the beach and the founder are one face. No lettering comes from the model.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gobelin_images import generate  # noqa: E402
from new_site_images import PICTURES as MOCKUP, RAW as MOCKUP_RAW  # noqa: E402

RAW = pathlib.Path.home() / ".cache" / "source-eclat-images"
IMG = pathlib.Path(__file__).resolve().parent.parent / "source-eclat" / "img"
STOCK = "lifestyle stock photograph, natural skin, sharp focus, warm golden light"
FACE = "head and shoulders portrait, looking at the camera, big smile"
PICTURES = {
    "source": (41, 1216, 832, "a small clear mountain spring running over mossy rocks into a turquoise pool, "
               "sunbeams through pines at sunrise, nature photograph, serene, wide shot, no people"),
    "arbre": (42, 1216, 832, "one huge solitary oak tree on a green hill at sunset, pink and gold sky, seen from "
              "far away, inspirational poster photograph, no people"),
    "convention": (43, 1216, 832, "huge corporate convention in a dark arena seen from the back of the crowd, "
                   "thousands of women raising their arms, pink and gold stage lights, gold confetti in the air, "
                   "one tiny woman in white on a distant stage, event photograph"),
    "villa": (44, 1216, 832, "a white modern seaside villa with a terrace and palm trees at golden hour, pink "
              "bougainvillea, pool, mediterranean, real estate photograph, no people"),
    "garage": (45, 1216, 832, "an ordinary suburban french garage completely full of stacked plain brown cardboard "
               "boxes up to the ceiling, an old family car squeezed outside, a narrow path between the boxes, neon "
               "light, amateur phone photograph, no people"),
    "cercle": (46, 1216, 832, "eight smiling women and two men in white linen sitting in a circle on a beach at "
               f"sunset, holding hands, eyes closed, seen from a distance, {STOCK}"),
    "scene": (247, 1216, 832, "a very wide shot of a huge arena stage seen from far away, one tiny distant woman in a buttoned "
              "white suit standing alone at the centre, arms wide open, pink and gold spotlights, gold confetti, the "
              "backs of the crowd's heads at the bottom, event photograph, fully clothed"),
    "salon": (48, 1216, 832, "five french women on sofas in an ordinary suburban living room, one standing and presenting "
              f"frosted glass water bottles on a coffee table, biscuits and coffee cups, the others listening, {STOCK}"),
    "christelle": (51, 1024, 1024, f"elegant blonde french woman of fifty five, white blazer, gold jewellery, "
                   f"perfect teeth, sunny terrace behind her, {FACE}, {STOCK}"),
    "regis": (52, 1024, 1024, f"tanned french man of sixty, grey hair, open white linen shirt, sunglasses pushed "
                f"up on his head, yacht harbour behind him, {FACE}, {STOCK}"),
    "jonathan": (53, 1024, 1024, "tired pale french man of thirty five, plain grey sweater, thin smile, sitting in a "
                 "small windowless office, head and shoulders portrait, looking at the camera, office neon light, "
                 "corporate photograph, natural skin, sharp focus"),
    "oceane": (54, 1024, 1024, f"young french woman of twenty four, long brown hair, white sundress, holding a phone, "
               f"pink flowers behind her, fully clothed, {FACE}, {STOCK}"),
    "berengere": (55, 1024, 1024, f"serious french woman of forty five, short dark hair, glasses, navy cardigan, thin "
                  "polite smile, a shelf of binders behind her, head and shoulders portrait, looking at the camera, "
                  "corporate photograph, natural skin, sharp focus"),
    "sandrine": (56, 1024, 1024, "selfie of a cheerful french woman of forty two with red hair, taken in the driver's "
                 "seat of a parked small car, seat belt on, phone held at arm's length, big smile, natural daylight, "
                 "amateur phone photograph, natural skin"),
    "didier": (57, 1024, 1024, "hopeful french man of fifty eight, balding, polo shirt, brave smile, in front of "
               "stacked brown cardboard boxes, head and shoulders portrait, looking at the camera, amateur phone "
               "photograph, flat light, natural skin"),
}
# name -> (width, quality), and the same picture smaller for a phone.
SHIP = {"plage": (1600, 76), "eau": (920, 78), "source": (1600, 74), "arbre": (1600, 74), "convention": (1600, 74),
        "villa": (1600, 74), "garage": (800, 72), "cercle": (1600, 74), "scene": (1600, 74), "salon": (1600, 74), "christelle": (320, 78), "regis": (320, 78),
        "jonathan": (320, 78), "oceane": (320, 78), "berengere": (320, 78), "sandrine": (320, 78), "didier": (320, 78)}
SMALLER = {"plage": (800, 72), "source": (800, 70), "arbre": (800, 70), "convention": (800, 70), "villa": (800, 70),
           "cercle": (800, 70), "scene": (800, 70), "salon": (800, 70)}
# Marie-Ange's portrait: her face and shoulders, out of plage (x0, y0, x1, y1 on the 1216 x 832 original).
FOUNDER = (440, 110, 760, 430)


def raw(name):
    kept = RAW / f"{name}.png"
    return kept if kept.exists() else MOCKUP_RAW / f"{name}.png"


def make(names):
    for name in names or PICTURES:
        name, _, other = name.partition(":")
        seed, width, height, subject = {**MOCKUP, **PICTURES}[name]
        generate(f"{name}-{other}" if other else name, subject, int(other or seed), width, height, RAW)


def ship():
    from PIL import Image
    IMG.mkdir(parents=True, exist_ok=True)
    for name, (width, quality) in SHIP.items():
        picture = Image.open(raw(name)).convert("RGB")
        out = [(IMG / f"{name}.webp", width, quality)]
        if name in SMALLER:
            small, small_quality = SMALLER[name]
            out.append((IMG / f"{name}-{small}.webp", small, small_quality))
        for target, size, q in out:
            height = round(picture.height * size / picture.width)
            picture.resize((size, height), Image.LANCZOS).save(target, quality=q, method=6)
            print(f"{target.name}: {size}x{height}, {target.stat().st_size // 1024} KB")
    face = Image.open(raw("plage")).convert("RGB").crop(FOUNDER).resize((320, 320), Image.LANCZOS)
    face.save(IMG / "marie-ange.webp", quality=78, method=6)


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    if action == "make":
        make(sys.argv[2:])
    elif action == "ship":
        ship()
    else:
        sys.exit(__doc__)
