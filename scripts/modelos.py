"""Etapa 4d: baselines (regex e TF-IDF + regressão logística) e avaliação comum.

Treino e teste vêm de data/labels/amostra_v2.csv (split por pessoa). Os rótulos
de referência são os do anotador A (data/labels/rotulos_anotador_a.csv). As
predições de cada modelo no teste ficam em data/labels/predicoes/<modelo>.csv,
e as métricas em data/labels/metricas.json.

Uso: python scripts/modelos.py
"""
import json
import re

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, cohen_kappa_score, confusion_matrix, f1_score
from sklearn.pipeline import make_pipeline, make_union

from common import DATA
from texto import APARENCIA, CONJUGE, FAMILIA, FILIACAO

LAB = DATA / "labels"
PRED = LAB / "predicoes"
ROTULOS = ["CAR", "FAM_ID", "FAM_DET", "FAM_ORIG", "FAM_CAP", "APAR", "GEN", "OUTRO"]
GEN_RX = re.compile(r"\bprimeir[ao] (mulher|homem)|\buma das (poucas|primeiras) mulheres|\bpioneir[ao] entre", re.I)


def carregar():
    a = pd.read_csv(LAB / "amostra_v2.csv")
    r = pd.read_csv(LAB / "rotulos_anotador_a.csv", dtype=str).rename(columns={"id": "sid"})
    return a.merge(r[["sid", "rotulo"]], on="sid", how="inner")


def regex(textos):
    out = []
    for t in textos:
        if GEN_RX.search(t):
            out.append("GEN")
        elif APARENCIA.search(t):
            out.append("APAR")
        elif CONJUGE.search(t):
            out.append("FAM_DET")
        elif FILIACAO.search(t):
            out.append("FAM_ORIG")
        elif FAMILIA.search(t):
            out.append("FAM_DET")
        else:
            out.append("CAR")
    return out


def tfidf_logreg(treino, teste):
    pipe = make_pipeline(
        make_union(TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True),
                   TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2, sublinear_tf=True)),
        LogisticRegression(max_iter=3000, class_weight="balanced", C=5))
    pipe.fit(treino.texto_mascarado, treino.rotulo)
    return pipe.predict(teste.texto_mascarado)


def metricas(y, p):
    rep = classification_report(y, p, labels=ROTULOS, output_dict=True, zero_division=0)
    return {
        "macro_f1": round(f1_score(y, p, labels=ROTULOS, average="macro", zero_division=0), 3),
        "acuracia": round(float(np.mean(np.asarray(y) == np.asarray(p))), 3),
        "kappa": round(cohen_kappa_score(y, p), 3),
        "f1_por_rotulo": {k: round(rep[k]["f1-score"], 3) for k in ROTULOS},
        "suporte": {k: int(rep[k]["support"]) for k in ROTULOS},
        "matriz": confusion_matrix(y, p, labels=ROTULOS).tolist(),
    }


def avaliar_todos():
    """Junta as predições de todos os modelos em PRED e grava metricas.json."""
    d = carregar()
    teste = d[d.split == "teste"].set_index("sid")
    res = {"n_teste": len(teste), "n_treino": int((d.split == "treino").sum()), "rotulos": ROTULOS, "modelos": {}}
    for f in sorted(PRED.glob("*.csv")):
        p = pd.read_csv(f).set_index("sid").reindex(teste.index)
        res["modelos"][f.stem] = metricas(teste.rotulo, p.pred.fillna("OUTRO"))
    b = LAB / "rotulos_anotador_b.csv"
    if b.exists():
        rb = pd.read_csv(b, dtype=str).rename(columns={"id": "sid"}).set_index("sid")
        comum = teste.index.intersection(rb.index)
        res["anotador_b_vs_a"] = {"n": len(comum), **metricas(teste.loc[comum, "rotulo"], rb.loc[comum, "rotulo"])}
    (LAB / "metricas.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    for m, v in res["modelos"].items():
        print(f"{m:15s} macro-F1 {v['macro_f1']:.3f}  acc {v['acuracia']:.3f}  κ {v['kappa']:.3f}")
    if "anotador_b_vs_a" in res:
        v = res["anotador_b_vs_a"]
        print(f"anotador B vs A (n={v['n']}): κ {v['kappa']:.3f}  macro-F1 {v['macro_f1']:.3f}")
    return res


def main():
    d = carregar()
    treino, teste = d[d.split == "treino"], d[d.split == "teste"]
    PRED.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"sid": teste.sid, "pred": regex(teste.texto_mascarado)}).to_csv(PRED / "regex.csv", index=False)
    pd.DataFrame({"sid": teste.sid, "pred": tfidf_logreg(treino, teste)}).to_csv(PRED / "tfidf_logreg.csv", index=False)
    avaliar_todos()


if __name__ == "__main__":
    main()
