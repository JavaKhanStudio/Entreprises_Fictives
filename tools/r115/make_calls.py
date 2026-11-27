#!/usr/bin/env python3
"""r115: what each image tool's make step would ask of generate(), without ComfyUI.

    python3 tools/r115/make_calls.py > calls.txt

Stubs gobelin_images.generate to print its arguments, then runs make (or new_site's main) of the
tools whose make loop was copied, with no names and with a name:seed take. Run before and after
a change and diff: the same lines mean the same pictures would be asked for.
"""
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import gobelin_images  # noqa: E402


def stub(*args):
    print(args[:2], args[2:])


gobelin_images.generate = stub
import dernier_prix_images  # noqa: E402
import inviolia_images  # noqa: E402
import new_site_images  # noqa: E402
import source_eclat_images  # noqa: E402

for module in (dernier_prix_images, inviolia_images, new_site_images, source_eclat_images):
    module.generate = stub
    run = getattr(module, "make", None) or module.main
    first = next(iter(module.PICTURES))
    print("#", module.__name__)
    run([])
    run([f"{first}:99"])
