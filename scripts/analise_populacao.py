"""Tabelas descritivas da população (usadas por notebooks/01_populacao.ipynb)."""
import pandas as pd

from common import DATA

POP = DATA / "processed" / "populacao.csv"


def carregar():
    return pd.read_csv(POP, dtype={"ano_nasc": "Int64", "ano_morte": "Int64", "decada_nasc": "Int64"})


def por_sexo(df):
    t = df.sexo.value_counts().rename("n").to_frame()
    t["%"] = (100 * t.n / t.n.sum()).round(2)
    return t


def binario(df):
    return df[df.sexo.isin(["F", "M"])]


def pct_mulheres(df, col):
    t = pd.crosstab(binario(df)[col], binario(df).sexo)
    t["total"] = t.F + t.M
    t["%F"] = (100 * t.F / t.total).round(1)
    return t


def por_area(df):
    return pct_mulheres(df, "area").sort_values("total", ascending=False)


def por_decada(df, inicio=1800, fim=2010):
    d = binario(df)
    d = d[d.decada_nasc.between(inicio, fim)]
    return pct_mulheres(d, "decada_nasc")


def por_seculo(df):
    d = binario(df).dropna(subset=["ano_nasc"]).copy()
    d["periodo"] = pd.cut(d.ano_nasc.astype(int), [-10_000, 1799, 1899, 1949, 1979, 3000],
                          labels=["antes de 1800", "1800–1899", "1900–1949", "1950–1979", "1980+"])
    return pct_mulheres(d, "periodo")


def cobertura(df):
    linhas = {
        "sem sexo (P21)": (df.sexo == "sem_dado").mean(),
        "sexo fora de F/M": df.sexo.isin(["outro", "multiplo"]).mean(),
        "sem ocupação (P106)": (df.area == "sem_ocupacao").mean(),
        "ocupação sem área (outros)": (df.area == "outros").mean(),
        "sem ano de nascimento (P569)": df.ano_nasc.isna().mean(),
    }
    t = pd.DataFrame({"% das pessoas": {k: round(100 * v, 1) for k, v in linhas.items()}})
    b = binario(df)
    t["% entre F"] = [None, None,
                      round(100 * (b[b.sexo == "F"].area == "sem_ocupacao").mean(), 1),
                      round(100 * (b[b.sexo == "F"].area == "outros").mean(), 1),
                      round(100 * b[b.sexo == "F"].ano_nasc.isna().mean(), 1)]
    t["% entre M"] = [None, None,
                      round(100 * (b[b.sexo == "M"].area == "sem_ocupacao").mean(), 1),
                      round(100 * (b[b.sexo == "M"].area == "outros").mean(), 1),
                      round(100 * b[b.sexo == "M"].ano_nasc.isna().mean(), 1)]
    return t


def ocupacoes_mais_comuns(df, sexo, n=15):
    d = binario(df)
    occ = d[d.sexo == sexo].ocupacoes.dropna().str.split("|").explode()
    return occ.value_counts().head(n).rename("n").to_frame()
