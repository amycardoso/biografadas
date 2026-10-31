PY := .venv/bin/python
ROTULOS ?= v3
JUPYTER := .venv/bin/jupyter

.PHONY: setup setup-ml populacao populacao-atualizar coleta sentencas criacao amostra lotes rotulos reforco rotulos-v3 modelos bertimbau inferencia resultados pagina notebooks limpar-cache

setup:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

## Ambiente separado para o BERTimbau (Python 3.12: torch + transformers)
setup-ml:
	python3.12 -m venv .venv-ml
	.venv-ml/bin/pip install -r requirements-ml.txt

## Etapa 1: população via Wikidata (usa cache em data/raw/ se existir)
populacao:
	cd scripts && ../$(PY) populacao.py

## Refaz as consultas ao Wikidata, ignorando o cache
populacao-atualizar:
	cd scripts && ../$(PY) populacao.py --sem-cache

## Etapa 2: wikitext dos artigos (retomável; ~1 h na primeira vez)
coleta:
	cd scripts && ../$(PY) coleta.py

## Data de criação estimada pelo pageid (~400 requisições de calibração)
criacao:
	cd scripts && ../$(PY) criacao.py

## Etapa 3: limpeza e segmentação em sentenças
sentencas:
	cd scripts && ../$(PY) sentencas.py

## Etapa 4: amostra estratificada, lotes para anotação e consolidação dos rótulos
amostra:
	cd scripts && ../$(PY) amostra.py

lotes:
	cd scripts && ../$(PY) lotes.py preparar

rotulos:
	cd scripts && ../$(PY) lotes.py consolidar

## Guia v3: reforço de FAM_ID, lotes e consolidação (ROTULOS=v3 nos alvos de modelo)
reforco:
	cd scripts && ../$(PY) amostra_reforco.py && ../$(PY) lotes_v3.py preparar

rotulos-v3:
	cd scripts && ../$(PY) lotes_v3.py consolidar

## Baselines (regex, TF-IDF) e avaliação de todos os modelos
modelos:
	cd scripts && ROTULOS=$(ROTULOS) ../$(PY) modelos.py

## Fine-tuning do BERTimbau (MPS se disponível), seguido da avaliação
bertimbau:
	ROTULOS=$(ROTULOS) nice -n 10 .venv-ml/bin/python scripts/bertimbau.py
	cd scripts && ROTULOS=$(ROTULOS) ../$(PY) -c "import modelos; modelos.avaliar_todos()"

## Etapa 5: aplicação às 1,12M sentenças e tabelas das perguntas 2–5
inferencia:
	nice -n 10 .venv-ml/bin/python scripts/inferencia.py

resultados:
	cd scripts && nice -n 10 ../$(PY) resultados.py

## Página estática (docs/): dados em docs/data/*.json
pagina:
	cd scripts && ../$(PY) pagina.py

## Servir a página localmente em http://localhost:8000
servir:
	cd docs && python3 -m http.server 8000

notebooks:
	cd scripts && ../$(PY) gerar_notebook_01.py && ../$(PY) gerar_notebook_02.py && ../$(PY) gerar_notebook_03.py && ../$(PY) gerar_notebook_04.py
	$(JUPYTER) nbconvert --to notebook --execute --inplace notebooks/01_populacao.ipynb
	$(JUPYTER) nbconvert --to notebook --execute --inplace notebooks/02_coleta.ipynb
	$(JUPYTER) nbconvert --to notebook --execute --inplace notebooks/03_classificador.ipynb
	$(JUPYTER) nbconvert --to notebook --execute --inplace notebooks/04_analises.ipynb

limpar-cache:
	rm -rf data/raw data/cache
