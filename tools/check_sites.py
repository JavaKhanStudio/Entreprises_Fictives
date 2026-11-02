#!/usr/bin/env python3
"""The gate of the fictional sites: must pass before any push. Python stdlib, plus dig.

    python3 tools/check_sites.py [root]

Walks every .html and .css under root (hidden folders aside) and prints each refusal as
path:line: [rule] what is wrong. Exit 0 when nothing is refused, 1 otherwise. The footer every
page must carry is the one in shared/modele.html, byte for byte.

A domain dig cannot answer for (no dig, no network) is a refusal too: unchecked is not clean.

Phone numbers the gate does not see, on purpose: fewer than 8 digits (118 218, 3615), a number
split across tags, a number with more digits after a single space, dot, slash or hyphen (two
numbers in a row, 01 23 45 67 89 24/24), a comma number that is not five pairs joined by bare
commas (01, 02, 03, 04, 05 is a list, and SVG points are not phones), a mark that is not in PHONE_SEPARATOR (middle dot, colon, semicolon, pipe, a
zero-width character), and a run of digits with no + that does not start with 0, 33 or the North
American shape (1-800-555-0100): it reads as a reference, and so does an unprefixed foreign
number in any other shape.

Phone numbers: the only ones allowed are those the French numbering plan keeps for fiction,
"Numéros pour œuvres audiovisuelles", ARCEP decision no 2025-2215 of 27 November 2025, plan
version of 1 January 2026, p. 54/67: https://www.arcep.fr/uploads/tx_gsavis/25-2215.pdf
"""

import html.parser
import os
import re
import subprocess
import sys
import urllib.parse

MODEL_PAGE = "shared/modele.html"
# The root index must link each of these once its index.html exists (check_index_links).
COMPANIES = ("merlin", "gobelin", "courtepaille")
FICTION_PHONE_ROOTS = ("019900", "026191", "035301", "046571", "053649", "063998")

EM_DASH = "\u2014"
FOOTER = re.compile(r"<footer\b.*?</footer>", re.I | re.S)
COMMENT = re.compile(r"<!--.*?-->", re.S)
CSS_COMMENT = re.compile(r"/\*.*?\*/", re.S)
CSS_URL = re.compile(r"""url\(\s*['"]?([^'")\s]*)|@import\s+['"]([^'"]+)""", re.I)
# Words joined by dots, ending in letters. Hits "bob@a.fr" and "a.fr/page" alike.
DOMAIN = re.compile(r"(?<![\w.@-])(?:([\w.+-]+)@)?((?:[\w-]+\.)+[^\W\d_]{2,})(?![\w-])")
BARE_EMAIL = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w-]+(?![\w-]|\.\w)")
# Not domains: the file names a page may show or link to.
FILE_SUFFIXES = {"html", "htm", "css", "svg", "png", "jpg", "jpeg", "gif", "webp", "ico",
                 "js", "pdf", "txt", "docx", "xlsx"}
# Digits with up to three separators between them: 01 99 00 12 34, +33 (0)1.99.00.12.34,
# 01 - 23 - 45 - 67 - 89, 01/23/45/67/89, 01,23,45,67,89. Not inside a word, a reference or a path.
# Whitespace of any kind and length counts once: a browser shows a hand-wrapped line as one space.
PHONE_MARKS = r".()/\-,_\u2010-\u2013\u2212"
PHONE_SEPARATOR = rf"(?:\s+(?!\s)|[{PHONE_MARKS}])"
PHONE = re.compile(rf"(?<![\w/\-])\+?\d(?:{PHONE_SEPARATOR}{{0,3}}\d)*(?!\w)")
# Between two numbers in a row, when the run is not one number: two separators or more
# ("01 99 00 12 34 - 2026"), or one that does not sit inside a number on its own account: a line
# break or tab, a comma, an underscore, a typographic dash.
PHONE_GAP = re.compile(rf"[\s{PHONE_MARKS}]{{2,}}|[^\S \u00a0\u2009\u202f]|[,_\u2010-\u2013\u2212]")
COMMA_NUMBER = re.compile(r"\d\d(?:,\d\d){4}")
# A date is many digits and no phone number. Blanked before reading digits, at the same length.
DATE = re.compile(r"(?<!\d)(?:\d{1,2}[/.\-]\d{1,2}[/.\-]\d{4}|\d{4}-\d{2}-\d{2})(?!\d)")
NORTH_AMERICAN_GAP = r"[\s.\-\u2010-\u2013\u2212]*"
NORTH_AMERICAN = re.compile(rf"1{NORTH_AMERICAN_GAP}\(?\d{{3}}\)?{NORTH_AMERICAN_GAP}\d{{3}}"
                            rf"{NORTH_AMERICAN_GAP}\d{{4}}")
