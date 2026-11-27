# #courtepaille: the full notes behind its context pack

The pack in .atelier/packs.toml is the short index an agent reads first; this is what it
points to. Cut from the pack, word for word, on r109. Fix a line here in the same commit
as what makes it wrong.

## FILES

7 pages in courtepaille/ (index, a-propos, equipe, organigramme, recrutement, communique, contact), courtepaille/courtepaille.css, courtepaille/base.css (a copy, see RULE in #shared). Domain: etude-courtepaille.example.

## NEW PAGE

copy shared/modele.html to courtepaille/, then add courtepaille.css after base.css and the icon, as its comment says. Render with tools/render_pages.py (see #shared).

## SURFACE

large property transfers, elderly clients, paper first, a website that looks its age. Simon kept the name (2026-11-02) though Courtepaille is also a restaurant chain: the site says nothing of restaurants.

## PICTURES

the portraits and the seal are SVG. The home page's photograph is courtepaille/img/facade-photo.jpg, painted and aged by tools/courtepaille_images.py, deliberately small and poor (Simon, r68). The counter's number on index.html links img/facade.svg with no look of a link: an easter egg, not a leftover.

## DATES

no year in the plot, it runs as a yearly habit (Simon, r4). The pages agree on: 16 novembre au 4 décembre, grandes ventes signed the troisième vendredi de décembre at 15 h, pli RIB three weeks before, funds the Friday before, successor the premier lundi de janvier. A duration never sits beside its start year (41 ans, no 1985). The footer reads "Dernière mise à jour : 2 novembre 2026 (la précédente datait de 2009)": Simon took back his flat 2009 on r86, so leave the bracket. No page says neveu: the surname says it. No real notary's name, checked by search: the public directory is https://www.notaires.fr/fr/directory.
