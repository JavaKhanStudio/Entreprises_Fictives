#!/usr/bin/env python3
"""The takes of r70, second round: three candidate companies, one full home page each.

    python3 tools/new_site_images.py          # first, the pictures, into ~/.cache/new-site-takes
    python3 tools/new_site_takes.py OUT_DIR

Writes take-A.png, take-B.png and take-C.png in OUT_DIR, full page at 1280, for
`atelier attach --stamp 1A`. Each has a plain band on top, where the stamp lands, so that it
covers no word of the page: on the first round the stamps sat on the names. The pages are built
in OUT_DIR and never join the sites, so the gate does not walk them. They keep its rules anyway
(no em dash, .example domains, nothing fetched from outside), so that the words can be reused.
Needs playwright and Pillow. Round one is in this file's history, at 9a0a735.
"""

import re
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

RAW = Path.home() / ".cache" / "new-site-takes"
BAND = 140

INVIOLIA = """
<style>
* { box-sizing: border-box; }
body { margin: 0; background: #060b16; color: #dbe6f5; font: 16px/1.55 Inter, sans-serif; }
.alerte { display: flex; justify-content: space-between; padding: 7px 64px; background: #b3101e; color: #fff;
  font: 600 13px/1.4 Inter, sans-serif; letter-spacing: .04em; }
.alerte i { display: inline-block; width: 9px; height: 9px; margin-right: 8px; border-radius: 50%; background: #fff;
  box-shadow: 0 0 10px 3px #ff8a94; }
header { display: flex; align-items: center; gap: 28px; padding: 16px 64px; border-bottom: 1px solid #16233b; }
.logo { display: flex; align-items: center; gap: 10px; margin-right: auto; font: 800 24px/1 Montserrat, Inter, sans-serif;
  letter-spacing: .14em; color: #fff; }
.logo small { display: block; margin-top: 4px; font: 500 10px/1 Inter, sans-serif; letter-spacing: .1em; color: #52e0ff; }
header a { color: #9db1cc; font-size: 14px; }
.cta { padding: 9px 16px; border-radius: 4px; background: #00c2ff; color: #04121f; font-weight: 700; font-size: 14px; }
.hero { display: grid; grid-template-columns: 1fr 1fr; align-items: center; min-height: 480px;
  background: linear-gradient(90deg, #060b16 45%, transparent 75%), url(%RAW%/pirate.png) right center / auto 100% no-repeat; padding: 0 64px; }
h1 { margin: 0 0 18px; color: #fff; font: 800 50px/1.08 Montserrat, Inter, sans-serif; letter-spacing: -.01em; }
.hero p { margin: 0 0 26px; color: #a9bbd4; font-size: 18px; }
.btns span { display: inline-block; margin-right: 10px; padding: 13px 20px; border-radius: 4px; font-weight: 700; }
.b1 { background: #00c2ff; color: #04121f; } .b2 { border: 1px solid #39506f; color: #dbe6f5; }
.chiffres { display: grid; grid-template-columns: repeat(4, 1fr); border-block: 1px solid #16233b; background: #0a1322; }
.chiffres div { padding: 24px 28px 22px 64px; border-right: 1px solid #16233b; color: #8ea3bf; font-size: 14px; }
.chiffres div + div { padding-left: 28px; }
.chiffres b { display: block; color: #fff; font: 800 30px/1.2 Montserrat, Inter, sans-serif; }
.chiffres .rouge { color: #ff4d5e; }
.carte { display: grid; grid-template-columns: 500px 1fr; gap: 48px; align-items: center; padding: 56px 64px; }
.carte img { width: 500px; height: 420px; object-fit: cover; border-radius: 10px; box-shadow: 0 0 80px #0a4d7a; }
h2 { margin: 0 0 8px; color: #fff; font: 700 28px/1.2 Montserrat, Inter, sans-serif; }
.flux { margin-top: 18px; border: 1px solid #16233b; border-radius: 8px; font: 13px/1.9 'DejaVu Sans Mono', monospace; color: #9db1cc; padding: 12px 18px; background: #0a1322; }
.flux b { float: right; color: #39e58c; font-weight: 400; }
.preuves { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; padding: 0 64px 48px; }
.preuves div { padding: 20px; border: 1px solid #1c2c49; border-top: 3px solid #00c2ff; border-radius: 6px; background: #0a1322; font-size: 15px; color: #b5c5da; }
.preuves h3 { margin: 0 0 8px; color: #fff; font-size: 16px; }
.bas { display: grid; grid-template-columns: 1.1fr 1fr; gap: 40px; padding: 40px 64px 56px; background: #0a1322; border-top: 1px solid #16233b; }
blockquote { margin: 0; color: #fff; font: 600 23px/1.35 Montserrat, Inter, sans-serif; }
cite { display: block; margin-top: 14px; color: #8ea3bf; font: 15px/1.5 Inter, sans-serif; }
.post { padding: 18px 20px; border-radius: 8px; background: #fff; color: #1b1f24; font-size: 15px; }
.post b { display: block; } .post small { color: #667; } .post p { margin: 10px 0; } .post .tag { color: #0a66c2; }
.clients { padding: 34px 64px 44px; text-align: center; color: #5f7696; font: 700 15px/2 Montserrat, sans-serif; }
.clients h2 { font-size: 20px; margin-bottom: 14px; }
</style>
<div class=alerte><span><i></i>NIVEAU DE MENACE ACTUEL : CRITIQUE</span><span>Cellule de crise 24/7 · Standard de 9 h à 17 h</span></div>
<header><div class=logo><svg width=34 height=40 viewBox="0 0 34 40"><path d="M17 1 33 7v13c0 10-7 16-16 19C8 36 1 30 1 20V7z" fill=#0a2a44 stroke=#00c2ff stroke-width=2 /><path d="M11 18v-4a6 6 0 0 1 12 0v4M9 18h16v11H9z" fill=none stroke=#fff stroke-width=2 /></svg><div>INVIOLIA<small>CYBER-RÉSILIENCE SOUVERAINE</small></div></div>
<a>Solutions</a><a>Experts</a><a>Organigramme</a><a>Carrières</a><a>Presse</a><a>Contact</a><span class=cta>Suis-je déjà piraté ?</span></header>
<section class=hero><div><h1>Vous avez déjà été piratés. Vous ne le savez pas encore.</h1>
<p>Inviolia protège 147 entreprises et collectivités avec Sentinelle Quantique™, sa plateforme Zero Trust de grade militaire, pilotée par l’IA.</p>
<div class=btns><span class=b1>Demander un audit gratuit</span><span class=b2>Télécharger le livre blanc</span></div></div></section>
<section class=chiffres>
<div><b class=rouge>4 812 336</b>attaques bloquées aujourd’hui</div>
<div><b>147</b>clients sous protection</div>
<div><b>6 min</b>pour prendre la main sur tout votre parc</div>
<div><b>2017</b>dernière intrusion détectée</div></section>
<section class=carte><img src="%RAW%/globe.png" alt=""><div>
<h2>Les cyberattaques, en temps réel</h2>
<p>Sentinelle Quantique™ voit tout.</p>
<div class=flux>
03:12:08 · Inconnu → France · Rançongiciel quantique <b>BLOQUÉE</b><br>
03:12:09 · Inconnu → Vos données · Hameçonnage IA <b>BLOQUÉE</b><br>
03:12:11 · Inconnu → Votre secteur · Menace persistante <b>BLOQUÉE</b><br>
03:12:14 · Inconnu → Votre PDG · Menace avancée <b>BLOQUÉE</b><br>
03:12:08 · Inconnu → France · Rançongiciel quantique <b>BLOQUÉE</b><br>
03:12:09 · Inconnu → Vos données · Hameçonnage IA <b>BLOQUÉE</b></div></div></section>
<section class=preuves>
<div><h3>Prise en main</h3>Pour démarrer, envoyez-nous vos accès administrateur par courriel, dans un ZIP chiffré. Le mot de passe suit dans un second courriel.</div>
<div><h3>Culture sécurité</h3>Chaque mois, nos collaborateurs reçoivent un faux courriel de notre part. Qui clique est formé dans la semaine.</div>
<div><h3>Certification</h3>ISO 27001 : en cours depuis 2019.</div>
<div><h3>Zero Trust</h3>Aucun collaborateur n’entre sans son badge. Les badges sont à l’accueil.</div></section>
<section class=bas><div><blockquote>« La question n’est pas de savoir si vous serez attaqué, mais quand. Nous vous dirons quand. »</blockquote>
<cite>Jean-Marc Ganivet, Président-Fondateur et Évangéliste de la Menace. Vingt ans à la Défense.</cite></div>
<div class=post><b>Steven Morvan</b><small>Analyste SOC Niveau 3 chez Inviolia</small>
<p>Formé pour la 11e fois cette année. On n’a jamais fini d’apprendre. <span class=tag>#HumanFirewall</span></p><small>👍 3</small></div></section>
<section class=clients><h2>Ils dorment tranquilles</h2>Clinique du Val-Fleuri · Mutuelle des Hauts-Cantons · Transports Rabouillet · Coopérative du Plateau · Ville de Saint-Ombrage · Caisse des Marais</section>
"""

