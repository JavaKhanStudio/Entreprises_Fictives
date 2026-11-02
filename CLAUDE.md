# Entreprises fictives: agent guide

Three small static sites of invented companies, the OSINT kits of a social engineering
workshop. Read README.md first. Sub board of `social-engineering`. THIS REPO IS PUBLIC: what
you push is published.

## Stack

Plain HTML and CSS. No build step, no framework, no JS unless a ticket shows the need. Relative
links only, nothing fetched from outside (no CDN, no web font): a page also opens by
double-click on Windows, macOS and Linux. Students need a browser, nothing else.

## Run and test (planned, ticket 1 makes them real)

```bash
python3 -m http.server 8802             # then http://127.0.0.1:8802/
python3 tools/check_sites.py            # the gate: must pass before any push
```

## Rules the gate holds

- Every page: `<meta name="robots" content="noindex">` and the footer saying the site is
  fictional and educational.
- No form that collects anything, no `tel:` link, no external resource, no em dash.
- Domains are reserved `.example` ones, never a real TLD. No real company, person or phone
  number; a phone number comes from a range ARCEP reserves for fiction.
- No live link to a fictional domain: it is shown as text.

## Tone

A parody with a straight face: absurd self-given titles, a post liked only by its author. The
model is `~/Documents/GitHub/Social_Engineering_en_visuel/faux-president/js/i18n.js`,
`steps.research.site`. The clues stay usable: the joke never hides what an attacker would read.
All page text is in French. Simon reads every site before it counts as done.

## Traps
