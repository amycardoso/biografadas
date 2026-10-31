"""Mapeamento ocupação (P106) -> área de atuação.

O mapeamento fica versionado em data/areas.csv (qid, rótulo, n_pessoas, area,
origem). Ocupações novas recebem uma área sugerida pelas regras abaixo
(origem=auto); correções manuais devem ser feitas direto no CSV com
origem=manual, e não são sobrescritas.
"""
import collections
import re

import pandas as pd

from common import DATA

AREAS_CSV = DATA / "areas.csv"

# A ordem importa: a primeira regra que casar com o rótulo define a área.
# Também é a ordem de desempate quando uma pessoa tem ocupações em várias áreas.
RULES = [
    ("esporte", r"futebol|jogador|atleta|nadador|lutador|judoca|tenista|automobil|ciclista|boxe|pugilista|velocist|ginasta|treinador|esgrim|surfist|skat|maratonist|remador|velejador|karat|carateca|taekwond|handebol|basquet|vôlei|volei|piloto de|xadrez|enxadrista|árbitro|desportist|esportist|dirigente esportivo|corredor|halterof|canoísta|triatl|lançador|saltador|jóquei|capoeir|artes marciais|polo aquático|arqueir|atirador|cavaleiro"),
    ("religiao", r"padre|bispo|diácono|freira|religios|sacerdote|pastor|monge|missionári|cardeal|teólogo|presbítero|frade|santo|evangelista|rabino|médium|ialorixá|babalorixá|mãe de santo|pai de santo"),
    ("politica", r"polític|advogad|juiz|jurista|diplomata|servidor público|militar|magistrad|promotor|deputad|senador|prefeit|governador|vereador|ativista|sindicalista|oficial|general|almirante|procurador|delegado|policial|ministro|desembargador|revolucionári|estadista|funcionário público|administrador público|primeira-dama|soldado|ambientalista|feminista"),
    ("ciencia_academia", r"professor|pesquisador|historiador|economista|engenheir|médico|cientista|físico|químico|biólog|sociólog|antropólog|filósof|linguista|matemátic|geógraf|psicólog|psicanalist|botânic|zoólog|astrônom|geólog|educador|pedagog|acadêmic|arqueólog|cirurgi|enfermeir|farmacêutic|farmacolog|veterinári|naturalista|entomólog|entomologist|paleontólog|bibliotecári|arquivista|filólog|estatístic|agrônom|pediatra|psiquiatra|neurocient|epidemiolog|ecólog|geneticist|dentista|musicólog|etnólog|etnologist|folclorist|urbanista|scientific collector|colecionador de plantas|sertanista|explorador|romanista|inventor"),
    ("musica", r"cantor|compositor|músic|pianista|guitarrista|vocalista|produtor musical|maestro|cantautor|discográfic|violonista|baterista|baixista|instrumentist|\bDJ\b|rapper|sambista|samba-enredo|percussionista|violinista|saxofonista|regente|organista|flautista|sanfoneir|acordeonist|trompetist|tecladista|arranjador|seresteiro|\bMC\b|beatmaker|cantora"),
    ("jornalismo_comunicacao", r"jornalista|repórter|colunista|apresentador|radialista|locutor|comentarista|youtuber|influenciador|blogueir|podcaster|criador de vídeos|criador de conteúdo|vlogueir|streamer|publicitári|relações públicas|comunicador|âncora"),
    ("literatura", r"escritor|poet|romancista|tradutor|crític|dramaturg|ensaísta|cronista|contista|autor|editor|biógraf|literat|cordelista|letrista|redator|memorialist|fanzineir|teatrólog"),
    ("atuacao_tv", r"\bator|atriz|modelo|comediante|humorista|dublador|ator de voz|personalidade|concurso de beleza|\bmiss\b|dançarin|bailarin|coreógraf|vedete|palhaç|celebridade|reality|showman|carnavalesco|passista|drag queen|performer|performista"),
    ("artes_visuais", r"pintor|escultor|artista|fotógraf|desenhista|cartunista|arquitet|diretor|cineasta|realizador|roteirista|guionista|produtor de cinema|produtor de televisão|ilustrador|gravador|designer|quadrinist|estilista|ceramista|cenógraf|animador|curador|montador|caricaturista|muralista|grafiteir|ourives|artesã|artesão|figurinist|paisagist"),
]
AREAS = [a for a, _ in RULES] + ["outros", "sem_ocupacao"]
_COMPILED = [(a, re.compile(p, re.I)) for a, p in RULES]


def sugerir_area(rotulo):
    for area, rx in _COMPILED:
        if rx.search(rotulo):
            return area
    return "outros"


def atualizar_mapeamento(contagem, rotulos):
    """Acrescenta ocupações novas ao data/areas.csv e atualiza n_pessoas.

    contagem: Counter qid -> nº de pessoas; rotulos: dict qid -> rótulo pt.
    """
    if AREAS_CSV.exists():
        m = pd.read_csv(AREAS_CSV, dtype=str).fillna("")
    else:
        m = pd.DataFrame(columns=["qid", "rotulo", "n_pessoas", "area", "origem"])
    conhecidos = set(m.qid)
    novos = [
        {"qid": q, "rotulo": rotulos.get(q, q), "area": sugerir_area(rotulos.get(q, q)), "origem": "auto"}
        for q in contagem if q not in conhecidos
    ]
    m = pd.concat([m, pd.DataFrame(novos)], ignore_index=True)
    auto = m.origem == "auto"
    m.loc[auto, "area"] = m.loc[auto, "rotulo"].map(sugerir_area)
    m["n_pessoas"] = m.qid.map(lambda q: contagem.get(q, 0)).astype(int)
    m = m.sort_values(["n_pessoas", "qid"], ascending=[False, True])
    m.to_csv(AREAS_CSV, index=False)
    return m


def carregar_mapeamento():
    m = pd.read_csv(AREAS_CSV, dtype=str).fillna("")
    return dict(zip(m.qid, m.area))


def area_principal(occs, occ2area):
    """Área mais frequente entre as ocupações; empate resolvido pela ordem de RULES."""
    if not occs:
        return "sem_ocupacao"
    c = collections.Counter(occ2area.get(o, "outros") for o in occs)
    c.pop("outros", None)
    if not c:
        return "outros"
    top = max(c.values())
    return next(a for a in AREAS if c.get(a) == top)
