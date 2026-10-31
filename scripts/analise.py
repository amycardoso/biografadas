"""Etapa 5b: estimativas por grupo com correção do erro de classificação.

Correção do erro de classificação. Em cada grupo, q é a fração de sentenças
com cada rótulo PREVISTO. Três estimativas:
  - "precisao" (principal): p = q · P, com P[j, i] = P(verdadeiro = i | previsto = j)
    estimada no teste fixo PONDERADO pelos pesos de amostragem (peso_v3), de modo
    que reflita a prevalência na população, e separadamente por sexo (a
    prevalência de FAM_ID difere entre os sexos). É estável para classes raras,
    mas assume que P se transfere do teste para cada grupo do mesmo sexo.
  - "acc" (Adjusted Classify and Count; Forman 2008): resolve q = Mᵀ p, com
    M[i, j] = P(previsto = j | verdadeiro = i), por mínimos quadrados não
    negativos. Não depende da prevalência, mas tem variância alta e tende a zerar
    classes raras (um único falso positivo de CAR no teste "explica" todo FAM_ID).
  - "nenhuma": a contagem bruta das predições.
Intervalos (todas as estimativas): bootstrap com B réplicas, que reamostra ao mesmo tempo (a) as
pessoas do corpus (pesos de Poisson por pessoa, mantendo todas as sentenças de
cada pessoa juntas) e (b) as sentenças do teste usadas para estimar M. Assim,
o intervalo inclui a incerteza da matriz de confusão.

Duas unidades de análise:
  - "sentença": fração das sentenças do grupo com o rótulo;
  - "pessoa": média, entre as pessoas do grupo, da fração das sentenças de cada uma
    (cada biografia pesa igual, independentemente do tamanho).
As correções são aplicadas nas duas, porque são lineares nas proporções.

Uso (importado pelo notebook 04):  import analise; analise.preparar()
"""
from functools import lru_cache

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy.optimize import nnls

from common import DATA

PROC, LAB = DATA / "processed", DATA / "labels"
ROTULOS = ["CAR", "FAM_ID", "FAM_DET", "FAM_ORIG", "FAM_CAP", "APAR", "GEN", "OUTRO"]
STUB = 150
B = 300
SEED = 7


# ---------------------------------------------------------------- dados
def _predicoes(cols):
    """predicoes.parquet; se ainda não existir, os blocos parciais da inferência (para testes)."""
    f = PROC / "predicoes.parquet"
    if f.exists():
        return pq.read_table(f, columns=cols).to_pandas()
    blocos = sorted((DATA / "cache" / "inferencia").glob("bloco_*.parquet"))
    return pd.concat([pq.read_table(b, columns=cols).to_pandas() for b in blocos])


@lru_cache(maxsize=1)
def preparar():
    """Contagens de rótulos previstos por pessoa (lead, corpo, total) + metadados."""
    s = pq.read_table(PROC / "sentencas.parquet", columns=["qid", "sent_idx", "lead"]).to_pandas()
    p = _predicoes(["qid", "sent_idx", "pred"])
    s = s.merge(p, on=["qid", "sent_idx"])
    s["pred"] = pd.Categorical(s.pred, ROTULOS)
    cont = {}
    for nome, sub in [("lead", s[s.lead]), ("corpo", s[~s.lead]), ("total", s)]:
        cont[nome] = pd.crosstab(sub.qid, sub.pred).reindex(columns=ROTULOS, fill_value=0)
    pop = pd.read_csv(PROC / "populacao.csv", usecols=["qid", "titulo", "sexo", "area", "decada_nasc", "ano_nasc"])
    txt = pd.read_csv(PROC / "artigos_texto.csv", usecols=["qid", "palavras"])
    cri = pd.read_csv(PROC / "artigos_criacao.csv", usecols=["qid", "ano_criacao"])
    meta = pop.merge(txt, on="qid").merge(cri, on="qid", how="left")
    meta = meta[meta.sexo.isin(["F", "M"]) & meta.qid.isin(cont["total"].index)].set_index("qid")
    meta["stub"] = meta.palavras < STUB
    meta["periodo_criacao"] = pd.cut(meta.ano_criacao, [2001, 2006, 2011, 2016, 2021, 2026],
                                     labels=["2002–06", "2007–11", "2012–16", "2017–21", "2022–26"])
    meta["periodo_nasc"] = pd.cut(meta.ano_nasc, [-10_000, 1899, 1949, 1979, 3000],
                                  labels=["até 1899", "1900–49", "1950–79", "1980+"])
    for k in cont:
        cont[k] = cont[k].reindex(meta.index, fill_value=0)
    return meta, cont


