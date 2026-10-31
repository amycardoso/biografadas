"""Etapa 4e: rotulagem com o guia v3.

Recebem rótulo novo (anotador A, guia v3):
  - as 350 sentenças de reforço;
  - no treino, as sentenças com rótulo v2 FAM_ID ou FAM_DET (a fronteira
    mudou com o teste da cópula) e as frases de abertura (pos_rel == 0)
    rotuladas OUTRO (a regra 0 mudou);
  - o teste fixo inteiro (622).
O anotador B (guia v3) refaz as mesmas 300 sentenças do teste usadas na v2.

  python scripts/lotes_v3.py preparar
  python scripts/lotes_v3.py consolidar  -> data/labels/rotulos_v3.csv (rótulo final + versão do guia)
"""
import sys

import pandas as pd

from common import DATA
from lotes import ROTULOS, TAM, validar

LAB = DATA / "labels"
LOTES = DATA / "cache" / "lotes_v3"
MODELOS = {"anotador_a_v3": "claude-sonnet (subagente Claude Code)", "anotador_b_v3": "claude-opus (subagente Claude Code)"}


def selecionar():
    u = pd.read_csv(LAB / "amostra_v3.csv")
    r2 = pd.read_csv(LAB / "rotulos_anotador_a.csv").rename(columns={"id": "sid", "rotulo": "rotulo_v2"})
    u = u.merge(r2[["sid", "rotulo_v2"]], on="sid", how="left")
    treino = u.split == "treino"
    motivo = pd.Series("", index=u.index)
    motivo[u.origem == "reforco_v3"] = "reforco"
    motivo[treino & u.rotulo_v2.isin(["FAM_ID", "FAM_DET"]) & (motivo == "")] = "fronteira_fam"
    motivo[treino & (u.pos_rel == 0) & (u.rotulo_v2 == "OUTRO") & (motivo == "")] = "regra_0"
    motivo[(u.split == "teste")] = "teste"
    return u.assign(motivo_v3=motivo)


def preparar():
    u = selecionar()
    sel = u[u.motivo_v3 != ""].sample(frac=1, random_state=11)
    LOTES.mkdir(parents=True, exist_ok=True)
    for k, i in enumerate(range(0, len(sel), TAM), 1):
        sel.iloc[i:i + TAM][["sid", "texto_mascarado"]].rename(columns={"sid": "id", "texto_mascarado": "texto"}) \
            .to_csv(LOTES / f"a_{k:02d}.csv", index=False)
    b_ids = pd.read_csv(LAB / "rotulos_anotador_b.csv").id
    seg = u.set_index("sid").loc[b_ids].reset_index()
    for k, i in enumerate(range(0, len(seg), TAM), 1):
        seg.iloc[i:i + TAM][["sid", "texto_mascarado"]].rename(columns={"sid": "id", "texto_mascarado": "texto"}) \
            .to_csv(LOTES / f"b_{k:02d}.csv", index=False)
    print(sel.motivo_v3.value_counts().to_dict(), f"-> {len(sel)} sentenças em lotes a_*; 300 em b_*")


def consolidar():
    log, por_anot = [], {}
    for anot, pref in [("anotador_a_v3", "a"), ("anotador_b_v3", "b")]:
        partes = []
        for entrada in sorted(LOTES.glob(f"{pref}_*.csv")):
            saida = LAB / anot / entrada.name
            if not saida.exists():
                print(f"{anot}: falta {saida.name}")
                continue
            r, prob = validar(saida, pd.read_csv(entrada).id)
            if prob:
                print(f"{anot}/{saida.name}: {'; '.join(prob)}")
                continue
            partes.append(r)
            log.append({"lote": f"v3_{entrada.stem}", "anotador": anot, "modelo": MODELOS[anot],
                        "guia": "docs/guia_rotulos_v3.md", "prompt": "docs/prompt_rotulagem_v3.md",
                        "n": len(r), "data": "2026-10-31"})
        if partes:
            por_anot[anot] = pd.concat(partes)
            por_anot[anot].to_csv(LAB / f"rotulos_{anot}.csv", index=False)
            print(f"{anot}: {len(por_anot[anot])} rótulos válidos")
    antigo = pd.read_csv(LAB / "log_rotulagem.csv")
    antigo = antigo[~antigo.lote.str.startswith("v3_")]
    pd.concat([antigo, pd.DataFrame(log)]).to_csv(LAB / "log_rotulagem.csv", index=False)

    u = selecionar()
    a3 = por_anot.get("anotador_a_v3", pd.DataFrame(columns=["id", "rotulo"])).set_index("id").rotulo
    u["rotulo"] = u.sid.map(a3).fillna(u.rotulo_v2)
    u["guia"] = u.sid.map(lambda s: "v3" if s in a3.index else "v2")
    u[["sid", "rotulo", "guia", "rotulo_v2", "motivo_v3"]].to_csv(LAB / "rotulos_v3.csv", index=False)
    print(u.guia.value_counts().to_dict(), "| sem rótulo:", int(u.rotulo.isna().sum()))


if __name__ == "__main__":
    {"preparar": preparar, "consolidar": consolidar}[sys.argv[1]]()
