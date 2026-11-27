# #gobelin: the full notes behind its context pack

The pack in .atelier/packs.toml is the short index an agent reads first; this is what it
points to. Cut from the pack, word for word, on r109. Fix a line here in the same commit
as what makes it wrong.

## FILES

8 pages in gobelin/ (index, a-propos, equipe, organigramme, offre-emploi, communique, contact, connexion-discord), gobelin/gobelin.css, gobelin/base.css (a copy, see RULE in #shared). Domain: gobelin-hurlant.example. gobelin/connexion-discord.html is the trap page: it leaves the fiction on purpose (Simon, r3).

## NEW PAGE

copy shared/modele.html to gobelin/, then add gobelin.css after base.css and the icon, as its comment says. Render with tools/render_pages.py (see #shared).

## SURFACE

a public Discord and its fans, a publisher, a build under NDA, crunch worn as a badge. Different from Merlin: the money is not the prize here, the build and the accounts are.

## DATES

the plot's dates stay as they are after 13 Nov 2026, though students then read a milestone already past (Simon, r3 answer 2A): do not move or drop them. They also sit in a picture: BOARD_LINES in tools/gobelin_images.py, the same words as the alt text in gobelin/a-propos.html and gobelin/equipe.html.

## PICTURES

the .webp in gobelin/img/ come from tools/gobelin_images.py. make paints into ~/.cache/gobelin-images with the local ComfyUI, which whoever runs it starts (nice -n 15 python main.py in ~/ComfyUI) and stops after the batch. ship resizes that cache into gobelin/img/ and needs no ComfyUI. The model's lettering is always false: what must be read is pasted on by ship.

## BADGE

the 3D badge on gobelin/a-propos.html is CSS only, in gobelin/gobelin.css. After touching it, run python3 tools/check_badge.py and python3 tools/check_badge_browsers.py OUT: check_badge.py alone cannot see 3D, its matrices read the same with the 3D flattened (r59). Firefox paints nothing for background-clip: text on the element that carries the 3D transform, so the gold of .crunch sits on its inner span. Safari: tools/check_badge_safari.py.

## CLUES

the list is in r3's done note (atelier show r3 --full), never in this repo.
