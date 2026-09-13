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
