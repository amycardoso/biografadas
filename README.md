# biografadas

Como a Wikipédia em português descreve as biografias de **mulheres e homens brasileiros**: quanto do texto trata de casamento, filhos, aparência e de ser "esposa de" alguém, em comparação com obra e carreira, e de que forma isso acontece.

> Status: **etapa 1 (população) concluída**. As próximas etapas são a coleta de texto, as medidas, o classificador de sentenças e a análise.

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

Um teste de viabilidade com 600 artigos e um piloto de 200 sentenças rotuladas mostraram duas coisas. Contar palavras de família quase não diferencia mulheres de homens. O que diferencia é a *função* da menção (família como identidade apareceu só em biografias de mulheres) e a marcação de gênero. Por isso o projeto mede a função de cada sentença, e não só a frequência de palavras. No piloto, a precisão do regex foi de 0,66 para família, 0,26 para marcação de gênero e 0,20 para aparência.

## Como reproduzir

```bash
make setup        # cria .venv e instala requirements.txt
make populacao    # etapa 1: Wikidata -> data/processed/populacao.csv
make notebooks    # executa os notebooks
```

As consultas ao Wikidata usam um User-Agent que identifica o projeto, são feitas em lotes sequenciais e recuam (backoff) ao receber HTTP 429 ou 5xx. As respostas brutas ficam em cache em `data/raw/`, que não é versionado. `make populacao-atualizar` refaz as consultas.

## Estrutura

```
scripts/
  common.py              cliente HTTP (User-Agent, backoff), SPARQL
  populacao.py           etapa 1: população via Wikidata
  areas.py               regras ocupação -> área; mantém data/areas.csv
  analise_populacao.py   tabelas usadas pelo notebook 01
  texto.py               wikitext -> texto, sentenças, léxicos (pré-filtro), mascaramento de nome
  gerar_notebook_01.py   gera notebooks/01_populacao.ipynb
notebooks/               só chamam scripts/ e plotam
data/
  areas.csv              mapeamento versionado ocupação (P106) -> área
  processed/populacao.csv
  raw/, cache/           não versionados
```

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

A data de criação do artigo não está no Wikidata. Ela será coletada na etapa de texto, pela API da Wikipédia.

## Limitações conhecidas

- **O critério herda os vieses do Wikidata.** A cidadania (P27), o sexo (P21) e as ocupações (P106) são preenchidos por voluntários. 7,3% das pessoas não têm ocupação e 9,9% não têm ano de nascimento.
- **Sexo binário.** As comparações usam F e M. Os 391 casos restantes são reportados, mas são poucos para análise estatística.
- **Áreas por regra.** O mapeamento automático cobre cerca de 95% das ocorrências de ocupação e deve ser revisado à mão nas ocupações mais frequentes.
- **Gênero gramatical.** O português flexiona por gênero ("casada", "ela", "brasileira"). Qualquer comparação lexical ou modelo de texto precisa neutralizar essa flexão.

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
