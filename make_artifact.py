"""Write a body-only copy of site/index.html for publishing as a Claude Artifact.

The Artifact host wraps the file in its own <html>/<head>/<body>, so this strips the
document shell and keeps <title>, <link>, <style>, <script> and body content in order.

    python make_artifact.py OUT_PATH
"""
import re
import sys
from pathlib import Path

src = (Path(__file__).parent / "site" / "index.html").read_text(encoding="utf-8")
head = re.search(r"<head>(.*?)</head>", src, re.S).group(1)
body = re.search(r"<body>(.*?)</body>", src, re.S).group(1)
# Drop meta tags the host already provides; keep the rest of head.
head = re.sub(r"<meta[^>]*>\s*", "", head)
out = head.strip() + "\n" + body.strip() + "\n"
Path(sys.argv[1]).write_text(out, encoding="utf-8")
print(f"wrote {sys.argv[1]} ({len(out)} bytes)")
