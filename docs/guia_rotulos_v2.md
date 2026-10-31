# Guia de rótulos v2: sentenças de biografias

**Versão:** v2 (31/10/2026). A v1 foi a do piloto de 200 sentenças, em que a concordância LLM–LLM foi κ = 0,63. A v2 acrescenta regras explícitas para as discordâncias medidas.

## Tarefa

Cada sentença vem de um artigo biográfico da Wikipédia em português. O nome da pessoa biografada aparece como `[PESSOA]` e alguns pronomes dela como `[PRON]`. Atribua **exatamente um** rótulo, pensando sempre na **pessoa biografada**: o que esta sentença diz sobre ela?

## Os 8 rótulos

| Rótulo | Definição curta |
|---|---|
| `CAR` | Carreira, obra, atuação pública, feitos, prêmios, cargos, opiniões públicas, controvérsias ligadas à atuação |
| `FAM_ID` | Família como **identidade**: a pessoa, sua notabilidade ou seu trabalho são apresentados **por meio** de um parente (cônjuge, pai, filho) |
| `FAM_DET` | Família ou relacionamento como **detalhe biográfico**: casamento, namoro, divórcio, filhos, sem definir quem a pessoa é |
| `FAM_ORIG` | Filiação e origem familiar: "filho/filha de X e Y", família de origem, infância em família, sem parente notável que explique a carreira |
| `FAM_CAP` | Família como **capital**: um parentesco notável (dinastia política, artística ou econômica) que explica ou acompanha a posição da pessoa |
| `APAR` | Aparência, corpo, beleza, sexualização **da pessoa biografada** |
| `GEN` | Marcação de gênero **da própria pessoa biografada**: "primeira mulher a…", "uma das poucas mulheres…", "pioneira entre as mulheres…" |
| `OUTRO` | Formação, nascimento, local, morte, saúde, terceiros, ficção, listas, ruído |

## Regras de decisão (aplique na ordem)

1. **Ruído e listas.** Linhas de lista sem verbo ("2009 – Exposição X – Galeria Y", "Título do livro, Editora, 2005"), legendas e resíduos de marcação recebem `OUTRO`. *Mudou na v2: na v1 havia ambiguidade com `CAR`.*
2. **Ficção e personagens.** Uma descrição do enredo ou de um personagem ("o personagem é ex-marido de…", "a história se passa em…") é `OUTRO`. Uma frase que diz que a pessoa **interpretou** ou **criou** algo é `CAR`, mesmo que cite um personagem.
3. **A pessoa não é o sujeito.** Se a sentença fala de terceiros e a pessoa biografada só aparece de passagem ("Fulano, colega de banda de [PESSOA], gravou…"), o rótulo é `OUTRO`. A exceção é quando a sentença descreve claramente a obra ou o trabalho da pessoa, como uma colaboração dela ou uma montagem da sua peça: aí é `CAR`.
4. **Parentes como fonte ou legado.** Um parente que dá informação, publica obra póstuma, recebe homenagem no lugar da pessoa ou assina documentos ("segundo a filha…", "a viúva publicou…") é `OUTRO`. O parente é um terceiro.
5. **Trabalho junto com o cônjuge.** "Estrelou a série ao lado da esposa" é `CAR`. Vira `FAM_ID` só se o cônjuge **define** o papel ou a notabilidade ("passou a integrar o grupo do marido", "ficou conhecida como esposa de…").
6. **"Uma dessas mulheres foi [PESSOA]" e similares.** É `GEN` quando a sentença põe a pessoa num grupo definido pelo gênero ou destaca o gênero dela como raridade ou pioneirismo. Se o gênero aparece só como tema da obra ("pesquisou a história das mulheres"), o rótulo é `CAR`.
7. **Mais de um tema.** Escolha o tema **principal** da oração principal. Se for impossível decidir entre carreira e família, prefira o rótulo de família **somente** quando a família muda a interpretação da carreira (`FAM_ID`/`FAM_CAP`). Caso contrário, use `CAR`.

## Fronteira identidade × detalhe × capital

Os exemplos abaixo são sintéticos, criados para este guia, e não vêm dos dados.

| Sentença | Rótulo | Por quê |
|---|---|---|
| "[PESSOA] foi a segunda esposa do maestro Antônio Lemos." | `FAM_ID` | A pessoa é definida pelo cônjuge |
| "Tornou-se conhecida como a viúva do poeta e passou a cuidar do acervo dele." | `FAM_ID` | A notabilidade vem do falecido |
| "Foi primeira-dama do estado durante o governo do marido." | `FAM_ID` | O papel público é derivado do cônjuge |
| "Abandonou a carreira para acompanhar o marido em missões diplomáticas." | `FAM_ID` | A trajetória é reorganizada em torno do cônjuge |
| "Casou-se em 1980 com o engenheiro Paulo Reis, com quem teve dois filhos." | `FAM_DET` | Informação pessoal; não define a pessoa |
| "[PESSOA] namorou o ator Lucas Prado entre 2015 e 2017." | `FAM_DET` | Relacionamento como detalhe, mesmo com parceiro famoso |
| "Em 2020 nasceu sua filha, Laura." | `FAM_DET` | Detalhe |
| "É filho de um pedreiro e de uma costureira." | `FAM_ORIG` | Origem, sem parente notável |
| "Neto do senador Afonso Duarte, iniciou a carreira política no partido do avô." | `FAM_CAP` | O parentesco explica a posição |
| "Pertence a uma família de músicos: o pai e os tios eram violonistas." | `FAM_CAP` | Capital artístico familiar |
| "Filha do pintor Rui Soares, cresceu entre ateliês e expôs pela primeira vez aos 15 anos." | `FAM_CAP` | Parente notável ligado à carreira |
| "Filha do industrial Otávio Mendes, estudou medicina em Paris." | `FAM_CAP` | Parente notável, mesmo sem ligação direta com a carreira |

**Teste rápido para `FAM_ID`:** se você apagar o parente da sentença, sobra alguma razão para a pessoa estar ali? Se não sobra, é `FAM_ID`. Se sobra, e o parente é só informação a mais, é `FAM_DET` ou `FAM_CAP`.

## Mascaramento

- **Nome:** as partes do nome do biografado, tiradas do título do artigo, viram `[PESSOA]`.
- **Pronomes:** os pronomes pessoais retos e oblíquos isolados da terceira pessoa (`ele`, `ela`, `eles`, `elas`, `dele`, `dela`) viram `[PRON]`. Isso pode atingir também pronomes que se referem a terceiros. Aceito esse custo.
- **O que não dá para neutralizar:** a flexão de gênero de adjetivos, particípios e substantivos ("casada", "brasileira", "atriz", "a primeira") e os artigos ("a [PESSOA]"). Reescrever isso exigiria resolução de correferência e mudaria o texto. Por isso **o gênero continua dedutível em boa parte das sentenças**. O vazamento é **medido**: um classificador tenta prever o sexo da pessoa a partir das sentenças mascaradas, e a AUC é registrada em `data/labels/vazamento_genero.json`. O guia pede aos anotadores que **não usem o gênero inferido** para decidir o rótulo, e a regra 6 (`GEN`) depende do conteúdo, não da gramática.

## Formato de saída dos anotadores

Um CSV com cabeçalho `id,rotulo`, uma linha por sentença, com o rótulo sendo um destes: `CAR, FAM_ID, FAM_DET, FAM_ORIG, FAM_CAP, APAR, GEN, OUTRO`.
