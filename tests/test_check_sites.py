#!/usr/bin/env python3
"""Each refusal of the gate, proved once on a scratch page; and what it must let through.

    python3 tests/test_check_sites.py

The scratch pages are built in a temporary folder from the real shared/ and index.html: nothing
here is an .html the gate or GitHub Pages would pick up.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "tools"))
import check_sites  # noqa: E402

with open(os.path.join(REPO, "shared/modele.html"), encoding="utf-8") as model_file:
    MODEL = model_file.read()
BODY = "<p>Le contenu de la page.</p>"
NOINDEX = '  <meta name="robots" content="noindex">\n'


def nothing_resolves(_domain):
    return "NXDOMAIN"


class Gate(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="check_sites_")
        self.addCleanup(shutil.rmtree, self.root)
        shutil.copytree(os.path.join(REPO, "shared"), os.path.join(self.root, "shared"))
        for name in ("index.html", "index.css"):
            shutil.copy(os.path.join(REPO, name), self.root)
        for company in check_sites.COMPANIES:
            os.mkdir(os.path.join(self.root, company))
        self.write("merlin/cible.html", MODEL)

    def write(self, path, content):
        with open(os.path.join(self.root, path), "w", encoding="utf-8") as handle:
            handle.write(content)

    def rules(self, status_of=nothing_resolves):
        lines = check_sites.check_tree(self.root, status_of)
        return sorted({line.split("[")[1].split("]")[0] for line in lines})

    def refused(self, rule, body=None, page=None, status_of=nothing_resolves):
        """The scratch page (the model with this body, or this whole page) is refused for rule."""
        self.write("merlin/page.html", page if page is not None else MODEL.replace(BODY, body))
        self.assertEqual(self.rules(status_of), [rule])
        os.remove(os.path.join(self.root, "merlin/page.html"))

    def test_the_real_skeleton_passes_and_so_does_the_model_page(self):
        self.assertEqual(check_sites.check_tree(self.root, nothing_resolves), [])

    def test_no_noindex(self):
        self.refused("noindex", page=MODEL.replace(NOINDEX, ""))

    def test_footer_differs_by_one_word(self):
        self.refused("footer", page=MODEL.replace("ne collecte rien", "collecte peu"))

    def test_footer_missing(self):
        start, end = MODEL.index("<footer"), MODEL.index("</footer>") + len("</footer>")
        self.refused("footer", page=MODEL[:start] + MODEL[end:])

    def test_footer_only_in_a_comment(self):
        start, end = MODEL.index("<footer"), MODEL.index("</footer>") + len("</footer>")
        self.refused("footer", page=MODEL[:start] + "<!--" + MODEL[start:end] + "-->" + MODEL[end:])

    def test_second_footer(self):
        self.refused("footer", "<footer>Mentions</footer>")

    def test_form(self):
        self.refused("form", '<form><input name="q"></form>')

    def test_tel_link(self):
        self.refused("tel", '<a href="tel:0199001234">Appeler</a>')

    def test_http_image(self):
        # Its host is not .example either, so two rules speak; here the host is fictional.
        self.refused("external", '<img src="https://images.papeterie-merlin.example/a.png" alt="">')

    def test_protocol_relative_script(self):
        self.refused("external", '<script src="//cdn.papeterie-merlin.example/a.js"></script>')

    def test_http_stylesheet(self):
        self.refused("external", '<link rel="stylesheet" href="https://x.example/a.css">')

    def test_http_in_srcset(self):
        self.refused("external", '<img src="" srcset="http://x.example/a.png 2x" alt="">')

    def test_http_in_a_style_attribute(self):
        self.refused("external", '<p style="background: url(https://x.example/a.png)">x</p>')

    def test_http_in_a_style_block(self):
        self.refused("external", '<style>@import "https://x.example/a.css";</style>')

    def test_http_in_a_css_file(self):
        self.write("merlin/merlin.css", "body { background: url('https://x.example/a.png'); }\n")
        self.assertEqual(self.rules(), ["external"])

    def test_em_dash(self):
        self.refused("em-dash", "<p>Le papier — notre passion</p>")

    def test_em_dash_as_entities(self):
        self.refused("em-dash", "<p>Le papier &mdash; notre passion</p>")
        self.refused("em-dash", "<p>Le papier &#8212; notre passion</p>")

    def test_em_dash_in_an_attribute(self):
        self.refused("em-dash", '<img src="" alt="Le papier — notre passion">')

    def test_em_dash_in_a_css_file(self):
        self.write("merlin/merlin.css", 'p::before { content: "\\2014"; }\n')
        self.assertEqual(self.rules(), ["em-dash"])

    def test_web_domain_not_example(self):
        self.refused("domain", "<p>Voir papeterie-merlin.fr pour tout savoir</p>")

    def test_example_is_not_enough_inside_a_name(self):
        self.refused("domain", "<p>Voir papeterie-merlin.example.com</p>")

    def test_email_not_example(self):
        self.refused("domain", "<p>Ecrire à bob@papeterie-merlin.fr</p>")

    def test_email_with_no_tld(self):
        self.refused("domain", "<p>Ecrire à bob@papeterie</p>")

    def test_domain_in_a_meta(self):
        self.refused("domain", '<meta property="og:url" content="https://merlin.fr/">')

    def test_domain_that_resolves(self):
        def everything_resolves(_domain):
            return "NOERROR"
        self.refused("resolves", "<p>papeterie-merlin.example</p>", status_of=everything_resolves)

    def test_domain_that_cannot_be_checked(self):
        def no_network(_domain):
            return "SERVFAIL"
        self.refused("resolves", "<p>papeterie-merlin.example</p>", status_of=no_network)

    def test_phone_outside_the_fiction_ranges(self):
        for number in ("02 40 12 34 56", "0612345678", "+33 6 12 34 56 78", "0033 1 23 45 67 89",
                       "0 800 123 456", "07.12.34.56.78", "01&nbsp;99&nbsp;01&nbsp;12&nbsp;34"):
            with self.subTest(number=number):
                self.refused("phone", f"<p>Appelez le {number}</p>")

    def test_foreign_phone(self):
        self.refused("phone", "<p>Bureau de Londres : +44 20 7946 0958</p>")

    def test_live_link_to_a_fictional_domain(self):
        self.refused("live-link", '<a href="https://papeterie-merlin.example/">le site</a>')

    def test_mailto_link(self):
        self.refused("live-link", '<a href="mailto:bob@papeterie-merlin.example">Bob</a>')

    def test_link_from_the_root_breaks_over_file(self):
        self.refused("relative", '<a href="/merlin/cible.html">Cible</a>')

    def test_dead_link(self):
        self.refused("dead-link", '<a href="nulle-part.html">Rien</a>')

    def test_link_in_the_wrong_case(self):
        self.refused("dead-link", '<a href="Cible.html">Cible</a>')

    def test_link_to_a_folder_opens_a_listing_over_file(self):
        self.refused("dead-link", '<a href="../gobelin/">Gobelin</a>')

    def test_site_missing_from_the_root_index(self):
        self.write("merlin/index.html", MODEL)
        self.assertEqual(self.rules(), ["index"])

    def test_what_the_gate_lets_through(self):
        allowed = """
        <p>01 99 00 12 34, 02 61 91 12 34, 03 53 01 12 34, 04 65 71 12 34, 05 36 49 12 34</p>
        <p>06.39.98.12.34 et +33 (0)6 39 98 12 34 et +33 1 99 00 12 34 et 0033 1 99 00 12 34</p>
        <p>01&nbsp;99&nbsp;00&nbsp;12&nbsp;34</p>
        <p>bob@papeterie-merlin.example, https://papeterie-merlin.example/portail en texte</p>
        <p>extranet.papeterie-merlin.example. Une phrase après le point.</p>
        <p>facture-2026.pdf, Merlin S.A.R.L., 12.50 EUR, le 02.11.2026, depuis 1987</p>
        <p>SIRET 123 456 789 00012, TVA FR76123456789, IBAN FR76 3000 6000 0112 3456 7890 189</p>
        <p>#PapierAgile, @MmeMerlin, 12 abonnés, 👏 1 (elle-même), 45 000 EUR</p>
        <a href="cible.html#equipe">interne</a> <a href="#haut">haut</a>
        <img src="data:image/gif;base64,R0lGOD" alt="">
        <style>.bob.ninja { color: red; } p { background: url(../shared/base.css); }</style>
        """
        self.write("merlin/page.html", MODEL.replace(BODY, allowed))
        self.assertEqual(check_sites.check_tree(self.root, nothing_resolves), [])

    def test_site_linked_from_the_root_index_passes(self):
        self.write("merlin/index.html", MODEL)
        with open(os.path.join(self.root, "index.html"), encoding="utf-8") as handle:
            index = handle.read()
        self.write("index.html", index.replace("Papeterie Merlin <span",
                                               '<a href="merlin/index.html">Merlin</a> <span'))
        self.assertEqual(check_sites.check_tree(self.root, nothing_resolves), [])


class RealDig(unittest.TestCase):
    def setUp(self):
        try:
            subprocess.run(["dig", "+time=3", "+tries=1", "python.org", "A"],
                           capture_output=True, timeout=10, check=True)
        except (OSError, subprocess.SubprocessError) as error:
            self.skipTest(f"no dig to ask: {error}")

    def test_a_real_domain_resolves(self):
        self.assertEqual(check_sites.dig_status("python.org"), "NOERROR")

    def test_a_fictional_domain_does_not(self):
        self.assertEqual(check_sites.dig_status("papeterie-merlin.example"), "NXDOMAIN")


if __name__ == "__main__":
    unittest.main()
