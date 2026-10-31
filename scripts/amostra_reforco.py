"""Etapa 4e: reforço de FAM_ID para o guia v3.

Acrescenta à amostra v2 cerca de 350 sentenças (175 por sexo) com construções
de cônjuge ou família que podem definir a pessoa ("esposa/marido/viúva/
mulher/companheira/filha/mãe de X", "casou-se com", "primeira-dama"). Só entram
pessoas do TREINO, para não contaminar o teste fixo, e no máximo 1 sentença
por pessoa, metade do lead e metade do corpo.

Pesos: pós-estratificação sobre a união v2 + reforço. Toda sentença que casa
com o padrão de reforço passa ao estrato "reforco" (célula sexo × reforco);
as demais mantêm a célula sexo × área × estrato da v2. peso_v3 = N_célula / n_célula.

Saída: data/labels/amostra_v3.csv (v2 + reforço, com estrato_v3, peso_v3 e origem)
"""
import re

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from amostra import SENT, POP, estrato, split_de
from common import DATA
from texto import mascarar_nome, mascarar_pronomes

LAB = DATA / "labels"
REFORCO = re.compile(
    r"\b([Ee]sposa|[Mm]arido|[Ee]sposo|[Vv]i[uú]v[ao]|[Mm]ulher|[Cc]ompanheir[oa]|[Ff]ilh[oa]|[Mm][ãa]e|[Pp]ai|[Nn]or[ao]|[Gg]enro|[Cc]unhad[oa])"
    r" d[eoa]s? (?:\w+ ){0,4}?[A-ZÁÉÍÓÚ]|\b[Cc]asou(-se)? com|\b[Cc]asad[oa] com|\bprimeira[- ]dama")
POR_SEXO = 175
SEED = 2026


def main():
    v2 = pd.read_csv(LAB / "amostra_v2.csv")
    s = pq.read_table(SENT).to_pandas()
    s = s[s.palavras.between(4, 120)]
    s["split"] = s.qid.map(split_de)
    s["estrato"] = estrato(s)
    s["reforco"] = s.texto.str.contains(REFORCO)
    chave = s.qid + "#" + s.sent_idx.astype(str)
    v2_chave = set(pq.read_table(SENT, columns=["qid", "sent_idx", "texto"]).to_pandas()
                   .merge(v2[["qid", "texto"]], on=["qid", "texto"]).pipe(lambda d: d.qid + "#" + d.sent_idx.astype(str)))

    cand = s[s.reforco & (s.split == "treino") & ~chave.isin(v2_chave)]
    cand = cand.iloc[np.random.default_rng(SEED).permutation(len(cand))].drop_duplicates("qid")
    partes = []
    for sexo in ("F", "M"):
        c = cand[cand.sexo == sexo]
        partes += [c[c.lead].head(POR_SEXO // 2 + 1), c[~c.lead].head(POR_SEXO // 2)]
    novo = pd.concat(partes)

    titulos = pd.read_csv(POP, usecols=["qid", "titulo"]).set_index("qid").titulo
    novo["texto_mascarado"] = [mascarar_pronomes(mascarar_nome(t, titulos.get(q, ""))) for t, q in zip(novo.texto, novo.qid)]
    novo["origem"] = "reforco_v3"
    novo["estrato"] = "reforco"
    novo["sid"] = [f"r{i:05d}" for i in range(1, len(novo) + 1)]

    v2 = v2.assign(origem="v2")
    u = pd.concat([v2, novo[[c for c in v2.columns if c != "peso"]]], ignore_index=True)

    # pós-estratificação
    s["celula"] = np.where(s.reforco, s.sexo + "|reforco", s.sexo + "|" + s.area + "|" + s.estrato)
    u_ref = u.texto.str.contains(REFORCO)
    u["estrato_v3"] = np.where(u_ref, "reforco", u.estrato)
    u["celula"] = np.where(u_ref, u.sexo + "|reforco", u.sexo + "|" + u.area + "|" + u.estrato)
    N = s.celula.value_counts()
    n = u.celula.value_counts()
    u["peso_v3"] = (u.celula.map(N) / u.celula.map(n)).round(3)
    u = u.drop(columns=["celula"])
    u.to_csv(LAB / "amostra_v3.csv", index=False)
    print(f"reforço: {len(novo)} sentenças ({novo.sexo.value_counts().to_dict()}; lead {int(novo.lead.sum())})")
    print(f"amostra_v3: {len(u)}; teste {int((u.split == 'teste').sum())} (inalterado)")
    print(u.groupby(["estrato_v3", "sexo"]).size().unstack())


if __name__ == "__main__":
    main()
