# #source-eclat: the full notes behind its context pack

The pack in .atelier/packs.toml is the short index an agent reads first; this is what it
points to. Cut from the pack, word for word, on r109. Fix a line here in the same commit
as what makes it wrong.

## FILES

7 pages in source-eclat/ (index, a-propos, equipe, organigramme, offre-emploi, communique, contact), source-eclat/source-eclat.css, source-eclat/source-eclat.js, source-eclat/base.css (a copy, see RULE in #shared). Domain: source-et-eclat.example.

## NEW PAGE

copy shared/modele.html to source-eclat/, then add source-eclat.css after base.css and the icon, as its comment says. Render with tools/render_pages.py (see #shared).

## START

the mock-up Simon chose on r70: SOURCE in tools/new_site_takes.py, its pictures plage and eau in tools/new_site_images.py. Read "A new company" in CLAUDE.md first.

## GENRE

multi-level marketing: sunset, countdown, rank ladder. Its voice is the nearest to merlin/equipe.html's posts: read them, and do not reuse a joke of theirs.

## SURFACE

a weekly message forwarded unchanged down the line, and money paid to a sponsor by a RIB sent in a message.

## SCRIPT

source-eclat/source-eclat.js only moves the countdown of the top band; it restarts at every page load, on purpose, as such timers do, and stands still under reduced motion, so render_pages.py compares one picture. Every word is in the HTML. No page says it restarts. python3 tools/check_source_eclat.py checks what moves, the numbers below and overflow at 8 widths.

## PICTURES

the .webp in source-eclat/img/ come from tools/source_eclat_images.py. make paints into ~/.cache/source-eclat-images with the local ComfyUI (see #gobelin's PICTURES), ship resizes into source-eclat/img/. plage and eau are the mock-up's, from ~/.cache/new-site-takes; Marie-Ange's portrait is cropped out of plage, so one face. The model's lettering is false, so no picture holds text to read.

## NUMBERS

the pages agree: 1+3+14+61+412+8679 = 9 170 Ambassadors, and the ladder's monthly incomes multiply out to the 5,8 M euros of commissions a year (a-propos, communique). Change one, change them all. The chain's hours on organigramme.html are the hours in Christelle's and Didier's posts.

## CLUES

the list is in r76's done note (atelier show r76 --full), never in this repo.
