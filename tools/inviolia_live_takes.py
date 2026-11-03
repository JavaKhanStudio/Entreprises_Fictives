#!/usr/bin/env python3
"""The takes of r90: the look of the comets on Inviolia's home, and its feed against its clock.

    python3 tools/inviolia_live_takes.py OUT     # films and sheets in OUT, for `atelier attach --stamp`
    python3 tools/inviolia_live_takes.py sweep   # each feed take's height and overflow over 30 s

Comets. A: as shipped on r78. B: neon, a short bright bolt with no arc left behind. C: none.
Feed.   A: the clock runs forward, lines drawn from the page's own targets and attacks.
        B: no clock, six lines. C: as shipped on r78, the clock jumps back.

A take is a patch on a scratch copy of inviolia/, opened over file://: the site itself is never
touched. A patch whose old text has gone raises, so this tool cannot film something else by mistake.
The sweep says whether a take makes the feed jump before Simon sees it. Needs Playwright, Chrome, Pillow and ffmpeg.
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

SITE = Path(__file__).resolve().parent.parent / "inviolia"
WIDE, PHONE = (1280, 800), (390, 844)
BAND = 56       # plain, on top of each panel, where the stamp lands: it covers no word
BLOCK = '<b>BLOQUÉE</b></p>'
LINES = [f'          <p>{t}Inconnu → {w} · {a} {BLOCK}\n' for t, w, a in (
    ("03:12:08 · ", "France", "Rançongiciel quantique"),
    ("03:12:09 · ", "Vos données", "Hameçonnage IA"),
    ("03:12:11 · ", "Votre secteur", "Menace persistante"),
    ("03:12:14 · ", "Votre PDG", "Menace avancée"),
    ("03:12:15 · ", "Vos données", "Rançongiciel quantique"),
    ("03:12:17 · ", "France", "Menace avancée"))]

# Feed A: the leaving line comes back at the bottom as a new one, later than the last, its pair not on screen.
FLUX_A = """
    var CIBLES = ["France", "Vos données", "Votre secteur", "Votre PDG"], SORTES = ["Rançongiciel quantique", "Hameçonnage IA", "Menace persistante", "Menace avancée"];
    var heure = 3 * 3600 + 12 * 60 + 17;
    function deux(n) { return (n < 10 ? "0" : "") + n; }
    function nouvelle(p) {
      var vues = tour.map(function (q) { return q.textContent.replace(/^[^·]*· /, "").replace(/ BLOQUÉE$/, ""); }), mots;
      do { mots = "Inconnu → " + CIBLES[Math.floor(Math.random() * 4)] + " · " + SORTES[Math.floor(Math.random() * 4)]; } while (vues.indexOf(mots) >= 0);
      heure += 1 + Math.floor(Math.random() * 2);
      p.firstChild.textContent = deux(Math.floor(heure / 3600) % 24) + ":" + deux(Math.floor(heure / 60) % 60) + ":" + deux(heure % 60) + " · " + mots + " ";
    }
"""
NEON = """      tirs.forEach(function (s, i) {
        var k = (t - s.t0) / s.ms;
        if (k < 0) return;
        c.globalCompositeOperation = "lighter";
        if (k < 1) {
          [[9, 0.16], [5, 0.3], [2, 1]].forEach(function (g) {
            c.lineWidth = g[0] * e;
            for (var n = 0; n < 14; n++) {
              var d = k - (n + 1) * 0.022, f = k - n * 0.022;
              if (d < 0) break;
              var p = point(s, d, l, h), q = point(s, f, l, h);
              c.strokeStyle = "rgba(255, 60, 90, " + g[1] * (1 - n / 14) + ")";
              c.beginPath(); c.moveTo(p[0], p[1]); c.lineTo(q[0], q[1]); c.stroke();
            }
          });
        } else {
          var r = (k - 1) / 0.4, o = point(s, 1, l, h);
          [[6, 0.25], [2, 1]].forEach(function (g) {
            c.strokeStyle = "rgba(57, 229, 140, " + g[1] * Math.max(0, 1 - r) + ")";
            c.lineWidth = g[0] * e;
            c.beginPath(); c.arc(o[0], o[1], (2 + r * 11) * e, 0, 6.3); c.stroke();
          });
        }
        c.globalCompositeOperation = "source-over";
        if (k > 1.4) tirs[i] = tir(t);
      });
