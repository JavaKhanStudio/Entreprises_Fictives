#!/usr/bin/env python3
"""Lighthouse's failed audits on one page of the checkout, served as atelier quality serves it.

    python3 tools/lighthouse_page.py gobelin/index.html [AUDIT ...] [--runs N]

Prints the performance score, the LCP, and for each AUDIT named its score and estimate.
Needs npx and the atelier checkout. A port is picked free; nothing else is touched.
"""

import json
import socket
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SERVE = Path.home() / "Documents/GitHub/atelier/tools/serve_static.py"


def run(path):
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    server = subprocess.Popen(["python3", str(SERVE), str(port)], cwd=REPO,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    try:
        out = subprocess.run(
            ["npx", "-y", "lighthouse@12", f"http://127.0.0.1:{port}/{path}", "--quiet",
             "--chrome-flags=--headless=new", "--only-categories=performance",
             "--output=json", "--output-path=stdout"],
            capture_output=True, text=True, timeout=180, check=True).stdout
    finally:
        server.kill()
    return json.loads(out)


def main():
    args = sys.argv[1:]
    runs = 1
    if "--runs" in args:
        at = args.index("--runs")
        runs = int(args[at + 1])
        del args[at:at + 2]
    if not args:
        sys.exit(__doc__)
    for _ in range(runs):
        report = run(args[0])
        audits = report["audits"]
        print("performance", round(report["categories"]["performance"]["score"] * 100),
              "lcp_ms", round(audits["largest-contentful-paint"]["numericValue"]))
        for name in args[1:]:
            audit = audits[name]
            print(" ", name, audit["score"], audit.get("displayValue", ""))
            for item in (audit.get("details") or {}).get("items", [])[:12]:
                if "url" in item:
                    print("   ", item["url"].rsplit("/", 1)[-1], item.get("wastedBytes"))


if __name__ == "__main__":
    main()
