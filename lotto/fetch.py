"""Small HTTP helper. Stdlib only so the pipeline runs anywhere Python does."""
from __future__ import annotations

import json
import ssl
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
# Headers a real browser sends; a few lottery CDNs answer 403/406 without them.
BROWSER_HEADERS = {
    "User-Agent": UA,
    "Accept": "application/json,text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-CH-UA": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
    "Sec-CH-UA-Mobile": "?0",
    "Sec-CH-UA-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}


def _open(req: urllib.request.Request, timeout: int):
    try:
        return urllib.request.urlopen(req, timeout=timeout)
    except ssl.SSLError as e:
        # Some corporate/school proxies re-sign TLS with certificates Python rejects.
        # Fall back to the OS trust store via `truststore` if it is installed.
        try:
            import truststore  # type: ignore
        except ImportError:
            raise RuntimeError(f"TLS failure fetching {req.full_url}: {e}. Try `pip install truststore`.") from e
        ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        return urllib.request.urlopen(req, timeout=timeout, context=ctx)


def get(
    url: str,
    timeout: int = 60,
    headers: dict | None = None,
    data: bytes | dict | None = None,
    json_body=None,
    method: str | None = None,
    retries: int = 2,
) -> bytes:
    """GET (or POST when data/json_body is given) and return the body bytes.

    data: bytes are sent as-is; a dict is form-encoded. json_body: any JSON-serialisable
    object, sent with a JSON content type. Retries transient failures with a short pause."""
    h = dict(BROWSER_HEADERS)
    if headers:
        h.update(headers)
    body = None
    if json_body is not None:
        body = json.dumps(json_body).encode("utf-8")
        h.setdefault("Content-Type", "application/json")
    elif isinstance(data, dict):
        body = urllib.parse.urlencode(data).encode("utf-8")
        h.setdefault("Content-Type", "application/x-www-form-urlencoded")
    elif data is not None:
        body = data
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    last: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with _open(req, timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            # 403/406/429 from a CDN are often a momentary bot-score decision; a pause and
            # another try usually gets through. Other 4xx are real.
            if (e.code < 500 and e.code not in (403, 406, 429)) or attempt == retries:
                raise
            last = e
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if attempt == retries:
                raise
            last = e
        time.sleep(4.0 * (attempt + 1))
    raise RuntimeError(f"unreachable: {last}")


def get_text(url: str, timeout: int = 60, **kw) -> str:
    return get(url, timeout, **kw).decode("utf-8", "replace")


def get_json(url: str, timeout: int = 60, **kw):
    return json.loads(get(url, timeout, **kw).decode("utf-8"))


def fetch_many(fn, items, workers: int = 4):
    """Run fn(item) for each item on a small thread pool; return results in order.
    Per-game page scrapers use this so a 100-game state takes seconds, not minutes.
    An exception in fn is returned in place of the result so one bad game does not
    sink the whole state."""

    def safe(x):
        try:
            return fn(x)
        except Exception as e:  # noqa: BLE001
            return e

    with ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(safe, items))
