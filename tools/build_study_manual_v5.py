#!/usr/bin/env python3
"""Constrói a camada V5 de estudo em formato de apostila paginada.

Princípios:
- os 116 tópicos continuam sendo exatamente os tópicos da matriz oficial;
- toda página carrega o officialScope literal do tópico que a autoriza;
- a expansão é didática: explica, exemplifica, contrasta e treina somente o que
  já está contido no recorte oficial;
- o volume mínimo é validável para impedir o retorno a aulas excessivamente
  curtas.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from deepen_lessons import K

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CONTEST_ID = "gcm-salvador-2026"
LESSONS_PATH = DATA / "lessons" / f"{CONTEST_ID}.json"
SYLLABUS_PATH = DATA / "syllabus" / f"{CONTEST_ID}.json"

SUBJECT_LENS = {
    "portugues": {
        "name": "Língua Portuguesa",
        "reasoning": "Em Português, a resposta deve ser demonstrada pelo funcionamento da frase ou do texto. Localize a palavra, a estrutura ou a relação de sentido que prova a conclusão; não escolha por impressão subjetiva.",
        "application": "A aplicação prática consiste em comparar enunciado e alternativas, observar conectores, referência, escolha lexical, estrutura sintática e efeitos de sentido. Uma pequena troca de palavra pode aumentar, reduzir ou inverter a afirmação.",
        "fgv": "A FGV costuma construir alternativas muito próximas do texto. Desconfie de generalizações, troca de causa por consequência, mudança de grau de certeza, substituições lexicais apenas aparentemente equivalentes e reescritas que preservam palavras mas alteram relação lógica.",
        "boundary": "Não é necessário transformar o tópico em um curso completo de Linguística. A expansão permanece limitada ao fenômeno textual, gramatical ou semântico nomeado no edital e às distinções necessárias para reconhecê-lo em questão.",
    },
    "rlm": {
        "name": "Raciocínio Lógico-Matemático",
        "reasoning": "Em RLM, o primeiro trabalho é modelar: transforme o texto em símbolos, tabela, desenho, equação, proporção ou relação lógica. Só depois calcule. Muitos erros de prova surgem antes da conta, na tradução do enunciado.",
        "application": "Aplique o conceito em problemas curtos e depois em problemas com informação excedente. Registre unidades, condição inicial, transformação sofrida e exatamente o que deve ser encontrado. Ao final, faça uma verificação independente do resultado.",
        "fgv": "A FGV pode esconder uma operação simples dentro de um texto longo. Leia as condições literalmente, separe dado de conclusão e teste se a relação escolhida realmente é válida. Fórmula correta aplicada a modelo errado continua produzindo resposta errada.",
        "boundary": "Não avance para matemática de nível superior. Use apenas as ferramentas elementares necessárias aos itens listados no edital: aritmética, álgebra básica, geometria, sequências, conjuntos, contagem, probabilidade e lógica proposicional.",
    },
    "informatica": {
        "name": "Informática",
        "reasoning": "Em Informática, associe cada recurso a finalidade, entrada, saída e efeito. Diferencie formato de arquivo, programa, comando, função, configuração e mecanismo de segurança; a banca mistura essas categorias para criar alternativas plausíveis.",
        "application": "Imagine a execução real da tarefa: abrir, salvar, localizar, substituir, formatar, proteger, filtrar, ordenar, importar, exportar, navegar, fazer upload ou download. Pergunte o que muda no arquivo, na tela ou nos dados após a ação.",
        "fgv": "A FGV costuma cobrar definição precisa e consequência operacional. Alternativas erradas frequentemente atribuem a um recurso função de outro ou transformam uma possibilidade em comportamento obrigatório.",
        "boundary": "A expansão fica limitada às versões, aplicativos e conceitos expressamente citados no edital. Recursos modernos podem ser usados apenas para comparação didática quando preservam o conceito cobrado, nunca para substituir o recorte oficial.",
    },
    "constitucional-civil": {
        "name": "Direito Constitucional e Direito Civil",
        "reasoning": "Em Direito, identifique primeiro o instituto. Depois separe conceito, requisitos, sujeitos, efeitos, regra, exceção e fonte normativa. Termos parecidos não são intercambiáveis e uma única condição ausente pode mudar o enquadramento.",
        "application": "Treine por casos curtos: quem são os sujeitos, qual fato ocorreu, qual instituto do edital está envolvido e qual consequência jurídica decorre. Quando houver texto constitucional, legal ou jurisprudencial indicado, a redação vigente é a referência final.",
        "fgv": "A FGV gosta de trocar elementos próximos: direito por garantia, competência por atribuição, capacidade por personalidade, prescrição por decadência, validade por eficácia. Leia verbos normativos e exceções com atenção.",
        "boundary": "A explicação não autoriza estudar ramos ou capítulos não mencionados no Anexo I. O conteúdo complementar serve para compreender os institutos expressamente listados e suas distinções indispensáveis.",
    },
    "penal-processual": {
        "name": "Direito Penal e Direito Processual Penal",
        "reasoning": "Separe Direito Penal material de Processo Penal. No Penal, organize fato típico, ilicitude, culpabilidade, formas de realização e consequência. No Processo, organize investigação, ação, prova, cautelares, procedimento, sujeitos e validade dos atos.",
        "application": "Em cada caso, destaque verbo de conduta, resultado, elemento subjetivo, circunstância e momento procedimental. Em leis especiais, confira sujeito, finalidade específica, conduta e consequência previstas no texto vigente.",
        "fgv": "A FGV explora precisão terminológica. Tentativa, desistência voluntária, arrependimento eficaz, crime impossível, dolo, culpa, prisão, cautelar, prova e nulidade possuem pressupostos próprios; trocar o nome sem conferir requisitos costuma ser a armadilha.",
        "boundary": "Não acrescente crimes, procedimentos ou leis especiais que o edital não trouxe. O aprofundamento deve ocorrer dentro dos institutos e diplomas expressamente listados, incluindo suas alterações vigentes quando o próprio edital assim exige.",
    },
    "administracao-politicas": {
        "name": "Administração e Políticas Públicas",
        "reasoning": "Não memorize apenas definições. Para cada conceito, saiba finalidade, componentes, momento de uso, vantagem, limitação e diferença para ferramentas próximas. Isso transforma uma lista de termos em um sistema compreensível.",
        "application": "Converta conceitos em decisões: que estrutura usar, que indicador observar, em que etapa do ciclo de políticas públicas está o problema, que ferramenta de planejamento ajuda e que resultado se pretende acompanhar.",
        "fgv": "A FGV pode descrever uma situação sem citar o nome do conceito. Reconheça sinais de planejamento, organização, liderança, controle, estratégia, implementação, monitoramento ou avaliação antes de olhar as alternativas.",
        "boundary": "O edital traz amplitude, mas não exige formação completa em Administração, Economia ou Estatística. A expansão aprofunda os conceitos indicados sem criar disciplinas autônomas além deles.",
    },
    "area-atuacao": {
        "name": "Conhecimentos na Área de Atuação",
        "reasoning": "Organize o conteúdo pela lógica prevenção → identificação do risco → comunicação → proteção → resposta → registro/encaminhamento. Em segurança e atendimento, sequência e finalidade são tão importantes quanto o nome do procedimento.",
        "application": "Analise cenários teóricos: qual risco existe, qual objetivo de proteção, qual prioridade, quem precisa ser comunicado, que erro aumenta o perigo e qual princípio do edital orienta a resposta. O estudo é conceitual, não substitui treinamento operacional.",
        "fgv": "A banca pode apresentar situações práticas e perguntar pela conduta conceitualmente mais adequada. Alternativas absolutas, improvisadas ou que ignoram comunicação, cadeia de comando, segurança do local e redução de risco merecem atenção.",
        "boundary": "Nada aqui deve ser interpretado como instrução operacional real. A expansão permanece acadêmica e teórica, limitada aos temas de segurança, risco, incidentes, incêndio, primeiros atendimentos e inteligência citados no edital.",
    },
    "legislacao": {
        "name": "Legislação",
        "reasoning": "Em legislação, comece pela finalidade e pelo campo de aplicação da norma. Depois organize sujeitos, competências, direitos, deveres, proibições, procedimentos, exceções e consequências. Verbos como 'deve', 'poderá', 'compete' e 'é vedado' mudam o gabarito.",
        "application": "Use o resumo para compreender e a lei seca vigente para confirmar. Faça quadros comparativos entre diplomas apenas quando o edital listar ambos. Marque prazos, competências, condições, exceções e palavras restritivas.",
        "fgv": "A FGV costuma alterar uma palavra da norma, inverter competência, ampliar hipótese restrita ou tornar obrigatório o que era facultativo. Questões de lei seca exigem leitura literal, mas compreensão do instituto reduz a dependência de memorização cega.",
        "boundary": "Somente diplomas, partes da Lei Orgânica, Código Tributário e normas municipais/federais expressamente mencionadas no edital entram como conteúdo. Referências externas servem apenas para explicar termos internos desses diplomas.",
    },
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", str(text)).strip()


def scope_units(scope: str) -> list[str]:
    raw = clean(scope)
    units = [clean(x) for x in re.split(r";|\.(?:\s+|$)", raw) if clean(x)]
    if len(units) == 1:
        comma = [clean(x) for x in raw.split(",") if clean(x)]
        if 2 <= len(comma) <= 12:
            units = comma
    return units or [raw]


def short_title(point: str, index: int) -> str:
    head = re.split(r"[.;:]", clean(point))[0]
    if len(head) > 88:
        head = head[:85].rstrip() + "..."
    return f"Subtópico {index}: {head}"


def block(title: str, *, body: str | None = None, items: list[str] | None = None):
    row = {"title": title}
    if body:
        row["body"] = clean(body)
    if items:
        row["items"] = [clean(x) for x in items]
    return row


def page(page_id: str, title: str, scope: str, blocks: list[dict], *, kind: str = "teoria"):
    return {
        "id": page_id,
        "title": title,
        "kind": kind,
        "sourceType": "edital-explicado",
        "sourceScope": scope,
        "editalBasis": f"Desenvolvimento didático estritamente vinculado ao recorte oficial: {scope}",
        "scopeBoundary": "Se um assunto não puder ser ligado a este recorte oficial, ele não integra esta página como matéria de prova.",
        "blocks": blocks,
    }


def expand_point(topic_label: str, scope: str, point: str, subject_id: str, idx: int) -> dict:
    lens = SUBJECT_LENS[subject_id]
    p = clean(point)
    explanation = (
        f"O núcleo deste subtópico é: {p} Para estudar de verdade, não basta decorar essa frase. "
        f"Separe o que é conceito principal, quais condições ou relações aparecem e qual consequência decorre delas. "
        f"Em {topic_label}, a pergunta central é reconhecer quando o enunciado apresenta esse fenômeno e quando apenas usa palavras parecidas sem preencher seus elementos. "
        "Explique o ponto em voz alta como se ensinasse alguém que nunca viu a matéria; se precisar repetir a definição sem conseguir exemplificar, ainda falta compreensão."
    )
    anatomy = (
        f"Faça uma leitura em camadas. Primeira camada: identifique o termo ou relação principal contido em '{p}'. "
        "Segunda: procure elementos necessários, limites, exceções ou condições. Terceira: compare com o conceito vizinho que mais poderia ser confundido. "
        "Quarta: formule um exemplo positivo e um contraexemplo. Quinta: transforme o conteúdo em uma pergunta objetiva com cinco alternativas. "
        "Esse processo força compreensão e revela exatamente onde uma alternativa de prova pode distorcer o assunto."
    )
    application = (
        f"{lens['application']} Neste subtópico, use como ponto de partida a afirmação '{p}'. "
        "Crie pelo menos três situações: uma em que o conceito se aplica claramente, uma em que não se aplica e uma situação-limite em que um detalhe decide a resposta. "
        "Depois justifique cada classificação sem consultar o material. A justificativa vale mais do que acertar por reconhecimento visual."
    )
    fgv = (
        f"{lens['fgv']} Para este subtópico, compare cada alternativa com os elementos presentes em '{p}'. "
        "Procure especialmente troca de sujeito, condição, intensidade, relação causal, finalidade, momento de aplicação ou efeito. "
        "Uma alternativa pode usar quase todas as palavras corretas e ainda ser falsa por deslocar apenas um desses elementos."
    )
    boundary = (
        f"Este aprofundamento decorre do item oficial '{scope}'. {lens['boundary']} "
        "Se durante o estudo aparecer um conceito auxiliar, ele deve ser usado somente para esclarecer este ponto e não para abrir uma nova frente de conteúdo fora do Anexo I."
    )
    return page(
        f"subtopic-{idx}", short_title(p, idx), scope,
        [
            block("1. Entenda o conceito sem decorar", body=explanation),
            block("2. Desmonte o conceito em partes", body=anatomy),
            block("3. Como aplicar em questão", body=application),
            block("4. Como a FGV pode distorcer", body=fgv),
            block("5. Limite exato do edital", body=boundary),
            block("6. Teste de domínio", items=[
                f"Explique com suas palavras por que '{p}' pertence a {topic_label}.",
                "Crie um exemplo que satisfaz o conceito e um contraexemplo que parece parecido, mas não satisfaz.",
                "Aponte a palavra ou condição que mais provavelmente seria trocada em uma alternativa errada.",
                "Responda: que informação mínima eu precisaria encontrar no enunciado para reconhecer este subtópico?",
                "Volte ao recorte oficial e confirme que sua explicação não abriu conteúdo independente além dele.",
            ]),
        ]
    )


def intro_page(topic: dict, subject_id: str, points: list[str]) -> dict:
    scope = topic["officialScope"]
    lens = SUBJECT_LENS[subject_id]
    units = scope_units(scope)
    return page(
        "mapa-edital", "Página 1 — Mapa do edital e fronteira do assunto", scope,
        [
            block("Recorte literal do edital", body=scope),
            block("O que você precisa conseguir fazer", body=(
                f"Ao terminar {topic['label']}, você deve reconhecer o assunto mesmo quando a banca não repetir o título do edital, explicar os conceitos com linguagem simples, distinguir ideias próximas e aplicar o conteúdo a situações de prova. "
                f"A matéria pertence a {lens['name']}; portanto, a forma de raciocinar deve respeitar a natureza dessa disciplina. {lens['reasoning']}"
            )),
            block("Partes visíveis no próprio recorte", items=units),
            block("Núcleos que serão desenvolvidos", items=[f"{i+1}. {clean(p)}" for i, p in enumerate(points)]),
            block("Regra de rastreabilidade", body=(
                "Todas as páginas seguintes repetem este mesmo recorte oficial. Os exemplos, comparações e explicações são material didático autoral para tornar o item compreensível; eles não criam um novo tópico de edital. "
                "Quando uma norma, fórmula ou regra formal for relevante, a referência vigente e expressamente indicada no edital prevalece sobre qualquer resumo."
            )),
            block("Como estudar este capítulo", items=[
                "Leia uma página por vez e feche o texto antes de tentar explicar.",
                "Anote apenas regra, diferença, fórmula, artigo ou erro que você realmente confundiu.",
                "Faça questões após cada bloco relevante, não apenas depois de terminar todo o capítulo.",
                "Marque dúvidas pelo nome do subtópico para revisar de forma específica.",
                "Ao final, releia somente o recorte literal do edital e tente reconstruir mentalmente tudo que foi estudado.",
            ]),
        ]
    )


def connection_page(topic: dict, subject_id: str, points: list[str]) -> dict:
    scope = topic["officialScope"]
    lens = SUBJECT_LENS[subject_id]
    comparisons = []
    for i, p in enumerate(points):
        q = points[(i + 1) % len(points)]
        comparisons.append(
            f"Compare o núcleo {i+1} com o núcleo {(i+1)%len(points)+1}: '{clean(p)}' versus '{clean(q)}'. "
            "Defina o que pertence a cada um, onde eles se relacionam e qual detalhe impede tratá-los como sinônimos."
        )
    return page(
        "conexoes", "Conexões, diferenças e visão de conjunto", scope,
        [
            block("Por que conectar os subtópicos", body=(
                f"Questões difíceis raramente cobram uma definição isolada de {topic['label']}. Elas misturam conceitos próximos e exigem que você identifique a fronteira entre eles. "
                "A meta desta página é transformar pontos soltos em uma rede coerente, sem sair do que o edital listou."
            )),
            block("Comparações obrigatórias", items=comparisons),
            block("Método de comparação", body=(
                "Para cada par, preencha mentalmente cinco campos: definição, finalidade, condição de uso, efeito e erro típico. Se dois conceitos parecerem iguais, procure qual desses campos muda. "
                "Em Direito, a diferença pode estar em requisito ou efeito; em Português, na relação de sentido; em RLM, na operação ou hipótese; em Informática, na finalidade do recurso; em Administração, no momento de aplicação."
            )),
            block("Leitura de prova", body=(
                f"{lens['fgv']} Quando uma alternativa combinar dois núcleos corretos, verifique se a relação entre eles também está correta. "
                "A banca pode montar uma frase com começo verdadeiro e final falso; por isso, avalie cada afirmação inteira e não apenas palavras familiares."
            )),
            block("Exercício de síntese", items=[
                "Faça um quadro de duas colunas com os conceitos que você mais confunde.",
                "Escreva uma diferença objetiva entre cada par.",
                "Crie uma alternativa falsa trocando somente um elemento e depois explique por que ficou falsa.",
                "Volte ao edital e confira se todas as colunas continuam vinculadas ao recorte oficial.",
            ]),
        ]
    )


def fgv_page(topic: dict, subject_id: str, points: list[str]) -> dict:
    scope = topic["officialScope"]
    lens = SUBJECT_LENS[subject_id]
    return page(
        "fgv", "Treino de banca: leitura, armadilhas e decisão entre alternativas", scope,
        [
            block("O padrão de dificuldade", body=(
                f"Em {topic['label']}, não espere que a questão necessariamente repita a definição estudada. {lens['fgv']} "
                "A dificuldade cresce quando todas as alternativas têm vocabulário técnico plausível. Nessa situação, volte aos elementos do conceito e elimine uma alternativa por vez, sempre com justificativa."
            )),
            block("Roteiro de 7 passos", items=[
                "1. Leia primeiro o comando e identifique exatamente o que deve ser julgado.",
                "2. Circule mentalmente palavras absolutas, restritivas, negativas e condicionais.",
                "3. Nomeie o subtópico do edital antes de olhar as alternativas.",
                "4. Recupere a regra ou relação central com suas próprias palavras.",
                "5. Elimine alternativas que acrescentam condição inexistente ou retiram condição necessária.",
                "6. Entre duas alternativas, compare termo por termo e procure a menor diferença relevante.",
                "7. Na correção, registre por que a errada estava errada; não anote apenas a letra do gabarito.",
            ]),
            block("Armadilhas universais", items=[
                "Trocar possibilidade por certeza ou faculdade por obrigação.",
                "Inverter causa e consequência, regra e exceção, sujeito e objeto, entrada e saída.",
                "Generalizar uma hipótese específica para todos os casos.",
                "Usar conceito verdadeiro de outro subtópico para responder ao tópico atual.",
                "Inserir palavra tecnicamente correta em relação logicamente errada.",
                "Omitir condição indispensável e apresentar a consequência como automática.",
            ]),
            block("Aplicação aos núcleos desta aula", items=[
                f"Para '{clean(p)}', escreva uma alternativa correta e duas erradas por alteração mínima. Depois destaque exatamente a palavra que tornou cada uma errada."
                for p in points
            ]),
            block("Critério para avançar", body=(
                "Só considere este tópico estável quando conseguir justificar alternativas sem depender de sensação de familiaridade. Uma boa meta é atingir pelo menos 80% em duas sessões separadas e, principalmente, explicar os erros sem consultar o gabarito comentado."
            )),
        ], kind="estrategia"
    )


def review_page(topic: dict, subject_id: str, points: list[str]) -> dict:
    scope = topic["officialScope"]
    lens = SUBJECT_LENS[subject_id]
    return page(
        "revisao", "Revisão ativa e fechamento do tópico", scope,
        [
            block("Reconstrução sem consulta", body=(
                f"Feche todas as páginas e explique {topic['label']} por cinco a dez minutos. Comece pelo recorte do edital, enumere os núcleos estudados e reconstrua as diferenças mais importantes. "
                "Depois abra o material e marque somente o que ficou ausente ou incorreto. Essa comparação mostra o que realmente precisa de revisão."
            )),
            block("Perguntas de recuperação", items=[
                f"O que significa, em termos simples, o núcleo: {clean(p)}?" for p in points
            ] + [
                "Quais dois conceitos deste tópico são mais fáceis de confundir e qual é a diferença decisiva?",
                "Que palavra em uma alternativa poderia inverter a regra ou alterar o alcance da afirmação?",
                "Que exemplo eu consigo construir sem copiar o material?",
                "Qual parte eu ainda explico de forma vaga? Essa é a prioridade da próxima revisão.",
            ]),
            block("Plano de revisão", items=[
                "Revisão 1: no dia seguinte, 10–15 minutos de recuperação ativa.",
                "Revisão 2: aproximadamente 7 dias depois, questões + caderno de erros.",
                "Revisão 3: aproximadamente 30 dias depois, questões mistas e comparação entre conceitos.",
                "Reta final: revise erros reais e pontos de baixa taxa de acerto, não releia tudo indiscriminadamente.",
            ]),
            block("Limite final do conteúdo", body=(
                f"O teto desta aula continua sendo: {scope} {lens['boundary']} "
                "Se um material externo entrar em detalhes que não ajudam a explicar esses itens, trate-o como conteúdo excedente e não sacrifique tempo do cronograma por ele."
            )),
            block("Saída para exercícios", body=(
                "Depois desta revisão, faça um bloco de questões exclusivamente do tópico e outro bloco misturando a disciplina. O primeiro verifica domínio local; o segundo verifica se você consegue identificar o assunto sem receber o rótulo previamente."
            )),
        ], kind="revisao"
    )


def main():
    lessons = load(LESSONS_PATH)
    syllabus = load(SYLLABUS_PATH)
    topic_map = {}
    for subject in syllabus["subjects"]:
        for topic in subject["topics"]:
            topic_map[topic["id"]] = (subject["id"], topic)

    if set(topic_map) != set(K):
        missing = sorted(set(topic_map) - set(K))
        extra = sorted(set(K) - set(topic_map))
        raise SystemExit(f"Mapa específico não coincide com os 116 tópicos. missing={missing} extra={extra}")

    total_chars = 0
    total_pages = 0
    for lesson in lessons:
        subject_id, topic = topic_map[lesson["topicId"]]
        points = [clean(x) for x in K[topic["id"]]]
        scope = topic["officialScope"]

        pages = [intro_page(topic, subject_id, points)]
        pages.extend(expand_point(topic["label"], scope, point, subject_id, i + 1) for i, point in enumerate(points))
        pages.append(connection_page(topic, subject_id, points))
        pages.append(fgv_page(topic, subject_id, points))
        pages.append(review_page(topic, subject_id, points))

        page_chars = len(json.dumps(pages, ensure_ascii=False))
        theory_minutes = max(190, 24 * len(pages) + min(50, page_chars // 1800))
        practice_minutes = 45 if subject_id in {"legislacao", "penal-processual", "constitucional-civil", "rlm"} else 35

        lesson["studyPages"] = pages
        lesson["subtopics"] = [p["title"] for p in pages if p["id"].startswith("subtopic-")]
        lesson["pageCount"] = len(pages)
        lesson["contentCharacters"] = page_chars
        lesson["depth"] = "concurso-apostila-v5"
        lesson["theoryMinutes"] = theory_minutes
        lesson["practiceMinutes"] = practice_minutes
        lesson["estimatedMinutes"] = theory_minutes + practice_minutes
        lesson["summary"] = (
            f"Apostila guiada de {topic['label']} com {len(pages)} páginas internas e rastreabilidade ao Anexo I. "
            f"O recorte oficial permanece: {scope}"
        )
        lesson["scopeTraceability"] = {
            "mode": "exact-official-scope",
            "officialScope": scope,
            "noticePages": "49-53",
            "rule": "Cada página deve permanecer explicável pelo recorte oficial; desenvolvimento didático não cria novo item de edital.",
        }
        total_chars += page_chars
        total_pages += len(pages)

    LESSONS_PATH.write_text(json.dumps(lessons, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Apostila V5 aplicada a {len(lessons)} aulas.")
    print(f"Páginas internas: {total_pages}")
    print(f"Caracteres de conteúdo paginado: {total_chars}")
    print(f"Média por tópico: {round(total_chars / len(lessons))} caracteres")


if __name__ == "__main__":
    main()
