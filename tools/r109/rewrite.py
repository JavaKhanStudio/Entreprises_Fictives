"""r109: replace each over-long pack's context with its trimmed text. What leaves a pack
goes, word for word, into .atelier/notes/<tag>.md, which the pack names."""
import pathlib, re, tomllib
ROOT = pathlib.Path(__file__).resolve().parents[2]
P = ROOT / ".atelier/packs.toml"
ROUND = 'ROUND (board skill §4, r4524): an ask\'s first picture is close on its subject (magick -crop WxH+X+Y +repage), captioned "Shows: <it>"; then the takes; one context picture at most.'

NEW = {
"shared": f"""
FILES: index.html + index.css (the root list; its words name no count, Simon on r10), shared/base.css (no company's look), shared/modele.html (every page's start and footer). Details: .atelier/notes/shared.md.
ROOT LIST: its envelopes are CSS only (r77), frozen by renders: after touching them run python3 tools/check_racine.py OUT, and for their timings or flap tools/check_racine_frames.py OUT. A new company: its name in CARDS in those tools, its --teinte and --cadre in index.css.
GATE: tools/check_sites.py; what it does not see is in its docstring. A new refusal gets a scratch page in tests/test_check_sites.py, a false alarm test_what_the_gate_lets_through.
RENDER: tools/render_pages.py fails on a failed request, base.css not applied, a page wider than its window or file:// and http differing. Attach the pictures.
RULE: what two sites share lives ONCE, in shared/, but base.css is copied into each company (CLAUDE.md, Traps) and the gate refuses a copy that differs. The footer is copied byte for byte from shared/modele.html: change its words on every page in one commit.
ICON: every page links <company>/img/icone.svg (icon.svg at the root), or Best Practices drops to 96. Read one at 16 px: tools/icon_takes.py --shipped OUT.
HEALTH: before chasing a Lighthouse audit, read HEALTH in the notes: eight are left on purpose.
{ROUND}
""",
"merlin": f"""
FILES: merlin/ (7 pages), merlin/merlin.css, merlin/merlin.js, merlin/base.css (a copy, RULE in #shared). Domain: papeterie-merlin.example. A new page links merlin.css after base.css and the icon, as shared/modele.html's comment says.
CANON: ~/Documents/GitHub/Social_Engineering_en_visuel/faux-president/js/i18n.js, steps.research: the capsule reuses Merlin's names and facts, so the site must not contradict them. The list, and what not to reuse from the Lumisol sample: .atelier/notes/merlin.md.
LOOK: a vibe-coded landing page (Simon on r2): dark bands, one gradient, glass header, cards. Nothing on the site says the clip is useless.
SCRIPT: merlin/merlin.js is a classic script (file:// refuses modules): the WebGL clip with no library, counters, reveals. Every word stays in the HTML, and merlin/img/trombone-3d.svg shows without WebGL or JS.
NO GPU: sansGpu() in merlin/merlin.js draws a cheap clip on a software renderer (Simon on r55), and Lighthouse's Chrome is one: its Merlin score follows the machine's load (99 to 100 near a load of 25, 68 to 81 above 60). Read uptime before calling it a regression.
MOTION: render_pages.py freezes the clip. When merlin.js or merlin.css changes, run python3 tools/check_trombone.py (the cheap path, the fallbacks, 8 widths) and tools/check_trombone_browsers.py OUT (the full one).
{ROUND}
""",
"gobelin": f"""
FILES: gobelin/ (8 pages), gobelin/gobelin.css, gobelin/base.css (a copy, RULE in #shared). Domain: gobelin-hurlant.example. A new page links gobelin.css after base.css and the icon, as shared/modele.html's comment says. gobelin/connexion-discord.html leaves the fiction on purpose: the trap page (Simon, r3).
SURFACE: a public Discord and its fans, a publisher, a build under NDA, crunch worn as a badge: the build and the accounts are the prize, not the money.
DATES: they stay as they are after 13 Nov 2026 (Simon, r3 answer 2A). They also sit in a picture: BOARD_LINES in tools/gobelin_images.py, the same words as the alt text in gobelin/a-propos.html and gobelin/equipe.html.
PICTURES: tools/gobelin_images.py. make paints with the local ComfyUI, which whoever runs it starts and stops (how: .atelier/notes/gobelin.md); ship resizes into gobelin/img/ without it. The model's lettering is always false: what must be read is pasted on by ship.
BADGE: CSS only, on gobelin/a-propos.html. Run python3 tools/check_badge.py AND tools/check_badge_browsers.py OUT: the first cannot see 3D (r59). Firefox paints no background-clip: text on the element carrying the 3D transform, so the gold of .crunch sits on its inner span. Safari: tools/check_badge_safari.py.
CLUES: in r3's done note (atelier show r3 --full), never in this repo.
{ROUND}
""",
"courtepaille": f"""
FILES: courtepaille/ (7 pages), courtepaille/courtepaille.css, courtepaille/base.css (a copy, RULE in #shared). Domain: etude-courtepaille.example. A new page links courtepaille.css after base.css and the icon, as shared/modele.html's comment says.
SURFACE: large property transfers, elderly clients, paper first, a website that looks its age. The name is also a restaurant chain's (Simon kept it, 2026-11-02): the site says nothing of restaurants.
PICTURES: the portraits and the seal are SVG. courtepaille/img/facade-photo.jpg is painted and aged by tools/courtepaille_images.py, small and poor on purpose (Simon, r68). The counter's number on index.html links img/facade.svg with no look of a link: an easter egg, not a leftover (tools/check_courtepaille_egg.py).
DATES: no year in the plot (Simon, r4); the dates every page agrees on are in .atelier/notes/courtepaille.md. A duration never sits beside its start year. Leave the footer's bracket "(la précédente datait de 2009)" (Simon, r86). No page says neveu. No real notary's name: check https://www.notaires.fr/fr/directory.
{ROUND}
""",
"inviolia": f"""
FILES: inviolia/ (7 pages), inviolia/inviolia.css, inviolia/inviolia.js, inviolia/base.css (a copy, RULE in #shared). Domain: inviolia.example. A new page links inviolia.css after base.css and the icon, as shared/modele.html's comment says, then inviolia.js.
GENRE: a vendor that sells fear: hood, glowing globe, threat level always critical. Words from Simon's pick on r70, INVIOLIA in tools/new_site_takes.py. SURFACE: admin access to its clients, staff used to fake emails.
PICTURES: tools/inviolia_images.py (make with the local ComfyUI, ship into inviolia/img/); pirate and globe from tools/new_site_images.py. No word sits in a picture.
MOTION: inviolia.js sets html.vivant and each block's --p from the scroll; inviolia.css moves only under .vivant, so without it the page stands still with every word in the HTML. Stops are data-stop in the pages (Simon, r75). Renders freeze it: python3 tools/check_inviolia.py OUT (Chrome, Firefox), tools/check_inviolia_safari.py.
LIVE MAP (r78, r90): the counter, the feed and the comets on the globe; how the feed reuses only the page's six lines is in .atelier/notes/inviolia.md. They start from the written values on each load.
DATES: the dates and counts the pages agree on are in the notes.
CLUES: in r75's done note (atelier show r75 --full), never in this repo.
{ROUND}
""",
"source-eclat": f"""
FILES: source-eclat/ (7 pages), source-eclat/source-eclat.css, source-eclat/source-eclat.js, source-eclat/base.css (a copy, RULE in #shared). Domain: source-et-eclat.example. A new page links source-eclat.css after base.css and the icon, as shared/modele.html's comment says.
GENRE: multi-level marketing: sunset, countdown, rank ladder. Its voice is nearest merlin/equipe.html's posts: read them, reuse no joke of theirs. SURFACE: a weekly message forwarded unchanged down the line, money paid to a sponsor by a RIB sent in a message.
SCRIPT: source-eclat.js moves only the top band's countdown, which restarts at each load on purpose; no page says so. python3 tools/check_source_eclat.py checks it, the numbers and 8 widths.
PICTURES: tools/source_eclat_images.py (make with the local ComfyUI, ship into source-eclat/img/). Marie-Ange's portrait is cropped out of plage, so one face. No picture holds text to read.
NUMBERS: 9 170 Ambassadors and 5,8 M euros a year are sums the pages share (.atelier/notes/source-eclat.md): change one, change them all.
CLUES: in r76's done note (atelier show r76 --full), never in this repo.
{ROUND}
""",
"dernier-prix": f"""
FILES: dernier-prix/ (8 pages), dernier-prix/dernier-prix.css, dernier-prix/configurateur.css (that page only), dernier-prix/base.css (a copy, RULE in #shared). Domain: au-dernier-prix.example. A new page links dernier-prix.css after base.css and the icon, as shared/modele.html's comment says.
SPICY: the whole site (.claude/skills/humour/SKILL.md). A spicy line beyond the three Simon passed on r70 (.atelier/notes/dernier-prix.md) goes to him by name on the card.
PICTURES: bois-*.webp from tools/dernier_prix_bois.py; the others from tools/dernier_prix_images.py (make with the local ComfyUI, ship into dernier-prix/img/; ship draws the shop's sign, not the model).
STILL: no JS, the cart collects nothing. Only configurateur.html moves: the coffin turns only on press and drag (configurateur.js, r89), its choices are radios outside any form, its total CSS counters, its prices the home page's. The occupant is written in by tools/dernier_prix_corps.py.
3D: each plane shows from its outside only (backface-visibility), or Firefox sorts a turned-away face over the lid. Prove a change with tools/check_configurateur.py and tools/check_configurateur_browsers.py OUT; Safari: tools/check_configurateur_safari.py.
DATES: the dates and figures the pages agree on are in the notes.
CLUES: in r77's note of 2026-11-03 02:30 (atelier show r77 --full), never in this repo.
{ROUND}
""",
}

