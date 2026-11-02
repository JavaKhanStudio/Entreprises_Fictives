#!/usr/bin/env python3
"""Two render_pages.py runs at the same moment each prove their own tree. Needs Playwright, Chrome.

    python3 tests/test_render_pages.py

Two scratch trees whose index.html differ, both started at once. A run served by the other's
server, or by anything else already on a port, gets another page over http than over file://,
and the tool fails on that. A page one colour level off over http must fail too: the comparison
has no tolerance.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def scratch_tree(root, name, title):
    tree = os.path.join(root, name)
    os.makedirs(os.path.join(tree, "tools"))
    shutil.copytree(os.path.join(REPO, "shared"), os.path.join(tree, "shared"))
    shutil.copy(os.path.join(REPO, "tools", "render_pages.py"), os.path.join(tree, "tools"))
    with open(os.path.join(REPO, "shared", "modele.html"), encoding="utf-8") as model:
        page = model.read().replace('href="base.css"', 'href="shared/base.css"').replace("Titre de la page", title)
    with open(os.path.join(tree, "index.html"), "w", encoding="utf-8") as index:
        index.write(page)
    return tree


class TwoRunsAtOnce(unittest.TestCase):
    def test_each_run_renders_its_own_tree(self):
        with tempfile.TemporaryDirectory() as root:
            trees = [scratch_tree(root, "un", "Premier arbre"),
                     scratch_tree(root, "deux", "Second arbre")]
            runs = [subprocess.Popen([sys.executable, os.path.join(tree, "tools/render_pages.py"),
                                      os.path.join(tree, "out"), "index.html"],
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                    for tree in trees]
            outputs = [run.communicate(timeout=120)[0] for run in runs]
            for run, output in zip(runs, outputs):
                self.assertEqual(run.returncode, 0, output)
            pictures = []
            for tree in trees:
                with open(os.path.join(tree, "out", "index.html-1280.png"), "rb") as picture:
                    pictures.append(picture.read())
            self.assertNotEqual(*pictures, "the two trees gave the same picture")

    def test_one_colour_level_over_http_fails(self):
        with tempfile.TemporaryDirectory() as root:
            tree = scratch_tree(root, "un", "Arbre")
            index = os.path.join(tree, "index.html")
            with open(index, encoding="utf-8") as page:
                text = page.read()
            with open(index, "w", encoding="utf-8") as page:
                page.write(text.replace("</main>", """<div id="pastille"
                  style="width:40px;height:40px;background:rgb(100,100,100)"></div>
                  <script>if (location.protocol === "http:")
                  document.getElementById("pastille").style.background = "rgb(100,100,101)";
                  </script></main>"""))
            run = subprocess.run([sys.executable, os.path.join(tree, "tools/render_pages.py"),
                                  os.path.join(tree, "out"), "index.html"],
                                 capture_output=True, text=True, timeout=120)
            self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
            self.assertIn("give different pictures", run.stdout)


if __name__ == "__main__":
    unittest.main()
