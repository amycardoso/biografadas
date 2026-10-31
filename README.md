# biografadas

Como a Wikipédia em português descreve as biografias de **mulheres e homens brasileiros**: quanto do texto trata de casamento, filhos, aparência e de ser "esposa de" alguém, em comparação com obra e carreira, e de que forma isso acontece.

> Status: **etapas 1 a 5 concluídas**: população, coleta, segmentação, classificador e análise das 1,12 milhão de sentenças. Os rótulos ainda não têm validação humana.

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

**Classificador de sentenças** ([`notebooks/03_classificador.ipynb`](notebooks/03_classificador.ipynb)): o teste fixo tem 622 sentenças de pessoas que não aparecem no treino, e a referência é o anotador A, um LLM. Houve duas rodadas:

- **v2** (commit `c27afe5`): 3.332 sentenças de treino, rótulos do guia v2.
- **v3** (atual): guia v3, com a regra da frase de abertura e o teste da cópula para FAM_ID. O treino tem 350 sentenças de reforço com construções de cônjuge e família, todas de pessoas do treino. Receberam rótulos novos com a v3 as sentenças FAM_ID e FAM_DET do treino, as frases de abertura rotuladas OUTRO e o teste fixo inteiro (`scripts/lotes_v3.py`).

Todos os modelos abaixo foram avaliados contra os **rótulos v3 do teste**. Os intervalos são de bootstrap, e o macro-F1 é calculado sem APAR, que tem 1 caso no teste.

| modelo | macro-F1 (sem APAR) | IC 95% | κ vs A | F1 FAM_ID | IC 95% |
|---|---:|---|---:|---:|---|
| regex (léxicos de `texto.py`) | — | — | 0,37 | — | — |
| TF-IDF + regressão logística (v3) | 0,66 | 0,58–0,71 | 0,58 | 0,56 | 0,20–0,80 |
| BERTimbau treinado com a v2 (`c27afe5`) | 0,70 | 0,63–0,76 | 0,71 | 0,33 | 0,00–0,67 |
| **BERTimbau treinado com a v3** | **0,77** | **0,71–0,83** | **0,78** | **0,63** | **0,29–0,86** |

F1 do BERTimbau v3 por rótulo (suporte no teste entre parênteses):

| CAR (280) | OUTRO (151) | FAM_DET (96) | GEN (22) | FAM_ORIG (36) | FAM_CAP (26) | FAM_ID (10) |
|---:|---:|---:|---:|---:|---:|---:|
| 0,91 | 0,78 | 0,86 | 0,87 | 0,70 | 0,66 | 0,63 |

- O macro-F1 melhorou de forma consistente: os intervalos quase não se sobrepõem.
- **FAM_ID passou de 0,33 para 0,63**, mas o teste tem só 10 casos, e o intervalo de 0,29 a 0,86 continua largo. A melhora é provável, mas mal estimada.
- O reforço rendeu menos FAM_ID do que o esperado: só 25 das 350 sentenças, 18 de mulheres e 7 de homens. Com o teste da cópula, a maioria das construções "esposa/marido de" é FAM_DET ou FAM_CAP. FAM_ID é de fato raro.
- Para estimar FAM_ID na população, as próximas etapas devem usar a correção de erro de classificação, com a matriz de confusão por classe, e reportar os intervalos.

O treino de cada rodada levou cerca de 7 a 8 minutos no MPS de um M1 Pro (4 épocas, batch 16, `max_len` 128, perda com peso de classe ∝ 1/√frequência). A época foi escolhida pelo macro-F1 numa validação separada por pessoa.

## Página interativa

[`docs/index.html`](docs/index.html) é uma página estática, sem build e sem bibliotecas externas, com os gráficos das perguntas 1 a 5 e a seção **Leads lado a lado**. Nela, a busca por nome mostra as primeiras sentenças de uma biografia destacadas pelo rótulo previsto, e há um botão de exemplo aleatório com filtros. Os dados vêm de `scripts/pagina.py` (`make pagina`). Para ver localmente: `make servir`.

## Achados principais

Fonte: [`notebooks/04_analises.ipynb`](notebooks/04_analises.ipynb), com as tabelas em [`data/resultados/`](data/resultados/).

- **Dados:** o BERTimbau v3 foi aplicado às 1.120.642 sentenças de 45.381 biografias (9.276 de mulheres e 36.105 de homens).
- **Unidade:** a **pessoa**, isto é, a média, entre as biografias, da fração das sentenças de cada uma com o rótulo.
- **Correção:** os números estão corrigidos pela precisão do classificador.
- **Intervalos:** os IC de 95% vêm de um bootstrap que reamostra as pessoas e o teste ao mesmo tempo.