src = P.read_text()
for slug, text in NEW.items():
    pat = re.compile(r'(\[tags\.' + re.escape(slug) + r'\][^\[]*?context = """)\n.*?\n(""")', re.S)
    src, n = pat.subn(lambda m: m.group(1) + text.rstrip("\n") + "\n" + m.group(2), src, count=1)
    assert n == 1, slug
P.write_text(src)
tomllib.loads(src)


def notes(old):
    """Write .atelier/notes/<tag>.md from a tag's pack as it was before r109, word for
    word, one paragraph per labelled line: nothing the pack lost is lost."""
    for slug in NEW:
        out = [f"# #{slug}: the full notes behind its context pack",
               "",
               f"The pack in .atelier/packs.toml is the short index an agent reads first; this is what it",
               f"points to. Cut from the pack, word for word, on r109. Fix a line here in the same commit",
               f"as what makes it wrong.", ""]
        for line in old[slug].strip().split("\n"):
            m = re.match(r"([A-Z][A-Z ]+?)(?: \(([^)]*)\))?: (.*)", line)
            if m and m.group(1) == "THE ROUND":
                continue  # kept in the pack
            if m:
                out += [f"## {m.group(1)}" + (f" ({m.group(2)})" if m.group(2) else ""), "", m.group(3), ""]
            else:
                out += [line, ""]
        (ROOT / f".atelier/notes/{slug}.md").write_text("\n".join(out))


if __name__ == "__main__" and len(__import__("sys").argv) > 1:
    import json
    notes(json.load(open(__import__("sys").argv[1])))
