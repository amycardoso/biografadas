"""Gera notebooks/02_coleta.ipynb (as células só chamam scripts/ e plotam)."""
import nbformat as nbf

from common import ROOT

md = nbf.v4.new_markdown_cell
code = nbf.v4.new_code_cell
cells = [
    md("# 02 · Coleta e segmentação\n\n"
       "O texto é o wikitext da revisão atual de cada artigo (`scripts/coleta.py`, `make coleta`). Ele é limpo e "
       "segmentado em sentenças por `scripts/sentencas.py` (`make sentencas`). A data de criação é estimada pelo "
       "pageid (`scripts/criacao.py`, `make criacao`). Este notebook só lê os resumos em `data/processed/`."),
    code("import sys; sys.path.insert(0, '../scripts')\n"
         "import matplotlib.pyplot as plt\n"
         "import pandas as pd\n"
         "import analise_coleta as ac\n"
         "plt.rcParams.update({'figure.dpi': 110, 'axes.spines.top': False, 'axes.spines.right': False})\n"
         "F_COR, M_COR = '#b5367a', '#3b6fb6'\n"
         "df = ac.carregar()\n"
         "ac.cobertura(df)"),
    md("## Tamanho dos artigos por sexo\n\nO tamanho é contado em palavras de prosa, depois da limpeza (sem infobox, tabelas, referências nem seções de lista)."),
    code("display(ac.tamanho_por_sexo(df))\n"
         "ok = df[df.status == 'ok']\n"
         "fig, ax = plt.subplots(figsize=(7, 3.5))\n"
         "bins = [0, 50, 100, 150, 250, 400, 600, 1000, 1600, 2500, 4000, 7000, 12000, 50000]\n"
         "for s, c in [('M', M_COR), ('F', F_COR)]:\n"
         "    v = ok[ok.sexo == s].palavras\n"
         "    ax.hist(v.clip(upper=49999), bins=bins, histtype='step', lw=2, color=c, density=True, label=f'{s} (n={len(v):,})'.replace(',', '.'))\n"
         "ax.set_xscale('log'); ax.axvline(ac.STUB, color='gray', ls='--', lw=1)\n"
         "ax.set_xlabel('palavras de prosa (escala log)'); ax.set_ylabel('densidade'); ax.legend(frameon=False)\n"
         "ax.set_title('Distribuição do tamanho dos artigos'); plt.tight_layout()"),
    md("## Tamanho por área"),
    code("ac.tamanho_por_area(df)"),
    md("## Ano de criação do artigo (estimado)\n\n"
       "A data é interpolada a partir do pageid, calibrada com uma amostra de primeiras revisões reais. O erro de "
       "calibração está em `data/processed/criacao_calibracao.csv` e é discutido no README."),
    code("t = ac.pct_mulheres_por_ano_criacao(df)\n"
         "if t is not None:\n"
         "    display(t)\n"
         "    fig, ax1 = plt.subplots(figsize=(8, 4))\n"
         "    ax1.bar(t.index, t.M, color=M_COR, alpha=.6, label='M'); ax1.bar(t.index, t.F, bottom=t.M, color=F_COR, alpha=.8, label='F')\n"
         "    ax1.set_ylabel('artigos criados'); ax1.legend(frameon=False, loc='upper left')\n"
         "    ax2 = ax1.twinx(); ax2.plot(t.index, t['%F'], color='black', marker='o', ms=3); ax2.set_ylim(0, 50)\n"
         "    ax2.set_ylabel('% mulheres'); ax2.spines['right'].set_visible(True)\n"
         "    ax1.set_title('Biografias de brasileiros criadas por ano (estimativa)'); plt.tight_layout()"),
    md("## Observações\n\n"
       "- Os stubs (menos de 150 palavras de prosa) têm poucas sentenças, e as proporções calculadas neles são ruidosas. As análises devem ponderar ou estratificar por tamanho.\n"
       "- Esporte tem artigos padronizados, com seções de carreira em clubes e de títulos. As seções de lista (títulos, estatísticas, discografia etc.) foram removidas.\n"
       "- O texto vem da revisão atual (data em `rev_timestamp`). A pergunta 5 (tempo) usa o ano de criação do artigo, não a data da versão."),
]
nb = nbf.v4.new_notebook(cells=cells, metadata={"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}})
nbf.write(nb, ROOT / "notebooks" / "02_coleta.ipynb")
