"""Etapa 5a: aplica o BERTimbau v3 a todas as sentenças.

Lê data/processed/sentencas.parquet, aplica o mesmo mascaramento da rotulagem
(nome -> [PESSOA], pronomes -> [PRON]) e classifica com o modelo em
data/cache/bertimbau_v3/. Processa em blocos de 50 mil sentenças, gravados em
data/cache/inferencia/ (retomável). No fim, junta tudo em
data/processed/predicoes.parquet (não versionado): qid, sent_idx, pred e
p_<RÓTULO> (probabilidade de cada uma das 8 classes).

Para não travar a máquina, roda com nice e batch moderado. As sentenças são
ordenadas por tamanho dentro de cada bloco (padding dinâmico).

Uso: nice -n 10 .venv-ml/bin/python scripts/inferencia.py
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from texto import mascarar_nome, mascarar_pronomes  # noqa: E402

PROC = ROOT / "data" / "processed"
MODELO = ROOT / "data" / "cache" / "bertimbau_v3"
BLOCOS = ROOT / "data" / "cache" / "inferencia"
OUT = PROC / "predicoes.parquet"
ROTULOS = ["CAR", "FAM_ID", "FAM_DET", "FAM_ORIG", "FAM_CAP", "APAR", "GEN", "OUTRO"]
TAM_BLOCO, BATCH, MAX_LEN = 50_000, 64, 128


@torch.no_grad()
def classificar(modelo, tok, textos, dev):
    ordem = np.argsort([len(t) for t in textos])
    probs = np.empty((len(textos), len(ROTULOS)), dtype=np.float32)
    for i in range(0, len(textos), BATCH):
        idx = ordem[i:i + BATCH]
        enc = tok([textos[j] for j in idx], truncation=True, max_length=MAX_LEN, padding=True, return_tensors="pt")
        prob = torch.softmax(modelo(**{k: v.to(dev) for k, v in enc.items()}).logits.float(), -1).cpu()
        probs[idx] = prob.numpy()
    return probs


def main():
    dev = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    tok = AutoTokenizer.from_pretrained(MODELO)
    modelo = AutoModelForSequenceClassification.from_pretrained(MODELO).to(dev).eval()
    s = pq.read_table(PROC / "sentencas.parquet", columns=["qid", "sent_idx", "texto"]).to_pandas()
    titulos = pd.read_csv(PROC / "populacao.csv", usecols=["qid", "titulo"]).set_index("qid").titulo
    BLOCOS.mkdir(parents=True, exist_ok=True)
    n_blocos = int(np.ceil(len(s) / TAM_BLOCO))
    print(f"{len(s):,} sentenças em {n_blocos} blocos; dispositivo {dev}".replace(",", "."), flush=True)
    t0 = time.time()
    for b in range(n_blocos):
        arq = BLOCOS / f"bloco_{b:03d}.parquet"
        if arq.exists():
            continue
        parte = s.iloc[b * TAM_BLOCO:(b + 1) * TAM_BLOCO]
        textos = [mascarar_pronomes(mascarar_nome(t, titulos.get(q, ""))) for t, q in zip(parte.texto, parte.qid)]
        probs = classificar(modelo, tok, textos, dev)
        cols = {"qid": parte.qid.to_numpy(), "sent_idx": parte.sent_idx.to_numpy(),
                "pred": np.array(ROTULOS)[probs.argmax(1)]}
        cols.update({f"p_{r}": probs[:, k] for k, r in enumerate(ROTULOS)})
        pq.write_table(pa.table(cols), arq)
        feito = b + 1
        print(f"bloco {feito}/{n_blocos}  {(time.time() - t0) / 60:.1f} min", flush=True)
    pq.write_table(pa.concat_tables([pq.read_table(f) for f in sorted(BLOCOS.glob("bloco_*.parquet"))]), OUT)
    print(f"-> {OUT.relative_to(ROOT)}", flush=True)


if __name__ == "__main__":
    main()
