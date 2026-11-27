#!/usr/bin/env python3
"""r113's proof: each Safari tool's --extract gives the same output before and after the driver
moved to tools/safari_driver.py. No Safari log is kept anywhere, so this makes one per tool.

    python3 tools/r113/extract_same.py make LOGS        # the logs; racine and configurateur come
                                                         # from their tests' Chrome flow (needs Chrome)
    python3 tools/r113/extract_same.py run TREE LOGS OUT   # each tool of TREE --extract on its log(s)
    diff -r OUT_BEFORE OUT_AFTER                         # stdout, exit code and a sha of each file

Trombone's and Inviolia's logs are frames only; Gobelin's carries META states written here, so its
reads give numbers that mean nothing but must come out the same.
"""

import hashlib
import importlib
import io
import json
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parents[2]
BEGIN, END, META = "=====FRAME", "=====END", "=====META"


def jpeg(size, seed):
    picture = Image.new("RGB", size, (240, 236, 228))
    draw = ImageDraw.Draw(picture)
    for i in range(6):
        x, y = (seed * 97 + i * 151) % size[0], (seed * 53 + i * 89) % size[1]
        draw.rectangle((x, y, x + size[0] // 5, y + size[1] // 6), fill=((i * 70) % 256, 180 - i * 20, (seed * 40) % 256))
    out = io.BytesIO()
    picture.save(out, "JPEG", quality=80)
    return out.getvalue()


def frame(name, data, prefix=""):
    import base64
    text = base64.b64encode(data).decode()
    lines = [f"{prefix}{BEGIN} {name}"]
    lines += [prefix + text[i:i + 100] for i in range(0, len(text), 100)]
    lines.insert(3, "")              # a blank line inside a frame
    return lines + [f"{prefix}{END}"]


def badge_log():
    lines = ["Safari 26.6", "safaridriver --enable: 0 "]
    state = {"facing": 0.97, "hover": False, "clip": "padding-box", "animations": 6, "reduced": False, "wide": 0,
             "inner": [1280, 1000], "vitrine": [400, 200, 880, 760], "crunch": [450, 260, 830, 330],
             "medal": [560, 400, 720, 560]}
    for n, (width, label, facing) in enumerate([(1280, "front", 0.97), (1280, "edge", 0.01), (1280, "turned", -0.9),
                                                (1280, "back", -0.95), (390, "front", 0.97), (390, "back", -0.9)]):
        key = f"{width}-{label}"
        lines.append(f"{META} {key} {json.dumps(dict(state, facing=facing))}")
        lines += frame(key, jpeg((1400, 1094), n))
    lines += frame("screen-1280-front", jpeg((1000, 625), 9))
    return lines + ["ALL OK"]


def frames_log(names, prefix=""):
    lines = ["Safari 26.6"]
    for n, name in enumerate(names):
        lines += [f"{name} {{\"wide\": 0}}"] + frame(name, jpeg((700, 547), n), prefix)
    return lines + ["ALL OK"]


def caught(test_name, logs):
    """Run a test's main with its tool's extract wrapped: each log it reads is kept."""
    sys.path[:0] = [str(REPO / "tests"), str(REPO / "tools")]
    test = importlib.import_module(test_name)
    real = test.tool.extract

    def keep(log, out):
        shutil.copy(log, logs / f"{test_name.removeprefix('test_check_')}--{Path(out).name}.log")
        return real(log, out)

    test.tool.extract = keep
    print(test_name, "->", test.main())


def make(logs):
    logs.mkdir(parents=True, exist_ok=True)
    (logs / "trombone_safari--x.log").write_text("\n".join(frames_log(
        ["still", "page-1280", "buffer-1280-0", "file-0"], prefix="2026-11-27T06:00:00.0000000Z ")) + "\n")
    (logs / "inviolia_safari--x.log").write_text("\n".join(frames_log(["home-top", "home-end", "equipe-middle"])) + "\n")
    (logs / "badge_safari--x.log").write_text("\n".join(badge_log()) + "\n")
    # One test a process: both read the same reports, and the second would read the first's t-load.
    if len(sys.argv) > 3:
        caught(sys.argv[3], logs)
        return
    for test in ("test_check_racine_safari", "test_check_configurateur_safari"):
        subprocess.run([sys.executable, __file__, "make", str(logs), test], check=True)


def run(tree, logs, out):
    out.mkdir(parents=True, exist_ok=True)
    for log in sorted(logs.glob("*.log")):
        tool, case = log.stem.split("--", 1)
        name = f"{tool}-{case}"
        done = subprocess.run([sys.executable, str(tree / "tools" / f"check_{tool}.py"), "--extract", str(log.resolve()), name],
                              cwd=out, capture_output=True, text=True, check=False)
        files = sorted((out / name).iterdir()) if (out / name).exists() else []
        sums = [f"{hashlib.sha256(f.read_bytes()).hexdigest()[:16]}  {f.name}" for f in files]
        (out / f"{name}.txt").write_text(f"exit {done.returncode}\n{done.stdout}\n--- stderr\n{done.stderr}\n--- files\n"
                                         + "\n".join(sums) + "\n")
        shutil.rmtree(out / name, ignore_errors=True)
        print(name, "exit", done.returncode, len(files), "files")


if __name__ == "__main__":
    if sys.argv[1] == "make":
        make(Path(sys.argv[2]))
    else:
        run(Path(sys.argv[2]).resolve(), Path(sys.argv[3]), Path(sys.argv[4]).resolve())
