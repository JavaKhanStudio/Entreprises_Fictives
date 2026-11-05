# Entreprises fictives: agent guide

Small static sites of invented companies, the OSINT kits of a social engineering
workshop. Read README.md first. Sub board of `social-engineering`. THIS REPO IS PUBLIC: what
you push is published.

## Stack

Plain HTML and CSS. No build step, no framework, no JS unless a ticket shows the need. Relative
links only, nothing fetched from outside (no CDN, no web font): a page also opens by
double-click on Windows, macOS and Linux. Students need a browser, nothing else.

## Run and test

```bash
python3 -m http.server 8802             # then http://127.0.0.1:8802/
python3 tools/check_sites.py            # the gate: must pass before any push (needs dig and DNS)
python3 tests/test_check_sites.py       # each refusal of the gate, on scratch pages
python3 tests/test_check_names.py       # tools/check_names.py --domains on names that make bad domains, no network
python3 tools/render_pages.py OUT index.html   # both file:// and http, 1280 and 390, pictures in OUT
python3 tools/check_trombone.py [OUT]   # Merlin's moving parts, which the renders freeze
python3 tools/check_trombone_browsers.py OUT   # the clip in Firefox and headed Chrome, real card, no window on screen
python3 tools/check_trombone_safari.py        # real Safari, run through skill test-windows-mac: its docstring says what it cannot prove
python3 tools/check_trombone_safari.py --file-probe   # same way: what Safari really loads over file://, each site's width against its window
python3 tools/check_badge.py [OUT]      # Gobelin's 3D badge: its sway, turn and flip, also frozen
python3 tools/check_badge_browsers.py OUT [--control flat|gold]   # the badge's pixels in Firefox against Chrome, no window on screen
python3 tools/check_badge_safari.py --extract LOG OUT   # read a Safari run; the run itself is in its docstring (macOS runner)
python3 tests/test_render_pages.py             # two render runs at once each prove their own tree
python3 tools/check_configurateur.py [OUT]   # Au Dernier Prix's 3D coffin: turning, options, the total in pixels, which the renders freeze
python3 tools/check_configurateur_browsers.py OUT [--control flat|counter|hollow]   # its pixels in Firefox against Chrome, no window on screen
python3 tools/check_configurateur_safari.py --extract LOG OUT   # read a Safari run of the coffin; the run itself is in its docstring (macOS runner)
python3 tests/test_check_configurateur_safari.py    # that tool's whole flow and pixel read, in Chrome, before a macOS minute is spent
python3 tools/dernier_prix_bois.py      # the coffin's woods, computed
python3 tools/check_pages.py [--render OUT]    # the served site: each page and local link answers 200, noindex and footer in the body
python3 tools/check_courtepaille_egg.py [OUT]  # Courtepaille's counter looks the same with its hidden link
python3 tools/check_racine.py [OUT]    # the root list's envelopes in Chrome and Firefox, which the renders freeze; no word under one, open or shut; --control flat and --control big must fail
python3 tools/check_racine_frames.py [OUT]   # the envelope seeked frame by frame, opening, closing and the phone's loop: no flap over the letter, no flap adrift; --control early and --control clip must fail
python3 tools/check_racine_safari.py --extract LOG OUT   # read a Safari run of the root list's envelopes; the run itself is in its docstring (macOS runner)
python3 tests/test_check_racine_safari.py    # that tool's scripts and pixel read, in Chrome, before a macOS minute is spent
python3 tools/check_source_eclat.py    # Source & Éclat: its countdown moving, which the renders freeze, and its numbers
python3 tools/check_inviolia.py [OUT]  # Inviolia: the scroll camera and its stops, which the renders freeze, Chrome and Firefox; also the live map (--live: only that)
python3 tools/check_inviolia_safari.py # same way as check_trombone_safari: the camera in real Safari; no wheel, so not its stops
```

A new page starts as a copy of `shared/modele.html`: its footer is compared byte for byte.

## Rules the gate holds

- Every page: `<meta name="robots" content="noindex">` and the footer saying the site is
  fictional and educational.
- No form that collects anything, no `tel:` link, no external resource, no em dash.
- Domains are reserved `.example` ones, never a real TLD. No real company, person or phone
  number; a phone number comes from a range ARCEP reserves for fiction.
- No live link to a fictional domain: it is shown as text.

## Tone

A parody with a straight face: a few absurd self-given titles. The
model is `~/Documents/GitHub/Social_Engineering_en_visuel/faux-president/js/i18n.js`,
`steps.research.site`. The clues stay usable: the joke never hides what an attacker would read.
All page text is in French. Simon reads every site before it counts as done.

Humour stays quiet (Simon, r4): never explain a joke, say the fact and stop. A joke exaggerates
something real and is funny once. The likes bias is in the numbers and nowhere else: "Women can
be silly too". Absurd titles are Simon's call per site: all seven at Courtepaille, four at Merlin.
Before writing or changing text a student reads, read `.claude/skills/humour/SKILL.md` (missing:
`atelier skills install humour`).

## A new company

Simon on r70: round 1 "all very, very bad", round 2 "WAY better. Keep the teachable moment".
Before proposing a company or building one, read r2, r3 and r4's verdicts (`atelier show r2`).
What changed between the rounds:

- Start from a kind of company everyone has met. Round 1 started from an attack and worked back
  to a premise: an abbey whose vows are the holes, a feud between heirs. Nobody has worked there.
- Copy a real web genre faithfully: the vibe-coded SaaS, the game studio, Frontpage 2009, the
  security vendor, the MLM, the hard-discount shop. Real pictures (`tools/new_site_images.py`).
- A voice that keeps producing lines for seven pages, not a premise stated in the headline: that
  is funny once. Clues go in afterwards, inside lines the company would write.
- A mock-up looks like the finished thing: a full home page (`tools/new_site_takes.py`), never
  flat text on a plain ground, the option's letter on a band that covers no word.

## Traps

- Safari over file:// refuses what is above the opened page's folder: a page loads nothing through `../`.
  So a site holds a copy of `shared/base.css` as `<company>/base.css`. Change the one in `shared/`, then copy it.
- Link `merlin/index.html`, never `merlin/`: over file:// a folder opens a listing.
- A dotted word in text reads as a domain (`fin.Le`, `M.Bob`): put the space in, the gate is right.
