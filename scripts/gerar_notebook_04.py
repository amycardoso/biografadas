"""Gera notebooks/04_analises.ipynb (só lê data/resultados/ e plota)."""
import nbformat as nbf

from common import ROOT

md = nbf.v4.new_markdown_cell
code = nbf.v4.new_code_cell
cells = [
    md("# 04 · Análises: perguntas 2 a 5\n\n"
       "- **Dados:** o BERTimbau v3 aplicado às 1,12 milhão de sentenças (`scripts/inferencia.py`). As tabelas são geradas por `scripts/resultados.py`.\n"
       "- **Correção:** as proporções são corrigidas pela **precisão ponderada por sexo**, P(verdadeiro | previsto) estimada no teste fixo com os pesos de amostragem.\n"
       "- **Intervalos:** os IC de 95% vêm de um bootstrap que reamostra as pessoas e o teste ao mesmo tempo.\n"
       "- **Unidade:** a **pessoa**. Cada biografia pesa igual: é a média da fração das suas sentenças com o rótulo.\n\n"
       "> Os rótulos de referência são de um LLM, sem validação humana. O gênero é dedutível do texto mascarado (AUC 0,80). FAM_ID é raro e tem F1 de 0,63 [0,29–0,86] no teste."),
    code("import json\nimport pandas as pd, matplotlib.pyplot as plt\n"
         "plt.rcParams.update({'figure.dpi': 110, 'axes.spines.top': False, 'axes.spines.right': False})\n"
         "F_COR, M_COR = '#b5367a', '#3b6fb6'\n"
         "R = '../data/resultados/'\n"
         "ler = lambda n: pd.read_csv(R + n + '.csv')\n"
         "print(json.load(open(R + 'resumo.json')))"),
    code("def barras_fm(df, cat, titulo, ylabel='% das sentenças (média por pessoa)', ax=None):\n"
         "    piv = df.pivot_table(index=cat, columns='sexo', values='%', observed=True)\n"
         "    lo = df.pivot_table(index=cat, columns='sexo', values='IC95_inf', observed=True)\n"
         "    hi = df.pivot_table(index=cat, columns='sexo', values='IC95_sup', observed=True)\n"
         "    ax = ax or plt.subplots(figsize=(8, 3.6))[1]\n"
         "    x = range(len(piv))\n"
         "    for k, (s, cor) in enumerate([('F', F_COR), ('M', M_COR)]):\n"
         "        if s not in piv: continue\n"
         "        xs = [i + (k - .5) * .38 for i in x]\n"
         "        ax.bar(xs, piv[s], width=.38, color=cor, label=s)\n"
         "        ax.errorbar(xs, piv[s], yerr=[piv[s] - lo[s], hi[s] - piv[s]], fmt='none', ecolor='black', lw=.8, capsize=2)\n"
         "    ax.set_xticks(list(x), piv.index, rotation=30, ha='right'); ax.set_ylabel(ylabel); ax.set_title(titulo); ax.legend(frameon=False)\n"
         "    return ax"),
    md("## Visão geral: composição do lead e do corpo"),
    code("g = ler('geral_por_sexo')\n"
         "g.pivot_table(index=['parte', 'rotulo'], columns='sexo', values='%').round(2)"),
    md("## Pergunta 2: identidade emprestada (FAM_ID)\n\nFração das sentenças do lead em que a pessoa é apresentada **por um parente**."),
    code("display(ler('q2_famid_dif_fm'))\n"
         "display(ler('q2_famid_lead_sem_stubs'))\n"
         "display(ler('q2_pessoas_com_famid_lead'))\n"
         "ler('q2_famid_lead_sensibilidade_metodo')"),
    code("d = ler('q2_famid_lead_por_area')\n"
         "barras_fm(d, 'area', 'FAM_ID no lead, por área (corrigido, IC 95%)')\n"
         "plt.tight_layout()\n"
         "ler('q2_famid_lead_dif_por_area')"),
    md("## Pergunta 3: marcação de gênero (GEN)"),
    code("fig, axs = plt.subplots(1, 2, figsize=(12, 3.8))\n"
         "barras_fm(ler('q3_gen_por_area'), 'area', 'GEN por área', ax=axs[0])\n"
         "barras_fm(ler('q3_gen_por_criacao'), 'periodo_criacao', 'GEN por período de criação do artigo', ax=axs[1])\n"
         "plt.tight_layout()\n"
         "display(ler('q3_gen_lead_dif_fm'))\n"
         "ler('q3_gen_por_nascimento')"),
    md("## Pergunta 4: família como capital (FAM_CAP) em política"),
    code("display(ler('q4_politica_familia').pivot_table(index=['parte', 'rotulo'], columns='sexo', values=['%', 'IC95_inf', 'IC95_sup']).round(2))\n"
         "display(ler('q4_politica_famcap_dif_fm'))\n"
         "ler('q4_famcap_dif_por_area')"),
    md("## Pergunta 5: os artigos recentes são escritos de outro jeito?"),
    code("t = ler('q5_por_criacao_total')\n"
         "fig, axs = plt.subplots(1, 3, figsize=(14, 3.6))\n"
         "for ax, rot in zip(axs, ['FAM_DET', 'FAM_ID', 'GEN']):\n"
         "    for s, cor in [('F', F_COR), ('M', M_COR)]:\n"
         "        x = t[(t.rotulo == rot) & (t.sexo == s)]\n"
         "        ax.plot(x.periodo_criacao, x['%'], marker='o', color=cor, label=s)\n"
         "        ax.fill_between(x.periodo_criacao, x.IC95_inf, x.IC95_sup, color=cor, alpha=.15)\n"
         "    ax.set_title(f'{rot} por período de criação'); ax.tick_params(axis='x', rotation=30)\n"
         "axs[0].set_ylabel('% das sentenças (média por pessoa)'); axs[0].legend(frameon=False)\n"
         "plt.tight_layout()\n"
         "display(ler('q5_famid_lead_dif_por_criacao'))\n"
         "ler('q5_famdet_dif_por_criacao')"),
    md("## Exemplos de leads\n\nPrimeiras sentenças com o rótulo previsto, com probabilidade acima de 0,8, cortadas em 220 caracteres."),
    code("pd.set_option('display.max_colwidth', 230)\nler('exemplos_leads')"),
]
nb = nbf.v4.new_notebook(cells=cells, metadata={"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}})
nbf.write(nb, ROOT / "notebooks" / "04_analises.ipynb")