# Attributes that hold a URL, and that a page therefore fetches or goes to.
URL_ATTRS = {"href", "src", "srcset", "poster", "data", "action", "formaction", "background",
             "cite", "ping", "xlink:href"}
# Attributes holding page plumbing rather than something to read.
PLAIN_ATTRS = {"class", "id", "style", "rel", "type", "charset", "lang", "name", "for", "media"}
URL_SCHEME = re.compile(r"^([a-z][a-z0-9+.-]*):", re.I)


class Refusals:
    def __init__(self):
        self.lines = []

    def add(self, path, line, rule, text):
        self.lines.append(f"{path}:{line}: [{rule}] {text}")


class Page(html.parser.HTMLParser):
    """What the checks need from one page, each piece with the line it starts on."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags = []        # (line, tag, {attr: value})
        self.readable = []    # (line, text): text, comments, and attributes worth reading
        self.styles = []      # (line, css): <style> blocks and style="" attributes
        self.in_style = False

    def handle_starttag(self, tag, attrs):
        line = self.getpos()[0]
        values = {name.lower(): (value or "") for name, value in attrs}
        self.tags.append((line, tag, values))
        for name, value in values.items():
            if name == "style":
                self.styles.append((line, value))
            elif name not in PLAIN_ATTRS and value:
                self.readable.append((line, value))
        self.in_style = tag == "style"

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.in_style = False

    def handle_endtag(self, tag):
        if tag == "style":
            self.in_style = False

    def handle_data(self, data):
        (self.styles if self.in_style else self.readable).append((self.getpos()[0], data))

    def handle_comment(self, data):
        self.readable.append((self.getpos()[0], data))


def dig_status(domain):
    """The DNS status of a name: NXDOMAIN, NOERROR, or why it could not be told."""
    try:
        run = subprocess.run(["dig", "+time=3", "+tries=2", domain, "A"],
                             capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as error:
        return f"dig failed ({error})"
    found = re.search(r"status: (\w+)", run.stdout)
    return found.group(1) if found else "no answer from dig"


def walk(root):
    for folder, subfolders, names in os.walk(root):
        subfolders[:] = sorted(s for s in subfolders if not s.startswith("."))
        for name in sorted(names):
            if name.lower().endswith((".html", ".htm", ".css")):
                yield os.path.relpath(os.path.join(folder, name), root).replace(os.sep, "/")


def read(root, path):
    with open(os.path.join(root, path), encoding="utf-8", newline="") as handle:
        return handle.read().replace("\r\n", "\n")


def exact_case_exists(root, relative):
    """Is this path there, with this case? Windows forgives a wrong case, GitHub Pages does not."""
    folder = root
    for part in relative.split("/"):
        if part == "":
            continue
        try:
            if part not in os.listdir(folder):
                return False
        except (NotADirectoryError, FileNotFoundError):
            return False
        folder = os.path.join(folder, part)
    return True


def check_url(root, refusals, path, line, url, from_tag=None):
    """One URL a page or a stylesheet uses. Everything that works must work over file://."""
    url = url.strip()
    if not url or url.startswith("#"):
        return
    scheme = URL_SCHEME.match(url)
    if scheme:
        name = scheme.group(1).lower()
        if name in ("tel", "callto", "sms"):
            refusals.add(path, line, "tel", f"phone link {url}: a number is shown as text")
        elif name == "data" and from_tag != "a":
            pass
        elif name in ("http", "https") and from_tag != "a":
            refusals.add(path, line, "external", f"loads an outside resource: {url}")
        else:
            refusals.add(path, line, "live-link", f"live link {url}: a domain is shown as text")
        return
    if url.startswith("//"):
        refusals.add(path, line, "external", f"loads an outside resource: {url}")
        return
    if url.startswith("/"):
        refusals.add(path, line, "relative", f"{url} starts at the root: it breaks over file://")
        return
    target = urllib.parse.unquote(url.split("#")[0].split("?")[0])
    resolved = os.path.normpath(os.path.join(os.path.dirname(path), target)).replace(os.sep, "/")
    if resolved.startswith("..") or not exact_case_exists(root, resolved):
        refusals.add(path, line, "dead-link", f"{url} leads to nothing")
    elif os.path.isdir(os.path.join(root, resolved)):
        refusals.add(path, line, "dead-link",
                     f"{url} is a folder: over file:// that opens a listing, name its index.html")


