"""Etapa 3: limpeza e segmentação em sentenças.

Lê o cache de wikitext (data/cache/wikitext.jsonl.gz), remove o que não é
prosa (infobox, navboxes, refs, tabelas, categorias, arquivos, seções de
lista) e segmenta em sentenças.

Saídas:
  data/processed/sentencas.parquet   uma linha por sentença (não versionado; CC BY-SA)
  data/processed/artigos_texto.csv   resumo por artigo (versionado)

Colunas de sentencas.parquet: qid, sexo, area, sec_idx, secao, lead, sent_idx,
pos_rel (0 = início, 1 = fim do artigo), palavras, texto.
"""
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd

from coleta import ler_cache
from common import DATA
from texto import secoes, sentencas

OUT = DATA / "processed" / "sentencas.parquet"
RESUMO = DATA / "processed" / "artigos_texto.csv"
SCHEMA = pa.schema([("qid", pa.string()), ("sexo", pa.string()), ("area", pa.string()),
                    ("sec_idx", pa.int16()), ("secao", pa.string()), ("lead", pa.bool_()),
                    ("sent_idx", pa.int32()), ("pos_rel", pa.float32()), ("palavras", pa.int32()),
                    ("texto", pa.string())])


def segmentar(a):
    linhas = []
    for sec_idx, titulo, txt in secoes(a["wikitext"]):
        for s in sentencas(txt):
            linhas.append({"qid": a["qid"], "sexo": a["sexo"], "area": a["area"], "sec_idx": sec_idx,
                           "secao": titulo, "lead": sec_idx == 0, "palavras": len(s.split()), "texto": s})
    n = len(linhas)
    for i, l in enumerate(linhas):
        l["sent_idx"] = i
        l["pos_rel"] = i / (n - 1) if n > 1 else 0.0
    return linhas


def main():
    resumo, buf = [], []
    with pq.ParquetWriter(OUT, SCHEMA, compression="zstd") as w:
        for k, a in enumerate(ler_cache()):
            if a.get("status") != "ok":
                resumo.append({"qid": a["qid"], "sexo": a["sexo"], "area": a["area"], "status": a.get("status")})
                continue
            ls = segmentar(a)
            buf += ls
            resumo.append({"qid": a["qid"], "sexo": a["sexo"], "area": a["area"], "status": "ok",
                           "sentencas": len(ls), "sentencas_lead": sum(l["lead"] for l in ls),
                           "palavras": sum(l["palavras"] for l in ls),
                           "palavras_lead": sum(l["palavras"] for l in ls if l["lead"]),
                           "secoes": len({l["sec_idx"] for l in ls})})
            if len(buf) > 200_000:
                w.write_table(pa.Table.from_pylist(buf, SCHEMA))
                buf = []
            if (k + 1) % 5000 == 0:
                print(f"{k + 1} artigos", flush=True)
        if buf:
            w.write_table(pa.Table.from_pylist(buf, SCHEMA))
    r = pd.DataFrame(resumo).drop_duplicates("qid", keep="last")
    r.to_csv(RESUMO, index=False)
    print(f"{len(r)} artigos, {int(r.sentencas.sum()):,} sentenças -> {OUT.relative_to(DATA.parent)}".replace(",", "."))


if __name__ == "__main__":
    main()
