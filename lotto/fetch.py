"""Small HTTP helper. Stdlib only so the pipeline runs anywhere Python does."""
import json
import ssl
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128 Safari/537.36 scratch-tracker/0.1"


def get(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": UA, "Accept": "application/json,text/html;q=0.9,*/*;q=0.8"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except ssl.SSLError as e:
        # Some corporate/school proxies re-sign TLS with certificates Python 3.13 rejects.
        # Fall back to the OS trust store via `truststore` if it is installed.
        try:
            import truststore  # type: ignore
        except ImportError:
            raise RuntimeError(f"TLS failure fetching {url}: {e}. Try `pip install truststore`.") from e
        ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return r.read()


def get_json(url: str, timeout: int = 60):
    return json.loads(get(url, timeout).decode("utf-8"))
