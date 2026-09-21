#!/usr/bin/env python3
"""Orquestrador da base V3 de estudo.

Objetivos:
- manter exatamente os 116 tópicos da matriz oficial;
- gerar pelo menos 2.650 questões válidas;
- impedir alternativas duplicadas mesmo após normalização;
- transformar cada aula curta em um módulo de estudo guiado com profundidade de concurso.

A expansão não cria tópicos fora do edital. O aprofundamento organiza e explica
os conceitos curados em expand_bank_v2.py e o officialScope do syllabus.
"""
from __future__ import annotations

import re
import unicodedata

import expand_bank_v2 as base


_original_make_concept_questions = base.make_concept_questions
_original_enrich_lessons = base.enrich_lessons


def _norm_option(text: str) -> str:
    value = unicodedata.normalize("NFKD", str(text))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"\s+", " ", value.lower()).strip(" .;,:-")
    return value


def safe_place_answer(correct: str, distractors: list[str]) -> tuple[list[str], int]:
    """Garante cinco alternativas realmente diferentes após normalização."""
    options: list[str] = []
    seen: set[str] = set()

    for value in [correct, *distractors]:
        if not value:
            continue
        key = _norm_option(value)
        if not key or key in seen:
            continue
        seen.add(key)
        options.append(str(value))

    filler_no = 1
    while len(options) < 5:
        filler = f"Afirmação incompatível com o conceito estudado ({filler_no})"
        filler_no += 1
        key = _norm_option(filler)
        if key in seen:
            continue
        seen.add(key)
        options.append(filler)

    options = options[:5]
    base.RNG.shuffle(options)
    return options, options.index(correct)


# Corrige também todas as rotinas internas que usam place_answer.
base.place_answer = safe_place_answer


SUBJECT_STUDY_TIME = {
    "portugues": 50,
    "rlm": 60,
    "informatica": 45,
    "constitucional-civil": 65,
    "penal-processual": 70,
    "administracao-politicas": 55,
    "area-atuacao": 55,
    "legislacao": 65,
}

SUBJECT_METHOD = {
    "portugues": [
        "Comece pelo sentido do texto ou da frase; depois aplique a regra gramatical.",
        "Identifique palavras que mudam a relação lógica: mas, embora, porque, portanto, se, apenas, sempre, pode, deve.",
        "Compare as alternativas palavra por palavra e elimine as que exageram, restringem ou alteram o sentido.",
        "Em gramática, localize primeiro a função da palavra na frase; decorar nome isolado é insuficiente para prova.",
    ],
    "rlm": [
        "Traduza o enunciado para uma representação simples: conta, tabela, desenho, equação ou relação lógica.",
        "Anote dados, unidade e exatamente o que a questão pede antes de calcular.",
        "Resolva em etapas curtas e confira o resultado substituindo-o no problema sempre que possível.",
        "Separe erro de interpretação de erro de cálculo no caderno de erros; eles exigem correções diferentes.",
    ],
    "informatica": [
        "Associe cada recurso à sua finalidade, ao local onde costuma aparecer e ao efeito produzido.",
        "Diferencie formato de arquivo, programa, comando e função. A banca costuma misturar essas categorias nas alternativas.",
        "Nos aplicativos, imagine a ação prática: abrir, salvar, localizar, proteger, filtrar, ordenar, importar, exportar ou imprimir.",
        "Em segurança, pergunte qual risco existe, qual mecanismo reduz esse risco e qual limitação permanece.",
    ],
    "constitucional-civil": [
        "Descubra primeiro qual ramo e qual instituto a questão está cobrando; só depois analise requisitos e efeitos.",
        "Monte pares de contraste: regra/exceção, capacidade/incapacidade, direito/dever, pessoa/bem, validade/invalidade, prescrição/decadência.",
        "Quando o tópico depender de texto normativo ou jurisprudência, use a redação vigente como referência final.",
        "Treine casos curtos: quem é o sujeito, qual fato ocorreu, qual norma/instituto se aplica e qual consequência jurídica resulta.",
    ],
    "penal-processual": [
        "Separe Direito Penal material de Processo Penal: crime e pena são uma coisa; investigação, prova, prisão e procedimento são outra.",
        "Para cada instituto, identifique conceito, requisitos, momento de aplicação, consequência e principal distinção de institutos próximos.",
        "Em tipos penais e leis especiais, não complete o texto por intuição: elementos e finalidades específicas mudam o gabarito.",
        "Em Processo Penal, organize mentalmente a sequência: fato, investigação, ação, prova, cautelares, procedimento e decisão.",
    ],
    "administracao-politicas": [
        "Para cada conceito, saiba definição, finalidade, componentes, exemplo e diferença para o conceito mais parecido.",
        "Em Administração, identifique se a questão trata de estrutura, pessoas, estratégia, processo, finanças ou controle.",
        "Em Políticas Públicas, localize a etapa do ciclo e diferencie formulação, implementação, monitoramento e avaliação.",
        "Ligue indicadores e evidências à decisão que eles ajudam a tomar; isso evita decorar termos sem compreender a função.",
    ],
    "area-atuacao": [
        "Estude a lógica de prevenção antes da reação: reconhecer risco, comunicar, proteger, controlar o ambiente e acionar resposta adequada.",
        "Organize procedimentos em sequência e identifique objetivo, risco evitado e ponto de falha de cada etapa.",
        "Em incidentes e atendimento, valorize comunicação clara, cadeia de comando, segurança do local e redução de tensão.",
        "O módulo é teórico para concurso: não transforme a leitura em improvisação operacional fora de treinamento oficial.",
    ],
    "legislacao": [
        "Comece pela finalidade da norma e pelo assunto que ela disciplina; depois avance para competências, direitos, deveres, proibições e consequências.",
        "Monte um quadro Lei/tema/palavras-chave para não confundir diplomas federais e municipais.",
        "Quando houver texto legal expresso, a redação vigente prevalece sobre resumo. Use o resumo para compreender e a lei seca para confirmar.",
        "Marque exceções, prazos, sujeitos, competências e verbos normativos como deve, poderá, é vedado e compete.",
    ],
}