def check_css(root, refusals, path, line, css):
    if EM_DASH in css or re.search(r"\\0*2014\b", css):
        refusals.add(path, line, "em-dash", "an em dash")
    for found in CSS_URL.finditer(CSS_COMMENT.sub("", css)):
        check_url(root, refusals, path, line + css.count("\n", 0, found.start()),
                  found.group(1) or found.group(2) or "")


def phone_refusal(number):
    """Why this run of digits is a refused phone number; None when it is fine or no phone."""
    digits = re.sub(r"\D", "", number)
    if len(digits) < 8:
        return None
    number = " ".join(number.split())    # a hand-wrapped number, on the one line of its refusal
    if number.startswith("+") or re.match(r"00[1-9]\d{7,}$", digits):
        country = digits.removeprefix("00")
        if not country.startswith("33"):
            return f"{number}: a foreign number, ARCEP reserves none of those for fiction"
        digits = "0" + country[2:].lstrip("0")
    elif re.fullmatch(r"33[1-9]\d{8}", digits):
        digits = "0" + digits[2:]
    elif NORTH_AMERICAN.fullmatch(number):
        return f"{number}: a foreign number, ARCEP reserves none of those for fiction"
    if not re.fullmatch(r"0[1-9]\d{8}", digits) or digits.startswith(FICTION_PHONE_ROOTS):
        return None
    return f"{number}: outside the ranges ARCEP reserves for fiction"


def is_one_number(run):
    digits = re.sub(r"\D", "", run)
    if "," in run:
        return COMMA_NUMBER.fullmatch(run)
    # No number runs past 15 digits (ITU E.164): beyond that a + number has another one behind it.
    return ((run.startswith("+") and len(digits) <= 15) or NORTH_AMERICAN.fullmatch(run)
            or re.fullmatch(r"0[1-9]\d{8}|33[1-9]\d{8}", digits))


def phone_refusals(text):
    """Each refused number in this text, as (where it starts, why)."""
    undated = DATE.sub(lambda date: "\u00a7" * len(date.group(0)), text)
    for run in PHONE.finditer(undated):
        pieces = [run.group(0)] if is_one_number(run.group(0)) else PHONE_GAP.split(run.group(0))
        for piece in pieces:
            why = phone_refusal(piece)
            if why:
                yield run.start() + run.group(0).index(piece), why


