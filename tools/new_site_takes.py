#!/usr/bin/env python3
"""The takes of r70: three candidate companies, one mock home page each.

    python3 tools/new_site_takes.py OUT_DIR

Writes take-A.png, take-B.png and take-C.png in OUT_DIR, at 1280 x 800, for
`atelier attach --stamp 1A`. Mock-ups only: the pages are built in memory and never join the
sites, so the gate does not walk them. They keep its rules anyway (no em dash, .example domains,
nothing fetched from outside), so that the words can be reused. Needs playwright.
"""

import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ABBAYE = """
<style>
body { margin: 0; background: #e9dcc0; color: #2b2118; font: 19px/1.5 Georgia, 'Liberation Serif', serif; }
.feuille { margin: 26px 70px; padding: 28px 48px; background: #f6edd8; min-height: 690px;
  border: 3px double #8a1f1a; outline: 10px solid #24406e; outline-offset: -18px; }
h1 { margin: 10px 0 0; font-size: 56px; font-weight: 400; color: #8a1f1a; text-align: center;
  letter-spacing: .04em; font-variant: small-caps; }
.sous { text-align: center; color: #24406e; font-style: italic; margin: 0 0 12px; }
nav { text-align: center; font-variant: small-caps; color: #8a1f1a; border-block: 1px solid #b8963a;
  padding: 4px 0; margin-bottom: 20px; }
.cols { display: grid; grid-template-columns: 2fr 1fr; gap: 40px; }
.lettrine { float: left; font-size: 92px; line-height: 76px; padding: 8px 10px 6px; margin: 4px 12px 0 0;
  color: #f3d77a; background: #8a1f1a; border: 3px solid #b8963a; }
aside { border-left: 2px solid #b8963a; padding-left: 24px; font-size: 17px; }
aside h2 { margin: 0 0 6px; font-size: 20px; font-weight: 400; font-variant: small-caps; color: #8a1f1a; }
table { border-collapse: collapse; width: 100%; }
td { padding: 1px 0; } td + td { text-align: right; }
.sign { margin-top: 18px; font-style: italic; }
</style>
<div class=feuille>
<h1>Abbaye Saint-Tacite</h1>
<p class=sous>Fromages et bières de moines depuis 1132 · Exportés dans 41 pays</p>
<nav>L’Abbaye · La Communauté · Le Fromage · Export · Presse · Écrire aux frères</nav>
<div class=cols><div>
<p><span class=lettrine>O</span>nze moines vivent ici selon la règle, dans la prière et le travail.
Le travail a dégagé 9,2 M€ de chiffre d’affaires en 2025. Les frères ne possèdent rien.</p>
<p>La communauté observe le silence. Elle ne répond pas au téléphone. Toute commande, toute
facture, toute demande s’adresse par courriel à freres@abbaye-saint-tacite.example et reçoit
réponse entre None et Vêpres.</p>
<p class=sign>Frère Hilarion, Cellérier et Directeur Export.<br>Obéit au Père Abbé depuis 1988.</p>
</div><aside>
<h2>Horaires de la communauté</h2>
<table>
<tr><td>Vigiles</td><td>4 h 00</td></tr>
<tr><td>Laudes</td><td>7 h 00</td></tr>
<tr><td>Messe</td><td>9 h 30</td></tr>
<tr><td>Sexte</td><td>12 h 15</td></tr>
<tr><td>None</td><td>14 h 00</td></tr>
<tr><td>Vêpres</td><td>17 h 30</td></tr>
<tr><td>Complies</td><td>20 h 00</td></tr>
</table>
<h2 style="margin-top:16px">À la une</h2>
Le Père Abbé part à Rome pour trois semaines. Il donnera ses ordres par écrit.
</aside></div></div>
"""

