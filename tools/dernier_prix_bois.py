#!/usr/bin/env python3
"""The three woods of Au Dernier Prix's 3D coffin, computed, so the same every run. No model, no network.

    python3 tools/dernier_prix_bois.py    # writes dernier-prix/img/bois-{pin,peuplier,chene}.webp

A tile wraps both ways: its noise is filtered in frequency, which is periodic. Planks run along x,
as on the coffins in dernier-prix/img/. The colours are read off those pictures: pale pine with
knots, poplar under white paint, dark red oak under varnish.
"""
import pathlib

import numpy as np
from PIL import Image

IMG = pathlib.Path(__file__).resolve().parent.parent / "dernier-prix" / "img"
W, H = 640, 320
PLANKS = 4
# name: seed, dark, light, grain strength, knots, groove depth, webp quality.
WOODS = {
    "pin": (7, (176, 120, 62), (240, 200, 140), 1.0, 7, 0.34, 72),
    "peuplier": (11, (226, 224, 218), (250, 249, 245), 0.25, 0, 0.13, 70),
    "chene": (23, (54, 20, 14), (122, 58, 36), 1.0, 0, 0.45, 72),
}


def noise(rng, fx, fy):
    """Periodic noise, smooth below fx cycles along x and fy cycles along y, from 0 to 1."""
    spectrum = np.fft.rfft2(rng.standard_normal((H, W)))
    x = np.fft.rfftfreq(W, 1 / W)[None, :] / fx
    y = np.fft.fftfreq(H, 1 / H)[:, None] / fy
    field = np.fft.irfft2(spectrum * np.exp(-(x * x + y * y)), s=(H, W))
    return (field - field.min()) / (field.max() - field.min())


def wood(seed, dark, light, strength, knots, groove):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    height = H / PLANKS
    plank = (yy // height).astype(int)
    # Each plank is its own board: the grain shifts, the tone changes a little.
    rows = yy + rng.uniform(-40, 40, PLANKS)[plank]
    tone = rng.uniform(-0.09, 0.09, PLANKS)[plank]
    warp = (noise(rng, 3, 7) - 0.5) * 42
    for _ in range(knots):
        kx, ky = rng.uniform(0, W), rng.uniform(0, H)
        size = rng.uniform(5, 11)
        dx = (xx - kx + W / 2) % W - W / 2
        dy = (yy - ky + H / 2) % H - H / 2
        warp += 24 * np.sign(dy) * np.exp(-(dx * dx / (size * 5) ** 2 + dy * dy / (size * 2.4) ** 2))
    rings = 0.5 + 0.5 * np.sin((rows + warp) * 2 * np.pi / 9.0)
    fine = noise(rng, 90, 110)
    grain = 0.56 + strength * (0.26 * (rings - 0.5) + 0.34 * (fine - 0.5)) + tone * strength
    for _ in range(knots):
        kx, ky = rng.uniform(0, W), rng.uniform(0, H)
        size = rng.uniform(3, 7)
        dx = (xx - kx + W / 2) % W - W / 2
        dy = (yy - ky + H / 2) % H - H / 2
        grain -= 0.75 * np.exp(-(dx * dx + 3 * dy * dy) / (2 * size * size))
    grain = np.clip(grain, 0, 1)[..., None]
    picture = np.array(dark) * (1 - grain) + np.array(light) * grain
    # The groove between two planks, a dark line and a lit edge under it.
    inside = yy % height
    shade = 1 - groove * np.exp(-((inside - 0.8) / 1.1) ** 2) + 0.35 * groove * np.exp(-((inside - 3) / 1.4) ** 2)
    return np.clip(picture * shade[..., None], 0, 255).astype("uint8")


def main():
    for name, (seed, dark, light, strength, knots, groove, quality) in WOODS.items():
        path = IMG / f"bois-{name}.webp"
        Image.fromarray(wood(seed, dark, light, strength, knots, groove)).save(path, quality=quality, method=6)
        print(path.relative_to(IMG.parent.parent), f"{path.stat().st_size / 1024:.1f}K")


if __name__ == "__main__":
    main()
