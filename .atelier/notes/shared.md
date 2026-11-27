# #shared: the full notes behind its context pack

The pack in .atelier/packs.toml is the short index an agent reads first; this is what it
points to. Cut from the pack, word for word, on r109. Fix a line here in the same commit
as what makes it wrong.

## FILES

index.html + index.css (the root list of the companies; its words name no count, Simon on r10, so a company can be added; a card shows a picture its own site ships, plus merlin/img/vignette.webp from tools/racine_images.py, and a manila envelope that opens on hover, CSS only, Simon on r77; after touching it run python3 tools/check_racine.py OUT, in Chrome and Firefox, because render_pages.py freezes it; a change to its timings or its flap also runs python3 tools/check_racine_frames.py OUT, which seeks every moment of the swing (r95: Chrome 156 draws a clip-path on the swinging flap adrift, so its triangles are masks, and the letter starts only once the flap has landed); real Safari, over file:// and http, is python3 tools/check_racine_safari.py on a macOS runner (r81, its docstring), which ten-times-priced minutes keep for a change of the 3D, the clip-paths and masks or where the pictures live; a new company also needs its name in CARDS there and in that tool, its --teinte and --cadre in index.css), shared/base.css (what every page shares, no company's look), shared/modele.html (the page every site starts from, and the reference footer), tools/check_sites.py (the gate), tests/test_check_sites.py (each refusal proved), tools/render_pages.py (the browser's view).

## GATE

python3 tools/check_sites.py walks every .html and .css and must pass before any push. It refuses, by rule name: noindex, footer, above-folder, base-copy, form, tel, external (an http(s) resource, also in CSS), live-link (an a href to any domain, mailto), relative (a link from /), dead-link (also a wrong case, also a folder), em-dash, domain (not .example), resolves (dig says the name exists or cannot tell: offline, the gate fails), phone (outside ARCEP's fiction ranges, cited in the script; what it does not read as a phone is listed at the top of the script: under 8 digits, split across tags, a long run whose groups of digits never add up to a number (0612 3456 7890, an IBAN, a SIRET), a comma number that is not five pairs joined by bare commas, a mark not in PHONE_SEPARATOR such as a middle dot or colon, a number glued to a word that is not in PHONE_LABEL or after a word and a slash or hyphen (FAC-0612345678, dossier/0612345678.pdf), an unprefixed run not starting 0, 33 or in the North American shape), index (a company's index.html the root list does not link).

## TEST

python3 tests/test_check_sites.py when the gate changes; a new refusal gets its scratch page there, and a false alarm goes into test_what_the_gate_lets_through.

## RENDER

python3 tools/render_pages.py OUT_DIR index.html merlin/index.html opens each page over file:// and over http from a server of its own on a free port, at 1280 and 390, fails on a failed request, on base.css not applied, on a page wider than its window or on the two ways differing. Two runs at once are safe: python3 tests/test_render_pages.py proves it. Attach the pictures with atelier attach.

## HEALTH

atelier quality audits the paths in lighthouse_paths of projects/entreprises-fictives.toml in the atelier checkout. Do not chase cache-insight or uses-long-cache-ttl: both are about the Cache-Control header of the server, here ~/Documents/GitHub/atelier/tools/serve_static.py, and no file in this repo can set a header. The largest image of a page takes fetchpriority="high" (lcp-discovery-insight), as gobelin/index.html and courtepaille/index.html do. Do not chase is-crawlable: it is the noindex tools/check_sites.py requires on every page, and removing it would fail the gate. Do not chase image-delivery-insight on gobelin/index.html: uses-responsive-images passes with the srcset there (r58), and this one counts CSS pixels and ignores screen density, so passing it means a 372 px picture that a phone at 1.75x shows blurred. A new company picture shown small gets a lighter copy through SMALLER in tools/gobelin_images.py. Do not chase meta-description: Simon accepted that loss on r19, because these noindex pages are not found by search and a description reaches SEO only 60, so seo stays 50 to 54. Do not chase network-dependency-tree-insight, render-blocking-insight or render-blocking-resources: all three report a page and its two stylesheets, shared/base.css and the company's, with no @import (Lighthouse 12.8.2 lists exactly those two on merlin/index.html). Inlining base.css would break RULE below. Inlining the company's would copy it into every page of that company, for a performance score already at 100. Deferring either needs JS and shows the page unstyled first.

## RULE

what two sites share lives ONCE, in shared/. One exception, shared/base.css: real Safari over file:// refuses what is above the opened page's folder (r61, tools/check_trombone_safari.py --file-probe), so each company holds a copy as <company>/base.css and its pages link base.css. Change shared/base.css, then copy it to the three: the gate refuses a copy that differs (base-copy) and any load going up a folder (above-folder). Their look does not: each company has its own CSS on top. HTML has no include, so the footer is copied verbatim from shared/modele.html into each page and the gate compares bytes. To change its words, change every page in the same commit.

## ICON

each page links its tab icon in its head: <company>/img/icone.svg, icon.svg for the root (Simon on r19). A page without one logs a 404 on /favicon.ico and Best Practices drops to 96. To change an icon, read it at 16 px with python3 tools/icon_takes.py --shipped OUT_DIR.

## OPEN

double-click must work, so links are relative and name their file (merlin/index.html, never merlin/: over file:// a folder opens a listing). A page tested only through http.server can hide a broken file:// path: render_pages.py tests both.