"""


def patch(text, old, new, regex=False):
    if regex:
        out, n = re.subn(old, lambda _: new, text, count=1, flags=re.S)
    else:
        out, n = text.replace(old, new, 1), old in text
    if not n:
        raise SystemExit(f"this take no longer applies, gone from the site: {old[:60]}")
    return out


def comets(js, take):
    if take == "A":
        return js
    if take == "C":
        return patch(js, "    carte();\n", "")
    return patch(js, r"      tirs\.forEach\(function \(s, i\) \{.*?\n      \}\);\n(?=    \}\n    enVue\(toile)", NEON, regex=True)


def feed(js, html, take):
    start = html.index('<div class="flux">\n') + len('<div class="flux">\n')
    end = html.index("        </div>", start)
    if take == "C":
        return js, html
    if take == "B":
        return js, html[:start] + "".join(re.sub(r"03:12:\d\d · ", "", line) for line in LINES) + html[end:]
    html = html[:start] + "".join(LINES) + html[end:]
    js = patch(js, "    function range() {", FLUX_A + "    function range() {")
    return patch(js, "tour.push(tour.shift());", "nouvelle(sort); tour.push(tour.shift());"), html


def site(tmp, name, comet, line):
    copy = Path(tmp) / name
    shutil.copytree(SITE, copy)
    js, html = feed(comets((SITE / "inviolia.js").read_text(), comet), (SITE / "index.html").read_text(), line)
    (copy / "inviolia.js").write_text(js)
    (copy / "index.html").write_text(html)
    return copy / "index.html"


CENTER = "(() => { const r = document.querySelector('.carte').getBoundingClientRect(); scrollTo(0, scrollY + r.top + r.height / 2 - innerHeight / 2); })()"
BOX = "s => { const r = document.querySelector(s).getBoundingClientRect(); return [r.x, r.y, r.width, r.height].map(Math.round); }"


def film(browser, path, tmp, what, seconds=12):
    """A film of the map centred on screen, and the box of `what` in it."""
    video = Path(tmp) / f"v{abs(hash(str(path)))}"
    context = browser.new_context(viewport={"width": WIDE[0], "height": WIDE[1]}, reduced_motion="no-preference",
                                  record_video_dir=str(video), record_video_size={"width": WIDE[0], "height": WIDE[1]})
    page = context.new_page()
    page.goto(path.as_uri())
    page.wait_for_load_state("load")
    page.mouse.move(640, 790)
    page.evaluate(CENTER)
    page.wait_for_timeout(2500)
    box = page.evaluate(BOX, what)
    page.wait_for_timeout(seconds * 1000)
    raw = Path(page.video.path())
    context.close()
    return raw, box


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def stack(clips, how, out, seconds=12):
    inputs, parts = [], []
    for i, (raw, (x, y, w, h)) in enumerate(clips):
        inputs += ["-ss", "3", "-t", str(seconds), "-i", str(raw)]
        parts.append(f"[{i}:v]crop={w}:{h}:{x}:{y},pad={w}:{h + BAND}:0:{BAND}:0x05080f,setsar=1[p{i}]")
    joined = "".join(f"[p{i}]" for i in range(len(clips)))
    ffmpeg(*inputs, "-filter_complex", ";".join(parts) + f";{joined}{how}=inputs={len(clips)}[o]", "-map", "[o]",
           "-c:v", "libvpx", "-b:v", "6M", "-an", str(out))


def phone_sheet(browser, paths, out, tmp):
    shots = []
    for i, path in enumerate(paths):
        page = browser.new_context(viewport={"width": PHONE[0], "height": PHONE[1]}, reduced_motion="no-preference").new_page()
        page.goto(path.as_uri())
        page.wait_for_load_state("load")
        page.evaluate(CENTER)
        page.wait_for_timeout(3600)
        shot = Path(tmp) / f"phone{i}.png"
        page.screenshot(path=shot)
        shots.append(Image.open(shot))
        page.close()
    sheet = Image.new("RGB", (sum(s.width for s in shots), shots[0].height + BAND), "#05080f")
    for i, shot in enumerate(shots):
        sheet.paste(shot, (i * shot.width, BAND))
    sheet.save(out)


def heights(browser, path, name):
    for width, height in (WIDE, PHONE, (360, 640)):
        page = browser.new_context(viewport={"width": width, "height": height}, reduced_motion="no-preference").new_page()
        page.goto(path.as_uri())
        page.wait_for_load_state("load")
        page.evaluate(CENTER)
        page.wait_for_timeout(800)
        seen, wide = set(), 0
        for _ in range(60):
            page.wait_for_timeout(500)
            seen.add(page.evaluate("document.querySelector('.flux').offsetHeight"))
            wide = max(wide, page.evaluate("document.documentElement.scrollWidth - innerWidth"))
        print(f"feed {name} at {width}: heights {sorted(seen)}, page wider by {wide}")
        page.close()


def main():
    sweep = sys.argv[1] == "sweep"
    out = Path(sys.argv[1])
    if not sweep:
        out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp, sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome")
        comet_sites = [site(tmp, f"c{t}", t, "C") for t in "ABC"]
        feed_sites = [site(tmp, f"f{t}", "A", t) for t in "ABC"]
        if sweep:
            for path, name in zip(feed_sites, "ABC"):
                heights(browser, path, name)
            browser.close()
            return
        stack([film(browser, p, tmp, ".carte img") for p in comet_sites], "hstack", out / "comets-1280.webm")
        stack([film(browser, p, tmp, ".carte > div") for p in feed_sites], "vstack", out / "fil-1280.webm")
        phone_sheet(browser, comet_sites, out / "comets-390.png", tmp)
        phone_sheet(browser, feed_sites, out / "fil-390.png", tmp)
        browser.close()


main()