@lru_cache(maxsize=1)
def teste():
    """Teste fixo: rótulo v3, predição do BERTimbau v3, peso (normalizado por sexo) e sexo."""
    a = pd.read_csv(LAB / "amostra_v3.csv", usecols=["sid", "split", "sexo", "peso_v3"])
    r = pd.read_csv(LAB / "rotulos_v3.csv", usecols=["sid", "rotulo"])
    pr = pd.read_csv(LAB / "predicoes_v3" / "bertimbau.csv")
    t = a[a.split == "teste"].merge(r, on="sid").merge(pr, on="sid")
    t["w"] = t.peso_v3 / t.groupby("sexo").peso_v3.transform("mean")
    return (t.rotulo.map(ROTULOS.index).to_numpy(), t.pred.map(ROTULOS.index).to_numpy(),
            t.w.to_numpy(), t.sexo.to_numpy())


# ---------------------------------------------------------------- correção
def matriz(y, p, suav=0.5):
    """P(previsto | verdadeiro), com suavização aditiva para classes raras no teste."""
    k = len(ROTULOS)
    m = np.full((k, k), 0.0)
    np.add.at(m, (y, p), 1)
    m += suav * np.eye(k) + suav / k  # leve prior na diagonal: evita linhas vazias
    return m / m.sum(1, keepdims=True)


def precisao(y, p, w, suav=0.5):
    """P(verdadeiro | previsto), ponderada; suavização na diagonal para colunas vazias."""
    k = len(ROTULOS)
    m = np.zeros((k, k))
    np.add.at(m, (p, y), w)
    m += suav * np.eye(k)
    return m / m.sum(1, keepdims=True)


def corrigir(q, metodo, y, p, w, sx, sexo):
    """Aplica a correção escolhida a q usando o teste (y, p, w, sx) — do sexo do grupo, se houver um só."""
    if metodo == "nenhuma":
        return q
    if sexo in ("F", "M"):
        sel = sx == sexo
        y, p, w = y[sel], p[sel], w[sel]
    if metodo == "precisao":
        return q @ precisao(y, p, w)
    return acc(q, matriz(y, p))


def acc(q, M):
    """Resolve q = Mᵀ p com p ≥ 0; normaliza para somar 1."""
    p, _ = nnls(M.T, q)
    return p / p.sum() if p.sum() > 0 else p


# ---------------------------------------------------------------- estimativas
def _proporcoes(c, w, unidade):
    """c: contagens (n_pessoas × 8); w: pesos por pessoa. Retorna q (8,)."""
    n = c.sum(1)
    ok = n > 0
    if unidade == "sentenca":
        return (c[ok] * w[ok, None]).sum(0) / (n[ok] * w[ok]).sum()
    frac = c[ok] / n[ok, None]
    return (frac * w[ok, None]).sum(0) / w[ok].sum()


def _sexo_do_grupo(m, idx):
    u = np.unique(m.sexo.to_numpy()[idx])
    return u[0] if len(u) == 1 else None


