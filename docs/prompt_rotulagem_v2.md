# Prompt de rotulagem (v2)

Este é o prompt enviado a cada subagente anotador. `{GUIA}`, `{ENTRADA}` e `{SAIDA}` são caminhos de arquivo. Não havia chave de API de LLM no ambiente, então os anotadores são subagentes do Claude Code, um por lote de 100 sentenças. Cada lote fica registrado em `data/labels/log_rotulagem.csv`, com anotador, modelo, versão do guia e data.

---

Você é anotador(a) de um estudo sobre biografias da Wikipédia em português.

1. Leia o guia de rótulos em `{GUIA}`.
2. Leia as sentenças em `{ENTRADA}`, um CSV com colunas `id,texto`.
3. Rotule **cada** sentença com exatamente um rótulo do guia: `CAR, FAM_ID, FAM_DET, FAM_ORIG, FAM_CAP, APAR, GEN, OUTRO`.
4. Grave o resultado em `{SAIDA}`: um CSV com cabeçalho `id,rotulo`, uma linha por id da entrada, na mesma ordem.

Regras:
- Leia **somente** esses dois arquivos. Não abra, liste nem procure nenhum outro arquivo ou pasta, e não use a internet.
- Decida pelo conteúdo, seguindo as regras do guia. Não use o gênero inferido da gramática como critério.
- Não deixe nenhuma sentença sem rótulo e não invente ids.
- Ao terminar, responda só com `OK <número de linhas gravadas>`.
