"""Tabelas descritivas da coleta (usadas por notebooks/02_coleta.ipynb)."""
import pandas as pd

from common import DATA

PROC = DATA / "processed"
STUB = 150  # palavras de prosa


def carregar():
    meta = pd.read_csv(PROC / "artigos_meta.csv")
    texto = pd.read_csv(PROC / "artigos_texto.csv")
    df = meta.drop(columns=["palavras"], errors="ignore").merge(
        texto.drop(columns=["sexo", "area", "status"]), on="qid", how="left")
    cri = PROC / "artigos_criacao.csv"
    if cri.exists():
        df = df.merge(pd.read_csv(cri)[["qid", "criacao_estimada", "ano_criacao"]], on="qid", how="left")
    df["stub"] = df.palavras < STUB
    return df


def cobertura(df):
    t = pd.DataFrame({
        "artigos": [len(df)],
        "ok": [(df.status == "ok").sum()],
        "ausentes": [(df.status != "ok").sum()],
        "via redirecionamento": [int(df.redirecionado.fillna(False).sum())],
        "sem sentenças após limpeza": [((df.status == "ok") & (df.sentencas.fillna(0) == 0)).sum()],
    }).T.rename(columns={0: "n"})
    return t


def tamanho_por_sexo(df):
    ok = df[df.status == "ok"]
    g = ok.groupby("sexo")
    return pd.DataFrame({
        "artigos": g.size(),
        "palavras (mediana)": g.palavras.median(),
        "palavras (média)": g.palavras.mean().round(0),
        "sentenças (mediana)": g.sentencas.median(),
        "palavras no lead (mediana)": g.palavras_lead.median(),
        "seções (mediana)": g.secoes.median(),
        "% stubs (<150 palavras)": (100 * g.stub.mean()).round(1),
    })


def tamanho_por_area(df):
    ok = df[df.status == "ok"]
    med = ok.pivot_table(index="area", columns="sexo", values="palavras", aggfunc="median")
    stub = ok.pivot_table(index="area", columns="sexo", values="stub", aggfunc="mean") * 100
    t = pd.concat({"palavras (mediana)": med, "% stubs": stub.round(1)}, axis=1)
    t[("razão F/M", "mediana")] = (med.F / med.M).round(2)
    return t.sort_values(("palavras (mediana)", "M"), ascending=False)


def pct_mulheres_por_ano_criacao(df):
    if "ano_criacao" not in df:
        return None
    t = pd.crosstab(df.ano_criacao, df.sexo)
    t["total"] = t.F + t.M
    t["%F"] = (100 * t.F / t.total).round(1)
    return t
