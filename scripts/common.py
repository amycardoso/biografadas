"""Cliente HTTP compartilhado: User-Agent descritivo, backoff em 429/5xx."""
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

UA = ("biografadas/0.1 (https://github.com/amycardoso/biografadas; "
      "pesquisa sobre gênero em biografias da Wikipédia) python-requests")
SPARQL = "https://query.wikidata.org/sparql"
WDAPI = "https://www.wikidata.org/w/api.php"
PTAPI = "https://pt.wikipedia.org/w/api.php"

_session = requests.Session()
_session.headers["User-Agent"] = UA


def get(url, params, tries=7, timeout=90, method="GET"):
    """Requisição com backoff exponencial; respeita Retry-After (limitado a 60 s)."""
    wait = 2
    for _ in range(tries):
        try:
            if method == "POST":
                r = _session.post(url, data=params, timeout=timeout)
            else:
                r = _session.get(url, params=params, timeout=timeout)
        except requests.RequestException as e:
            print(f"erro de rede: {e}; nova tentativa em {wait}s")
            time.sleep(wait)
            wait *= 2
            continue
        if r.status_code in (429, 500, 502, 503, 504):
            ra = r.headers.get("Retry-After")
            t = min(int(ra), 60) if ra and ra.isdigit() else min(wait, 60)
            print(f"HTTP {r.status_code}; aguardando {t}s")
            time.sleep(t)
            wait *= 2
            continue
        r.raise_for_status()
        return r
    raise RuntimeError(f"falhou após {tries} tentativas: {url}")


def sparql(query, timeout=180):
    r = get(SPARQL, {"query": query, "format": "json"}, timeout=timeout, method="POST")
    return r.json()["results"]["bindings"]


def val(row, key, default=""):
    return row.get(key, {}).get("value", default)


def qid(uri):
    return uri.rsplit("/", 1)[-1] if uri else ""
