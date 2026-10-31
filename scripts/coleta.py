"""Etapa 2: coleta do wikitext dos artigos na pt.wikipedia.

Baixa o wikitext em lotes de 50 páginas (prop=revisions, maxlag=5), segue
redirecionamentos e marca páginas ausentes. É retomável: pula QIDs já
presentes no cache. A limpeza e a segmentação ficam em sentencas.py.

Saídas:
  data/cache/wikitext.jsonl.gz     wikitext da revisão atual (não versionado; CC BY-SA)
  data/processed/artigos_meta.csv  metadados por artigo (versionado)

Uso: python scripts/coleta.py [--limite N] [--pausa 2.0]
"""
import argparse
import gzip
import json
import time

import pandas as pd

from common import DATA, PTAPI, get
from texto import wikitext_para_texto

POP = DATA / "processed" / "populacao.csv"
OUT = DATA / "cache" / "wikitext.jsonl.gz"
META = DATA / "processed" / "artigos_meta.csv"
LOTE = 50


def ler_cache():
    """Itera os registros do cache, tolerando um final truncado por interrupção."""
    if not OUT.exists():
        return
    with gzip.open(OUT, "rt") as f:
        try:
            for linha in f:
                try:
                    yield json.loads(linha)
                except json.JSONDecodeError:
                    pass
        except (EOFError, gzip.BadGzipFile):
            return


def ja_coletados():
    return {a["qid"] for a in ler_cache()}


def baixar_lote(titulos):
    params = {"action": "query", "prop": "revisions|info", "rvprop": "content|ids|timestamp",
              "rvslots": "main", "titles": "|".join(titulos), "redirects": 1, "maxlag": 5,
              "format": "json", "formatversion": 2}
    for espera in (5, 10, 20, 40, 60, 60):
        j = get(PTAPI, params, timeout=120).json()
        if j.get("error", {}).get("code") != "maxlag":
            break
        print(f"maxlag; aguardando {espera}s", flush=True)
        time.sleep(espera)
    q = j.get("query", {})
    origem = {}
    for n in q.get("normalized", []) + q.get("redirects", []):
        origem[n["to"]] = n["from"]
    pedidos = set(titulos)
    paginas = {}
    for p in q.get("pages", []):
        t = p["title"]
        visto = set()
        while t not in pedidos and t in origem and t not in visto:
            visto.add(t)
            t = origem[t]
        paginas[t] = p
    return paginas


def registro(row, p):
    base = {"qid": row.qid, "titulo": row.titulo, "sexo": row.sexo, "area": row.area}
    if not p or "revisions" not in p:
        return {**base, "status": "ausente", "wikitext": ""}
    rev = p["revisions"][0]
    return {**base, "status": "ok", "pageid": p["pageid"], "titulo_atual": p["title"],
            "redirecionado": p["title"] != row.titulo, "revid": rev["revid"],
            "rev_timestamp": rev["timestamp"], "bytes_wikitext": p.get("length"),
            "wikitext": rev["slots"]["main"]["content"]}


def escrever_meta():
    linhas = []
    for a in ler_cache():
        wt = a.pop("wikitext", "")
        a["palavras"] = len(wikitext_para_texto(wt).split()) if wt else 0
        linhas.append(a)
    m = pd.DataFrame(linhas).drop_duplicates("qid", keep="last")
    m.to_csv(META, index=False)
    print(f"meta: {len(m)} artigos ({(m.status == 'ok').sum()} ok) -> {META.relative_to(DATA.parent)}")


def main(limite=None, pausa=2.0):
    pop = pd.read_csv(POP)
    pop = pop[pop.sexo.isin(["F", "M"])]
    feitos = ja_coletados()
    todo = [r for r in pop.itertuples() if r.qid not in feitos]
    if limite:
        todo = todo[:limite]
    print(f"{len(feitos)} já coletados; {len(todo)} a coletar", flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with gzip.open(OUT, "at") as f:
        for i in range(0, len(todo), LOTE):
            lote = todo[i:i + LOTE]
            paginas = baixar_lote([r.titulo for r in lote])
            for r in lote:
                f.write(json.dumps(registro(r, paginas.get(r.titulo)), ensure_ascii=False) + "\n")
            f.flush()
            feito = i + len(lote)
            if feito % 1000 < LOTE or feito == len(todo):
                taxa = feito / (time.time() - t0)
                print(f"{feito}/{len(todo)}  ~{(len(todo) - feito) / taxa / 60:.0f} min restantes", flush=True)
            time.sleep(pausa)
    escrever_meta()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limite", type=int)
    ap.add_argument("--pausa", type=float, default=2.0)
    a = ap.parse_args()
    main(a.limite, a.pausa)
