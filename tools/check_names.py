#!/usr/bin/env python3
"""Is an invented name already someone's? Search it, and prove each search can answer.

    python3 tools/check_names.py "Prénom Nom" "Nom de produit" ...

Three sources for the exact string. French and English Wikipedia and Wikidata give the verdict
on "is this notable": their APIs answer a script. The open web (Brave) refuses scripts when it
likes (429), so it is reported on its own line, as "web: refused" when so, and that is NOT a
pass: say which names went unchecked on the web.

A known name and a nonsense one go first through each source: a source where the known one
scores nothing or the nonsense one scores something is not answering, and is not used. Bing and
DuckDuckGo failed this control on 2026-11-02 (a score of zero for Thomas Pesquet), so they are
not here. Exit 1 when a name has a hit, to read by eye; 2 when the APIs fail their control.
Python stdlib. Needs the network. A student never runs this.
"""

import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BROWSER = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0",
           "Accept-Language": "fr,en;q=0.8"}
API = {"User-Agent": "EntreprisesFictives-check_names/1.0 (educational, fictional sites)"}
KNOWN = "Thomas Pesquet"
NONSENSE = "Zorglaxe Vrumpfeldt"
PAUSE = 6
WEB_PAUSE = 20  # Brave answers 429 to anything quicker


def fetch(url, headers):
    """The page. Waits as long as a refusal asks, and gives up after three."""
    request = urllib.request.Request(url, headers=headers)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=20) as answer:
                return answer.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == 3:
                raise
            wait = error.headers.get("Retry-After", "")
            time.sleep(int(wait) if wait.isdigit() else 30 * (attempt + 1))
    raise AssertionError("unreachable")


def api(url, key):
    """The API's JSON. A rate limit may also come as an error inside a 200: wait, then ask again."""
    for wait in (60, 120, 240):
        answer = json.loads(fetch(url, API))
        if key in answer:
            return answer
        time.sleep(wait)
    raise RuntimeError(f"no {key} from {url}: {answer}")


def wikipedia_hits(name):
    found = []
    for lang in ("fr", "en"):
        query = urllib.parse.urlencode({"action": "query", "list": "search", "format": "json",
                                        "srlimit": 5, "srsearch": f'"{name}"'})
        answer = api(f"https://{lang}.wikipedia.org/w/api.php?{query}", "query")
        for item in answer["query"]["search"]:
            snippet = html.unescape(re.sub(r"<[^>]+>", "", item["snippet"]))
            found.append(f"{lang}.wikipedia {item['title']}: {snippet[:90]}")
    return found


def wikidata_hits(name):
    query = urllib.parse.urlencode({"action": "wbsearchentities", "search": name, "language": "fr",
                                    "uselang": "fr", "format": "json", "limit": 5})
    answer = api(f"https://www.wikidata.org/w/api.php?{query}", "search")
    return [f"wikidata {item.get('label')}: {item.get('description', '')}"
            for item in answer["search"] if item.get("label", "").lower() == name.lower()]


def web_mentions(name):
    """Bits of visible Brave result text holding the exact name, the page's own echo included."""
    query = urllib.parse.quote(f'"{name}"')
    page = fetch(f"https://search.brave.com/search?q={query}", BROWSER)
    body = page[page.find("<body"):]
    body = re.sub(r"<(script|style|svg|input|form)\b.*?</\1>", " ", body, flags=re.S | re.I)
    text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", body)))
    return [text[max(0, hit.start() - 50):hit.end() + 60]
            for hit in re.finditer(re.escape(name), text, re.I)]


def web_control():
    """How many mentions the page's echo alone makes; None when the web is not answering."""
    try:
        known = web_mentions(KNOWN)
        time.sleep(WEB_PAUSE)
        echo = len(web_mentions(NONSENSE))
    except urllib.error.URLError as error:
        print(f"web: refused at the control ({error})")
        return None
    if len(known) <= echo:
        print(f"web: not answering ({KNOWN} {len(known)} mentions, {NONSENSE} {echo})")
        return None
    print(f"web control: {KNOWN} {len(known)} mentions, {NONSENSE} {echo} (the echo)")
    return echo


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    if (not wikipedia_hits(KNOWN) or not wikidata_hits(KNOWN)
            or wikipedia_hits(NONSENSE) or wikidata_hits(NONSENSE)):
        print("Wikipedia or Wikidata failed the control, stopping")
        return 2
    echo = web_control()
    taken = 0
    for name in sys.argv[1:]:
        time.sleep(PAUSE)
        hits = wikipedia_hits(name) + wikidata_hits(name)
        web = "web: skipped, control failed"
        if echo is not None:
            time.sleep(WEB_PAUSE)
            try:
                extra = web_mentions(name)[echo:]
                hits += [f"web ...{bit}..." for bit in extra[:3]]
                web = f"web: {len(extra)} mentions"
            except urllib.error.URLError as error:
                web = f"web: refused ({error})"
        print(f"{name}: {len(hits)} hits, {web}", flush=True)
        for line in hits[:6]:
            print(f"    {line}", flush=True)
        taken += bool(hits)
    return 1 if taken else 0


if __name__ == "__main__":
    sys.exit(main())
