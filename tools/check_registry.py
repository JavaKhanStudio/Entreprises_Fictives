#!/usr/bin/env python3
"""Is this invented name a French company or a French commune? tools/check_names.py asks the
encyclopedias and the web; this asks the two public registers.

    python3 tools/check_registry.py "Nom" ...

recherche-entreprises.api.gouv.fr and geo.api.gouv.fr, whole phrase, accents and case aside.
A control goes first: a known company and commune must score, or it stops (exit 2). Exit 1 when
a name has a hit, to read by eye. Python stdlib, needs the network. A student never runs this.
"""

import html
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request

UA = {"User-Agent": "EntreprisesFictives-check_registry/1.0 (educational, fictional sites)"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25) as answer:
        return json.loads(answer.read().decode("utf-8", "replace"))


def plain(text):
    text = unicodedata.normalize("NFKD", html.unescape(text)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def companies(name):
    url = ("https://recherche-entreprises.api.gouv.fr/search?per_page=25"
           f"&q={urllib.parse.quote(name)}")
    return [r["nom_complet"] for r in get(url)["results"] if plain(name) in plain(r["nom_complet"])]


def communes(name):
    url = f"https://geo.api.gouv.fr/communes?limit=5&nom={urllib.parse.quote(name)}"
    return [c["nom"] for c in get(url) if plain(c["nom"]) == plain(name)]


def main():
    if not companies("Papeterie de la Bièvre") or not communes("Nantes"):
        print("the registers failed the control, stopping")
        return 2
    taken = 0
    for name in sys.argv[1:]:
        hits = companies(name) + communes(name)
        print(f"{name}: {len(hits)} hits {' | '.join(hits[:4])}".rstrip(), flush=True)
        taken += bool(hits)
        time.sleep(0.5)
    return 1 if taken else 0


if __name__ == "__main__":
    sys.exit(main())
