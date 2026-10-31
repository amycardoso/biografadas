"""Etapa 5c: gera as tabelas das perguntas 2–5 em data/resultados/ (versionado).

Todas as proporções são em %, com correção por precisão ponderada (ver
analise.py) e IC de 95% por bootstrap (pessoas + teste). Unidade principal:
PESSOA (média, entre as biografias, da fração das suas sentenças com o rótulo).

Uso: python scripts/resultados.py
"""
import json

import numpy as np
import pandas as pd

import analise as a
from common import DATA

OUT = DATA / "resultados"
FAM_GEN = ["FAM_ID", "FAM_DET", "FAM_ORIG", "FAM_CAP", "APAR", "GEN"]


def salvar(df, nome):
    df.to_csv(OUT / f"{nome}.csv", index=False)
    print(f"{nome}: {len(df)} linhas", flush=True)
    return df


def pct_pessoas_com(rotulo, parte="lead"):
    """% de pessoas com ao menos uma sentença prevista com o rótulo (bruto, sem correção)."""
    meta, cont = a.preparar()
    tem = cont[parte][rotulo] > 0
    t = pd.DataFrame({"sexo": meta.sexo, "area": meta.area, "tem": tem})
    g = t.groupby(["sexo"]).tem.agg(["mean", "size"]).reset_index()
    g["mean"] = (100 * g["mean"]).round(2)
    return g.rename(columns={"mean": f"% pessoas com {rotulo} ({parte}, bruto)", "size": "pessoas"})


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    meta, _ = a.preparar()
    nao_stub = ~meta.stub

    # visão geral: todas as classes, por sexo, lead / corpo / total
    partes = [a.estimar("sexo", parte=p).assign(parte=p) for p in ("lead", "corpo", "total")]
    salvar(pd.concat(partes), "geral_por_sexo")
    salvar(a.estimar("sexo", parte="lead", unidade="sentenca").assign(parte="lead"), "geral_por_sexo_unidade_sentenca")

    # Q2 identidade emprestada: FAM_ID no lead
    salvar(pd.concat([a.diferenca_fm(None, parte=p, rotulo="FAM_ID").assign(parte=p) for p in ("lead", "total")]),
           "q2_famid_dif_fm")
    salvar(a.diferenca_fm("area", parte="lead", rotulo="FAM_ID"), "q2_famid_lead_dif_por_area")
    salvar(a.estimar(["area", "sexo"], parte="lead", rotulos=["FAM_ID"]), "q2_famid_lead_por_area")
    salvar(a.diferenca_fm(None, parte="lead", rotulo="FAM_ID", filtro=nao_stub).assign(filtro="sem stubs"),
           "q2_famid_lead_sem_stubs")
    salvar(pct_pessoas_com("FAM_ID", "lead"), "q2_pessoas_com_famid_lead")
    sens = []
    for met in ("nenhuma", "precisao", "acc"):
        sens.append(a.diferenca_fm(None, parte="lead", rotulo="FAM_ID", metodo=met).assign(metodo=met))
    salvar(pd.concat(sens), "q2_famid_lead_sensibilidade_metodo")

    # Q3 marcação de gênero
    salvar(a.estimar(["area", "sexo"], parte="total", rotulos=["GEN"]), "q3_gen_por_area")
    salvar(a.estimar(["periodo_nasc", "sexo"], parte="total", rotulos=["GEN"]), "q3_gen_por_nascimento")
    salvar(a.estimar(["periodo_criacao", "sexo"], parte="total", rotulos=["GEN"]), "q3_gen_por_criacao")
    salvar(a.diferenca_fm(None, parte="lead", rotulo="GEN"), "q3_gen_lead_dif_fm")

    # Q4 família como capital em política
    pol = meta.area == "politica"
    salvar(pd.concat([a.estimar("sexo", parte=p, filtro=pol, rotulos=["FAM_CAP", "FAM_ORIG", "FAM_ID", "FAM_DET"]).assign(parte=p)
                      for p in ("lead", "total")]), "q4_politica_familia")
    salvar(a.diferenca_fm(None, parte="total", rotulo="FAM_CAP", filtro=pol), "q4_politica_famcap_dif_fm")
    salvar(a.diferenca_fm("area", parte="total", rotulo="FAM_CAP"), "q4_famcap_dif_por_area")

    # Q5 tempo: período de criação do artigo
    salvar(a.estimar(["periodo_criacao", "sexo"], parte="total", rotulos=["CAR"] + FAM_GEN), "q5_por_criacao_total")
    salvar(a.estimar(["periodo_criacao", "sexo"], parte="lead", rotulos=["FAM_ID", "FAM_DET", "GEN"]), "q5_por_criacao_lead")
    salvar(a.diferenca_fm("periodo_criacao", parte="lead", rotulo="FAM_ID"), "q5_famid_lead_dif_por_criacao")
    salvar(a.diferenca_fm("periodo_criacao", parte="total", rotulo="FAM_DET"), "q5_famdet_dif_por_criacao")

    # exemplos de leads (curtos)
    ex = pd.concat([a.exemplos_lead("FAM_ID", "F", 6).assign(rotulo="FAM_ID"),
                    a.exemplos_lead("FAM_ID", "M", 4).assign(rotulo="FAM_ID"),
                    a.exemplos_lead("GEN", "F", 4).assign(rotulo="GEN"),
                    a.exemplos_lead("FAM_CAP", None, 4).assign(rotulo="FAM_CAP")])
    salvar(ex, "exemplos_leads")

    resumo = {"pessoas": int(len(meta)), "F": int((meta.sexo == "F").sum()), "M": int((meta.sexo == "M").sum()),
              "bootstrap_replicas": a.B, "metodo_principal": "precisao ponderada por sexo",
              "unidade_principal": "pessoa"}
    (OUT / "resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
