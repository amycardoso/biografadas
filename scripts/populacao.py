"""Etapa 1: população de biografias de brasileiros na Wikipédia em português.

Critério: humano (P31=Q5) com cidadania brasileira (P27=Q155) e artigo na
pt.wikipedia. Saída: data/processed/populacao.csv, com uma linha por pessoa.

Uso: python scripts/populacao.py [--sem-cache]
"""
import argparse
import collections
import json
import time

import pandas as pd

from areas import area_principal, atualizar_mapeamento, carregar_mapeamento
from common import DATA, WDAPI, get, qid, sparql, val

RAW = DATA / "raw"
OUT = DATA / "processed" / "populacao.csv"
SEXO = {"Q6581072": "F", "Q6581097": "M"}
LOTE = 1000

Q_BASE = """
SELECT ?p ?titulo (GROUP_CONCAT(DISTINCT STRAFTER(STR(?sx), "entity/"); separator="|") AS ?sexo) WHERE {
  ?p wdt:P31 wd:Q5; wdt:P27 wd:Q155.
  ?art schema:about ?p; schema:isPartOf <https://pt.wikipedia.org/>; schema:name ?titulo.
  OPTIONAL { ?p wdt:P21 ?sx }
} GROUP BY ?p ?titulo
"""

Q_DETALHES = """
SELECT ?p (GROUP_CONCAT(DISTINCT STRAFTER(STR(?occ), "entity/"); separator="|") AS ?occs)
       (MIN(YEAR(?nasc)) AS ?ano_nasc) (MIN(YEAR(?morte)) AS ?ano_morte) WHERE {
  VALUES ?p { %s }
  OPTIONAL { ?p wdt:P106 ?occ }
  OPTIONAL { ?p wdt:P569 ?nasc }
  OPTIONAL { ?p wdt:P570 ?morte }
} GROUP BY ?p
"""


def cache_json(nome, fn, usar_cache=True):
    path = RAW / nome
    if usar_cache and path.exists():
        return json.loads(path.read_text())
    dados = fn()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dados, ensure_ascii=False))
    return dados


def baixar_base():
    t = time.time()
    rows = sparql(Q_BASE, timeout=300)
    print(f"base: {len(rows)} linhas em {time.time() - t:.0f}s")
    return [{"qid": qid(val(r, "p")), "titulo": val(r, "titulo"), "sexo_qids": val(r, "sexo")} for r in rows]


def baixar_detalhes(qids):
    out = []
    for i in range(0, len(qids), LOTE):
        lote = qids[i:i + LOTE]
        rows = sparql(Q_DETALHES % " ".join(f"wd:{q}" for q in lote))
        out += [{"qid": qid(val(r, "p")), "occs": val(r, "occs"),
                 "ano_nasc": val(r, "ano_nasc"), "ano_morte": val(r, "ano_morte")} for r in rows]
        print(f"detalhes: {min(i + LOTE, len(qids))}/{len(qids)}")
        time.sleep(1)
    return out


def baixar_rotulos(qids):
    rotulos = {}
    for i in range(0, len(qids), 50):
        r = get(WDAPI, {"action": "wbgetentities", "ids": "|".join(qids[i:i + 50]), "props": "labels",
                        "languages": "pt-br|pt|en", "languagefallback": 1, "format": "json"})
        for q, e in r.json().get("entities", {}).items():
            lab = e.get("labels", {})
            rotulos[q] = (lab.get("pt-br") or lab.get("pt") or lab.get("en") or {}).get("value", q)
        time.sleep(0.5)
    return rotulos


def sexo_de(qids):
    qs = [q for q in qids.split("|") if q]
    if not qs:
        return "sem_dado"
    if len(qs) > 1:
        return "multiplo"
    return SEXO.get(qs[0], "outro")


def ano(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return pd.NA


def main(usar_cache=True):
    base = pd.DataFrame(cache_json("wikidata_base.json", baixar_base, usar_cache))
    det = pd.DataFrame(cache_json("wikidata_detalhes.json",
                                  lambda: baixar_detalhes(sorted(base.qid.unique())), usar_cache))
    df = base.merge(det, on="qid", how="left").fillna({"occs": ""})

    occs = df.occs.str.split("|").map(lambda xs: sorted(x for x in xs if x))
    contagem = collections.Counter(o for xs in occs for o in xs)
    rotulos = cache_json("rotulos_ocupacoes.json", lambda: baixar_rotulos(sorted(contagem)), usar_cache)
    atualizar_mapeamento(contagem, rotulos)
    occ2area = carregar_mapeamento()

    df["sexo"] = df.sexo_qids.map(sexo_de)
    df["ocupacoes_qid"] = occs.map("|".join)
    df["ocupacoes"] = occs.map(lambda xs: "|".join(rotulos.get(o, o) for o in xs))
    df["area"] = occs.map(lambda xs: area_principal(xs, occ2area))
    df["ano_nasc"] = df.ano_nasc.map(ano).astype("Int64")
    df["ano_morte"] = df.ano_morte.map(ano).astype("Int64")
    df["decada_nasc"] = (df.ano_nasc // 10 * 10).astype("Int64")
    cols = ["qid", "titulo", "sexo", "sexo_qids", "area", "ocupacoes", "ocupacoes_qid",
            "ano_nasc", "ano_morte", "decada_nasc"]
    df = df[cols].sort_values("qid", key=lambda s: s.str[1:].astype(int))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"{len(df)} linhas ({df.qid.nunique()} pessoas) -> {OUT.relative_to(DATA.parent)}")
    print(df.sexo.value_counts().to_string())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sem-cache", action="store_true", help="refaz as consultas em vez de usar data/raw")
    main(usar_cache=not ap.parse_args().sem_cache)
