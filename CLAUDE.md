# Entreprises fictives: agent guide

Three small static sites of invented companies, the OSINT kits of a social engineering
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
python3 tools/render_pages.py OUT index.html   # both file:// and http, 1280 and 390, pictures in OUT
python3 tools/check_trombone.py [OUT]   # Merlin's moving parts, which the renders freeze
python3 tests/test_render_pages.py             # two render runs at once each prove their own tree
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

Humour stays quiet (Simon, r4, 2026-11-02). Never explain a joke; a reader who misses it is
fine, it is for the ones who think. Say the fact and stop:
- Not "Dernière mise à jour : 2 novembre 2026 (la précédente datait de 2009)", but "Dernière
  mise à jour : 2 novembre 2009".
- Not "fait par mon neveu", but "Fait par Robert Courtepaille": the family name, on a company
  whose owner has another first name, lets a reader work out the rest.
- Cut a sentence where the company winks at its own absurdity (`Le stationnement est libre, le
  temps l'est aussi`). Nobody at that company would write it. What they would write straight
  can stay, however absurd (`Il ne sera pas joignable, n'ayant pas de téléphone`).
- A joke is an exaggeration of something relatable. It is funny once: `👏 1 (lui-même)` on every
  post is not a joke any more, and neither is an absurd title on every employee.
- Likes and hashtags belong to a social network. Use them only on a site that could have them
  (a notary's own site does not). Where they exist they follow real life: a woman gets more
  likes than a man, the young secretary too many. Subtle, dark, never explained.
- A clue goes where the company would put it for its own reasons. A table called "Qui signe
  quoi" is on the nose; the same fact in the org chart's boxes is not.
- A joke the reader cannot decode is not subtle, it is a miss (`goût des cartons`).
Do not try too hard.

## Traps

- Link `merlin/index.html`, never `merlin/`: over file:// a folder opens a listing.
- A dotted word in text reads as a domain (`fin.Le`, `M.Bob`): put the space in, the gate is right.
