"""Etapa 4c: prepara os lotes de rotulagem e consolida as respostas.

  python scripts/lotes.py preparar      -> data/cache/lotes/lote_NN.csv (só id e texto mascarado)
  python scripts/lotes.py consolidar    -> valida data/labels/anotador_*/lote_NN.csv e junta tudo

Os lotes não carregam sexo, área, estrato nem split: o anotador vê só o texto.
"""
import sys

import pandas as pd

from common import DATA

AMOSTRA = DATA / "labels" / "amostra_v2.csv"
LOTES = DATA / "cache" / "lotes"
ROTULOS = {"CAR", "FAM_ID", "FAM_DET", "FAM_ORIG", "FAM_CAP", "APAR", "GEN", "OUTRO"}
TAM = 100
# Proveniência: subagentes do Claude Code (sem chave de API no ambiente). O
# modelo é o alias pedido ao harness; a versão exata não é exposta ao script.
ANOTADORES = {"anotador_a": "claude-sonnet (subagente Claude Code)", "anotador_b": "claude-opus (subagente Claude Code)"}
GUIA = "docs/guia_rotulos_v2.md"
PROMPT = "docs/prompt_rotulagem_v2.md"
N_SEGUNDO = 300  # sentenças do teste com segundo anotador


def preparar():
    a = pd.read_csv(AMOSTRA)
    LOTES.mkdir(parents=True, exist_ok=True)
    for k, i in enumerate(range(0, len(a), TAM), 1):
        a.iloc[i:i + TAM][["sid", "texto_mascarado"]].rename(columns={"sid": "id", "texto_mascarado": "texto"}) \
            .to_csv(LOTES / f"lote_{k:02d}.csv", index=False)
    seg = a[a.split == "teste"].sample(N_SEGUNDO, random_state=7)
    for k, i in enumerate(range(0, len(seg), TAM), 1):
        seg.iloc[i:i + TAM][["sid", "texto_mascarado"]].rename(columns={"sid": "id", "texto_mascarado": "texto"}) \
            .to_csv(LOTES / f"segundo_{k:02d}.csv", index=False)
    print(f"{k} lotes do segundo anotador; lotes principais em {LOTES}")


def validar(path, ids_esperados):
    r = pd.read_csv(path, dtype=str).apply(lambda c: c.str.strip())
    problemas = []
    if list(r.columns) != ["id", "rotulo"]:
        problemas.append(f"cabeçalho {list(r.columns)}")
    else:
        if set(r.id) != set(ids_esperados):
            problemas.append(f"ids: faltam {len(set(ids_esperados) - set(r.id))}, sobram {len(set(r.id) - set(ids_esperados))}")
        inval = r[~r.rotulo.isin(ROTULOS)]
        if len(inval):
            problemas.append(f"{len(inval)} rótulos inválidos: {inval.rotulo.unique()[:5]}")
        if r.id.duplicated().any():
            problemas.append("ids duplicados")
    return r, problemas


def consolidar():
    log = []
    for anot, prefixo in [("anotador_a", "lote"), ("anotador_b", "segundo")]:
        pasta = DATA / "labels" / anot
        partes = []
        for entrada in sorted(LOTES.glob(f"{prefixo}_*.csv")):
            saida = pasta / entrada.name
            if not saida.exists():
                print(f"{anot}: falta {saida.name}")
                continue
            r, prob = validar(saida, pd.read_csv(entrada).id)
            if prob:
                print(f"{anot}/{saida.name}: {'; '.join(prob)}")
                continue
            partes.append(r.assign(lote=entrada.stem))
            log.append({"lote": entrada.stem, "anotador": anot, "modelo": ANOTADORES[anot], "guia": GUIA,
                        "prompt": PROMPT, "n": len(r), "data": "2026-10-31"})
        if partes:
            out = pd.concat(partes)
            out.to_csv(DATA / "labels" / f"rotulos_{anot}.csv", index=False)
            print(f"{anot}: {len(out)} rótulos válidos em {len(partes)} lotes")
    pd.DataFrame(log).to_csv(DATA / "labels" / "log_rotulagem.csv", index=False)


if __name__ == "__main__":
    {"preparar": preparar, "consolidar": consolidar}[sys.argv[1]]()
