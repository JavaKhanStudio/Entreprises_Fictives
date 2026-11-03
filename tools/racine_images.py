#!/usr/bin/env python3
"""The one picture the root list needs that no site had: Merlin's, whose hero is a live 3D clip.

    python3 tools/racine_images.py make [seed]   # paint into RAW with the local ComfyUI
    python3 tools/racine_images.py ship          # RAW to merlin/img/vignette.webp, as .webp

The other five cards of index.html show pictures their own site ships, so a repaint follows.
ComfyUI is started and stopped by whoever runs this: nice -n 15 venv/bin/python main.py in
~/ComfyUI. generate() comes from tools/gobelin_images.py: one image at a time, under the GPU flock.
"""
import pathlib
import sys

from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gobelin_images import generate  # noqa: E402

RAW = pathlib.Path.home() / ".cache" / "racine-images"
SHIPPED = pathlib.Path(__file__).resolve().parent.parent / "merlin" / "img" / "vignette.webp"
SEED = 73
SUBJECT = ("one giant polished chrome paperclip standing upright on a glossy dark stage like a "
           "product launch keynote, dramatic violet and coral rim lights, haze, very dark indigo "
           "background, 3d render, luxury tech advertising")


def main(args):
    if args[:1] == ["make"]:
        seed = int(args[1]) if len(args) > 1 else SEED
        RAW.mkdir(parents=True, exist_ok=True)
        generate(f"vignette-{seed}", SUBJECT, seed, 1216, 832, RAW)
    elif args[:1] == ["ship"]:
        picture = Image.open(RAW / f"vignette-{SEED}.png").convert("RGB")
        picture.thumbnail((800, 800))
        picture.save(SHIPPED, "WEBP", quality=80, method=6)
        print(SHIPPED, SHIPPED.stat().st_size)
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
