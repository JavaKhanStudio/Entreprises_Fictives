#!/usr/bin/env python3
"""The pictures of r70's second round of mock-ups, painted by the local ComfyUI.

    python3 tools/new_site_images.py [name[:seed] ...]

Writes PNGs in ~/.cache/new-site-takes, for tools/new_site_takes.py. Reuses generate() from
tools/gobelin_images.py, so one image at a time under the GPU flock, and only with memory free.
ComfyUI is started and stopped by whoever runs this: nice -n 15 venv/bin/python main.py in ~/ComfyUI.
No lettering comes from the model; the page's text is HTML.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gobelin_images import generate  # noqa: E402

RAW = pathlib.Path.home() / ".cache" / "new-site-takes"
STOCK = "corporate stock photograph, sharp focus, professional lighting"
PICTURES = {
    "pirate": (11, 1216, 832, "anonymous hacker in a black hood, face entirely in shadow, sitting at a laptop "
               f"in a dark room, blue glowing binary light, cybersecurity concept, {STOCK}"),
    "globe": (12, 1024, 1024, "glowing digital planet earth from space on a very dark navy background, dozens of "
              "bright red and cyan arcs between cities, cyber attack map, 3d render, high tech"),
    "plage": (21, 1216, 832, "radiant smiling woman of fifty in white linen, sitting cross-legged on a beach at "
              f"golden hour with a laptop on her knees, arms open with joy, lifestyle, warm, {STOCK}"),
    "eau": (22, 1024, 1024, "luxury product photograph, six slim frosted glass water bottles with rose gold caps, "
            "no label, on a pale pink marble table, pearls scattered, soft light, cosmetics advertising"),
    "cercueil": (32, 1216, 832, "catalogue product photograph of a plain light pine wood coffin with simple metal "
                 "handles, three quarter view, isolated on a pure white background, e-commerce packshot"),
    "gerbe": (33, 1024, 1024, "catalogue product photograph of a round funeral wreath of white and yellow flowers, "
              "isolated on a pure white background, e-commerce packshot"),
    "urne": (34, 1024, 1024, "catalogue product photograph of a brushed steel funeral urn with a lid, isolated on "
             "a pure white background, e-commerce packshot"),
}


def main(names):
    for name in names or PICTURES:
        name, _, other = name.partition(":")
        seed, width, height, subject = PICTURES[name]
        generate(f"{name}-{other}" if other else name, subject, int(other or seed), width, height, RAW)


if __name__ == "__main__":
    main(sys.argv[1:])
