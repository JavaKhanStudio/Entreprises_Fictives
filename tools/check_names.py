#!/usr/bin/env python3
"""Is an invented name already someone's? Search it, and prove each search can answer.

    python3 tools/check_names.py [--no-web] [--domains] "Prénom Nom" "Nom de produit" ...

Three sources for the exact string. French and English Wikipedia and Wikidata give the verdict
on "is this notable": their APIs answer a script. The open web (Brave) refuses scripts when it
likes (429), so it is reported on its own line, as "web: refused" when so, and that is NOT a
pass: say which names went unchecked on the web.

A known name and a nonsense one go first through each source: a source where the known one
scores nothing or the nonsense one scores something is not answering, and is not used. On the web
the known name is a modest one, because fame hides a fuzzy engine: on 2026-11-02 Bing gave Thomas
Pesquet 15 mentions and Odile Decq 0, answering a script with pages on the first name Odile, its
quotes ignored. A zero from it means nothing, so it is not here, nor DuckDuckGo. Brave answered
this client 429 at 20 s and at 120 s between requests, so a slower pace does not cure it.
On 2026-11-02 DuckDuckGo's HTML page gave one curl real results, then 202 and its bot challenge on
every query, so it is out too. Getting past a challenge or a filter is not this tool's job.

So --no-web skips the web and says so, and PUBLIC holds what is open to scripts and can name a
real company, game, band or book: Steam, GLEIF, MusicBrainz, Open Library, GitHub. Each returned
name must hold the exact string, because some of them search loosely, and each source is run on a
known name and on nonsense first; one that fails is reported and counts as unchecked. --domains
adds RDAP for the name's .com and .fr, for companies and products, on the name's letters and digits
(Source & Éclat is sourceeclat and source-eclat): a registered domain is a hit to read by eye, a
domain RDAP will not answer on counts as unchecked, as does every domain when RDAP does not answer
its control, and a name with no domain to make is said so.
None of this is the open web: a small firm with a site and none of these still goes unseen, which
is why --no-web can never exit 0.
Exit 1 when a name has a hit, to read by eye; 2 when the APIs fail their control; 3 when no name
has a hit but one went unchecked on the web, which is not a pass.
Python stdlib. Needs the network. A student never runs this.
"""

import html
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

BROWSER = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0",
           "Accept-Language": "fr,en;q=0.8"}
API = {"User-Agent": "EntreprisesFictives-check_names/1.0 (educational, fictional sites)"}
KNOWN = "Thomas Pesquet"
WEB_KNOWN = "Odile Decq"
NONSENSE = "Zorglaxe Vrumpfeldt"
PAUSE = 6
WEB_PAUSE = 20


def fetch(url, headers):
    """The page. Waits as long as a refusal asks, and gives up after three."""
    request = urllib.request.Request(url, headers=headers)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=20) as answer:
                return answer.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as error:
            if error.code not in (429, 503) or attempt == 3:
                raise
            wait = error.headers.get("Retry-After", "")
            time.sleep(int(wait) if wait.isdigit() else 30 * (attempt + 1))
        except (urllib.error.URLError, ConnectionError) as error:
            # A reset connection: HTTPError, a real answer, came first. urlopen lets a connection
            # dropped before the answer through bare (RemoteDisconnected), and callers read URLError.
            if attempt == 3:
                raise urllib.error.URLError(error) from error
            time.sleep(10 * (attempt + 1))
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


LIGATURES = str.maketrans({"œ": "oe", "Œ": "OE", "æ": "ae", "Æ": "AE"})  # NFKD does not split them


def flat(text):
    """Lower case, no accents, single spaces: how two spellings of a name are compared."""
    text = unicodedata.normalize("NFKD", text.translate(LIGATURES)).encode("ascii", "ignore").decode()
    return " ".join(text.casefold().split())


def holding(name, labels):
    """The labels with the exact name in them as whole words, not merely near it."""
    wanted = re.compile(rf"(?<!\w){re.escape(flat(name))}(?!\w)")
    return [label for label in labels if label and wanted.search(flat(label))]


def steam(name):
    query = urllib.parse.urlencode({"term": name, "l": "french", "cc": "FR"})
    answer = api(f"https://store.steampowered.com/api/storesearch/?{query}", "items")
    return [item["name"] for item in answer["items"]]


def gleif(name):
    query = urllib.parse.urlencode({"filter[fulltext]": name, "page[size]": 20})
    answer = api(f"https://api.gleif.org/api/v1/lei-records?{query}", "data")
    return [item["attributes"]["entity"]["legalName"]["name"] for item in answer["data"]]


def musicbrainz(kind, key, label, name):
    time.sleep(2)  # MusicBrainz answers 503 above one request a second
    query = urllib.parse.urlencode({"query": f'"{name}"', "limit": 25, "fmt": "json"})
    answer = api(f"https://musicbrainz.org/ws/2/{kind}?{query}", key)
    return [item[label] for item in answer[key]]


def open_library(name):
    query = urllib.parse.urlencode({"q": f'"{name}"', "limit": 25, "fields": "title,author_name"})
    answer = api(f"https://openlibrary.org/search.json?{query}", "docs")
    return [text for doc in answer["docs"] for text in [doc.get("title"), *doc.get("author_name", [])]]


