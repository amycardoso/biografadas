# biografadas

Como a Wikipédia em português descreve as biografias de **mulheres e homens brasileiros**: quanto do texto trata de casamento, filhos, aparência e de ser "esposa de" alguém, em comparação com obra e carreira, e de que forma isso acontece.

> Status: **etapas 1 a 4 concluídas** (população, coleta, segmentação, classificador). Próxima: aplicar o classificador às 1,1 milhão de sentenças e responder às perguntas.

## Perguntas

1. **Quem tem biografia:** qual a fração de mulheres por área, por década de nascimento e por ano de criação do artigo? Campanhas como Women in Red deixaram marca visível?
2. **Identidade emprestada:** com que frequência a mulher é apresentada pelo cônjuge, pelo pai ou por um filho ("a última esposa do sambista Cartola"), sobretudo no primeiro parágrafo? Em que áreas isso acontece mais?
3. **Marcação de gênero:** frases como "primeira mulher a…" e "uma das poucas mulheres…" funcionam como reconhecimento ou como marca de "outro"?
4. **Família como capital:** como a genealogia ("filho do senador…", "neta do governador…") aparece nas biografias de políticos, por gênero?
5. **Tempo:** os artigos recentes são escritos de outro jeito?

## Método

- **Unidade de análise:** a sentença. Léxicos e regex amplos (`scripts/texto.py`) servem só como pré-filtro de candidatas.
- **Rótulos:** carreira, família como identidade, família como detalhe, filiação, família como capital, aparência, marcação de gênero e outro. Os rótulos são atribuídos por um LLM com o nome do biografado mascarado (`[PESSOA]`), seguindo um guia de anotação.
- **Validação manual:** uma amostra rotulada às cegas por uma pessoa, com concordância medida pelo κ de Cohen entre a pessoa e o LLM.
- **Comparação de modelos:** regex, LLM zero-shot e BERTimbau ajustado com os rótulos, avaliados contra o conjunto validado à mão (F1 por classe e custo).
- **Análise:** diferenças F−M por área, posição no texto (lead ou corpo), década de nascimento e ano de criação do artigo, com intervalos de confiança e controle de tamanho do artigo.

## Resultados até agora

**População** ([`notebooks/01_populacao.ipynb`](notebooks/01_populacao.ipynb)): segundo o Wikidata, consultado em 31/10/2026, há **45.788** pessoas com cidadania brasileira e artigo na pt.wiki. São **9.281 mulheres (20,3%)**, 36.116 homens e 391 sem sexo registrado ou com outro valor.

| Área | Mulheres | Homens | % mulheres |
|---|---:|---:|---:|
| política / direito / militar | 1.170 | 11.633 | 9,1 |
| esporte | 1.653 | 7.144 | 18,8 |
| música | 927 | 2.897 | 24,2 |
| ciência / academia | 902 | 2.912 | 23,6 |
| atuação / TV | 1.975 | 1.676 | **54,1** |
| artes visuais / cinema / arquitetura | 558 | 1.975 | 22,0 |
| literatura | 684 | 1.815 | 27,4 |
| jornalismo / comunicação | 594 | 1.353 | 30,5 |
| religião | 80 | 1.282 | 5,9 |
| sem ocupação no Wikidata | 519 | 2.647 | 16,4 |

A participação das mulheres cresce com a década de nascimento: 6,1% entre os nascidos no século XIX, 15,8% entre 1900 e 1949, 23,9% entre 1950 e 1979 e 33,9% de 1980 em diante.

**Coleta e segmentação** ([`notebooks/02_coleta.ipynb`](notebooks/02_coleta.ipynb)): baixei o texto de 45.383 dos 45.397 artigos de pessoas com sexo F ou M. Os 14 restantes não existem mais na pt.wiki (sitelinks desatualizados no Wikidata), e 260 foram alcançados por redirecionamento. A segmentação deu **1.120.642 sentenças**: 243.631 de mulheres e 877.011 de homens; 15% delas estão no lead.

| | Mulheres | Homens |
|---|---:|---:|
| palavras de prosa (mediana) | 330 | 303 |
| sentenças (mediana) | 16 | 15 |
| palavras no lead (mediana) | 48 | 45 |
| % stubs (< 150 palavras) | 21,2 | 25,7 |