BARBEZANGE = """
<style>
body { margin: 0; font: 18px/1.45 Georgia, 'Liberation Serif', serif; }
.deux { display: grid; grid-template-columns: 1fr 14px 1fr; height: 660px; }
.elle { background: #f4ead2; color: #3c2a14; padding: 26px 40px; }
.mur { background: repeating-linear-gradient(0deg, #8d8478 0 18px, #6e665b 18px 20px); }
.lui { background: #a51f14; color: #fff6e6; padding: 26px 40px;
  font-family: 'Liberation Sans', Arial, sans-serif; }
h1 { margin: 0; font-size: 42px; line-height: 1.1; }
.elle h1 { font-weight: 400; font-style: italic; }
.lui h1 { font-weight: 800; text-transform: uppercase; letter-spacing: .02em; }
nav { font-size: 15px; margin: 8px 0 26px; opacity: .85; }
.slogan { font-size: 30px; line-height: 1.2; margin: 0 0 22px; }
.lui .slogan { font-weight: 700; }
.ident { font-size: 16px; margin-top: 22px; padding-top: 12px; border-top: 1px solid currentColor; }
.commun { height: 140px; box-sizing: border-box; padding: 26px; background: #2f2a24; color: #eee3cc;
  text-align: center; font-family: 'Liberation Sans', Arial, sans-serif; font-size: 17px; }
</style>
<div class=deux>
<section class=elle>
<h1>Conserves Barbezange</h1>
<nav>La Maison · Le Cassoulet · Direction · Fournisseurs · Contact</nav>
<p class=slogan>Le vrai cassoulet.<br>Sans tomate. Depuis 1921.</p>
<p>Mme Odile Barbezange, Directrice Générale :<br>« Je n’ai pas de frère à la direction. »</p>
<p class=ident>Seule adresse officielle : barbezange.example<br>
Factures : compta@barbezange.example</p>
</section>
<div class=mur></div>
<section class=lui>
<h1>Conserves Barbezange</h1>
<nav>La Maison · Le Cassoulet · Direction · Fournisseurs · Contact</nav>
<p class=slogan>Le vrai cassoulet.<br>Avec tomate. Depuis 1921.</p>
<p>M. Régis Barbezange, Directeur Général :<br>« Ma sœur ne travaille pas ici. Son bureau est de
l’autre côté du mur. »</p>
<p class=ident>Seule adresse officielle : barbezange-authentique.example<br>
Factures : compta@barbezange-authentique.example</p>
</section>
</div>
<div class=commun>Mme Pélagie Roumégous, Secrétaire des Deux Directions, transmet depuis 1994.<br>
Merci de ne pas lui demander ce que l’autre a répondu.</div>
"""

SERPILLIA = """
<style>
body { margin: 0; background: #0d1420; color: #dbe7f5; font: 17px/1.45 'Liberation Sans', Arial, sans-serif; }
header { display: flex; justify-content: space-between; align-items: baseline; padding: 20px 44px;
  border-bottom: 1px solid #24344a; }
.marque { font-size: 26px; font-weight: 700; color: #6ff2c5; }
nav { color: #8ea3bd; font-size: 15px; }
main { padding: 30px 44px; }
h1 { margin: 0 0 6px; font-size: 44px; line-height: 1.1; color: #fff; }
.sous { color: #8ea3bd; margin: 0 0 24px; }
.tuiles { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px; }
.tuile { background: #152133; border: 1px solid #24344a; border-radius: 10px; padding: 14px 20px; }
.tuile b { display: block; font-size: 38px; color: #6ff2c5; }
.fil { background: #152133; border: 1px solid #24344a; border-radius: 10px; padding: 14px 20px;
  font: 15.5px/1.75 'Liberation Mono', monospace; }
.fil span { color: #6ff2c5; }
</style>
<header><div class=marque>Serpillia</div>
<nav>Plateforme · Nos agents · Humain · Recrutement · Presse</nav></header>
<main>
<h1>Le nettoyage industriel, sans humain dans la boucle.</h1>
<p class=sous>Bureaux, entrepôts, cliniques. Toute l’entreprise est pilotée par nos agents autonomes.</p>
<div class=tuiles>
<div class=tuile><b>31</b>agents</div>
<div class=tuile><b>24 000 m²</b>nettoyés par nuit</div>
<div class=tuile><b>1</b>Kévin</div>
</div>
<div class=fil>
<span>03:12</span> Agent Compta a payé une facture reçue à 03:11. Motif : demande polie.<br>
<span>03:12</span> Kévin a validé.<br>
<span>22:00</span> Agent Planning a affecté Kévin aux étages 3, 7 et 12, de 22:00 à 22:30.<br>
<span>21:40</span> Agent RH a nommé Kévin employé du mois.<br>
<span>21:39</span> Agent Com a publié : « Fiers de notre équipe. »<br>
<span>hier</span> Kévin a validé 1 412 actions, en 0,8 s chacune.
</div>
</main>
"""

TAKES = {"A": ABBAYE, "B": BARBEZANGE, "C": SERPILLIA}


def french_spaces(page):
    """The non-breaking spaces French puts before : and inside guillemets, in the text only."""
    style, text = page.split("</style>")
    text = re.sub(r" ([:;?!»])", " \\1", text).replace("« ", "« ")
    return style + "</style>" + text


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        for letter, words in TAKES.items():
            assert "—" not in words, f"{letter}: em dash"
            page.set_content("<!doctype html><html lang=fr><meta charset=utf-8>" + french_spaces(words))
            page.screenshot(path=out / f"take-{letter}.png")
            print(out / f"take-{letter}.png")
        browser.close()


if __name__ == "__main__":
    main()
