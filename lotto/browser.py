"""Headless-browser helper for the few states whose pages assemble their data in the
browser behind a token the page itself obtains. We load the public page like any visitor
and read what it fetched or rendered; no credentials are handled by this code.

Requires `pip install playwright && playwright install chromium`. Importing this module
without Playwright raises ImportError, which build.py reports as a failed state."""
from __future__ import annotations

import json
from contextlib import contextmanager

from playwright.sync_api import sync_playwright

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"


@contextmanager
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(user_agent=UA, viewport={"width": 1280, "height": 900}, locale="en-US")
        try:
            yield ctx
        finally:
            ctx.close()
            b.close()


def capture(ctx, url: str, match: tuple[str, ...], settle_ms: int = 4000, timeout_ms: int = 60000) -> tuple[str, list[tuple[str, object]]]:
    """Load url in a new page; return (final HTML, [(response url, parsed JSON)]) for every
    JSON response whose URL contains one of the match substrings."""
    got: list[tuple[str, object]] = []
    page = ctx.new_page()

    def on_response(r):
        if any(m in r.url for m in match):
            try:
                got.append((r.url, r.json()))
            except Exception:  # noqa: BLE001 - not JSON
                pass

    page.on("response", on_response)
    page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
    try:
        page.wait_for_load_state("networkidle", timeout=timeout_ms)
    except Exception:  # noqa: BLE001
        pass
    page.wait_for_timeout(settle_ms)
    html = page.content()
    page.close()
    return html, got


def all_requests(ctx, url: str, settle_ms: int = 4000) -> list[str]:
    """Debug helper: every request URL a page makes."""
    seen: list[str] = []
    page = ctx.new_page()
    page.on("request", lambda r: seen.append(r.url))
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    try:
        page.wait_for_load_state("networkidle", timeout=60000)
    except Exception:  # noqa: BLE001
        pass
    page.wait_for_timeout(settle_ms)
    page.close()
    return seen


CHALLENGE = ("<title>Just a moment", "Verify you are human")


class Session:
    """A browser session that loads pages and waits for the content we need. Cloudflare
    clears its challenge within seconds for a fresh session but tends to re-challenge a
    session that has already browsed a site, so a page that comes back as a challenge is
    retried once in a brand-new session."""

    def __init__(self):
        self._cm = None
        self.ctx = None
        self._open()

    def _open(self):
        self._cm = browser()
        self.ctx = self._cm.__enter__()

    def renew(self):
        self.close()
        self._open()

    def close(self):
        if self._cm is not None:
            self._cm.__exit__(None, None, None)
            self._cm = None
            self.ctx = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def _load_once(self, url: str, selector: str | None, settle_ms: int, timeout_ms: int) -> str:
        page = self.ctx.new_page()
        try:
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=max(timeout_ms, 30000))
            except Exception:  # noqa: BLE001 - navigation timed out; treat like a challenge
                return "<title>Just a moment</title>"
            if selector:
                try:
                    page.wait_for_selector(selector, timeout=timeout_ms)
                except Exception:  # noqa: BLE001 - return whatever rendered
                    pass
            page.wait_for_timeout(settle_ms)
            return page.content()
        finally:
            page.close()

    def load(self, url: str, selector: str | None = None, settle_ms: int = 500, timeout_ms: int = 20000) -> str:
        html = self._load_once(url, selector, settle_ms, timeout_ms)
        if any(c in html for c in CHALLENGE):
            self.renew()
            html = self._load_once(url, selector, settle_ms, timeout_ms)
        return "" if any(c in html for c in CHALLENGE) else html