def check_text(refusals, path, line, text, domains):
    if EM_DASH in text:
        refusals.add(path, line + text.count("\n", 0, text.index(EM_DASH)), "em-dash", "an em dash")
    for found in DOMAIN.finditer(text):
        domain = found.group(2).lower().rstrip(".")
        here = line + text.count("\n", 0, found.start())
        if found.group(1) is None and domain.rsplit(".", 1)[1] in FILE_SUFFIXES:
            continue
        domains.setdefault(domain, (path, here))
        if not domain.endswith(".example"):
            kind = "email" if found.group(1) else "domain"
            refusals.add(path, here, "domain", f"{kind} {found.group(0)} does not end in .example")
    for found in BARE_EMAIL.finditer(text):
        refusals.add(path, line + text.count("\n", 0, found.start()), "domain",
                     f"email {found.group(0)} does not end in .example")
    for start, why in phone_refusals(text):
        refusals.add(path, line + text.count("\n", 0, start), "phone", why)


def check_page(root, refusals, path, source, footer, domains):
    page = Page()
    page.feed(source)
    page.close()

    robots = [values.get("content", "") for _, tag, values in page.tags
              if tag == "meta" and values.get("name", "").lower() == "robots"]
    if not any("noindex" in content.lower() for content in robots):
        refusals.add(path, 1, "noindex", 'no <meta name="robots" content="noindex">')

    footers = FOOTER.findall(COMMENT.sub("", source))
    if footers != [footer]:
        refusals.add(path, 1, "footer", f"found {len(footers)} footer(s), expected one, "
                                        f"byte for byte the one in {MODEL_PAGE}")

    for line, tag, values in page.tags:
        if tag == "form":
            refusals.add(path, line, "form", "a <form>")
        for name, value in values.items():
            if name == "srcset":
                for item in value.split(","):
                    check_url(root, refusals, path, line, item.split()[0] if item.split() else "")
            elif name in URL_ATTRS:
                check_url(root, refusals, path, line, value, tag)

    for line, css in page.styles:
        check_css(root, refusals, path, line, css)
    for line, text in page.readable:
        check_text(refusals, path, line, text, domains)


def check_index_links(root, refusals):
    """A company whose site exists must be reachable from the root list."""
    if not os.path.isfile(os.path.join(root, "index.html")):
        refusals.add("index.html", 1, "index", "no index.html at the root")
        return
    page = Page()
    page.feed(read(root, "index.html"))
    links = {values.get("href", "") for _, tag, values in page.tags if tag == "a"}
    for company in COMPANIES:
        target = f"{company}/index.html"
        if os.path.isfile(os.path.join(root, target)) and target not in links:
            refusals.add("index.html", 1, "index", f"{target} exists and is not linked from here")


def check_tree(root, status_of=dig_status):
    """Every refusal in the tree, as a list of lines. status_of is the DNS lookup."""
    refusals = Refusals()
    if not os.path.isfile(os.path.join(root, MODEL_PAGE)):
        refusals.add(MODEL_PAGE, 1, "footer", "the model page is missing, nothing to compare to")
        return refusals.lines
    footer = FOOTER.search(COMMENT.sub("", read(root, MODEL_PAGE)))
    if footer is None:
        refusals.add(MODEL_PAGE, 1, "footer", "the model page has no footer, nothing to compare to")
        return refusals.lines

    domains = {}
    for path in walk(root):
        source = read(root, path)
        if path.lower().endswith(".css"):
            check_css(root, refusals, path, 1, source)
        else:
            check_page(root, refusals, path, source, footer.group(0), domains)
    check_index_links(root, refusals)

    for domain, (path, line) in sorted(domains.items()):
        status = status_of(domain)
        if status == "NOERROR":
            refusals.add(path, line, "resolves", f"{domain} resolves: it must not exist")
        elif status != "NXDOMAIN":
            refusals.add(path, line, "resolves", f"{domain} could not be checked: {status}")
    return refusals.lines


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))
    lines = check_tree(root)
    for line in lines:
        print(line)
    if lines:
        print(f"REFUSED: {len(lines)} problem(s)")
        return 1
    print(f"OK: {sum(1 for _ in walk(root))} files checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