def github(name):
    query = urllib.parse.urlencode({"q": f'"{name}"', "per_page": 30})
    answer = api(f"https://api.github.com/search/repositories?{query}", "items")
    return [f"{item['name'].replace('-', ' ')}: {item['description']}" for item in answer["items"]]


PUBLIC = {"steam": ("Dead Cells", steam),
          "gleif": ("Ubisoft", gleif),
          "musicbrainz artist": ("Daft Punk", lambda n: musicbrainz("artist", "artists", "name", n)),
          "musicbrainz album": ("Random Access Memories",
                                lambda n: musicbrainz("release-group", "release-groups", "title", n)),
          "open library": ("Odile Decq", open_library),
          "github": ("Dead Cells", github)}


def public_control():
    """The sources that find their known name and not the nonsense."""
    usable = {}
    for source, (known, search) in PUBLIC.items():
        try:
            good, bad = holding(known, search(known)), holding(NONSENSE, search(NONSENSE))
        except (OSError, RuntimeError, KeyError, ValueError) as error:
            print(f"{source}: failed at the control ({error})")
            continue
        time.sleep(PAUSE)
        if good and not bad:
            print(f"{source} control: {known} {len(good)}, {NONSENSE} 0")
            usable[source] = search
        else:
            print(f"{source}: not answering ({known} {len(good)}, {NONSENSE} {len(bad)})")
    return usable


def registered(domain):
    """Whether RDAP knows the domain. Only 200 and 404 are answers."""
    tld = domain.rsplit(".", 1)[1]
    base = {"com": "https://rdap.verisign.com/com/v1", "fr": "https://rdap.nic.fr"}[tld]
    try:
        fetch(f"{base}/domain/{domain}", API)
        return True
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return False
        raise


def domains_of(name):
    """The name's letters and digits as domains. Empty when no label of 1 to 63 of them can be made."""
    words = re.findall(r"[a-z0-9]+", flat(name))
    return [f"{joined}.{tld}" for joined in dict.fromkeys(("".join(words), "-".join(words)))
            if 0 < len(joined) <= 63 for tld in ("com", "fr")]


def domain_hits(name):
    """The name's registered domains, and those RDAP gave no answer on: one must not stop the run."""
    hits, missed = [], []
    for domain in domains_of(name):
        try:
            if registered(domain):
                hits.append(f"rdap {domain} is registered")
        except OSError:
            missed.append(f"rdap {domain}")
    return hits, missed


def domain_control():
    return (registered("ubisoft.com") and registered("ubisoft.fr")
            and not registered("zorglaxevrumpfeldt.com") and not registered("zorglaxevrumpfeldt.fr"))


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
        known = web_mentions(WEB_KNOWN)
        time.sleep(WEB_PAUSE)
        echo = len(web_mentions(NONSENSE))
    except urllib.error.URLError as error:
        print(f"web: refused at the control ({error})")
        return None
    if len(known) <= echo:
        print(f"web: not answering ({WEB_KNOWN} {len(known)} mentions, {NONSENSE} {echo})")
        return None
    print(f"web control: {WEB_KNOWN} {len(known)} mentions, {NONSENSE} {echo} (the echo)")
    return echo


def main():
    names = [arg for arg in sys.argv[1:] if arg not in ("--no-web", "--domains")]
    no_web, domains = "--no-web" in sys.argv, "--domains" in sys.argv
    if not names:
        print(__doc__)
        return 2
    if (not wikipedia_hits(KNOWN) or not wikidata_hits(KNOWN)
            or wikipedia_hits(NONSENSE) or wikidata_hits(NONSENSE)):
        print("Wikipedia or Wikidata failed the control, stopping")
        return 2
    echo = None if no_web else web_control()
    usable = public_control()
    rdap_down = False
    try:
        if domains and not domain_control():
            print("RDAP failed the control, stopping")
            return 2
    except OSError as error:
        print(f"rdap: failed at the control ({error})")
        rdap_down = True
    taken = unchecked = 0
    for name in names:
        time.sleep(PAUSE)
        hits = wikipedia_hits(name) + wikidata_hits(name)
        missed = [source for source in PUBLIC if source not in usable]
        for source, search in usable.items():
            try:
                hits += [f"{source} {label[:100]}" for label in holding(name, search(name))]
            except (OSError, RuntimeError, KeyError, ValueError):
                missed.append(source)
        if rdap_down:
            missed += ["rdap"] if domains_of(name) else []
        elif domains:
            found, unanswered = domain_hits(name)
            hits += found
            missed += unanswered
        web = "web: skipped by --no-web" if no_web else "web: skipped, control failed"
        if echo is not None:
            time.sleep(WEB_PAUSE)
            try:
                extra = web_mentions(name)[echo:]
                hits += [f"web ...{bit}..." for bit in extra[:3]]
                web = f"web: {len(extra)} mentions"
            except urllib.error.URLError as error:
                web = f"web: refused ({error})"
        unchecked += not web.endswith("mentions") or bool(missed)
        web += f", unchecked on {', '.join(missed)}" if missed else ""
        web += ", cannot be a domain" if domains and not domains_of(name) else ""
        print(f"{name}: {len(hits)} hits, {web}", flush=True)
        for line in hits[:6]:
            print(f"    {line}", flush=True)
        taken += bool(hits)
    return 1 if taken else 3 if unchecked else 0


if __name__ == "__main__":
    sys.exit(main())
