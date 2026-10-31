"""Gera notebooks/01_populacao.ipynb (as células só chamam scripts/ e plotam)."""
import nbformat as nbf
from common import ROOT

md = nbf.v4.new_markdown_cell
code = nbf.v4.new_code_cell
cells = [
    md("# 01 · População\n\nHumanos (P31=Q5) com cidadania brasileira (P27=Q155) e artigo na Wikipédia em português, "
       "segundo o Wikidata. Os dados são gerados por `scripts/populacao.py` (`make populacao`). Este notebook só lê "
       "`data/processed/populacao.csv` e faz tabelas e gráficos."),
    code("import sys; sys.path.insert(0, '../scripts')\n"
         "import matplotlib.pyplot as plt\n"
         "import analise_populacao as ap\n"
         "plt.rcParams.update({'figure.dpi': 110, 'axes.spines.top': False, 'axes.spines.right': False})\n"
         "F_COR, M_COR = '#b5367a', '#3b6fb6'\n"
         "df = ap.carregar()\n"
         "print(f'{len(df):,} pessoas'.replace(',', '.'))"),
    md("## Total por sexo (P21)\n\n`multiplo` = mais de um valor em P21; `outro` = valores fora de feminino e masculino (mulher trans, não binário etc.)."),
    code("ap.por_sexo(df)"),
    md("## % de mulheres por área\n\nA área é a mais frequente entre as ocupações P106 da pessoa, segundo `data/areas.csv`."),
    code("t = ap.por_area(df)\n"
         "display(t)\n"
         "t2 = t.sort_values('%F')\n"
         "fig, ax = plt.subplots(figsize=(7, 4.5))\n"
         "ax.barh(t2.index, t2['%F'], color=F_COR)\n"
         "ax.axvline(100 * (df.sexo == 'F').sum() / df.sexo.isin(['F', 'M']).sum(), color='gray', ls='--', lw=1, label='média geral')\n"
         "for y, (v, n) in enumerate(zip(t2['%F'], t2.total)): ax.text(v + 0.5, y, f'{v:.0f}% (n={n:,})'.replace(',', '.'), va='center', fontsize=8)\n"
         "ax.set_xlabel('% de mulheres'); ax.set_xlim(0, 70); ax.legend(frameon=False)\n"
         "ax.set_title('Mulheres entre biografados brasileiros, por área'); plt.tight_layout()"),
    md("## % de mulheres por década de nascimento"),
    code("d = ap.por_decada(df)\n"
         "fig, ax1 = plt.subplots(figsize=(8, 4))\n"
         "ax1.bar(d.index, d.total, width=8, color='#cccccc', label='total de biografias')\n"
         "ax1.set_ylabel('biografias (F+M)')\n"
         "ax2 = ax1.twinx(); ax2.plot(d.index, d['%F'], color=F_COR, marker='o', ms=3, label='% mulheres')\n"
         "ax2.set_ylabel('% mulheres', color=F_COR); ax2.set_ylim(0, 50); ax2.spines['right'].set_visible(True)\n"
         "ax1.set_xlabel('década de nascimento'); ax1.set_title('Biografias por década de nascimento (1800–2010)')\n"
         "plt.tight_layout()\n"
         "ap.por_seculo(df)"),
    md("## Cobertura dos metadados"),
    code("ap.cobertura(df)"),
    md("## Ocupações mais frequentes"),
    code("import pandas as pd\n"
         "pd.concat({'F': ap.ocupacoes_mais_comuns(df, 'F').reset_index(), 'M': ap.ocupacoes_mais_comuns(df, 'M').reset_index()}, axis=1)"),
    md("## Observações\n\n"
       "- O critério depende do Wikidata. Quem não tem P27=Q155 fica de fora, e imigrantes naturalizados entram.\n"
       "- O sexo vem de P21. Os poucos casos fora de F/M são reportados, mas não entram nas comparações binárias.\n"
       "- Esporte e política juntos são mais de 40% da população e quase todos homens. As análises de texto devem estratificar por área.\n"
       "- A data de criação do artigo na pt.wiki não está no Wikidata. Vou buscá-la na etapa de coleta de texto, pela API (`prop=revisions&rvdir=newer`)."),
]
nb = nbf.v4.new_notebook(cells=cells, metadata={"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}})
nbf.write(nb, ROOT / "notebooks" / "01_populacao.ipynb")
