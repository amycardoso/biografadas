"""Data de criação dos artigos, estimada pelo pageid.

Buscar a primeira revisão de cada página (prop=revisions&rvdir=newer&rvlimit=1)
exige uma requisição por página, o que daria cerca de 45 mil requisições. Como o
MediaWiki atribui pageids em ordem crescente na criação da página, uso uma
amostra estratificada de N páginas com a data real da primeira revisão e
interpolo (função monótona) pageid -> data para todos os artigos. O erro é
medido por validação cruzada e registrado em data/processed/criacao_calibracao.csv.

Limitações: páginas apagadas e recriadas ganham um pageid novo (a data
estimada é a da recriação, que é também a da revisão mais antiga que existe);
históricos importados ou fundidos podem ter revisões anteriores ao pageid.

Uso: python scripts/criacao.py [--amostra 400]
"""
import argparse
import time

import numpy as np
import pandas as pd

from common import DATA, PTAPI, get

META = DATA / "processed" / "artigos_meta.csv"
CALIB = DATA / "processed" / "criacao_calibracao.csv"
OUT = DATA / "processed" / "artigos_criacao.csv"


def primeira_revisao(pageid):
    j = get(PTAPI, {"action": "query", "prop": "revisions", "pageids": pageid, "rvdir": "newer",
                    "rvlimit": 1, "rvprop": "timestamp|ids", "maxlag": 5,
                    "format": "json", "formatversion": 2}).json()
    p = j["query"]["pages"][0]
    return p["revisions"][0]["timestamp"] if p.get("revisions") else None


def amostrar(meta, n):
    """Uma página por faixa de quantil do pageid, para cobrir todo o intervalo."""
    m = meta.dropna(subset=["pageid"]).sort_values("pageid").reset_index(drop=True)
    idx = np.unique(np.linspace(0, len(m) - 1, n).round().astype(int))
    return m.loc[idx, ["qid", "pageid"]]


def interpolar(px, py, x):
    py = np.maximum.accumulate(py)  # força monotonia (remove páginas recriadas fora de ordem)
    return np.interp(x, px, py)


def main(n=400):
    meta = pd.read_csv(META)
    if CALIB.exists():
        cal = pd.read_csv(CALIB)
    else:
        cal = amostrar(meta, n)
        datas = []
        for k, pid in enumerate(cal.pageid.astype(int)):
            datas.append(primeira_revisao(pid))
            if (k + 1) % 50 == 0:
                print(f"{k + 1}/{len(cal)}", flush=True)
            time.sleep(1)
        cal["primeira_revisao"] = datas
        cal.to_csv(CALIB, index=False)
    cal = cal.dropna(subset=["primeira_revisao"]).sort_values("pageid")
    px = cal.pageid.to_numpy(float)
    epoca = pd.Timestamp("1970-01-01", tz="UTC")
    py = ((pd.to_datetime(cal.primeira_revisao, utc=True) - epoca) / pd.Timedelta(seconds=1)).to_numpy(float)

    # validação: deixa um de fora, a cada 2 pontos
    erros = []
    for i in range(1, len(px) - 1, 2):
        mask = np.ones(len(px), bool)
        mask[i] = False
        est = interpolar(px[mask], py[mask], px[i])
        erros.append(abs(est - py[i]) / 86400)
    erros = np.array(erros)
    print(f"erro absoluto (dias): mediana {np.median(erros):.0f}, p90 {np.percentile(erros, 90):.0f}, "
          f"% < 365 dias: {100 * (erros < 365).mean():.0f}%")

    m = meta.dropna(subset=["pageid"]).copy()
    est = interpolar(px, py, m.pageid.to_numpy(float))
    m["criacao_estimada"] = pd.to_datetime(est, unit="s").strftime("%Y-%m-%d")
    m["ano_criacao"] = pd.to_datetime(m.criacao_estimada).dt.year
    m[["qid", "pageid", "criacao_estimada", "ano_criacao"]].to_csv(OUT, index=False)
    print(f"{len(m)} artigos -> {OUT.relative_to(DATA.parent)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--amostra", type=int, default=400)
    main(ap.parse_args().amostra)
