#!/usr/bin/env python3
"""A name that makes a bad domain gets a verdict, and the names after it still get theirs.

    python3 tests/test_check_names.py

No network: main() runs with every source stubbed, and RDAP answers 400 to what is not a domain,
as the real one did on source&eclat.com (r73).
"""

import contextlib
import email.message
import io
import os
import re
import sys
import unittest
import urllib.error
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import check_names  # noqa: E402


def http_error(code):
    return urllib.error.HTTPError("https://rdap.example/", code, "refused", email.message.Message(), io.BytesIO())


def rdap(domain):
    """A registry: 400 on a label outside letters, digits and hyphens, 404 on any other."""
    if not re.fullmatch(r"[a-z0-9-]+\.(com|fr)", domain):
        raise http_error(400)
    if domain == "panne.com":
        raise http_error(500)
    if domain == "sourceeclat.fr":
        return True
    raise http_error(404)


def fetching(url, headers):
    return rdap(url.rsplit("/", 1)[1])


def run(*names):
    """main() on these names, without the network or the pauses: its exit code and what it printed."""
    out = io.StringIO()
    with (mock.patch.object(sys, "argv", ["check_names.py", "--no-web", "--domains", *names]),
          mock.patch.object(check_names, "fetch", fetching),
          mock.patch.object(check_names, "wikipedia_hits", lambda name: ["known"] if name == check_names.KNOWN else []),
          mock.patch.object(check_names, "wikidata_hits", lambda name: ["known"] if name == check_names.KNOWN else []),
          mock.patch.object(check_names, "public_control", lambda: dict.fromkeys(check_names.PUBLIC, lambda name: [])),
          mock.patch.object(check_names, "domain_control", lambda: True),
          mock.patch.object(check_names.time, "sleep", lambda seconds: None),
          contextlib.redirect_stdout(out)):
        return check_names.main(), out.getvalue()


class DomainsOf(unittest.TestCase):
    def test_keeps_letters_and_digits_only(self):
        self.assertEqual(check_names.domains_of("Source & Éclat"),
                         ["sourceeclat.com", "sourceeclat.fr", "source-eclat.com", "source-eclat.fr"])
        self.assertEqual(check_names.domains_of("L'Atelier-2"),
                         ["latelier2.com", "latelier2.fr", "l-atelier-2.com", "l-atelier-2.fr"])

    def test_no_domain_from_marks_or_past_63(self):
        self.assertEqual(check_names.domains_of("& & &"), [])
        self.assertEqual(check_names.domains_of("a" * 64), [])
        self.assertEqual(check_names.domains_of("a" * 63)[0], "a" * 63 + ".com")


class Run(unittest.TestCase):
    def test_ampersand_gets_its_verdict(self):
        code, out = run("Source & Éclat")
        self.assertEqual(code, 1, out)
        self.assertIn("Source & Éclat: 1 hits", out)
        self.assertIn("rdap sourceeclat.fr is registered", out)

    def test_name_with_no_domain_is_said_and_the_run_goes_on(self):
        code, out = run("& & &", "Zorglaxe")
        self.assertEqual(code, 3, out)
        self.assertRegex(out, r"(?m)^& & &: 0 hits.*cannot be a domain$")
        self.assertRegex(out, r"(?m)^Zorglaxe: 0 hits")

    def test_rdap_failing_on_one_name_is_unchecked_and_the_run_goes_on(self):
        code, out = run("Panne", "Source & Éclat")
        self.assertEqual(code, 1, out)
        self.assertRegex(out, r"(?m)^Panne: 0 hits.*unchecked on rdap panne\.com$")
        self.assertIn("Source & Éclat: 1 hits", out)


if __name__ == "__main__":
    unittest.main(warnings="ignore")  # each HTTPError stubbed here leaves an unclosed temp file
