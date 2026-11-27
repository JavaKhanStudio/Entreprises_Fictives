# #merlin: the full notes behind its context pack

The pack in .atelier/packs.toml is the short index an agent reads first; this is what it
points to. Cut from the pack, word for word, on r109. Fix a line here in the same commit
as what makes it wrong.

## FILES

7 pages in merlin/ (index, a-propos, equipe, organigramme, offre-emploi, communique, contact), merlin/merlin.css, merlin/merlin.js, merlin/base.css (a copy, see RULE in #shared). Domain: papeterie-merlin.example.

## NEW PAGE

copy shared/modele.html to merlin/, then add merlin.css after base.css and the icon, as its comment says. Render with tools/render_pages.py (see #shared).

## CANON

~/Documents/GitHub/Social_Engineering_en_visuel/faux-president/js/i18n.js, steps.research (the page on Eve's laptop): since 1987, 12 followers, Mme Merlin "Presidente Executive Principale" always travelling, Alice "Directrice des Directions" Bob's boss, Bob "Ninja des virements" the accountant, conquering abroad, #PapierAgile. The capsule reuses these names: the site must not contradict them. faux-president/sources.md says what is invented there.

ATTACK SURFACE TO KEEP, from the Lumisol sample (~/Documents/Claude_GDrive_HQ/boards/social-engineering/verif/r32/kit.py, company dropped by Simon): an address format, a client portal, supplier invoices by PDF mail, a recent hire in accounting, a lone overworked IT person mid migration to Microsoft 365, a payment threshold, a press release naming a contract. Do not reuse from it: the 02 40 number, PayFlow, Claire Fontaine, Thomas Berger, Karim Haddad, Saint-Herblain.

## LOOK

Simon on r2: more real, more professional, and the company would vibe-code its site. So a generated-landing-page look (dark bands, one gradient, glass header, cards). Its jokes stay quiet: nothing on the site says the clip is useless.

## SCRIPT

merlin/merlin.js is the one JS of the sites: the WebGL clip with no library, counters, reveals. A classic script, because file:// refuses modules. Every word stays in the HTML, and merlin/img/trombone-3d.svg shows without WebGL or JS. The clip is a tube swept along the same path as merlin/img/trombone.svg.

## NO GPU

where WebGL's renderer names software, sansGpu() in merlin/merlin.js draws the clip without antialiasing, at 1x pixels and 30 frames a second (Simon on r55). Lighthouse's Chrome is such a machine, so its Merlin score measures this path, not what a student with a GPU sees. That score follows the machine's load: 99 to 100 at a load average near 25, 68 to 81 above 60, so read uptime before calling it a regression. check_trombone.py proves the cheap path, check_trombone_browsers.py the full one.

## MOTION

tools/render_pages.py renders under reduced motion, so its pictures show the clip standing still. python3 tools/check_trombone.py checks what moves, the two fallbacks, and overflow at 8 widths. Run it when merlin.js or merlin.css changes.