Os artigos de mulheres são um pouco mais longos no geral, e a diferença varia por área. Em política, a mediana das mulheres é 1,42 vez a dos homens: há muitos stubs de políticos homens (34%). Em esporte é o contrário, 0,71 vez, com 33% de stubs entre as atletas. Isso bate com o "teto de vidro" de Wagner et al. (2016): as mulheres que entram na Wikipédia tendem a ser mais notáveis.

**Ano de criação do artigo** (estimado pelo pageid; o erro de calibração na validação cruzada tem mediana de 1 dia, p90 de 4 dias e 99% das estimativas a menos de 1 ano): a fração de mulheres entre as biografias **criadas** em cada ano mudou muito.

| período de criação | artigos criados | % mulheres |
|---|---:|---:|
| 2002–2006 | 7.238 | 20,3 |
| 2007–2011 | 17.417 | 13,5 |
| 2012–2016 | 8.292 | 21,9 |
| 2017–2021 | 7.782 | 23,4 |
| 2022–2026 | 4.654 | **39,0** |

Entre 2022 e 2023, cerca de 41 a 47% das biografias de brasileiros criadas eram de mulheres. Isso é compatível com campanhas como Women in Red e as editatonas da Wikimedia Brasil, mas ainda não é prova de causa. A pergunta 1 vai cruzar esse dado com o histórico de edições e com as categorias e predefinições de projetos de gênero.

**Classificador de sentenças** ([`notebooks/03_classificador.ipynb`](notebooks/03_classificador.ipynb)): os modelos foram treinados com 3.332 sentenças rotuladas e avaliados num teste fixo de 622 sentenças, de pessoas que não aparecem no treino. A referência é o anotador A, um LLM.

| modelo | macro-F1 | acurácia | κ vs A |
|---|---:|---:|---:|
| regex (léxicos de `texto.py`) | 0,34 | 0,52 | 0,34 |
| TF-IDF + regressão logística | 0,50 | 0,69 | 0,56 |
| **BERTimbau base, ajustado** | **0,70** | **0,81** | **0,74** |
| *anotador B (outro LLM, n = 300), como teto* | *0,74* | *0,84* | *0,78* |

F1 do BERTimbau por rótulo (suporte no teste entre parênteses):

| CAR (248) | OUTRO (171) | FAM_DET (106) | GEN (23) | FAM_ORIG (38) | FAM_CAP (25) | APAR (2) | FAM_ID (9) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0,88 | 0,79 | 0,83 | 0,84 | 0,61 | 0,60 | 0,67 | **0,36** |

O BERTimbau chega perto da concordância entre os dois anotadores LLM. Ele vai bem em carreira, família como detalhe e marcação de gênero, mas ainda erra em **FAM_ID**, a categoria central da pergunta 2: há só 51 exemplos no total e 9 no teste. Antes de usar o modelo nessa pergunta, é preciso ampliar FAM_ID com mais sentenças de lead que tenham termos de cônjuge e trocar o macro-F1 por intervalos de confiança.

O treino levou cerca de 7 minutos no MPS de um M1 Pro (4 épocas, batch 16, `max_len` 128). A época foi escolhida pelo macro-F1 numa validação separada por pessoa.

Um teste de viabilidade com 600 artigos e um piloto de 200 sentenças rotuladas mostraram duas coisas. Contar palavras de família quase não diferencia mulheres de homens. O que diferencia é a *função* da menção (família como identidade apareceu só em biografias de mulheres) e a marcação de gênero. Por isso o projeto mede a função de cada sentença, e não só a frequência de palavras. No piloto, a precisão do regex foi de 0,66 para família, 0,26 para marcação de gênero e 0,20 para aparência.

## Como reproduzir

```bash
make setup        # cria .venv e instala requirements.txt
make populacao    # etapa 1: Wikidata -> data/processed/populacao.csv
make coleta       # etapa 2: wikitext dos artigos -> data/cache/ (retomável; ~1 h)
make criacao      # data de criação estimada pelo pageid (~400 requisições)
make sentencas    # etapa 3: limpeza e segmentação -> data/processed/sentencas.parquet
make amostra      # etapa 4: amostra estratificada para rotulagem
make rotulos      # valida e consolida os rótulos dos anotadores
make modelos      # baselines regex e TF-IDF + avaliação
make setup-ml && make bertimbau   # fine-tuning do BERTimbau (Python 3.12, MPS)
make notebooks    # executa os notebooks
```