SUBJECT_TECHNICAL = {
    "portugues": "A FGV costuma exigir leitura fina de relações de sentido. Uma alternativa pode parecer correta e ainda estar errada por trocar possibilidade por certeza, causa por consequência, concessão por oposição ou referência por opinião externa.",
    "rlm": "O resultado numérico é a última etapa. O núcleo da questão costuma estar em modelar corretamente a situação, reconhecer a relação entre grandezas e manter unidades e condições consistentes.",
    "informatica": "Questões de informática frequentemente descrevem uma tarefa prática e oferecem comandos parecidos. O estudo precisa ligar nome, função, entrada, saída e efeito do recurso, não apenas memorizar siglas.",
    "constitucional-civil": "O nível de concurso exige reconhecer o instituto em um caso concreto e separar conceitos próximos. Texto constitucional, legislação civil e jurisprudência indicada no edital devem ser tratados como fontes distintas.",
    "penal-processual": "A precisão vocabular é decisiva: dolo, culpa, tentativa, desistência, excludente, ação penal, prova, cautelar e nulidade não são rótulos intercambiáveis. Cada instituto possui pressupostos e efeitos próprios.",
    "administracao-politicas": "A banca pode cobrar tanto conceito quanto aplicação. Saber para que serve uma ferramenta, em qual etapa é usada e qual decisão ela apoia é mais seguro do que decorar definições soltas.",
    "area-atuacao": "O conteúdo reúne segurança, atendimento, risco, incidentes, incêndio, socorrismo e inteligência. A compreensão deve seguir princípios de prevenção, organização, comunicação e resposta dentro dos limites do conteúdo teórico do edital.",
    "legislacao": "Em legislação, detalhes de redação importam. O módulo deve criar compreensão suficiente para a leitura da lei seca, mas não substituir a conferência da versão oficial vigente antes da prova.",
}