def estimar(por, parte="total", unidade="pessoa", filtro=None, rotulos=None, b=B, metodo="precisao"):
    """Proporção (%) de cada rótulo por grupo, com IC de 95% por bootstrap (pessoas + teste).

    por: coluna(s) de metadados (ex.: "sexo" ou ["area", "sexo"]). parte: "lead", "corpo" ou "total".
    filtro: máscara booleana sobre as pessoas. metodo: "precisao", "acc" ou "nenhuma".
    """
    meta, cont = preparar()
    y, pt, wt, st = teste()
    m, c = meta, cont[parte].to_numpy()
    if filtro is not None:
        m, c = meta[filtro], c[np.asarray(filtro)]
    por = [por] if isinstance(por, str) else por
    grupos = m.groupby(por, observed=True).indices
    rng = np.random.default_rng(SEED)
    est, reps = {}, {g: [] for g in grupos}
    for g, idx in grupos.items():
        q = _proporcoes(c[idx], np.ones(len(idx)), unidade)
        est[g] = (corrigir(q, metodo, y, pt, wt, st, _sexo_do_grupo(m, idx)), q)
    for _ in range(b):
        ti = rng.integers(0, len(y), len(y))
        for g, idx in grupos.items():
            w = rng.poisson(1.0, len(idx)).astype(float)
            if w.sum() == 0:
                continue
            q = _proporcoes(c[idx], w, unidade)
            reps[g].append(corrigir(q, metodo, y[ti], pt[ti], wt[ti], st[ti], _sexo_do_grupo(m, idx)))
    rotulos = rotulos or ROTULOS
    linhas = []
    for g, idx in grupos.items():
        r = np.array(reps[g])
        chave = g if isinstance(g, tuple) else (g,)
        for k, rot in enumerate(ROTULOS):
            if rot in rotulos:
                linhas.append({**dict(zip(por, chave)), "rotulo": rot, "pessoas": len(idx),
                               "%": round(100 * est[g][0][k], 2),
                               "IC95_inf": round(100 * np.percentile(r[:, k], 2.5), 2),
                               "IC95_sup": round(100 * np.percentile(r[:, k], 97.5), 2),
                               "% bruto": round(100 * est[g][1][k], 2)})
    return pd.DataFrame(linhas)


def diferenca_fm(por=None, parte="total", unidade="pessoa", filtro=None, rotulo="FAM_ID", b=B, metodo="precisao"):
    """Diferença F − M (pontos percentuais) de um rótulo, por grupo, com IC por bootstrap."""
    meta, cont = preparar()
    y, pt, wt, st = teste()
    m, c = meta, cont[parte].to_numpy()
    if filtro is not None:
        m, c = meta[filtro], c[np.asarray(filtro)]
    por = [por] if isinstance(por, str) else (por or [])
    k = ROTULOS.index(rotulo)
    rng = np.random.default_rng(SEED + 1)
    chaves = m.groupby(por, observed=True).indices if por else {("todos",): np.arange(len(m))}
    um = lambda ii, w, sexo, ti: corrigir(_proporcoes(c[ii], w, unidade), metodo,
                                         y[ti], pt[ti], wt[ti], st[ti], sexo)[k]
    tudo = np.arange(len(y))
    out = []
    for g, idx in chaves.items():
        sx = m.sexo.to_numpy()[idx]
        iF, iM = idx[sx == "F"], idx[sx == "M"]
        if len(iF) < 20 or len(iM) < 20:
            continue
        d0 = um(iF, np.ones(len(iF)), "F", tudo) - um(iM, np.ones(len(iM)), "M", tudo)
        ds = []
        for _ in range(b):
            ti = rng.integers(0, len(y), len(y))
            ds.append(um(iF, rng.poisson(1.0, len(iF)).astype(float), "F", ti)
                      - um(iM, rng.poisson(1.0, len(iM)).astype(float), "M", ti))
        chave = g if isinstance(g, tuple) else (g,)
        out.append({**dict(zip(por, chave)), "F": len(iF), "M": len(iM), "dif F−M (p.p.)": round(100 * d0, 2),
                    "IC95_inf": round(100 * np.percentile(ds, 2.5), 2), "IC95_sup": round(100 * np.percentile(ds, 97.5), 2)})
    return pd.DataFrame(out)


def exemplos_lead(rotulo="FAM_ID", sexo=None, n=6, max_chars=220, seed=3):
    """Leads curtos (1ª sentença com o rótulo previsto, prob alta) para ilustrar."""
    s = pq.read_table(PROC / "sentencas.parquet", columns=["qid", "sent_idx", "lead", "texto"]).to_pandas()
    p = _predicoes(["qid", "sent_idx", "pred", f"p_{rotulo}"])
    meta, _ = preparar()
    d = s[s.lead].merge(p, on=["qid", "sent_idx"])
    d = d[(d.pred == rotulo) & (d[f"p_{rotulo}"] > 0.8)].join(meta[["titulo", "sexo", "area"]], on="qid")
    if sexo:
        d = d[d.sexo == sexo]
    d = d.sample(min(n, len(d)), random_state=seed)
    d["texto"] = d.texto.str.slice(0, max_chars)
    return d[["titulo", "sexo", "area", "texto"]].reset_index(drop=True)
