"""Gera os dados da página estática (docs/data/*.json).

  graficos.json  números das perguntas 1–5 (de data/resultados/ e da população)
  leads.json     leads com sentenças rotuladas, para a busca "leads lado a lado":
                 todas as biografias com algum rótulo de família, gênero ou aparência
                 nas 4 primeiras sentenças do lead, mais uma amostra aleatória
                 das demais (metade por sexo). Até 4 sentenças por lead, cortadas
                 em 320 caracteres. Textos da Wikipédia (CC BY-SA 4.0).

Uso: python scripts/pagina.py
"""
import json

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from common import DATA, ROOT

RES, PROC = DATA / "resultados", DATA / "processed"
OUT = ROOT / "docs" / "data"
ROTULOS = ["CAR", "FAM_ID", "FAM_DET", "FAM_ORIG", "FAM_CAP", "APAR", "GEN", "OUTRO"]
AREAS = {"politica": "Política", "esporte": "Esporte", "musica": "Música", "ciencia_academia": "Ciência",
         "atuacao_tv": "Atuação/TV", "artes_visuais": "Artes visuais", "literatura": "Literatura",
         "jornalismo_comunicacao": "Jornalismo", "religiao": "Religião", "outros": "Outros",
         "sem_ocupacao": "Sem ocupação"}
N_OUTROS, MAX_SENT, MAX_CHARS, SEED = 2500, 4, 320, 5


def ler(nome):
    return pd.read_csv(RES / f"{nome}.csv")


def linhas(df, chave, rotulo=None):
    if rotulo:
        df = df[df.rotulo == rotulo]
    cols = [c for c in [chave, "sexo"] if c in df]
    return [{**{c: (AREAS.get(r[c], r[c]) if c == "area" else r[c]) for c in cols},
             "v": r["%"], "lo": r["IC95_inf"], "hi": r["IC95_sup"]} for _, r in df.iterrows()]


def difs(df, chave=None):
    out = []
    for _, r in df.iterrows():
        d = {"v": r["dif F−M (p.p.)"], "lo": r["IC95_inf"], "hi": r["IC95_sup"], "F": int(r["F"]), "M": int(r["M"])}
        if chave:
            d[chave] = AREAS.get(r[chave], r[chave]) if chave == "area" else r[chave]
        out.append(d)
    return out


def q1():
    pop = pd.read_csv(PROC / "populacao.csv", usecols=["qid", "sexo", "area"])
    pop = pop[pop.sexo.isin(["F", "M"])]
    a = pop.groupby("area").sexo.apply(lambda s: (s == "F").mean() * 100)
    n = pop.groupby("area").size()
    por_area = [{"area": AREAS[k], "v": round(v, 1), "n": int(n[k])} for k, v in a.sort_values().items()]
    cri = pd.read_csv(PROC / "artigos_criacao.csv", usecols=["qid", "ano_criacao"]).merge(pop, on="qid")
    t = cri.groupby("ano_criacao").sexo.agg(lambda s: (s == "F").mean() * 100)
    n2 = cri.groupby("ano_criacao").size()
    por_ano = [{"ano": int(k), "v": round(v, 1), "n": int(n2[k])} for k, v in t.items() if n2[k] >= 50]
    return {"geral": round((pop.sexo == "F").mean() * 100, 1), "n": int(len(pop)), "por_area": por_area, "por_ano": por_ano}


def graficos():
    g = ler("geral_por_sexo")
    tot = g[g.parte == "total"]
    return {
        "q1": q1(),
        "volume": linhas(tot[tot.rotulo.isin(["FAM_DET", "FAM_ID", "GEN", "FAM_CAP"])], "rotulo"),
        "q2": {"lead_sexo": linhas(g[(g.parte == "lead") & (g.rotulo == "FAM_ID")], "rotulo"),
               "dif": difs(ler("q2_famid_dif_fm"))[0], "dif_sem_stubs": difs(ler("q2_famid_lead_sem_stubs"))[0],
               "por_area": linhas(ler("q2_famid_lead_por_area"), "area", "FAM_ID"),
               "dif_area": difs(ler("q2_famid_lead_dif_por_area"), "area"),
               "sens": [{"metodo": r.metodo, "v": r["dif F−M (p.p.)"], "lo": r.IC95_inf, "hi": r.IC95_sup}
                        for _, r in ler("q2_famid_lead_sensibilidade_metodo").iterrows()]},
        "q3": {"por_area": linhas(ler("q3_gen_por_area"), "area", "GEN"),
               "por_nasc": linhas(ler("q3_gen_por_nascimento"), "periodo_nasc", "GEN"),
               "por_criacao": linhas(ler("q3_gen_por_criacao"), "periodo_criacao", "GEN")},
        "q4": linhas(ler("q4_politica_familia").query("parte == 'total'"), "rotulo"),
        "q4_dif": difs(ler("q4_politica_famcap_dif_fm"))[0],
        "q5": {"famid_lead": linhas(ler("q5_por_criacao_lead"), "periodo_criacao", "FAM_ID"),
               "famdet": linhas(ler("q5_por_criacao_total"), "periodo_criacao", "FAM_DET"),
               "gen": linhas(ler("q5_por_criacao_total"), "periodo_criacao", "GEN"),
               "dif_famid": difs(ler("q5_famid_lead_dif_por_criacao"), "periodo_criacao")},
    }


def leads():
    s = pq.read_table(PROC / "sentencas.parquet", columns=["qid", "sent_idx", "lead", "texto"]).to_pandas()
    s = s[s.lead]
    p = pq.read_table(PROC / "predicoes.parquet", columns=["qid", "sent_idx", "pred"]).to_pandas()
    d = s.merge(p, on=["qid", "sent_idx"]).sort_values(["qid", "sent_idx"])
    d["ns"] = d.groupby("qid").cumcount()
    d = d[d.ns < MAX_SENT]
    pop = pd.read_csv(PROC / "populacao.csv", usecols=["qid", "titulo", "sexo", "area"]).set_index("qid")
    meta = pd.read_csv(PROC / "artigos_meta.csv", usecols=["qid", "titulo_atual"]).set_index("qid")
    d = d[d.qid.isin(pop.index[pop.sexo.isin(["F", "M"])])]
    dest = set(d[~d.pred.isin(["CAR", "OUTRO"])].qid)
    resto = pop.loc[sorted(set(d.qid) - dest)]
    rng = np.random.default_rng(SEED)
    outros = []
    for sx in ("F", "M"):
        ids = resto.index[resto.sexo == sx].to_numpy()
        outros += list(rng.choice(ids, min(N_OUTROS // 2, len(ids)), replace=False))
    sel = dest | set(outros)
    d = d[d.qid.isin(sel)]
    out = []
    for q, g in d.groupby("qid", sort=False):
        r = pop.loc[q]
        titulo = meta.titulo_atual.get(q, r.titulo) if q in meta.index else r.titulo
        out.append([r.titulo, titulo, r.sexo, AREAS.get(r.area, r.area),
                    [[ROTULOS.index(pr), t[:MAX_CHARS] + ("…" if len(t) > MAX_CHARS else "")] for pr, t in zip(g.pred, g.texto)]])
    out.sort(key=lambda x: x[0])
    return {"rotulos": ROTULOS, "n_com_destaque": len(dest), "n_amostra_outros": len(outros), "leads": out}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for nome, dados in [("graficos", graficos()), ("leads", leads())]:
        f = OUT / f"{nome}.json"
        f.write_text(json.dumps(dados, ensure_ascii=False, separators=(",", ":")))
        print(f"{f.relative_to(ROOT)}: {f.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