As requisições usam um User-Agent que identifica o projeto e são sequenciais. Elas recuam (backoff) ao receber HTTP 429 ou 5xx, e a API da Wikipédia é chamada com `maxlag=5`. As respostas brutas ficam em cache em `data/raw/` e `data/cache/`, que não são versionados. `make populacao-atualizar` refaz as consultas ao Wikidata.

**Por que wikitext, e não `prop=extracts`:** com o texto completo, o TextExtracts devolve um artigo por requisição e a pt.wiki passou a responder 429. Com `prop=revisions` vêm 50 páginas por requisição: cerca de 900 requisições para a população toda.

**Data de criação:** a primeira revisão de cada página exigiria cerca de 45 mil requisições individuais. Como o pageid é atribuído em ordem crescente na criação da página, `scripts/criacao.py` busca a primeira revisão de 400 páginas espalhadas por todo o intervalo de pageids e interpola uma função monótona pageid → data para todos os artigos. O erro é medido por validação cruzada (ver abaixo). Páginas apagadas e recriadas recebem a data da recriação.

## Estrutura

```
scripts/
  common.py              cliente HTTP (User-Agent, backoff), SPARQL
  populacao.py           etapa 1: população via Wikidata
  areas.py               regras ocupação -> área; mantém data/areas.csv
  analise_populacao.py   tabelas usadas pelo notebook 01
  coleta.py              etapa 2: wikitext em lotes de 50 (retomável)
  criacao.py             data de criação estimada pelo pageid
  sentencas.py           etapa 3: limpeza e segmentação em sentenças
  analise_coleta.py      tabelas usadas pelo notebook 02
  texto.py               limpeza de wikitext, seções, sentenças, léxicos (pré-filtro), mascaramento de nome
  gerar_notebook_0*.py   geram os notebooks
notebooks/               só chamam scripts/ e plotam
data/
  areas.csv              mapeamento versionado ocupação (P106) -> área
  processed/populacao.csv
  processed/artigos_meta.csv       por artigo: pageid, revid, timestamp, bytes, redirecionamento
  processed/artigos_texto.csv      por artigo: sentenças, palavras, palavras no lead, seções
  processed/artigos_criacao.csv    data de criação estimada
  processed/criacao_calibracao.csv amostra de primeiras revisões reais
  processed/sentencas.parquet      uma linha por sentença (não versionado; ~70 MB)
  raw/, cache/                     não versionados
```

### `data/processed/sentencas.parquet`

As colunas são `qid`, `sexo`, `area`, `sec_idx` (0 = lead), `secao` (título da seção de nível 2), `lead`, `sent_idx`, `pos_rel` (0 = início e 1 = fim do artigo), `palavras` e `texto`. A limpeza remove templates (infobox, navboxes, citações), `<ref>`, tabelas, galerias, links de categoria e de arquivo e as seções de lista: Referências, Ver também, Ligações externas, Bibliografia, Discografia, Filmografia, Obras, Prêmios, Títulos, Estatísticas, Publicações etc.

### `data/areas.csv`

Cada ocupação P106 recebe uma área sugerida por regras sobre o rótulo em português (`origem=auto`). Para corrigir uma ocupação, edite a linha e marque `origem=manual`; as próximas execuções não sobrescrevem essa linha. A área de uma pessoa é a mais frequente entre as suas ocupações. Os empates seguem a ordem de `RULES` em `scripts/areas.py`.

### `data/processed/populacao.csv`

| coluna | descrição |
|---|---|
| `qid` | item no Wikidata |
| `titulo` | título do artigo na pt.wikipedia |
| `sexo` | `F`, `M`, `outro` (valor de P21 fora de F/M), `multiplo` ou `sem_dado` |
| `sexo_qids` | valores brutos de P21 |
| `area` | área principal (ver acima) |
| `ocupacoes`, `ocupacoes_qid` | todas as ocupações P106 (rótulos em pt e QIDs), separadas por `\|` |
| `ano_nasc`, `ano_morte`, `decada_nasc` | anos de P569 e P570 (o mais antigo, se houver mais de um) |

A data de criação do artigo não está no Wikidata. Ela é estimada na etapa 2 (`scripts/criacao.py`).

### `data/labels/`: sentenças rotuladas

