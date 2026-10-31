"""Etapa 4d: fine-tuning do BERTimbau base (neuralmind/bert-base-portuguese-cased).

Roda no ambiente .venv-ml (Python 3.12, torch + transformers); usa MPS se
disponível. Para não pesar na máquina: batch 16, max_len 128, até 4 épocas.
A época é escolhida pelo macro-F1 num conjunto de validação separado POR
PESSOA dentro do treino (10%). O teste fixo só é usado na predição final.

Saídas: data/labels/predicoes/bertimbau.csv e data/labels/bertimbau_treino.json
(o modelo treinado fica em data/cache/bertimbau/, não versionado).

Uso: .venv-ml/bin/python scripts/bertimbau.py
"""
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import f1_score
from torch.utils.data import DataLoader, TensorDataset
from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "data" / "labels"
CACHE = ROOT / "data" / "cache" / "bertimbau"
MODELO = "neuralmind/bert-base-portuguese-cased"
ROTULOS = ["CAR", "FAM_ID", "FAM_DET", "FAM_ORIG", "FAM_CAP", "APAR", "GEN", "OUTRO"]
CFG = {"max_len": 128, "batch": 16, "epocas": 4, "lr": 3e-5, "warmup": 0.1, "seed": 13}


def dados():
    a = pd.read_csv(LAB / "amostra_v2.csv")
    r = pd.read_csv(LAB / "rotulos_anotador_a.csv", dtype=str).rename(columns={"id": "sid"})
    d = a.merge(r[["sid", "rotulo"]], on="sid")
    h = d.qid.map(lambda q: int(hashlib.md5(q.encode()).hexdigest()[:6], 16) / 0xFFFFFF)
    d["parte"] = np.where(d.split == "teste", "teste", np.where(h < 0.10, "val", "treino"))
    return d


def tensores(tok, df):
    enc = tok(list(df.texto_mascarado), truncation=True, max_length=CFG["max_len"], padding="max_length",
              return_tensors="pt")
    y = torch.tensor([ROTULOS.index(r) for r in df.rotulo])
    return TensorDataset(enc["input_ids"], enc["attention_mask"], y)


@torch.no_grad()
def prever(modelo, ds, dev):
    modelo.eval()
    out = []
    for ids, mask, _ in DataLoader(ds, batch_size=64):
        out.append(modelo(input_ids=ids.to(dev), attention_mask=mask.to(dev)).logits.argmax(-1).cpu())
    return torch.cat(out).numpy()


def main():
    torch.manual_seed(CFG["seed"])
    dev = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    d = dados()
    tr, va, te = (d[d.parte == p] for p in ("treino", "val", "teste"))
    print(f"dispositivo {dev}; treino {len(tr)}, val {len(va)}, teste {len(te)}", flush=True)

    tok = AutoTokenizer.from_pretrained(MODELO)
    modelo = AutoModelForSequenceClassification.from_pretrained(MODELO, num_labels=len(ROTULOS)).to(dev)
    ds_tr, ds_va, ds_te = tensores(tok, tr), tensores(tok, va), tensores(tok, te)

    cont = tr.rotulo.value_counts().reindex(ROTULOS).fillna(0).to_numpy() + 1
    pesos = torch.tensor((cont.sum() / (len(ROTULOS) * cont)) ** 0.5, dtype=torch.float).to(dev)
    perda = torch.nn.CrossEntropyLoss(weight=pesos)
    opt = torch.optim.AdamW(modelo.parameters(), lr=CFG["lr"], weight_decay=0.01)
    passos = CFG["epocas"] * int(np.ceil(len(ds_tr) / CFG["batch"]))
    sched = get_linear_schedule_with_warmup(opt, int(CFG["warmup"] * passos), passos)

    hist, melhor = [], -1
    for ep in range(1, CFG["epocas"] + 1):
        modelo.train()
        t0, soma = time.time(), 0.0
        for ids, mask, y in DataLoader(ds_tr, batch_size=CFG["batch"], shuffle=True):
            opt.zero_grad()
            logits = modelo(input_ids=ids.to(dev), attention_mask=mask.to(dev)).logits
            loss = perda(logits, y.to(dev))
            loss.backward()
            torch.nn.utils.clip_grad_norm_(modelo.parameters(), 1.0)
            opt.step()
            sched.step()
            soma += loss.item()
        pv = prever(modelo, ds_va, dev)
        f1 = f1_score(ds_va.tensors[2].numpy(), pv, average="macro", labels=range(len(ROTULOS)), zero_division=0)
        hist.append({"epoca": ep, "perda": round(soma / len(ds_tr) * CFG["batch"], 4), "val_macro_f1": round(f1, 3),
                     "segundos": round(time.time() - t0)})
        print(hist[-1], flush=True)
        if f1 > melhor:
            melhor = f1
            CACHE.mkdir(parents=True, exist_ok=True)
            modelo.save_pretrained(CACHE)
            tok.save_pretrained(CACHE)

    modelo = AutoModelForSequenceClassification.from_pretrained(CACHE).to(dev)
    pt = prever(modelo, ds_te, dev)
    (LAB / "predicoes").mkdir(exist_ok=True)
    pd.DataFrame({"sid": te.sid, "pred": [ROTULOS[i] for i in pt]}).to_csv(LAB / "predicoes" / "bertimbau.csv", index=False)
    (LAB / "bertimbau_treino.json").write_text(json.dumps(
        {"modelo": MODELO, "config": CFG, "dispositivo": str(dev), "historico": hist,
         "melhor_val_macro_f1": round(melhor, 3), "n": {"treino": len(tr), "val": len(va), "teste": len(te)}},
        ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
