# #inviolia: the full notes behind its context pack

The pack in .atelier/packs.toml is the short index an agent reads first; this is what it
points to. Cut from the pack, word for word, on r109. Fix a line here in the same commit
as what makes it wrong.

## FILES

7 pages in inviolia/ (index, a-propos, equipe, organigramme, offre-emploi, communique, contact), inviolia/inviolia.css, inviolia/inviolia.js, inviolia/base.css (a copy, see RULE in #shared). Domain: inviolia.example.

## NEW PAGE

copy shared/modele.html to inviolia/, then add inviolia.css after base.css and the icon, as its comment says, and inviolia.js after them. Render with tools/render_pages.py (see #shared).

## GENRE

a security vendor that sells fear: hood, glowing globe, threat level always critical. Simon saw the Guy Fawkes mask the model painted on pirate and kept the picture. The words of inviolia/index.html start from his pick on r70, INVIOLIA in tools/new_site_takes.py.

## SURFACE

a vendor holding admin access to its clients, and staff used to fake emails.

## PICTURES

the .webp in inviolia/img/ come from tools/inviolia_images.py: make paints into ~/.cache/inviolia-images with the local ComfyUI, ship resizes into inviolia/img/. pirate and globe come from tools/new_site_images.py. The model's lettering is always false, so no word sits in a picture.

## MOTION

inviolia/inviolia.js (a classic script in the head) sets html.vivant and each block's --p from the scroll; inviolia.css moves things only under .vivant, so without the script or under reduced motion the page stands still and every word is in the HTML. Stops are hand hooks, data-stop in the pages (Simon on r75, the gentle locking of ficelle-site r67). Render pictures freeze all this: python3 tools/check_inviolia.py [OUT] proves it in Chrome and Firefox, tools/check_inviolia_safari.py on a macOS runner. LIVE MAP (r78, r90): the same script climbs the counter at the rate its words give (4 812 336 a day), rolls the feed by CSS order, and paints neon comets on a canvas over the globe, Simon's pick on r90; none of it runs off screen. The line that leaves comes back as a new one: its clock later than the last, its target and attack both from the HTML's own lines, its pair not on screen, so the page's six lines are all the words the feed can use. tools/inviolia_live_takes.py holds the takes he chose from. The counter and the feed's clock start at the written values on each load.

## DATES

staff posts run from September to November 2026, the press release is 20 October 2026, and the migration it announces is 11 to 15 January 2027. Pages agree on 147 clients, 8 staff, 2017, 212 podcast episodes.

## CLUES

the list is in r75's done note (atelier show r75 --full), never in this repo.
