#!/usr/bin/env bash
# r115: run the ship step of each image tool that shares the writing block, from the cached raw
# pictures in ~/.cache, and print sha256 of every picture it writes. Run before and after a change
# to the tools and diff the two lists: the same hashes mean byte-identical pictures.
#     bash tools/r115/ship_hashes.sh > before.txt
set -euo pipefail
cd "$(dirname "$0")/../.."
export PYTHONDONTWRITEBYTECODE=1
for tool in gobelin dernier_prix inviolia source_eclat; do
    python3 "tools/${tool}_images.py" ship > /dev/null
done
sha256sum gobelin/img/*.webp dernier-prix/img/*.webp inviolia/img/*.webp source-eclat/img/*.webp