SOURCE = """
<style>
* { box-sizing: border-box; }
body { margin: 0; background: #fbf6f1; color: #4a3a3a; font: 16px/1.6 Inter, sans-serif; }
.compte { padding: 8px; background: linear-gradient(90deg, #b9825f, #e5b98f, #b9825f); color: #fff; text-align: center; font-weight: 600; font-size: 14px; }
.compte b { margin: 0 3px; padding: 2px 6px; border-radius: 4px; background: #fff; color: #a26a48; }
header { display: flex; align-items: center; gap: 26px; padding: 18px 64px; background: #fff; }
.logo { margin-right: auto; color: #a26a48; font: italic 400 33px/1 'Liberation Serif', Georgia, serif; letter-spacing: .01em; }
header a { font-size: 14px; color: #7a6660; }
.cta { padding: 10px 22px; border-radius: 30px; background: #c98f6c; color: #fff; font-weight: 600; font-size: 14px; }
.hero { position: relative; height: 560px; background: linear-gradient(90deg, #fbf6f1 36%, transparent 58%), url(%RAW%/plage.png) right center / auto 100% no-repeat, #fbf6f1; }
.hero div.txt { position: absolute; left: 64px; top: 92px; width: 520px; }
h1 { margin: 0 0 14px; color: #6f4630; font: italic 400 48px/1.1 'Liberation Serif', Georgia, serif; }
.hero p { margin: 0 0 22px; font-size: 17px; }
.btn { display: inline-block; margin-right: 8px; padding: 12px 22px; border-radius: 30px; background: #c98f6c; color: #fff; font-weight: 600; }
.btn.b { background: none; color: #a26a48; box-shadow: inset 0 0 0 1px #c98f6c; }
.toast { position: absolute; right: 40px; bottom: 34px; display: flex; gap: 12px; align-items: center; padding: 12px 18px; border-radius: 14px; background: #fff; box-shadow: 0 10px 30px rgba(90,50,30,.25); font-size: 14px; }
.toast i { width: 34px; height: 34px; border-radius: 50%; background: radial-gradient(circle at 35% 30%, #fff, #7fb1e6 45%, #2b5fa8); }
.toast small { display: block; color: #a08d85; }
section { padding: 56px 64px; }
h2 { margin: 0 0 8px; color: #6f4630; text-align: center; font: italic 400 36px/1.15 'Liberation Serif', Georgia, serif; }
.chapo { margin: 0 auto 30px; max-width: 640px; text-align: center; color: #7a6660; }
.arbre { background: #fff; }
.rang { display: grid; grid-template-columns: 1fr 760px 1fr; align-items: center; margin: 3px 0; }
.rang > span:last-child { padding-left: 16px; color: #8d7a72; font-size: 14px; }
.rang > span:first-child { padding-right: 16px; text-align: right; color: #8d7a72; font-size: 14px; }
.rang div { margin: auto; padding: 9px 0; border-radius: 4px; color: #fff; text-align: center; font-weight: 600; white-space: nowrap; }
.prod { display: grid; grid-template-columns: 460px 1fr; gap: 50px; align-items: center; }
.prod img { width: 460px; height: 400px; object-fit: cover; object-position: center 80%; border-radius: 20px; }
.prod h2, .dup h2 { text-align: left; }
.prix { margin: 14px 0; padding: 18px 22px; border-radius: 14px; background: #fff; box-shadow: 0 4px 18px rgba(120,80,50,.1); }
.posts { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; background: #f4e9e0; }
.posts h2 { grid-column: 1 / -1; margin-bottom: 12px; }
.posts article { padding: 20px; border-radius: 14px; background: #fff; }
.posts b { display: block; color: #6f4630; } .posts small { color: #a08d85; }
.posts p { margin: 10px 0; } .coeur { color: #d0556f; font-weight: 600; font-size: 14px; }
.dup { display: grid; grid-template-columns: 1fr 1fr; gap: 50px; background: #fff; }
.dup .cadre { padding: 22px 24px; border-radius: 14px; border: 1px dashed #c98f6c; font-style: italic; }
</style>
<div class=compte>Pack Démarrage à −20 % : plus que <b>02</b> j <b>14</b> h <b>37</b> min</div>
<header><div class=logo>Source &amp; Éclat</div><a>Notre histoire</a><a>L’Eau Alignée</a><a>L’Arbre de Réussite</a><a>Témoignages</a><a>Rejoindre</a><span class=cta>Je change de vie</span></header>
<section class=hero style="padding:0"><div class=txt><h1>Et si vous deveniez enfin la PDG de votre vie ?</h1>
<p>Rejoignez nos 9 170 Ambassadrices et Ambassadeurs indépendants. Depuis chez eux, sans patron, sans horaires, sans limite.</p>
<span class=btn>Je découvre l’opportunité</span><span class="btn b">Parler à ma marraine</span></div>
<div class=toast><i></i><div><b>Sandrine vient de passer Saphir</b><small>il y a 4 minutes</small></div></div></section>
<section class=arbre><h2>Notre Arbre de Réussite</h2><p class=chapo>Chacune et chacun monte à son rythme. Revenus mensuels moyens déclarés en 2025.</p>
<div class=rang><span>1</span><div style="width:190px;background:#6f4630">Diamant Royal</div><span>118 000 €</span></div>
<div class=rang><span>3</span><div style="width:280px;background:#85573c">Double Diamant</div><span>31 000 €</span></div>
<div class=rang><span>14</span><div style="width:370px;background:#a26a48">Diamant</div><span>6 200 €</span></div>
<div class=rang><span>61</span><div style="width:480px;background:#b9825f">Rubis</div><span>940 €</span></div>
<div class=rang><span>412</span><div style="width:610px;background:#c98f6c">Saphir</div><span>85 €</span></div>
<div class=rang><span>8 679</span><div style="width:760px;background:#ddb394">Perle</div><span>11 €</span></div></section>
<section class=prod><img src="%RAW%/eau.png" alt=""><div><h2>L’Eau Alignée</h2>
<p>Six bouteilles, 89 €. Puisée à une source que nous ne divulguons pas, alignée à la main, prête à partager.</p>
<div class=prix><b>Pack Démarrage Éclat : 1 490 €</b><br>120 bouteilles, votre kit de partage et votre rang de Perle. À régler par virement à votre marraine, qui vous transmet son RIB par message.</div>
<p>Vos commissions sont versées le 5 du mois sur le RIB envoyé à commissions@source-et-eclat.example.</p></div></section>
<section class=posts><h2>Elles et ils rayonnent</h2>
<article><b>Marie-Ange Sauvaire</b><small>Diamant Royal · Fondatrice et Première Source</small><p>Ce matin, j’ai remercié mon ancien patron. De tout cœur. #LibreEtAlignée</p><span class=coeur>♥ 4 812</span></article>
<article><b>Sandrine</b><small>Saphir · Marraine de 14 belles âmes</small><p>Merci à ma marraine, qui a cru en moi avant ma banque. #Saphir</p><span class=coeur>♥ 212</span></article>
<article><b>Didier</b><small>Perle depuis 3 mois</small><p>Mon garage est plein, mon cœur aussi. #Abondance</p><span class=coeur>♥ 3</span></article></section>
<section class=dup><div><h2>La Duplication</h2><p>Un message qui marche ne se réécrit pas : il se duplique. Chaque lundi, Marie-Ange adresse son Message de la Semaine à ses Double Diamant. Chacune et chacun le transfère à sa lignée, sans y changer une virgule. À midi, 9 170 personnes l’ont lu.</p></div>
<div class=cadre>« Ma belle lumière, ne cherche pas à comprendre ce lien, ton cœur sait déjà. Transfère avant midi. »<br><br>Message de la Semaine, lundi dernier</div></section>
"""