**1. Identidade emprestada (P2).** No lead, **0,68%** das sentenças apresentam a mulher por um parente (IC 0,45–0,96), contra **0,29%** nos homens (0,26–0,33).
- A diferença F−M é de +0,38 p.p. (IC 0,15–0,67). Ela se mantém sem os stubs: +0,40 (0,16–0,69).
- Em biografias inteiras: 2,3% das mulheres têm ao menos uma sentença de lead desse tipo, contra 1,1% dos homens (contagem bruta).
- O efeito se concentra em **política**: 2,13% (1,37–2,90) nas mulheres contra 0,36% (0,30–0,41) nos homens, uma diferença de +1,77 p.p. (1,05–2,52). Há cônjuges de políticos classificadas como políticas pelo Wikidata.
- Também aparece em literatura (+0,35; 0,04–0,72) e entre pessoas sem ocupação no Wikidata (+1,01; 0,40–1,78).
- Nas artes, na atuação, na música e no esporte, a diferença é nula.
- *Exemplos de lead:* "Foi esposa de Mestre Didi por meio século." / "É viúva do 59.º governador de São Paulo…" / "Era mãe do deputado federal…". Entre os homens, o padrão aparece sobretudo como "pai de" alguém notável.

**2. Marcação de gênero (P3).** Frases como "primeira mulher a…" ou "a única mulher…" aparecem em **0,95%** das sentenças das biografias de mulheres (0,59–1,46) e quase nunca nas de homens (0,02%).
- No lead são 1,69% (1,03–2,59).
- É mais frequente em política (2,23%; 1,33–3,46).
- É mais comum para mulheres nascidas até 1899 (1,72%) do que para as nascidas a partir de 1950 (0,81%).
- Não mudou de forma clara com o ano de criação do artigo: de 0,80% em 2002–06 para 1,11% em 2022–26, com intervalos que se sobrepõem.

**3. Família como capital em política (P4).** **Não há diferença por sexo**: 1,48% (1,08–2,00) nas mulheres e 1,55% (1,02–2,17) nos homens, F−M de −0,07 p.p. (−0,89 a 0,66).
- A genealogia política ("filho do ex-prefeito…") é comum aos dois sexos.
- O que distingue as mulheres em política é a identidade emprestada (item 1), não o capital familiar.

**4. Tempo (P5).** A identidade emprestada no lead **caiu nos artigos mais recentes**, para os dois sexos: nas mulheres, de 1,06% (2007–11) para 0,54% (2022–26). Mas **a diferença F−M persiste**: +0,71 p.p. (0,37–1,13) em 2007–11 e +0,40 p.p. (0,16–0,72) em 2022–26. Família como detalhe não difere por sexo em nenhum período.

**5. O que não muda.** O volume de família como detalhe, como casamento e filhos, é igual entre os sexos: 2,43% contra 2,37% das sentenças. Isso confirma o teste de viabilidade, em que o viés aparece na **função** da menção, não na quantidade.

**Sensibilidade ao método de correção** (FAM_ID no lead, F−M):
- contagem bruta: +0,37 (0,27–0,48);
- correção por precisão: +0,38 (0,15–0,67);
- ACC: −0,23 (−0,32 a 1,21). O ACC é instável para classes raras, porque um único falso positivo de CAR no teste zera a estimativa. Por isso não é o método principal.

### Método de correção

`scripts/analise.py`: a estimativa principal multiplica as proporções previstas em cada grupo pela matriz P(verdadeiro | previsto).
- **Estimativa da matriz:** no teste fixo, ponderada pelos pesos de amostragem (para refletir a prevalência na população) e **separada por sexo**, porque a prevalência de FAM_ID e GEN difere entre os sexos.
- **Bootstrap:** cada réplica reamostra as pessoas do corpus (pesos de Poisson por pessoa) **e** as sentenças do teste. Assim, os intervalos incluem a incerteza da matriz de confusão.
- **Pressuposto:** a precisão do classificador num grupo (por exemplo, mulheres em política) é igual à do teste do mesmo sexo. Com só 622 sentenças no teste, não dá para estimá-la por área.

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
make modelos      # baselines regex e TF-IDF + avaliação (ROTULOS=v3 make modelos para a v3)
make setup-ml && make bertimbau   # fine-tuning do BERTimbau (Python 3.12, MPS)
make inferencia   # etapa 5: BERTimbau v3 nas 1,12 milhão de sentenças (~95 min no M1 Pro)
make resultados   # tabelas das perguntas 2–5 em data/resultados/
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
| `amostra_v3.csv` | v2 + 350 de reforço (`scripts/amostra_reforco.py`), com `estrato_v3`, `peso_v3` (pós-estratificação) e `origem` |
| `rotulos_anotador_a_v3.csv`, `rotulos_anotador_b_v3.csv` | rótulos do guia v3: A nas 1.622 sentenças afetadas, B nas mesmas 300 do teste |
| `rotulos_v3.csv` | rótulo final por sentença (v3 quando houve rótulo novo, v2 nas demais), com `guia`, `rotulo_v2` e `motivo_v3` |
| `concordancia_v3.json`, `discordancias_v3.csv`, `metricas_v3.json` | κ da v3, discordâncias e métricas com bootstrap |
| `vazamento_genero.json` | AUC de um classificador que prevê o sexo a partir do texto mascarado |

