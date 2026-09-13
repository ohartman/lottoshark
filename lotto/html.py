"""Just-enough HTML helpers on top of html.parser (no external dependencies).

    tables(html)            -> list of tables; each table is a list of rows; each row a
                               list of cell strings (whitespace-collapsed, tags stripped).
                               <th> and <td> are treated alike.
    text(fragment)          -> visible text of an HTML fragment
    attr_all(html, tag, a)  -> every value of attribute `a` on `tag` elements, in order
"""
from __future__ import annotations

import re
from html import unescape
from html.parser import HTMLParser

_WS = re.compile(r"\s+")


def _clean(s: str) -> str:
    return _WS.sub(" ", unescape(s)).strip()


class _Tables(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[str]]] = []
        self._stack: list[list[list[str]]] = []  # nested tables
        self._row: list[str] | None = None
        self._cell: list[str] | None = None
        self._skip = 0  # inside <script>/<style>

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip += 1
        elif tag == "table":
            t: list[list[str]] = []
            self.tables.append(t)
            self._stack.append(t)
        elif tag == "tr" and self._stack:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []
        elif tag == "br" and self._cell is not None:
            self._cell.append(" ")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._skip = max(0, self._skip - 1)
        elif tag in ("td", "th") and self._cell is not None and self._row is not None:
            self._row.append(_clean("".join(self._cell)))
            self._cell = None
        elif tag == "tr" and self._row is not None and self._stack:
            if self._cell is not None:  # unclosed last cell
                self._row.append(_clean("".join(self._cell)))
                self._cell = None
            if self._row:
                self._stack[-1].append(self._row)
            self._row = None
        elif tag == "table" and self._stack:
            self._stack.pop()

    def handle_data(self, data):
        if self._skip == 0 and self._cell is not None:
            self._cell.append(data)


def tables(html: str) -> list[list[list[str]]]:
    p = _Tables()
    p.feed(html)
    p.close()
    return p.tables


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip += 1
        elif tag in ("br", "p", "div", "li", "tr", "h1", "h2", "h3", "h4"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._skip = max(0, self._skip - 1)

    def handle_data(self, data):
        if self._skip == 0:
            self.parts.append(data)


def text(fragment: str) -> str:
    p = _Text()
    p.feed(fragment)
    p.close()
    return _clean("".join(p.parts))


class _Attrs(HTMLParser):
    def __init__(self, tag: str, attr: str):
        super().__init__()
        self.tag, self.attr, self.values = tag, attr, []

    def handle_starttag(self, tag, attrs):
        if tag == self.tag:
            for k, v in attrs:
                if k == self.attr and v is not None:
                    self.values.append(unescape(v))


def attr_all(html: str, tag: str, attr: str) -> list[str]:
    p = _Attrs(tag, attr)
    p.feed(html)
    p.close()
    return p.values


def num(s) -> int:
    """'1,234' -> 1234; '' / '—' / None -> 0."""
    m = re.search(r"-?\d[\d,]*", str(s or ""))
    return int(m.group(0).replace(",", "")) if m else 0


def money(s) -> float:
    """'$1,234.50' -> 1234.5; handles K/M suffixes ('$1M'). 0.0 when no number."""
    t = str(s or "").upper().replace(",", "")
    m = re.search(r"(\d+(?:\.\d+)?)\s*(K|M)?\b", t)
    if not m:
        return 0.0
    return float(m.group(1)) * {"K": 1_000, "M": 1_000_000}.get(m.group(2) or "", 1)


def odds(s) -> float | None:
    """'1 in 4.12' / '1:4.12' / '4.12' -> 4.12."""
    m = re.search(r"1\s*(?:in|:)\s*([\d,]+(?:\.\d+)?)", str(s or ""), re.I)
    return float(m.group(1).replace(",", "")) if m else None
