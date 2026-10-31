PY := .venv/bin/python
JUPYTER := .venv/bin/jupyter

.PHONY: setup populacao populacao-atualizar notebooks limpar-cache

setup:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

## Etapa 1: população via Wikidata (usa cache em data/raw/ se existir)
populacao:
	cd scripts && ../$(PY) populacao.py

## Refaz as consultas ao Wikidata, ignorando o cache
populacao-atualizar:
	cd scripts && ../$(PY) populacao.py --sem-cache

notebooks:
	cd scripts && ../$(PY) gerar_notebook_01.py
	$(JUPYTER) nbconvert --to notebook --execute --inplace notebooks/01_populacao.ipynb

limpar-cache:
	rm -rf data/raw data/cache