| arquivo | conteúdo |
|---|---|
| `amostra_v2.csv` | 3.954 sentenças (`scripts/amostra.py`): estrato, peso de amostragem, split por pessoa (622 no teste fixo), texto original e mascarado |
| `rotulos_anotador_a.csv` | 1 rótulo por sentença, anotador A (subagente Claude Sonnet), guia v2, lotes de 100 |
| `rotulos_anotador_b.csv` | 300 sentenças do teste, anotador B (subagente Claude Opus), para medir concordância |
| `log_rotulagem.csv` | proveniência por lote: anotador, modelo, guia, prompt, data |
| `concordancia_v2.json`, `discordancias_v2.csv` | κ de A×B e as sentenças em que os dois discordam |
| `vazamento_genero.json` | AUC de um classificador que prevê o sexo a partir do texto mascarado |

**Como foi a rotulagem:** não havia chave de API de LLM no ambiente. Por isso os anotadores são subagentes do Claude Code. Cada um recebe só o guia (`docs/guia_rotulos_v2.md`) e um lote com `id,texto` mascarado, sem sexo, área ou estrato (prompt em `docs/prompt_rotulagem_v2.md`). As saídas são validadas: todos os ids e só rótulos do conjunto. Um lote com ids malformados foi refeito.

**Concordância:** κ = **0,78** entre A e B com o guia v2 (84% de concordância bruta, n = 300). No piloto com o guia v1, o κ entre dois LLMs tinha sido 0,63. FAM_ID ficou com κ = 0,92 e GEN com 1,00. A maior parte do desacordo que sobra é **OUTRO vs CAR na primeira frase do lead** ("[PESSOA] (cidade, data – data) foi um bispo…"): 22 dos 48 casos. Isso fica para o guia v3. Atenção: **esta é concordância LLM–LLM, não humana**. Uma validação humana do conjunto de teste continua pendente.

**Licença:** os textos das sentenças são trechos curtos da Wikipédia e seguem sob CC BY-SA 4.0, como o restante dos dados derivados.

## Limitações conhecidas

- **O critério herda os vieses do Wikidata.** A cidadania (P27), o sexo (P21) e as ocupações (P106) são preenchidos por voluntários. 7,3% das pessoas não têm ocupação e 9,9% não têm ano de nascimento.
- **Sexo binário.** As comparações usam F e M. Os 391 casos restantes são reportados, mas são poucos para análise estatística.
- **Áreas por regra.** O mapeamento automático cobre cerca de 95% das ocorrências de ocupação e deve ser revisado à mão nas ocupações mais frequentes.
- **Gênero gramatical.** O português flexiona por gênero ("casada", "ela", "brasileira"). Mesmo com o nome e os pronomes mascarados, um classificador simples prevê o sexo da pessoa a partir de uma única sentença com AUC de 0,80. Os anotadores e os modelos "veem" o gênero. O guia proíbe usá-lo como critério, mas não há como garantir isso.
- **Rótulos de LLM.** Os rótulos de referência vêm de um LLM. As métricas dos modelos medem a concordância com esse anotador, não com uma verdade humana.

## Fontes e créditos

- **Wikipédia em português**: textos sob [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Os créditos são das pessoas que editaram cada artigo, e o histórico de edições está em cada página.
- **Wikidata**: dados sob [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/).

### Trabalhos anteriores

- Salles, I. & Pappa, G. L. (2021). *Viés de Gênero em Biografias da Wikipédia em Português*. BRASNAM 2021, SBC. <https://sol.sbc.org.br/index.php/brasnam/article/view/16142>
- Wagner, C., Garcia, D., Jadidi, M. & Strohmaier, M. (2015). *It's a Man's Wikipedia? Assessing Gender Inequality in an Online Encyclopedia*. ICWSM 2015. Cobre seis edições (de, en, es, fr, it, ru), sem o português.
- Wagner, C., Graells-Garrido, E., Garcia, D. & Menczer, F. (2016). *Women through the glass ceiling: gender asymmetries in Wikipedia*. EPJ Data Science 5, 5. <https://doi.org/10.1140/epjds/s13688-016-0066-4>

## Licença

- **Código:** [MIT](LICENSE), © 2026 Amélia Cardoso.
- **Dados derivados** (`data/`, e futuramente as sentenças extraídas e rotuladas): [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), por derivarem de textos da Wikipédia. Os metadados vindos só do Wikidata são CC0 na origem.
