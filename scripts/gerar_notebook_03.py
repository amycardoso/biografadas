"""Gera notebooks/03_classificador.ipynb (as células só leem data/labels/ e plotam)."""
import nbformat as nbf

from common import ROOT

md = nbf.v4.new_markdown_cell
code = nbf.v4.new_code_cell
cells = [
    md("# 03 · Classificador de sentenças\n\n"
       "- **Amostra:** 3.954 sentenças, de `scripts/amostra.py`.\n"
       "- **Rótulos:** anotador A, um subagente LLM seguindo o guia v2. O anotador B rotulou 300 sentenças do teste para medir concordância.\n"
       "- **Modelos:** regex, TF-IDF com regressão logística e BERTimbau, de `scripts/modelos.py` e `scripts/bertimbau.py`.\n"
       "- **Avaliação:** no teste fixo, separado **por pessoa**.\n\n"
       "> As métricas medem a concordância com o anotador A (um LLM), não com uma verdade humana."),
    code("import json, sys\nsys.path.insert(0, '../scripts')\n"
         "import numpy as np, pandas as pd, matplotlib.pyplot as plt\n"
         "plt.rcParams.update({'figure.dpi': 110, 'axes.spines.top': False, 'axes.spines.right': False})\n"
         "LAB = '../data/labels/'\n"
         "met = json.load(open(LAB + 'metricas.json'))\n"
         "conc = json.load(open(LAB + 'concordancia_v2.json'))\n"
         "vaz = json.load(open(LAB + 'vazamento_genero.json'))\n"
         "R = met['rotulos']\n"
         "print('treino', met['n_treino'], '| teste', met['n_teste'])"),
    md("## Rótulos na amostra\n\nAs contagens são brutas, na amostra estratificada. Elas **não** estimam a população: para isso é preciso usar a coluna `peso`."),
    code("am = pd.read_csv(LAB + 'amostra_v2.csv').merge(pd.read_csv(LAB + 'rotulos_anotador_a.csv').rename(columns={'id': 'sid'}), on='sid')\n"
         "t = pd.crosstab(am.rotulo, am.sexo).reindex(R).fillna(0).astype(int)\n"
         "t['total'] = t.sum(axis=1)\n"
         "t"),
    md("## Concordância entre anotadores (guia v2)"),
    code("print(f\"κ A×B = {conc['kappa']} (n={conc['n']}); concordância bruta {conc['concordancia']:.0%}; κ do piloto (v1) = {conc['kappa_v1_piloto']}\")\n"
         "pd.Series(conc['kappa_por_rotulo'], name='κ por rótulo (um contra o resto)').to_frame()"),
    md("## Vazamento de gênero após o mascaramento"),
    code("pd.Series(vaz['auc'], name='AUC prevendo sexo=F').to_frame()"),
    md("## Modelos no teste fixo"),
    code("linhas = {m: {'macro-F1': v['macro_f1'], 'acurácia': v['acuracia'], 'κ vs A': v['kappa']} for m, v in met['modelos'].items()}\n"
         "b = met.get('anotador_b_vs_a')\n"
         "if b: linhas[f\"anotador B (LLM, n={b['n']})\"] = {'macro-F1': b['macro_f1'], 'acurácia': b['acuracia'], 'κ vs A': b['kappa']}\n"
         "pd.DataFrame(linhas).T"),
    code("f1 = pd.DataFrame({m: v['f1_por_rotulo'] for m, v in met['modelos'].items()})\n"
         "f1['suporte no teste'] = pd.Series(next(iter(met['modelos'].values()))['suporte'])\n"
         "display(f1)\n"
         "ax = f1.drop(columns='suporte no teste').plot.bar(figsize=(8, 3.5), width=.8)\n"
         "ax.set_ylabel('F1'); ax.set_ylim(0, 1); ax.set_title('F1 por rótulo no teste'); ax.legend(frameon=False)\n"
         "plt.tight_layout()"),
    md("## Matriz de confusão do melhor modelo"),
    code("melhor = max(met['modelos'], key=lambda m: met['modelos'][m]['macro_f1'])\n"
         "cm = np.array(met['modelos'][melhor]['matriz'])\n"
         "fig, ax = plt.subplots(figsize=(6, 5))\n"
         "ax.imshow(cm / cm.sum(axis=1, keepdims=True).clip(1), cmap='Blues', vmin=0, vmax=1)\n"
         "for i in range(len(R)):\n"
         "    for j in range(len(R)):\n"
         "        if cm[i, j]: ax.text(j, i, cm[i, j], ha='center', va='center', fontsize=8, color='black' if cm[i, j] < cm[i].sum() * .6 else 'white')\n"
         "ax.set_xticks(range(len(R)), R, rotation=45, ha='right'); ax.set_yticks(range(len(R)), R)\n"
         "ax.set_xlabel('previsto'); ax.set_ylabel('anotador A'); ax.set_title(f'{melhor}: matriz de confusão (teste)')\n"
         "plt.tight_layout()"),
    code("import os\n"
         "if os.path.exists(LAB + 'bertimbau_treino.json'):\n"
         "    bt = json.load(open(LAB + 'bertimbau_treino.json'))\n"
         "    print(bt['modelo'], bt['dispositivo'], bt['config'])\n"
         "    display(pd.DataFrame(bt['historico']))"),
    md("## Guia v3 e reforço de FAM_ID\n\n"
       "- **Guia v3:** acrescenta a regra 0 (frase de abertura) e o teste da cópula.\n"
       "- **Reforço:** 350 sentenças de pessoas do treino.\n"
       "- **Rótulos novos com a v3:** as sentenças de reforço, as de FAM_ID e FAM_DET do treino, as frases de abertura rotuladas OUTRO e o **teste fixo inteiro**.\n\n"
       "Na comparação abaixo, todos os modelos são avaliados contra os **rótulos v3 do teste**, inclusive o BERTimbau treinado com a v2 (`bertimbau_treino_v2`)."),
    code("m3 = json.load(open(LAB + 'metricas_v3.json'))\n"
         "c3 = json.load(open(LAB + 'concordancia_v3.json'))\n"
         "print(f\"κ A×B: v1 {c3['kappa_v1_piloto']} → v2 {c3['kappa_v2']} → v3 {c3['kappa']} (n={c3['n']})\")\n"
         "t = pd.DataFrame({m: {'macro-F1': v['macro_f1'], 'κ vs A': v['kappa'], 'F1 FAM_ID': v['f1_por_rotulo']['FAM_ID']} for m, v in m3['modelos'].items()}).T\n"
         "bs = pd.DataFrame(m3['bootstrap']).T\n"
         "t.join(bs)"),
    code("f1v3 = pd.DataFrame({m: v['f1_por_rotulo'] for m, v in m3['modelos'].items()})\n"
         "f1v3['suporte no teste'] = pd.Series(m3['modelos']['bertimbau']['suporte'])\n"
         "f1v3"),
    md("## Observações\n\n"
       "- APAR e FAM_ID são raros. Com os rótulos v3, há 77 casos de FAM_ID na amostra, 10 deles no teste, e 17 de APAR, 1 no teste. O F1 dessas classes tem intervalo largo (ver bootstrap). O macro-F1 sem APAR é a medida mais estável.\n"
       "- O teto prático é a concordância entre anotadores: o anotador B atinge macro-F1 de cerca de 0,74 contra A. Um modelo acima disso estaria aprendendo os vieses do anotador A.\n"
       "- O próximo passo é aplicar o melhor modelo às 1,1 milhão de sentenças e estimar as proporções por sexo, área e período, com os pesos e as correções de erro de classificação."),
]
nb = nbf.v4.new_notebook(cells=cells, metadata={"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}})
nbf.write(nb, ROOT / "notebooks" / "03_classificador.ipynb")
