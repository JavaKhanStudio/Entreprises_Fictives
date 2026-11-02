#!/usr/bin/env python3
"""Each refusal of the gate, proved once on a scratch page; and what it must let through.

    python3 tests/test_check_sites.py

The scratch pages are built in a temporary folder from the real shared/ and a frozen root index
(the real one links each finished site, and those folders are not copied): nothing here is an
.html the gate or GitHub Pages would pick up.
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
SCRATCH_INDEX = MODEL.replace(BODY, """<h2>Papeterie Merlin <span class="a-venir">à venir</span></h2>
    <h2>Gobelin Hurlant <span class="a-venir">à venir</span></h2>
    <h2>Étude Courtepaille <span class="a-venir">à venir</span></h2>""").replace("../shared/", "shared/")


def nothing_resolves(_domain):
    return "NXDOMAIN"


class Gate(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="check_sites_")
        self.addCleanup(shutil.rmtree, self.root)
        shutil.copytree(os.path.join(REPO, "shared"), os.path.join(self.root, "shared"))
        self.write("index.html", SCRATCH_INDEX)
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

    def test_phone_with_wide_separators(self):
        self.refused("phone", "<p>Appelez le 01 - 23 - 45 - 67 - 89</p>")

    def test_phone_with_slashes(self):
        self.refused("phone", "<p>Appelez le 01/23/45/67/89</p>")

    def test_french_phone_with_33_and_no_plus(self):
        self.refused("phone", "<p>Appelez le 33123456789</p>")

    def test_north_american_phone_with_no_plus(self):
        self.refused("phone", "<p>Bureau de Chicago : 1-800-555-0100</p>")

    def test_phone_wrapped_by_hand(self):
        self.refused("phone", "<p>Appelez le 01 23\n45 67 89</p>")
        self.refused("phone", "<p>Appelez le 01 23\n            45 67 89</p>")
        self.write("merlin/page.html", MODEL.replace(BODY, "<p>01 23\n    45 67 89</p>"))
        refusal = check_sites.check_tree(self.root, nothing_resolves)[0]
        self.assertIn("01 23 45 67 89: outside", refusal)

    def test_phone_with_tabs(self):
        self.refused("phone", "<p>Appelez le 01\t23\t45\t67\t89</p>")

    def test_phone_with_en_dashes(self):
        self.refused("phone", "<p>Appelez le 01\u201323\u201345\u201367\u201389</p>")
        self.refused("phone", "<p>Appelez le 01&ndash;23&ndash;45&ndash;67&ndash;89</p>")

    def test_phone_with_non_breaking_hyphens(self):
        self.refused("phone", "<p>Appelez le 01\u201123\u201145\u201167\u201189</p>")

    def test_phone_with_commas(self):
        self.refused("phone", "<p>Appelez le 01,23,45,67,89</p>")

    def test_phone_with_underscores(self):
        self.refused("phone", "<p>Appelez le 01_23_45_67_89</p>")

    def test_north_american_phone_with_an_en_dash(self):
        self.refused("phone", "<p>Bureau de Chicago : 1\u2013800\u2013555\u20130100</p>")

    def test_widened_separators_do_not_hide_a_second_number(self):
        # Each of these ended a number before the separators widened: it still must.
        for between in ("\n", "\n        ", "\t", ",", ", ", "\u2013", "\u2011", "_", "  "):
            for first in ("01 99 00 12 34", "+33 1 99 00 12 34"):
                with self.subTest(between=between, first=first):
                    self.refused("phone", f"<p>{first}{between}02 40 12 34 56</p>")
                    self.refused("phone", f"<p>2026{between}02 40 12 34 56</p>")

    def test_phone_touching_other_digits_after_it(self):
        self.refused("phone", "<p>Appelez le 01 23 45 67 89 24/24</p>")

    def test_phone_touching_a_postcode(self):
        self.refused("phone", "<p>75007 01 23 45 67 89</p>")

    def test_phone_touching_a_year(self):
        self.refused("phone", "<p>&copy; 2026 01 23 45 67 89</p>")

    def test_two_phones_joined_by_a_slash(self):
        self.refused("phone", "<p>0612345678/0712345678</p>")
        self.refused("phone", "<p>0639981234/0712345678</p>")

    def test_two_phones_joined_by_a_hyphen(self):
        self.refused("phone", "<p>0612345678-0712345678</p>")

    def test_two_phones_with_one_space(self):
        self.refused("phone", "<p>01 99 00 12 34 02 40 12 34 56</p>")

    def test_prefixed_phones_touching_other_digits(self):
        for number in ("+33 6 12 34 56 78 24", "0033 6 12 34 56 78 24", "2026 33 6 12 34 56 78",
                       "2026 1-800-555-0100"):
            with self.subTest(number=number):
                self.refused("phone", f"<p>{number}</p>")

    def test_phone_glued_to_a_label_with_a_hyphen(self):
        self.refused("phone", "<p>Tel-0612345678</p>")

    def test_phone_glued_to_a_label(self):
        self.refused("phone", "<p>T0612345678</p>")

    def test_phone_glued_to_a_label_with_a_slash(self):
        self.refused("phone", "<p>T\u00e9l/0612345678</p>")

    def test_phone_after_a_bare_slash_or_hyphen(self):
        self.refused("phone", "<p>/0612345678</p>")
        self.refused("phone", "<p>Appelez le -0612345678</p>")

    def test_phone_glued_to_each_label(self):
        for label in ("TEL", "T\u00c9L", "tel_", "Fax", "Fax-", "Mob", "Mob/", "Mobile",
                      "T\u00e9l\u00e9phone-", "Portable", "GSM", "Phone"):
            with self.subTest(label=label):
                self.refused("phone", f"<p>{label}0612345678</p>")

    def test_second_phone_in_a_row_is_still_read(self):
        self.refused("phone", "<p>01 99 00 12 34 - 02 40 12 34 56</p>")
        self.refused("phone", "<p>02 40 12 34 56 / 01 99 00 12 34</p>")

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
        <p>01 - 99 - 00 - 12 - 34, 06/39/98/12/34, 33199001234</p>
        <p>01 99 00 12 34 - 01 99 00 12 35</p>
        <p>Du 01/02/2026 - 03/04/2026, 2026-11-02, 02-11-2026, en 2026. 01 99 00 12 34</p>
        <p>Réf. 2026-004512-17, dossier 2026/0001234, FAC-0612345678, de 10 000 - 20 000 EUR</p>
        <p>01\u201399\u201300\u201312\u201334, 01,99,00,12,34, 01_99_00_12_34, 01\t99\t00\t12\t34</p>
        <p>01 99
           00 12 34
           01 99 00 12 35</p>
        <p>1,50 EUR, 12,50 EUR, de 10\u201320 EUR, 10 000\u201320 000 EUR, 1 500,50\u20132 500,50 EUR</p>
        <p>pages 01, 02, 03, 04, 05 et 0,5 0,6 0,7 0,8 0,9</p>
        <p>en 2026
           depuis 1987, 45 000
           EUR, du 02/11/2026\u201303/11/2026, photo_2026_11.png</p>
        <svg><polygon points="0,10 5,20 3,40,1"/></svg>
        <p>01 99 00 12 34 24/24, 75007 01 99 00 12 34, 2026 01 99 00 12 34</p>
        <p>0199001234/0639981234, +33 1 99 00 12 34 24, 01 99 00 12 34 06 39 98 12 34</p>
        <p>IBAN FR14 2004 1010 0505 0001 3000 606, SIRET 012 345 678 00012, 0612 3456 7890</p>
        <p>Tel-0199001234, T0199001234, T\u00e9l/0199001234, /0199001234, T-shirt 2026, T2, Fax 2026</p>
        <p>Hotel-0612345678, Contact0612345678, FAC/0612345678, dossier/0612345678.pdf</p>
        <p>a/b-0612345678, ./0612345678.pdf</p>
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
