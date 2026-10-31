"""Etapa 4a: amostra de sentenças para rotulagem.

Desenho:
- O split treino/teste é feito por PESSOA, com hash estável do QID: cerca de
  15% das pessoas vão para o teste fixo.
- A amostra é estratificada por sexo × área. Dentro de cada célula há 4 estratos
  disjuntos, aplicados nesta ordem:
    raro   lead com termo de cônjuge, ou marcação de gênero ("primeira mulher",
           "uma das poucas mulheres"); garante casos de FAM_ID e GEN
    cand   qualquer termo de família, aparência ou gênero (regex de texto.py)
    lead   demais sentenças do lead
    corpo  demais sentenças
- Peso de amostragem = N_estrato / n_estrato, para estimativas na população.
- No máximo 2 sentenças por pessoa e estrato, para espalhar entre artigos.

Saídas: data/labels/amostra_v2.csv e data/labels/vazamento_genero.json
"""
import hashlib
import json
import warnings

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from common import DATA
from texto import APARENCIA, CONJUGE, FAMILIA, FILIACAO, GENERO, mascarar_nome, mascarar_pronomes

warnings.filterwarnings("ignore", message="This pattern is interpreted as a regular expression")

SENT = DATA / "processed" / "sentencas.parquet"
POP = DATA / "processed" / "populacao.csv"
OUT_DIR = DATA / "labels"
ALOCACAO = {"raro": 20, "cand": 80, "lead": 40, "corpo": 40}  # por célula sexo × área
FRACAO_TESTE = 0.15
SEED = 42
RARO_GEN = r"\bprimeir[ao] (mulher|homem)|\buma das (poucas|primeiras) mulheres|\bum dos (poucos|primeiros) homens"


def split_de(qid):
    h = int(hashlib.sha1(qid.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
    return "teste" if h < FRACAO_TESTE else "treino"


def estrato(df):
    t = df.texto
    cand = (t.str.contains(FAMILIA) | t.str.contains(CONJUGE) | t.str.contains(FILIACAO)
            | t.str.contains(APARENCIA) | t.str.contains(GENERO))
    raro = (df.lead & t.str.contains(CONJUGE)) | t.str.contains(RARO_GEN, case=False, regex=True)
    return np.select([raro, cand, df.lead], ["raro", "cand", "lead"], "corpo")


def vazamento(amostra):
    """AUC de um classificador que prevê o sexo a partir do texto mascarado."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import GroupKFold, cross_val_predict
    from sklearn.metrics import roc_auc_score
    y = (amostra.sexo == "F").astype(int)
    res = {}
    for col in ["texto_so_nome", "texto_mascarado"]:
        pipe = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)
        x = pipe.fit_transform(amostra[col])
        p = cross_val_predict(LogisticRegression(max_iter=2000, C=2), x, y, cv=GroupKFold(5),
                              groups=amostra.qid, method="predict_proba")[:, 1]
        res[col] = round(float(roc_auc_score(y, p)), 3)
    return res


def main():
    s = pq.read_table(SENT).to_pandas()
    s = s[s.palavras.between(4, 120)]
    s["estrato"] = estrato(s)
    s["split"] = s.qid.map(split_de)
    N = s.groupby(["sexo", "area", "estrato"]).size().rename("N")

    rng = np.random.default_rng(SEED)
    s = s.iloc[rng.permutation(len(s))]
    s = s.groupby(["qid", "estrato"]).head(2)  # no máximo 2 por pessoa e estrato
    partes = []
    for (sexo, area, est), g in s.groupby(["sexo", "area", "estrato"]):
        partes.append(g.head(ALOCACAO[est]))
    a = pd.concat(partes)
    a = a.join(N, on=["sexo", "area", "estrato"])
    a["n"] = a.groupby(["sexo", "area", "estrato"]).qid.transform("size")
    a["peso"] = (a.N / a.n).round(3)

    titulos = pd.read_csv(POP, usecols=["qid", "titulo"]).set_index("qid").titulo
    a["texto_so_nome"] = [mascarar_nome(t, titulos.get(q, "")) for t, q in zip(a.texto, a.qid)]
    a["texto_mascarado"] = a.texto_so_nome.map(mascarar_pronomes)
    a = a.sample(frac=1, random_state=SEED).reset_index(drop=True)
    a.insert(0, "sid", [f"s{i:05d}" for i in range(1, len(a) + 1)])
    cols = ["sid", "qid", "sexo", "area", "estrato", "peso", "split", "lead", "secao", "pos_rel",
            "palavras", "texto", "texto_mascarado"]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    a[cols].to_csv(OUT_DIR / "amostra_v2.csv", index=False)

    vz = vazamento(a)
    (OUT_DIR / "vazamento_genero.json").write_text(json.dumps(
        {"descricao": "AUC (GroupKFold por pessoa) de TF-IDF+LogReg prevendo sexo=F a partir do texto",
         "auc": vz, "n": len(a)}, ensure_ascii=False, indent=1))
    print(f"{len(a)} sentenças, {a.qid.nunique()} pessoas")
    print(pd.crosstab([a.split], a.sexo, margins=True))
    print(pd.crosstab(a.estrato, a.sexo))
    print("vazamento de gênero (AUC):", vz)


if __name__ == "__main__":
    main()
