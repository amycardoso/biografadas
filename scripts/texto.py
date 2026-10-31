"""Utilidades de texto para as próximas etapas (coleta e medidas).

Reaproveitado do teste de viabilidade, com as correções de regex já
aplicadas (ex.: "Belo Horizonte"/"Belas Artes" não contam como aparência;
"primeira mulher do país" não conta como "mulher de"). Os léxicos servem só
como PRÉ-FILTRO de candidatas: no piloto, a precisão do regex de família foi
0,66, a de aparência 0,20 e a de marcação de gênero 0,26.
"""
import re

import mwparserfromhell as mw

FAMILIA = re.compile(
    r"\b(cas(ou|ou-se|ada|ado|amento|aram|ar-se)|marido|esposa|espos[oa]|vi[uú]v[ao]|filh[oa]s?|"
    r"m[ãa]e de|pai de|namorad[oa]|namor(ou|o)|divorci(ou|ada|ado|o)|noiv[oa]|matrim[oô]nio|"
    r"c[oô]njuge|companheir[oa])\b", re.I)
CONJUGE = re.compile(
    r"\b([Ee]sposa|[Mm]arido|[Ee]sposo|[Vv]i[uú]v[ao]|[Cc]ompanheir[oa]|[Cc]asad[oa] com|[Cc]asou(-se)? com)\b"
    r"|\bmulher d[eoa] [A-ZÁÉÍÓÚ]")
FILIACAO = re.compile(r"\b([Ff]ilh[oa]|[Nn]et[oa]|[Ss]obrinh[oa]|[Ii]rm[ãa]o?|[Mm][ãa]e|[Pp]ai) d[eoa]s? (?!personagem)")
APARENCIA = re.compile(
    r"\b(beleza(?! negra)|bonit[ao]s?|musa|sensual|sensualidade|sex[yi]|atraente|charmos[ao]|vaidos[ao]|"
    r"curvas|corpo escultural)\b", re.I)
GENERO = re.compile(r"\bprimeir[ao] (mulher|homem)|\bmulheres\b|\bfeminin|\bfeminis|\bmasculin", re.I)

_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇ0-9\"“(])")
_SECOES_LISTA = re.compile(
    r"^(refer[eê]ncias|notas|liga[cç][oõ]es externas|bibliografia|ver tamb[eé]m|fontes|leitura adicional|"
    r"discografia|filmografia|obras|pr[eê]mios.*|t[ií]tulos|estat[ií]sticas|conquistas|galeria|honrarias|condecora[cç][oõ]es|publica[cç][oõ]es.*|resultados.*)$", re.I)
_RUIDO = re.compile(r"^\s*[|{}!].*$|^(Categoria|Category|miniaturadaimagem|thumb)\b.*$|\[\[(Ficheiro|Arquivo|Imagem|File):[^\]]*\]\]",
                    re.I | re.M)


_REF = re.compile(r"<ref[^>/]*/>|<ref[^>]*>.*?</ref>|<!--.*?-->", re.I | re.S)
_LINK_NAO_TEXTO = re.compile(r"^\s*:?\s*(Categoria|Category|Ficheiro|Arquivo|Imagem|File|Image)\s*:", re.I)


def _remover(code, nodes):
    for n in nodes:
        try:
            code.remove(n)
        except ValueError:
            pass  # já removido junto com o nó pai


def limpar_codigo(code, remover_titulos=False):
    """Remove do wikicode o que não é prosa: templates (infobox, navbox), refs, galerias,
    tabelas, links de categoria e de arquivo e, opcionalmente, os títulos de seção."""
    _remover(code, code.filter_templates(recursive=False))
    _remover(code, [t for t in code.filter_tags() if str(t.tag).lower() in ("ref", "gallery", "table", "references")])
    _remover(code, [l for l in code.filter_wikilinks() if _LINK_NAO_TEXTO.match(str(l.title))])
    if remover_titulos:
        _remover(code, code.filter_headings())
    return code


def secoes(wt):
    """Itera (indice, titulo, texto) das seções de nível 2; o lead tem indice 0 e titulo "".

    Seções de lista (Referências, Ver também, Ligações externas, Discografia etc.) são puladas.
    """
    code = mw.parse(_REF.sub("", wt))
    for i, sec in enumerate(code.get_sections(levels=[2], include_lead=True)):
        heads = sec.filter_headings(recursive=False)
        titulo = heads[0].title.strip_code().strip() if heads and i > 0 else ""
        if i > 0 and not heads:
            continue
        if titulo and _SECOES_LISTA.match(titulo):
            continue
        txt = limpar_codigo(mw.parse(str(sec)), remover_titulos=True).strip_code(normalize=True, collapse=True)
        txt = _RUIDO.sub("", txt)
        yield i, titulo, re.sub(r"\n{2,}", "\n", txt).strip()


def wikitext_para_texto(wt):
    """Wikitext -> texto plano, sem templates, refs, tabelas, seções de lista e linhas de categoria."""
    code = limpar_codigo(mw.parse(_REF.sub("", wt)))
    linhas, pulando = [], False
    for linha in code.strip_code(normalize=True, collapse=True).split("\n"):
        s = linha.strip()
        if _SECOES_LISTA.match(s):
            pulando = True
            continue
        if pulando and len(s) < 60 and not s.endswith("."):
            continue
        linhas.append(linha)
    texto = _RUIDO.sub("", "\n".join(linhas))
    return re.sub(r"\n{2,}", "\n", texto).strip()


def sentencas(texto, min_chars=20):
    out = []
    for par in re.sub(r"\n+", "\n", texto).split("\n"):
        out += [s.strip() for s in _SPLIT.split(par) if len(s.strip()) > min_chars]
    return out


def lead(texto):
    return texto.strip().split("\n")[0]


def mascarar_nome(sentenca, titulo):
    """Troca as partes do nome do biografado (a partir do título) por [PESSOA]."""
    base = re.sub(r"\(.*?\)", "", titulo)
    partes = {t for t in re.split(r"\s+", base) if len(t) > 2 and t[0].isupper() and t.lower() not in {"dos", "das", "del"}}
    for p in sorted(partes, key=len, reverse=True):
        sentenca = re.sub(r"\b" + re.escape(p) + r"\b", "[PESSOA]", sentenca)
    return re.sub(r"(\[PESSOA\]\s*)+", "[PESSOA] ", sentenca).replace("[PESSOA] ,", "[PESSOA],").strip()


_PRONOMES = re.compile(r"\b([Ee]les?|[Ee]las?|[Dd]el[ea]s?|[Nn]el[ea]s?)\b")


def mascarar_pronomes(sentenca):
    """Troca pronomes pessoais de 3ª pessoa por [PRON] (ver docs/guia_rotulos_v2.md)."""
    return _PRONOMES.sub("[PRON]", sentenca)
