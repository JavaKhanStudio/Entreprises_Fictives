# #dernier-prix: the full notes behind its context pack

The pack in .atelier/packs.toml is the short index an agent reads first; this is what it
points to. Cut from the pack, word for word, on r109. Fix a line here in the same commit
as what makes it wrong.

## FILES

8 pages in dernier-prix/ (index, a-propos, equipe, organigramme, offre-emploi, communique, contact, configurateur), dernier-prix/dernier-prix.css, dernier-prix/configurateur.css (that page only), dernier-prix/base.css (a copy, see RULE in #shared). Domain: au-dernier-prix.example.

## NEW PAGE

copy shared/modele.html to dernier-prix/, then add dernier-prix.css after base.css and the icon, as its comment says. Render with tools/render_pages.py (see #shared).

## START

the mock-up Simon chose on r70: DERNIER in tools/new_site_takes.py, its pictures cercueil, gerbe and urne in tools/new_site_images.py. Read "A new company" in CLAUDE.md first.

## GENRE

a hard-discount shop: starbursts, stars, stock left, cart.

## SPICY

the whole site is, so .claude/skills/humour/SKILL.md applies to every line. Simon's r70 pick passed Partez moins cher, Offre Couple and Je reviendrai. Any other spicy line goes to him by name on the card.

## SURFACE

death notices naming the family, the date and the address, and invoices sent as PDF by email to people who do not read them closely.

## PICTURES

bois-*.webp are computed by tools/dernier_prix_bois.py. The other .webp in dernier-prix/img/ come from tools/dernier_prix_images.py: make paints into ~/.cache/dernier-prix-images with the local ComfyUI, ship resizes into dernier-prix/img/. cercueil, gerbe and urne come from tools/new_site_images.py. ship crops the false logos off the portraits, and mirrors the shop and letters its sign along the cladding: the sign is not the model's.

## STILL

no JS, the page stands still. AJOUTER AU PANIER and Mon panier go to the empty cart on the home page, which collects nothing; the search box is a link. Only configurateur.html moves, in CSS but for configurateur.js, the press and drag that turns the coffin (r89: a pointer alone turns nothing, a release stops it): Configurer en 3D opens it. Its choices are radios outside any form, its total is summed by CSS counters. The occupant's planes are written into the page by tools/dernier_prix_corps.py. Prove a change with tools/check_configurateur.py and tools/check_configurateur_browsers.py, real Safari with tools/check_configurateur_safari.py: each plane shows from its outside only (backface-visibility), or Firefox sorts a turned-away face over the lid. Prices there are the home page's.

## DATES

the notices are dated for the week of 2 November 2026 (Thursday 5, Friday 6, Saturday 7). Pages agree on: press release 2 November, Didier at the salon and the new bank 16 November, Black Friday 27 November, Toussaint offer to 30 November, invoice job from 4 January to 26 March. Also on 1952, 14 staff, 1 140 families in 2025, 8 days and 10 %, 48 h, 5 000 euros, 6 400 cards, 2 300 contracts, the reference FAC-2026-xxxxx.

## CLUES

the list is in r77's note of 2026-11-03 02:30 (atelier show r77 --full), never in this repo.