# Fórmulas/procedimentos úteis apenas nos tópicos em que o edital os pede.
TOPIC_TOOLBOX = {
    "proposicoes": ["Conjunção P∧Q: só é verdadeira se P e Q forem verdadeiras.", "Disjunção inclusiva P∨Q: só é falsa se P e Q forem falsas.", "Condicional P→Q: só é falsa quando P é verdadeira e Q é falsa."],
    "equivalencias": ["P→Q ≡ ¬P∨Q.", "Contrapositiva: P→Q ≡ ¬Q→¬P.", "De Morgan: ¬(P∧Q) ≡ ¬P∨¬Q e ¬(P∨Q) ≡ ¬P∧¬Q."],
    "porcentagem-proporcao": ["p% de V = (p/100)×V.", "Aumento percentual = (aumento/valor inicial)×100%.", "Na proporcionalidade inversa ideal, o produto das grandezas correspondentes permanece constante."],
    "algebra": ["Em equação do 1º grau, faça a mesma operação nos dois membros até isolar a incógnita.", "Em sistema 2×2, substituição e adição/eliminações são métodos usuais; confira o par nas duas equações."],
    "sequencias-pa-pg": ["PA: a_n = a_1 + (n-1)r.", "PG: a_n = a_1·q^(n-1).", "Antes de usar fórmula, confirme se a diferença (PA) ou razão multiplicativa (PG) é realmente constante."],
    "juros": ["Juros simples: J=C·i·t e M=C+J.", "Juros compostos: M=C·(1+i)^t.", "Taxa e tempo precisam estar na mesma unidade temporal."],
    "geometria-basica": ["Retângulo: A=b·h e P=2(b+h).", "Quadrado: A=l² e P=4l.", "Triângulo: A=(b·h)/2. Circunferência: comprimento 2πr e área do círculo πr²."],
    "semelhanca-triangulo": ["Semelhança: lados correspondentes mantêm a mesma razão.", "Pitágoras no triângulo retângulo: h²=a²+b²."],
    "medidas-area-volume": ["Conversões de área usam fator ao quadrado; de volume, fator ao cubo.", "Paralelepípedo retângulo: V=comprimento×largura×altura."],
    "contagem-probabilidade": ["Princípio multiplicativo: etapas independentes sucessivas → multiplicar quantidades de escolhas.", "Em casos equiprováveis: P(A)=casos favoráveis/casos possíveis."],
    "excel": ["Fórmulas normalmente começam por '='.", "Referência de célula identifica posição como A1; copiar fórmula pode alterar referências relativas.", "Filtro restringe visualização por critérios; ordenação reorganiza registros segundo uma chave."],
    "internet-seguranca": ["Upload envia dados; download recebe dados.", "Senha forte reduz adivinhação, mas não substitui autenticação adicional e cuidados contra phishing.", "Criptografia protege dados por transformação controlada com algoritmos/chaves; não é sinônimo de backup."],
    "leg-guardas": ["Lei 13.022/2014: caráter civil das guardas municipais e competência geral de proteção municipal dentro dos limites legais.", "Estude princípios mínimos, competências e relação com a proteção de bens, serviços, logradouros e instalações municipais."],
    "leg-abuso": ["Na Lei 13.869/2019, a finalidade específica prevista no tipo é elemento relevante; mera divergência de interpretação da lei ou avaliação de fatos/provas não configura abuso por si só."],
}


def _section_map(lesson: dict) -> dict[str, dict]:
    return {section.get("title", ""): section for section in lesson.get("sections", [])}


def deep_enrich_lessons(lessons: list[dict], topics: dict[str, dict], subjects: dict[str, dict]) -> None:
    """Transforma resumos em módulos guiados com duração compatível com estudo real."""
    _original_enrich_lessons(lessons, topics, subjects)

    for lesson in lessons:
        topic = topics.get(lesson["topicId"])
        if not topic:
            continue
        subject_id = topic["subjectId"]
        facts = [fact for fact in base.all_facts(topic) if fact[0] != "recorte oficial do edital"]
        scope_parts = base.split_scope(topic["officialScope"]) or [topic["officialScope"]]

        complexity_bonus = min(20, max(0, (len(scope_parts) - 1) * 5))
        theory_minutes = SUBJECT_STUDY_TIME[subject_id] + complexity_bonus
        question_minutes = 25 if subject_id not in {"penal-processual", "legislacao", "constitucional-civil"} else 35
        lesson["estimatedMinutes"] = theory_minutes + question_minutes
        lesson["theoryMinutes"] = theory_minutes
        lesson["practiceMinutes"] = question_minutes
        lesson["depth"] = "concurso-aprofundado-v3"

        concept_paragraphs = []
        distinction_items = []
        worked_items = []
        for idx, (term, definition, example) in enumerate(facts, start=1):
            concept_paragraphs.append(
                f"{idx}. {term}: {definition}. Não trate isso como uma definição para decorar isoladamente. "
                f"Pergunte qual problema o conceito resolve, como ele aparece no enunciado e o que o diferencia dos conceitos próximos."
            )
            worked_items.append(
                f"Exemplo {idx}: {example}. Ao resolver uma questão com situação semelhante, identifique primeiro o indício que liga o caso a '{term}' e só depois escolha a alternativa."
            )

        if len(facts) >= 2:
            distinction_items.append(
                f"Compare '{facts[0][0]}' com '{facts[1][0]}': o primeiro significa {facts[0][1]}; o segundo significa {facts[1][1]}. "
                "Se a alternativa trocar essas funções, ela deve ser descartada."
            )
        distinction_items.append(SUBJECT_TECHNICAL[subject_id])

        deep_sections = [
            {
                "title": "Como usar esta aula",
                "body": (
                    f"Reserve cerca de {theory_minutes} minutos para teoria e {question_minutes} minutos para prática. "
                    "Leia uma seção de cada vez, feche o material e tente explicar com suas palavras antes de avançar. "
                    "Se não conseguir explicar sem repetir a frase decorada, o conceito ainda não foi compreendido."
                ),
            },
            {
                "title": "Objetivo da aula",
                "body": (
                    f"Ao terminar {topic['label']}, você deve conseguir reconhecer o assunto em uma questão, explicar os conceitos centrais, "
                    "aplicar o conteúdo a um exemplo e eliminar alternativas que saem do recorte oficial. "
                    f"O edital exige: {topic['officialScope']}."
                ),
            },
            {
                "title": "Fundamentos explicados passo a passo",
                "items": concept_paragraphs,
            },
            {
                "title": "Método de resolução",
                "items": SUBJECT_METHOD[subject_id],
            },
            {
                "title": "Exemplos comentados",
                "items": worked_items,
            },
            {
                "title": "Diferenças que a banca pode explorar",
                "items": distinction_items,
            },
            {
                "title": "Conteúdo técnico para memorizar depois de compreender",
                "items": TOPIC_TOOLBOX.get(topic["id"], [
                    f"Termo central: {term} — {definition}" for term, definition, _ in facts
                ]),
            },
            {
                "title": "Checklist antes de fazer exercícios",
                "items": [
                    f"Consigo explicar {topic['label']} sem olhar o resumo.",
                    "Consigo dar pelo menos um exemplo correto e um exemplo que não pertence ao conceito.",
                    "Consigo diferenciar os conceitos centrais sem depender das alternativas.",
                    "Consigo apontar quais palavras do enunciado mudariam o resultado da questão.",
                    "Se houver lei, fórmula ou regra expressa, sei onde confirmá-la e quais elementos preciso memorizar.",
                ],
            },
            {
                "title": "Prática obrigatória",
                "body": (
                    f"Depois da teoria, faça de 20 a {max(25, base.TARGETS[subject_id])} questões deste tópico. "
                    "Na correção, não registre apenas a letra correta: escreva em uma frase por que sua alternativa estava errada. "
                    "Refaça os erros em outro dia e busque pelo menos 80% de acertos em duas sessões separadas."
                ),
            },
        ]

        old = _section_map(lesson)
        # Mantém o mapa exato do edital e os blocos úteis anteriores, mas coloca
        # primeiro a sequência didática mais completa.
        preserved_titles = ["Mapa exato do edital", "Armadilha de prova", "Meta de domínio", "Revisão ativa"]
        preserved = [old[t] for t in preserved_titles if t in old]
        lesson["sections"] = deep_sections + preserved
        lesson["summary"] = (
            f"Módulo aprofundado de {topic['label']}, limitado ao conteúdo oficial: {topic['officialScope']}. "
            f"Tempo planejado: aproximadamente {theory_minutes} min de teoria + {question_minutes} min de prática."
        )
        lesson.setdefault("source", {})["note"] = (
            "Organização didática baseada no recorte do Anexo I. Conceitos adicionais exibidos nesta aula vêm da curadoria interna do projeto; "
            "quando houver legislação, a redação oficial vigente deve ser a referência final."
        )


