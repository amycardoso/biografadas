PY := .venv/bin/python
JUPYTER := .venv/bin/jupyter

.PHONY: setup populacao populacao-atualizar coleta sentencas criacao notebooks limpar-cache

setup:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

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

notebooks:
	cd scripts && ../$(PY) gerar_notebook_01.py && ../$(PY) gerar_notebook_02.py
	$(JUPYTER) nbconvert --to notebook --execute --inplace notebooks/01_populacao.ipynb
	$(JUPYTER) nbconvert --to notebook --execute --inplace notebooks/02_coleta.ipynb

limpar-cache:
	rm -rf data/raw data/cache