DERNIER = """
<style>
* { box-sizing: border-box; }
body { margin: 0; background: #f1f1f1; color: #222; font: 15px/1.4 'Liberation Sans', Arial, sans-serif; }
.promo { padding: 8px; background: #d4001a; color: #fff; text-align: center; font-weight: 700; font-size: 16px; letter-spacing: .02em; }
header { display: flex; align-items: center; gap: 24px; padding: 14px 40px; background: #ffd400; }
.logo { padding: 6px 14px; background: #111; color: #ffd400; font: 900 28px/1 Montserrat, Arial, sans-serif; transform: skew(-8deg); white-space: nowrap; }
.logo small { display: block; margin-top: 3px; color: #fff; font: 700 10px/1 Arial, sans-serif; letter-spacing: .08em; }
.cherche { flex: 1; display: flex; border: 2px solid #111; background: #fff; }
.cherche span { flex: 1; padding: 10px 14px; color: #777; }
.cherche b { padding: 10px 20px; background: #111; color: #ffd400; }
.panier { font-weight: 700; white-space: nowrap; }
nav { display: flex; gap: 26px; padding: 10px 40px; background: #111; color: #fff; font-weight: 700; font-size: 14px; }
nav .x { color: #ffd400; }
.hero { position: relative; display: grid; grid-template-columns: 1fr 1fr; align-items: center; height: 450px; padding: 0 40px; overflow: hidden; background: #fff; border-bottom: 6px solid #d4001a; }
.hero > img { position: absolute; right: 0; top: 0; height: 100%; width: 660px; object-fit: cover; -webkit-mask-image: linear-gradient(90deg, transparent, #000 16%); }
.hero > div:first-child { position: relative; z-index: 1; }
h1 { margin: 0 0 10px; color: #d4001a; font: 900 80px/.95 Montserrat, Arial, sans-serif; letter-spacing: -.03em; text-transform: uppercase; }
.hero p { margin: 0 0 20px; font-size: 20px; font-weight: 700; }
.go { display: inline-block; padding: 14px 26px; background: #d4001a; color: #fff; font-weight: 900; font-size: 18px; }
.go.c { margin-left: 8px; background: #111; color: #ffd400; }
.burst { position: absolute; right: 54px; top: 22px; width: 190px; height: 190px; display: grid; place-items: center; text-align: center; background: #ffd400; color: #d4001a; font: 900 22px/1 Montserrat, Arial, sans-serif; transform: rotate(-10deg);
  clip-path: polygon(50% 0,59% 12%,71% 4%,75% 18%,89% 15%,87% 29%,100% 34%,92% 45%,100% 56%,88% 62%,91% 76%,77% 77%,73% 91%,60% 85%,50% 100%,40% 85%,27% 91%,23% 77%,9% 76%,12% 62%,0 56%,8% 45%,0 34%,13% 29%,11% 15%,25% 18%,29% 4%,41% 12%); }
.burst b { display: block; font-size: 40px; white-space: nowrap; }
.rassure { display: grid; grid-template-columns: repeat(4, 1fr); background: #111; color: #fff; text-align: center; font-weight: 700; }
.rassure div { padding: 12px; border-right: 1px solid #444; } .rassure b { color: #ffd400; }
section { padding: 30px 40px; }
h2 { margin: 0 0 16px; padding-left: 12px; border-left: 8px solid #d4001a; font: 900 25px/1.1 Montserrat, Arial, sans-serif; text-transform: uppercase; }
.grille { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
.fiche { position: relative; padding: 14px; background: #fff; border: 1px solid #ddd; }
.fiche img { display: block; width: 100%; height: 170px; object-fit: contain; }
.fiche h3 { margin: 8px 0 3px; font-size: 16px; }
.etoiles { color: #e59a00; font-size: 14px; } .etoiles small { color: #666; }
.barre { color: #777; text-decoration: line-through; margin-right: 6px; }
.prixf { margin: 5px 0; color: #d4001a; font: 900 34px/1 Montserrat, Arial, sans-serif; }
.stock { color: #c04000; font-weight: 700; font-size: 13px; }
.ajout { margin-top: 8px; padding: 9px; background: #ffd400; text-align: center; font-weight: 900; }
.pastille { position: absolute; left: 0; top: 12px; padding: 4px 10px; background: #d4001a; color: #fff; font-weight: 900; }
.offre { display: grid; place-content: center; padding: 18px; background: #d4001a; color: #fff; text-align: center; }
.offre b { display: block; font: 900 27px/1.08 Montserrat, Arial, sans-serif; margin-bottom: 8px; color: #ffd400; }
.deux { display: grid; grid-template-columns: 1.2fr 1fr; gap: 20px; padding-top: 0; }
.bloc { padding: 18px 20px; background: #fff; border: 1px solid #ddd; }
.bloc h2 { font-size: 20px; }
.avis { margin: 0 0 12px; padding: 0 0 12px; border-bottom: 1px solid #eee; }
.mort { padding: 10px 0; border-bottom: 1px solid #eee; }
.fin { padding: 18px 40px; background: #111; color: #ffd400; text-align: center; font-weight: 700; }
</style>
<div class=promo>SPÉCIAL TOUSSAINT : −30 % SUR TOUT LE CHÊNE, JUSQU’AU 30 NOVEMBRE</div>
<header><div class=logo>AU DERNIER PRIX<small>POMPES FUNÈBRES · DISCOUNT DEPUIS 1952</small></div>
<div class=cherche><span>Rechercher un cercueil, une gerbe, un proche</span><b>OK</b></div><div class=panier>Mon panier (0)</div></header>
<nav><span>Cercueils</span><span>Urnes</span><span>Fleurs</span><span>Plaques</span><span>Contrats obsèques</span><span>Avis de décès</span><span class=x>Déstockage</span><span class=x>Carte Fidélité</span></nav>
<section class=hero><div><h1>Partez moins cher.</h1><p>Le pin massif à prix d’usine,<br>livré en 24 h dans tout le canton.</p><span class=go>J’en profite</span><span class="go c">Configurer en 3D</span></div>
<img src="%RAW%/cercueil.png" alt=""><div class=burst><div>JUSQU’À<b>−30 %</b></div></div></section>
<div class=rassure><div><b>Livraison offerte</b> dès 500 €</div><div><b>Paiement en 4 fois</b> sans frais</div><div><b>Retrait</b> en magasin</div><div><b>Aucun retour client</b> depuis 1952</div></div>
<section><h2>Les meilleures ventes</h2><div class=grille>
<div class=fiche><span class=pastille>−43 %</span><img src="%RAW%/cercueil.png" alt=""><h3>Repos Éco, pin massif</h3><div class=etoiles>★★★★★ <small>4,9 (312 avis)</small></div><div class=prixf>449 €</div><span class=barre>790 €</span><span class=stock>Plus que 3 en stock</span><div class=ajout>AJOUTER AU PANIER</div></div>
<div class=fiche><span class=pastille>−25 %</span><img src="%RAW%/urne.png" alt=""><h3>Urne Inox Essentiel</h3><div class=etoiles>★★★★☆ <small>4,3 (87 avis)</small></div><div class=prixf>89 €</div><span class=barre>119 €</span><span class=stock>En stock</span><div class=ajout>AJOUTER AU PANIER</div></div>
<div class=fiche><span class=pastille>−20 %</span><img src="%RAW%/gerbe.png" alt=""><h3>Couronne Souvenir, 60 cm</h3><div class=etoiles>★★★★★ <small>4,8 (540 avis)</small></div><div class=prixf>59 €</div><span class=barre>74 €</span><span class=stock>Souvent achetée avec Repos Éco</span><div class=ajout>AJOUTER AU PANIER</div></div>
<div class=offre><div><b>OFFRE COUPLE</b>Le second à −50 %.<br>Valable 5 ans.</div></div></div></section>
<section class=deux><div class=bloc><h2>Avis de décès du jour</h2>
<div class=mort><b>M. Raymond Tessonneau, 84 ans.</b> Cérémonie jeudi 5 novembre à 14 h 30, église de Saint-Ombrage. De la part de Jeanne, son épouse, de Claire et Hervé, ses enfants. Condoléances au domicile, 12 rue des Lilas, à partir de 18 h.</div>
<div class=mort><b>Mme Yvonne Piédalu, 91 ans.</b> Cérémonie vendredi 6 novembre à 10 h. De la part de son neveu Patrice, seul héritier.</div>
<p style="margin:10px 0 0">Les familles reçoivent leur facture par courriel sous 48 h, en PDF, réglable par virement sous 8 jours : facturation@au-dernier-prix.example</p></div>
<div class=bloc><h2>Ils ont choisi</h2>
<div class=avis><span class=etoiles>★★★★★</span> « Très bon service, livré à l’heure. Je reviendrai. »<br><small>Mme L., 3e commande</small></div>
<div class=avis><span class=etoiles>★★★★☆</span> « Bon rapport qualité-prix. Maman n’aurait pas aimé la couleur. »<br><small>Hervé T.</small></div>
<div><b>Employé du mois :</b> Jordan, 41 cercueils.</div></div></section>
<div class=fin>Carte Fidélité : la troisième cérémonie offerte. Parrainez un proche.</div>
"""

TAKES = {"A": INVIOLIA, "B": SOURCE, "C": DERNIER}


def french_spaces(page):
    """The non-breaking spaces French puts before : and inside guillemets, in the text only."""
    style, text = page.split("</style>")
    text = re.sub(r" ([:;?!»])", " \\1", text).replace("« ", "« ")
    return style + "</style>" + text


def main():
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        for letter, words in TAKES.items():
            assert "—" not in words, f"{letter}: em dash"
            draft = out / f"take-{letter}.html"
            draft.write_text("<!doctype html><html lang=fr><meta charset=utf-8>"
                             + french_spaces(words).replace("%RAW%", RAW.as_uri()), encoding="utf-8")
            page.goto(draft.as_uri())
            page.wait_for_load_state("networkidle")
            shot = out / f"take-{letter}.png"
            page.screenshot(path=shot, full_page=True)
            picture = Image.open(shot).convert("RGB")
            framed = Image.new("RGB", (picture.width, picture.height + BAND), (58, 58, 62))
            framed.paste(picture, (0, BAND))
            framed.save(shot)
            print(shot, framed.size)
        browser.close()


if __name__ == "__main__":
    main()