base.enrich_lessons = deep_enrich_lessons


def make_concept_questions_with_margin(subject, topic, topics):
    rows = _original_make_concept_questions(subject, topic, topics)
    facts = base.all_facts(topic)
    other_terms = base.distractor_pool(subject, topics, 0, topic["id"])
    other_defs = base.distractor_pool(subject, topics, 1, topic["id"])
    other_examples = base.distractor_pool(subject, topics, 2, topic["id"])

    for fact_no, (term, definition, example) in enumerate(facts, start=1):
        variants = [
            (
                f"Ao revisar {topic['label']}, qual anotação sobre '{term}' está alinhada ao conteúdo estudado?",
                definition,
                base.RNG.sample(other_defs, 4),
                f"A anotação correta preserva o conceito de '{term}': {definition}.",
            ),
            (
                f"A situação '{example}' deve ser relacionada a qual conceito de {topic['label']}?",
                term,
                base.RNG.sample(other_terms, 4),
                f"O exemplo pertence a '{term}'.",
            ),
            (
                f"Qual exemplo abaixo permanece coerente com o estudo de '{term}' em {topic['label']}?",
                example,
                base.RNG.sample(other_examples, 4),
                f"O exemplo coerente é: {example}.",
            ),
        ]

        for variant_no, (stem, correct, wrong, explanation) in enumerate(variants, start=1):
            options, answer = base.place_answer(correct, wrong)
            rows.append({
                "id": f"v2x-{subject['id']}-{topic['id']}-{fact_no:02d}-{variant_no:02d}",
                "contestId": base.CONTEST_ID,
                "subjectId": subject["id"],
                "topicIds": [topic["id"]],
                "difficulty": "medium",
                "sourceType": "authorial",
                "sourceLabel": "Questão autoral focada no tópico do edital - não é questão oficial da FGV",
                "stem": stem,
                "options": options,
                "answerIndex": answer,
                "explanation": explanation,
                "tags": ["v3", "conteudo-topico", "margem-validacao"],
            })

    return rows


base.make_concept_questions = make_concept_questions_with_margin

if __name__ == "__main__":
    base.main()