**Como foi a rotulagem:** não havia chave de API de LLM no ambiente. Por isso os anotadores são subagentes do Claude Code. Cada um recebe só o guia (`docs/guia_rotulos_v2.md`) e um lote com `id,texto` mascarado, sem sexo, área ou estrato (prompt em `docs/prompt_rotulagem_v2.md`). As saídas são validadas: todos os ids e só rótulos do conjunto. Um lote com ids malformados foi refeito.

**Concordância:** κ = **0,78** entre A e B com o guia v2 (84% de concordância bruta, n = 300). No piloto com o guia v1, o κ entre dois LLMs tinha sido 0,63. FAM_ID ficou com κ = 0,92 e GEN com 1,00. A maior parte do desacordo que sobra é **OUTRO vs CAR na primeira frase do lead** ("[PESSOA] (cidade, data – data) foi um bispo…"): 22 dos 48 casos. O guia v3 tratou esse caso. **Com o guia v3, o κ entre A e B nas mesmas 300 sentenças subiu para 0,87** (91% de concordância). FAM_ID ficou com κ de 0,83 e CAR com 0,93. O desacordo que sobra é principalmente OUTRO × CAR (8 casos) e FAM_DET × OUTRO (7). Ao rotular de novo com a v3, 295 das 1.272 sentenças que já tinham rótulo v2 mudaram de rótulo. A maior mudança foi a das frases de abertura: 167 passaram de OUTRO para CAR. Os padrões do guia v3 foram tirados dos erros do BERTimbau no teste, mas os exemplos do guia são sintéticos e não reproduzem sentenças do teste. Mesmo assim, esse é um pequeno risco de ajuste ao teste. Atenção: **esta é concordância LLM–LLM, não humana**. Uma validação humana do conjunto de teste continua pendente.

**Licença:** os textos das sentenças são trechos curtos da Wikipédia e seguem sob CC BY-SA 4.0, como o restante dos dados derivados.

## Limitações conhecidas

- **O critério herda os vieses do Wikidata.** A cidadania (P27), o sexo (P21) e as ocupações (P106) são preenchidos por voluntários. 7,3% das pessoas não têm ocupação e 9,9% não têm ano de nascimento.
- **Sexo binário.** As comparações usam F e M. Os 391 casos restantes são reportados, mas são poucos para análise estatística.
- **Áreas por regra.** O mapeamento automático cobre cerca de 95% das ocorrências de ocupação e deve ser revisado à mão nas ocupações mais frequentes.
- **Gênero gramatical.** O português flexiona por gênero ("casada", "ela", "brasileira"). Mesmo com o nome e os pronomes mascarados, um classificador simples prevê o sexo da pessoa a partir de uma única sentença com AUC de 0,80. Os anotadores e os modelos "veem" o gênero. O guia proíbe usá-lo como critério, mas não há como garantir isso.
- **Rótulos de LLM, sem validação humana.** Os rótulos de referência vêm de um LLM. As métricas e a correção medem a concordância com esse anotador, não com uma verdade humana. A concordância LLM–LLM é κ 0,87.
- **FAM_ID é raro.** Representa cerca de 0,3% a 0,7% das sentenças do lead, e o teste tem só 10 casos (F1 0,63, IC 0,29–0,86). As diferenças acima são estatisticamente distinguíveis de zero com a correção por precisão, mas não com o ACC. Elas dependem do pressuposto de transferência da precisão.
- **Áreas do Wikidata.** Algumas mulheres notáveis como cônjuges de políticos aparecem com ocupação "político". Parte do efeito em política é de composição (quem entra na Wikipédia, e por quê), não só de redação.
- **Leads e corpo.** Leads são curtos. A unidade "pessoa" dá o mesmo peso a stubs e artigos longos. Os resultados sem stubs estão em `q2_famid_lead_sem_stubs.csv`.

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
